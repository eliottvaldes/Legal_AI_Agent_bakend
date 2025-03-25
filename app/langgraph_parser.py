# app/langgraph_parser.py

from typing import Dict, Any
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from langgraph.graph import StateGraph, END
from app.config import OPENAI_API_KEY

class ChatState:
    def __init__(self, user_input: str):
        self.input = user_input
        self.intent = None
        self.action = None
        self.entities = {}
        self.response = None


def detect_intent(state: ChatState) -> ChatState:
    llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, temperature=0)
    prompt = (
        "You are an intent detection system for a legal case management chatbot.\n"
        "Classify the following user message into one of the following intents:\n"
        "- 'create_case'\n"
        "- 'read_cases'\n"
        "- 'update_case'\n"
        "- 'delete_case'\n"
        "- 'general_question'\n\n"
        f"User message: \"{state.input}\"\n"
        "Respond ONLY with the intent string."
    )
    result = llm([HumanMessage(content=prompt)])
    state.intent = result.content.strip()
    return state


def extract_entities(state: ChatState) -> ChatState:
    llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, temperature=0)
    prompt = (
        f"You are an entity extractor for the '{state.intent}' intent in a legal case management chatbot.\n"
        "Extract all relevant entities from the user's message.\n"
        "Respond ONLY with a valid JSON object with the following structure when applicable:\n\n"
        "{\n"
        "  \"title\": string,\n"
        "  \"status\": string,\n"
        "  \"description\": string,\n"
        "  \"attorney\": string,\n"
        "  \"criteria\": string,\n"
        "  \"new_status\": string\n"
        "}\n\n"
        "Leave fields blank if not mentioned explicitly.\n"
        f"User message: \"{state.input}\""
    )
    result = llm([HumanMessage(content=prompt)])
    try:
        extracted = eval(result.content.strip())
        state.entities = extracted
    except Exception:
        state.entities = {}
    return state


def route_action(state: ChatState) -> str:
    if state.intent in {"create_case", "read_cases", "update_case", "delete_case"}:
        return state.intent
    return "general_question"


def pass_through(state: ChatState) -> ChatState:
    return state


graph_builder = StateGraph(ChatState)

graph_builder.add_node("detect_intent", detect_intent)
graph_builder.add_node("extract_entities", extract_entities)
graph_builder.add_node("general_question", pass_through)
graph_builder.add_node("create_case", pass_through)
graph_builder.add_node("read_cases", pass_through)
graph_builder.add_node("update_case", pass_through)
graph_builder.add_node("delete_case", pass_through)

graph_builder.set_entry_point("detect_intent")
graph_builder.add_edge("detect_intent", "extract_entities")
graph_builder.add_conditional_edges("extract_entities", route_action, {
    "create_case": "create_case",
    "read_cases": "read_cases",
    "update_case": "update_case",
    "delete_case": "delete_case",
    "general_question": "general_question"
})
graph_builder.add_edge("create_case", END)
graph_builder.add_edge("read_cases", END)
graph_builder.add_edge("update_case", END)
graph_builder.add_edge("delete_case", END)
graph_builder.add_edge("general_question", END)

graph = graph_builder.compile()


def parse_message(message: str) -> Dict[str, Any]:
    initial_state = ChatState(user_input=message)
    final_state = graph.invoke(initial_state)
    return {
        "intent": final_state.intent,
        "entities": final_state.entities
    }