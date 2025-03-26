# app/langgraph_parser.py

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from langgraph.graph import StateGraph, END
from app.config import OPENAI_API_KEY

def detect_intent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect the intent of the user message using a language model.
    Args:
        state (Dict[str, Any]): Is a dictionary containing the user message.
    Returns:
        Dict[str, Any]: A dictionary containing the detected intent. 
    """
    llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, temperature=0)
    prompt = (
        "You are an intent detection system for a legal case management chatbot.\n"
        "Classify the following user message into one of the following intents:\n"
        "- 'create_case'\n"
        "- 'read_cases'\n"
        "- 'update_case'\n"
        "- 'delete_case'\n"
        "- 'general_question'\n\n"
        f"User message: \"{state['input']}\"\n"
        "Respond ONLY with the intent string."
    )
    result = llm([HumanMessage(content=prompt)])
    return {**state, "intent": result.content.strip()}


def extract_entities(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract entities from the user message using a language model
    Args:
        state (Dict[str, Any]): Is a dictionary containing the user message and the detected intent.
    Returns:
        Dict[str, Any]: A dictionary containing the extracted entities.
    """
    llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, temperature=0)
    prompt = (
        f"You are an entity extractor for the '{state['intent']}' intent in a legal case management chatbot.\n"
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
        f"User message: \"{state['input']}\""
    )
    result = llm([HumanMessage(content=prompt)])
    try:
        extracted = eval(result.content.strip())
        return {**state, "entities": extracted}
    except Exception:
        return {**state, "entities": {}}


def route_action(state: Dict[str, Any]) -> str:
    """
    Route the action based on the detected intent.
    Args:
        state (Dict[str, Any]): The current state of the conversation. It contains the detected intent.        
    Returns:
        str: The name of the next node in the state graph.
    """
    intent = state.get("intent")
    if intent in {"create_case", "read_cases", "update_case", "delete_case"}:
        return intent
    return "general_question"


def pass_through(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    A pass-through function that does nothing. It is not implemented because we separate the crud operations in different functions.
    Args:
        state (Dict[str, Any]): The current state of the conversation.
    Returns:
        Dict[str, Any]: The same state dictionary.
    """
    return state


# ==================================
# Define the state graph
graph_builder = StateGraph(Dict[str, Any])

# Define the nodes and edges of the state graph
graph_builder.add_node("detect_intent", detect_intent)
graph_builder.add_node("extract_entities", extract_entities)
graph_builder.add_node("general_question", pass_through)
graph_builder.add_node("create_case", pass_through)
graph_builder.add_node("read_cases", pass_through)
graph_builder.add_node("update_case", pass_through)
graph_builder.add_node("delete_case", pass_through)

# Define the edges between the nodes
graph_builder.set_entry_point("detect_intent")
graph_builder.add_edge("detect_intent", "extract_entities")
# Route the action based on the detected intent
graph_builder.add_conditional_edges("extract_entities", route_action, {
    "create_case": "create_case",
    "read_cases": "read_cases",
    "update_case": "update_case",
    "delete_case": "delete_case",
    "general_question": "general_question"
})
# End the conversation after the CRUD operations
graph_builder.add_edge("create_case", END)
graph_builder.add_edge("read_cases", END)
graph_builder.add_edge("update_case", END)
graph_builder.add_edge("delete_case", END)
graph_builder.add_edge("general_question", END)

# Compile the state graph
graph = graph_builder.compile()


def parse_message(message: str) -> Dict[str, Any]:
    """
    Parse the user message using the state graph to detect the intent and extract entities.
    Args:
        message (str): The user message to be parsed.
    Returns:
        Dict[str, Any]: A dictionary containing the detected intent and extracted entities.
    """
    initial_state = {"input": message}
    final_state = graph.invoke(initial_state)
    return {
        "intent": final_state.get("intent"),
        "entities": final_state.get("entities", {})
    }