"""Configuración central del proyecto.

Este módulo concentra tres cosas:
1. La carga del archivo .env.
2. Las rutas del proyecto (para que funcionen desde cualquier carpeta).
3. La creación del modelo de chat y del modelo de embeddings.

La idea es que el resto de los módulos NO lea variables de entorno directamente.
Así, si mañana cambia el modelo o el proveedor, se modifica un solo archivo.
"""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# BASE_DIR es la carpeta Pre-entrega-3.
# __file__ apunta a .../Pre-entrega-3/src/config.py
# .parent       -> .../Pre-entrega-3/src
# .parent.parent -> .../Pre-entrega-3
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargamos el .env que está en la raíz de la entrega.
# Le pasamos la ruta explícita para que funcione aunque ejecutemos el script
# desde otra carpeta. Si el archivo no existe, load_dotenv no falla.
load_dotenv(BASE_DIR / ".env")

# Rutas configurables por variables de entorno, con valores por defecto.
# str(...) es necesario porque os.getenv espera un string como valor por defecto.
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
VECTORSTORE_DIR = Path(
    os.getenv("VECTORSTORE_DIR", str(BASE_DIR / "vectorstore"))
)

# Nombre de la colección dentro de Chroma.
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "curso_ai_docs")

# Modelos. Se pueden cambiar desde el .env sin tocar el código.
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")


def _get_openai_api_key() -> str:
    """Devuelve la API key de OpenAI o lanza un error claro si falta.

    Es mejor fallar acá, al inicio, que dejar que el SDK falle más adelante
    con un mensaje confuso. También detectamos el placeholder del .env.example.
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if not api_key or api_key.startswith("sk-reemplazar"):
        raise ValueError(
            "Falta OPENAI_API_KEY. Copiá .env.example a .env y completá tu clave."
        )

    return api_key


@lru_cache(maxsize=1)
def get_chat_model() -> ChatOpenAI:
    """Crea el modelo de chat una sola vez y lo reutiliza.

    - temperature=0: respuestas lo más deterministas posible. En RAG
      priorizamos fidelidad al contexto, no creatividad.
    - max_tokens=600: alcanza para respuestas técnicas breves y evita
      respuestas innecesariamente largas.
    """
    return ChatOpenAI(
        model=LLM_MODEL,
        temperature=0,
        api_key=_get_openai_api_key(),
        max_tokens=600,
    )


@lru_cache(maxsize=1)
def get_embeddings() -> OpenAIEmbeddings:
    """Crea el modelo de embeddings una sola vez y lo reutiliza.

    IMPORTANTE: esta misma configuración se usa para indexar y para consultar.
    Si se usaran modelos distintos, los vectores vivirían en espacios
    diferentes y la búsqueda por similitud no tendría sentido.
    """
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=_get_openai_api_key(),
    )
