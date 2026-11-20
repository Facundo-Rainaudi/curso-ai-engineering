"""Modelos Pydantic del sistema RAG.

Usamos dos modelos de salida con responsabilidades distintas:

1. RespuestaLLM: es lo que el modelo de lenguaje debe devolver y lo que
   parsea PydanticOutputParser. Solo incluye texto y un booleano.
2. RAGResponse: es la respuesta final que recibe el usuario. Agrega las
   fuentes, que se construyen desde los metadatos REALES de Chroma.

¿Por qué separarlos? Porque las fuentes no las debe inventar el LLM.
Si le pidiéramos las fuentes en el JSON, podría alucinar un archivo que no
existe. En cambio, nosotros sabemos exactamente qué fragmentos se recuperaron.
"""

from pydantic import BaseModel, Field


class RespuestaLLM(BaseModel):
    """Formato exacto que se le pide al modelo de lenguaje."""

    respuesta: str = Field(
        description=(
            "Respuesta breve basada exclusivamente en el contexto. "
            "Si la información no está en el contexto, debe ser exactamente "
            "'No lo sé.'"
        )
    )

    encontrado: bool = Field(
        description=(
            "True si la respuesta está respaldada por el contexto. "
            "False si el contexto no alcanza para responder."
        )
    )


class Fuente(BaseModel):
    """Referencia a un fragmento real recuperado de la base vectorial."""

    archivo: str = Field(description="Nombre del archivo de origen.")
    fragmento: str = Field(description="Extracto del fragmento recuperado.")
    chunk_index: int = Field(description="Índice del chunk dentro del corpus.")


class RAGResponse(RespuestaLLM):
    """Respuesta final: hereda respuesta/encontrado y agrega las fuentes.

    Al heredar de RespuestaLLM reutilizamos los dos campos ya definidos.
    Agregar 'fuentes' acá no obliga al LLM a generarlas: las completa nuestro
    código después de leer los metadatos de Chroma.
    """

    fuentes: list[Fuente] = Field(
        default_factory=list,
        description="Fragmentos de la base vectorial usados como contexto.",
    )
