# Async LLM Manager

Proyecto desarrollado en Python que permite interactuar de manera asíncrona con diferentes proveedores de modelos de lenguaje (LLM), utilizando una interfaz unificada y soportando generación de respuestas mediante streaming.

Actualmente, el proyecto permite trabajar con **OpenAI** y **Anthropic**, seleccionando el proveedor y el modelo mediante variables de entorno.

## Características

- **Gestión de múltiples proveedores:** integración con OpenAI y Anthropic mediante una única clase administradora.
- **Programación asíncrona:** utilización de `asyncio` para realizar operaciones de manera no bloqueante.
- **Streaming de respuestas:** recepción y visualización progresiva de los fragmentos generados por el modelo.
- **Validación de configuración:** utilización de Pydantic para validar parámetros como temperatura, cantidad máxima de tokens y modelo.
- **Manejo de errores:** captura de errores de conexión, límites de solicitudes, tiempos de espera y errores generales de API mediante objetos estructurados.
- **Configuración mediante variables de entorno:** protección de las API keys y selección del proveedor y modelo sin modificar el código.

## Tecnologías utilizadas

- Python 3.12
- Asyncio
- OpenAI SDK
- Anthropic SDK
- Pydantic
- Python-dotenv
- Git

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
│   ├── test_schema.py
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

Se requiere Python 3.12.

```bash
python3.12 -m venv .venv
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
pip install openai anthropic pydantic python-dotenv
```

### 4. Configurar las variables de entorno

Crear un archivo `.env` en la raíz del proyecto, tomando como referencia `.env.example`.

```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini

OPENAI_API_KEY=tu_api_key_de_openai
ANTHROPIC_API_KEY=tu_api_key_de_anthropic
```

Reemplazar los valores de las API keys por las correspondientes.

Para seleccionar el proveedor y modelo, modificar las variables:

- `LLM_PROVIDER`: permite seleccionar `openai` o `anthropic`.
- `LLM_MODEL`: permite especificar el modelo correspondiente al proveedor seleccionado.

**Importante:** no compartir ni subir el archivo `.env` al repositorio.

## Ejecución

Una vez configurado el entorno y las variables correspondientes, ejecutar:

```bash
python3 main.py
```

El programa enviará un prompt al proveedor seleccionado y mostrará la respuesta progresivamente a medida que se reciben los fragmentos de texto.

## Configuración de parámetros

El proyecto permite configurar los parámetros del modelo mediante variables de entorno y la clase `LLMConfig`.

El parámetro `temperature` se utiliza en las solicitudes a OpenAI. En Anthropic no se envía este parámetro, ya que la implementación actual del SDK utilizado no lo admite en esta llamada.

## Manejo de errores

Los errores se representan mediante el esquema `LLMError`, definido con Pydantic.

Este objeto contiene dos campos:

- `type`: identifica el tipo de error.
- `message`: describe el error ocurrido.

De esta manera, quien consume el generador puede distinguir entre fragmentos de texto y errores, sin confundirlos con respuestas generadas por el modelo.

Los tipos de errores contemplados son:

- `rate_limit`
- `connection`
- `timeout`
- `api_error`

## Pruebas

El proyecto incluye pruebas para verificar el manejo de diferentes errores y la validación de esquemas.

Desde la raíz de `Pre-entrega-1`, ejecutar:

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
| Schema | Verifica la validación de los esquemas mediante Pydantic. |

Las pruebas de errores utilizan simulaciones del SDK de OpenAI.

## Arquitectura

El proyecto utiliza una clase central llamada `AsyncLLMManager`, responsable de administrar la comunicación con los distintos proveedores.

La selección del proveedor y del modelo se realiza mediante variables de entorno, mientras que la configuración de los parámetros se valida utilizando Pydantic.

El método `generate()` utiliza programación asíncrona y streaming para entregar fragmentos de texto progresivamente, sin esperar a que finalice toda la generación.

Cuando ocurre un error, el método devuelve un objeto `LLMError` con su tipo y mensaje correspondiente.

De esta manera, la aplicación puede interactuar con distintos proveedores utilizando una misma interfaz, manteniendo separadas la configuración, la validación y la lógica de comunicación.

---

**Proyecto desarrollado como parte de la pre-entrega-1 del curso de AI Engineering.**