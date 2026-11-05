# Async LLM Manager

Proyecto desarrollado en Python que permite interactuar de manera asíncrona con diferentes proveedores de modelos de lenguaje (LLM), utilizando una interfaz unificada y soportando generación de respuestas mediante streaming.

Actualmente, el proyecto permite trabajar con **OpenAI** y **Anthropic**, seleccionando el proveedor mediante variables de entorno.

## Características

- **Gestión de múltiples proveedores:** integración con OpenAI y Anthropic mediante una única clase administradora.
- **Programación asíncrona:** utilización de `asyncio` para realizar operaciones de manera no bloqueante.
- **Streaming de respuestas:** recepción y visualización progresiva de los fragmentos generados por el modelo.
- **Validación de configuración:** utilización de Pydantic para validar parámetros como temperatura, cantidad máxima de tokens y modelo.
- **Manejo de errores:** captura de errores de conexión, límites de solicitudes, tiempos de espera y errores generales de API.
- **Configuración mediante variables de entorno:** protección de las API keys y selección del proveedor sin modificar el código.

## Tecnologías utilizadas

- Python
- Asyncio
- OpenAI SDK
- Anthropic SDK
- Pydantic
- Python-dotenv

## Estructura del proyecto

```text
Pre-entrega-1/
│
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── schemas.py
│   └── manager.py
│
├── test/
|   ├── test_schema.py
│   ├── test_timeout.py
│   ├── test_connection.py
│   ├── test_rate_limit.py
│   └── test_errors.py
│
├── .env.example
├── .gitignore
├── main.py
└── README.md
```

## Instalación y configuración

### 1. Clonar el repositorio

```bash
git clone https://github.com/Facundo-Rainaudi/curso-ai-engineering.git
cd curso-ai-engineering/Pre-entrega-1
```

### 2. Crear un entorno virtual

```bash
python3 -m venv .venv
```

Activarlo:

**macOS / Linux**
```bash
source .venv/bin/activate
```

**Windows**
```bash
.venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install openai anthropic pydantic python-dotenv httpx
```

### 4. Configurar las variables de entorno

Crear un archivo `.env` en la raíz del proyecto, tomando como referencia `.env.example`.

```env
LLM_PROVIDER=openai

OPENAI_API_KEY=tu_api_key
ANTHROPIC_API_KEY=tu_api_key
```

Reemplazar los valores por las API keys correspondientes.

Para seleccionar el proveedor, modificar `LLM_PROVIDER`:

- `openai`: utiliza OpenAI.
- `anthropic`: utiliza Anthropic.

**Importante:** no compartir ni subir el archivo `.env` al repositorio.

## Ejecución

Una vez configurado el entorno y las variables correspondientes, ejecutar:

```bash
python3 main.py
```

El programa enviará un prompt al proveedor seleccionado y mostrará la respuesta progresivamente a medida que se reciben los fragmentos de texto.

## Pruebas

El proyecto incluye pruebas para verificar el manejo de diferentes errores.

Desde la raíz del proyecto, ejecutar:

```bash
PYTHONPATH=. python3 test/test_timeout.py
PYTHONPATH=. python3 test/test_connection.py
PYTHONPATH=. python3 test/test_rate_limit.py
PYTHONPATH=. python3 test/test_errors.py
PYTHONPATH=. python3 test/test_schema.py
```

Las pruebas simulan diferentes escenarios:

| Prueba | Descripción |
|---|---|
| Timeout | Simula una operación que supera el tiempo máximo de espera. |
| Connection | Simula un error de conexión con el proveedor. |
| Rate Limit | Simula un exceso en el límite de solicitudes (HTTP 429). |
| API Error | Simula un error general de API (HTTP 404). |

Estas pruebas de errores utilizan simulaciones del SDK de OpenAI.

## Arquitectura

El proyecto utiliza una clase central llamada `AsyncLLMManager`, responsable de administrar la comunicación con los distintos proveedores.

La selección del proveedor se realiza mediante variables de entorno, mientras que la configuración del modelo se valida utilizando Pydantic.

El método `generate()` utiliza programación asíncrona y streaming para entregar fragmentos de texto progresivamente, sin esperar a que finalice toda la generación.

De esta manera, la aplicación puede interactuar con distintos proveedores utilizando una misma interfaz, manteniendo separadas la configuración, la validación y la lógica de comunicación.

---

**Proyecto desarrollado como parte de la pre-entrega-1 del curso de AI Engineering.**
