# Pre-entrega 2 - Extracción de Entidades Técnicas con LangChain

## Descripción

Este proyecto implementa un pipeline de procesamiento de texto utilizando LangChain y modelos de lenguaje (LLM).

El objetivo es analizar textos técnicos y extraer información estructurada mediante un esquema definido con Pydantic.

El sistema permite identificar tecnologías, determinar el nivel de criticidad de una situación y generar un resumen técnico del contenido analizado.

## Tecnologías utilizadas

- Python 3
- LangChain
- LangChain OpenAI
- LangChain Anthropic
- Pydantic
- Python-dotenv
- OpenAI API
- Anthropic API

## Funcionalidades

- Extracción de tecnologías, herramientas y lenguajes mencionados en un texto.
- Clasificación del nivel de criticidad en tres categorías: baja, media y alta.
- Generación de un resumen técnico.
- Validación de la respuesta mediante un esquema Pydantic.
- Generación de respuestas estructuradas mediante `with_structured_output()`.
- Composición del pipeline utilizando LCEL.
- Reintentos automáticos ante errores mediante `with_retry()`.
- Procesamiento asíncrono mediante `ainvoke()`.
- Registro de eventos y errores mediante logging.
- Selección del proveedor y modelo mediante variables de entorno.

## Estructura del proyecto

```text
Pre-entrega-2/
│
├── .env.example
├── .gitignore
├── README.md
├── chain.py
├── main.py
└── schemas.py
```

## Configuración del entorno

### 1. Clonar el repositorio

```bash
git clone https://github.com/Facundo-Rainaudi/curso-ai-engineering.git
cd curso-ai-engineering/Pre-entrega-2
```

### 2. Crear un entorno virtual

```bash
python3 -m venv .venv
```

### 3. Activar el entorno virtual

En macOS o Linux:

```bash
source .venv/bin/activate
```

### 4. Instalar las dependencias

```bash
pip install langchain langchain-openai langchain-anthropic pydantic python-dotenv
```

### 5. Configurar las variables de entorno

Crear un archivo `.env` tomando como referencia `.env.example`.

Configurar el proveedor, el modelo y la API Key correspondiente.

Ejemplo para OpenAI:

```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini

OPENAI_API_KEY=tu_api_key
ANTHROPIC_API_KEY=tu_api_key
```

Para utilizar Anthropic:

```env
LLM_PROVIDER=anthropic
LLM_MODEL=claude-haiku-4-5-20251001
```

**Importante:** Las API Keys son privadas. El archivo `.env` está excluido del repositorio mediante `.gitignore`.

## Ejecución

Con el entorno virtual activado y las variables de entorno configuradas, ejecutar:

```bash
python3 main.py
```

El programa procesa el texto de prueba y muestra el resultado del análisis en formato JSON.

## Esquema de salida

La respuesta generada sigue el esquema `EntidadTecnica`, definido mediante Pydantic.

Ejemplo:

```json
{
  "tecnologias": [
    "FastAPI",
    "PostgreSQL",
    "Redis"
  ],
  "nivel_de_criticidad": "alta",
  "resumen_tecnico": "La API presenta problemas de rendimiento y disponibilidad relacionados con las conexiones a PostgreSQL y el funcionamiento de Redis."
}
```

## Arquitectura del pipeline

El procesamiento se realiza mediante una cadena LCEL que combina:

1. `ChatPromptTemplate`: define las instrucciones y el formato del mensaje enviado al modelo.
2. `with_structured_output()`: solicita una respuesta estructurada según el esquema Pydantic.
3. `with_retry()`: permite reintentar la ejecución ante errores.
4. `ainvoke()`: ejecuta el procesamiento de manera asíncrona.
5. `logging`: registra el inicio, la finalización y los errores del procesamiento.

El proveedor y el modelo se seleccionan mediante variables de entorno, permitiendo utilizar OpenAI o Anthropic sin modificar la lógica principal del pipeline.