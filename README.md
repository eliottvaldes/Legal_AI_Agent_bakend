# Legal Case Chat API

Este proyecto es un sistema de **gestión de casos legales** que expone una API tipo chat para crear, leer, actualizar o eliminar casos en una base de datos PostgreSQL, utilizando **FastAPI** y la **API de OpenAI** para generación dinámica de consultas SQL y respuestas.  

Además, se hace uso de la librería [`langgraph`](https://pypi.org/project/langgraph/) para construir flujos de estados (State Graphs) que permiten la **detección de intenciones** y la **extracción de entidades** de manera altamente flexible.

## Tabla de Contenido

- [Descripción General](#descripción-general)
- [Enfoque con `langgraph`](#enfoque-con-langgraph)
- [Arquitectura de la Aplicación](#arquitectura-de-la-aplicación)
- [Requerimientos](#requerimientos)
- [Instalación](#instalación)
- [Configuración (.env)](#configuración-env)
- [Ejecución del Servidor](#ejecución-del-servidor)
- [Uso de la API](#uso-de-la-api)
  - [Endpoint: `/chat`](#endpoint-chat)
- [Contribución](#contribución)
- [Licencia](#licencia)

---

## Descripción General

Este sistema expone un único endpoint (`POST /chat`) que recibe un mensaje en texto natural. Internamente, se detecta la **intención** del usuario (crear, leer, actualizar, eliminar un caso o hacer una pregunta general) y se procesan las **entidades** relevantes para luego ejecutar la operación correspondiente.  

Entre las funcionalidades destacan:
1. **Creación de casos**: Permite crear un caso en la tabla `Cases`, con un título, estado, descripción y abogado a cargo.
2. **Lectura/Consulta de casos**: A través de instrucciones en lenguaje natural, se generan dinámicamente consultas `SELECT` a la base de datos.
3. **Actualización de casos**: Genera dinámicamente sentencias `UPDATE`.
4. **Eliminación de casos**: Genera dinámicamente sentencias `DELETE`.
5. **Respuesta a preguntas generales**: Cuando no se identifica una intención CRUD, se reenvía la pregunta al modelo de ChatGPT configurado para obtener una respuesta coherente.

## Enfoque con `langgraph`

En particular, este proyecto destaca por el uso de la librería [`langgraph`](https://pypi.org/project/langgraph/) en el archivo [`langgraph_parser.py`](./app/langgraph_parser.py).  

- **`langgraph`** provee la estructura para construir un **State Graph**.  
- Permite definir **nodos** y **transiciones** basadas en condiciones (por ejemplo, la detección de la intención, para dirigir la ejecución hacia la acción correspondiente: `create_case`, `read_cases`, `update_case`, `delete_case` o `general_question`).  
- Facilita la **modularidad** y la **escalabilidad**, ya que cada paso del flujo de conversación (detección de intención, extracción de entidades, etc.) se encapsula en un nodo.

En el archivo `langgraph_parser.py`, se definen:
1. Funciones de procesamiento: `detect_intent`, `extract_entities`, etc.
2. Se crea el grafo de estados con `StateGraph(Dict[str, Any])`.
3. Se añaden nodos y transiciones condicionales.
4. Finalmente, se **compila** el grafo y se expone la función `parse_message` para el uso en la ruta principal.

Este enfoque modular hace más sencillo **modificar** o **agregar** nuevas intenciones o rutas de lógica en el futuro, adaptando el chatbot a distintas necesidades.

## Arquitectura de la Aplicación

La aplicación se organiza en varios archivos principales dentro de la carpeta `app`:

- **`config.py`**  
  Carga las variables de entorno (principalmente para configurar la conexión a la base de datos y la clave de OpenAI).

- **`db.py`**  
  Maneja la conexión a la base de datos PostgreSQL y la creación de la tabla `Cases` si no existe.

- **`crud.py`**  
  Contiene las operaciones CRUD para la tabla `Cases`. También incluye la lógica para comunicarse con la API de OpenAI y generar consultas SQL dinámicas.

- **`langgraph_parser.py`**  
  Contiene la definición de un flujo de estados (`StateGraph`) que detecta la intención del usuario y extrae entidades relevantes. Esto se hace usando `langgraph`, `langchain_openai` y la clase `ChatOpenAI`.

- **`routes.py`**  
  Define el router principal de FastAPI. Expone el endpoint `POST /chat`, que orquesta la lógica de análisis de intención y llamadas a `crud.py`.

- **`main.py`**  
  - Inicializa la aplicación FastAPI.
  - Agrega el middleware de CORS.
  - Crea la tabla `Cases` en la base de datos al arrancar el servidor.
  - Incluye las rutas definidas en `routes.py`.

```
app/
├── __init__.py
├── config.py
├── crud.py
├── db.py
├── langgraph_parser.py
├── main.py
└── routes.py
```

## Requerimientos

- Python 3.9+
- PostgreSQL 12+ (o versión compatible con `psycopg2`)
- Cuenta de OpenAI con una **API Key** válida (para generar consultas y responder preguntas)

## Instalación

1. **Clona** este repositorio (o descarga los archivos).
2. Crea y activa un **entorno virtual** (opcional pero recomendado):
   ```bash
   python -m venv venv
   source venv/bin/activate    # En Unix/Mac
   venv\Scriptsctivate       # En Windows
   ```
3. **Instala las dependencias** usando el archivo `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```
4. Verifica que todas las dependencias se hayan instalado correctamente.

## Configuración (.env)

En el archivo `.env` debes definir las variables de entorno que utiliza la aplicación. Ejemplo:

```env
OPENAI_API_KEY=tu_api_key_de_openai
DB_HOST=localhost
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=cases_db
DB_PORT=5432
```

## Ejecución del Servidor

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Uso de la API

### Endpoint: `/chat`

- **Método**: `POST`
- **Body (JSON)**:
  ```json
  {
    "message": "texto en lenguaje natural"
  }
  ```

## Contribución

¡Las contribuciones son bienvenidas! Para mejorar o extender la funcionalidad:

1. Haz un **fork** del repositorio.
2. Crea una rama con tus cambios.
3. Envía un **pull request** para revisión.

## Licencia

Este proyecto se distribuye bajo los términos de la [MIT License](https://opensource.org/licenses/MIT).  
Siéntete libre de usarlo y adaptarlo a tus necesidades.
