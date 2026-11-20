"""Pipeline RAG: recuperación, prompt de veracidad y generación asíncrona.

La cadena LCEL hace todo el flujo:

    pregunta
       |
       v
    retriever (Chroma)
       |
       v
    contexto formateado
       |
       v
    prompt + LLM + PydanticOutputParser
       |
       v
    RespuestaLLM
       |
       v
    RAGResponse (con fuentes reales)
"""

import logging
from functools import lru_cache
from operator import itemgetter

from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from src.config import get_chat_model
from src.ingest import collection_count, get_chroma_client, get_vectorstore
from src.schemas import Fuente, RAGResponse, RespuestaLLM

logger = logging.getLogger(__name__)

# top_k=4 está dentro del rango 3-5 recomendado por la consigna.
# Más fragmentos no siempre ayudan: el modelo se distrae y se gastan más tokens.
TOP_K = 4

# Prompt de sistema: actúa como "filtro de veracidad".
# Las reglas están numeradas para que el modelo las siga en orden.
SYSTEM_PROMPT = """Sos un asistente técnico especializado en la documentación de PagoNube.

Reglas obligatorias:
1. Respondé ÚNICAMENTE con información que aparezca en el CONTEXTO.
2. Si la respuesta no está en el CONTEXTO, respondé exactamente: "No lo sé."
3. No inventes datos, endpoints, plazos, códigos ni fuentes.
4. No uses conocimiento externo ni supongas información que no esté escrita.
5. Sé breve y claro.
6. El campo "encontrado" debe ser true solo si la respuesta está respaldada
   por el CONTEXTO. Si no podés responder, debe ser false.
"""

# Prompt human: recibe el contexto recuperado y la pregunta.
# Delimitamos el contexto con etiquetas para que el modelo distinga
# claramente los datos de las instrucciones.
HUMAN_PROMPT = """CONTEXTO:
<contexto>
{context}
</contexto>

PREGUNTA DEL USUARIO:
{question}

{format_instructions}
"""


def format_docs(docs) -> str:
    """Convierte los documentos recuperados en un bloque de texto.

    Incluimos el archivo y el número de chunk como referencia interna.
    Si no hay documentos, devolvemos un texto explícito para que el modelo
    sepa que el contexto está vacío.
    """
    if not docs:
        return "(No se recuperaron fragmentos.)"

    partes = []

    for doc in docs:
        archivo = doc.metadata.get("source", "desconocido")
        chunk = doc.metadata.get("chunk_index", "?")
        partes.append(
            f"[Fuente: {archivo} | chunk {chunk}]\n{doc.page_content}"
        )

    return "\n\n".join(partes)


def get_retriever():
    """Crea el retriever de Chroma con búsqueda por similitud.

    Antes de crear el retriever verificamos que la base tenga datos.
    Así, si el usuario se olvidó de correr la ingesta, recibe un error claro
    en lugar de una respuesta vacía o inventada.
    """
    client = get_chroma_client()

    if collection_count(client) == 0:
        raise RuntimeError(
            "La base vectorial está vacía. "
            "Ejecutá primero: python -m src.ingest"
        )

    vectorstore = get_vectorstore(client)

    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": TOP_K},
    )


@lru_cache(maxsize=1)
def build_chain():
    """Construye la cadena LCEL completa una sola vez.

    Se cachea para no recrear el modelo, el retriever y el parser en cada
    consulta. La primera llamada tarda un poco; las siguientes reutilizan
    los mismos objetos.
    """
    retriever = get_retriever()
    llm = get_chat_model()
    parser = PydanticOutputParser(pydantic_object=RespuestaLLM)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", HUMAN_PROMPT),
        ]
    ).partial(
        # partial precarga las instrucciones de formato una sola vez.
        # El parser genera un texto que le explica al LLM qué JSON devolver.
        format_instructions=parser.get_format_instructions()
    )

    # La generación se envuelve con reintentos para tolerar fallos transitorios
    # del proveedor o respuestas con formato inválido.
    generation = (prompt | llm | parser).with_retry(
        stop_after_attempt=2,
        wait_exponential_jitter=True,
    )

    # RunnablePassthrough.assign recibe un diccionario, ejecuta la pieza
    # indicada y agrega el resultado al mismo diccionario sin borrar las
    # claves anteriores.
    #
    # Paso 1: toma "question", ejecuta el retriever y agrega "docs".
    # Paso 2: transforma "docs" en texto y agrega "context".
    # Paso 3: ejecuta prompt | llm | parser y agrega "respuesta".
    chain = (
        RunnablePassthrough.assign(
            docs=itemgetter("question") | retriever,
        )
        | RunnablePassthrough.assign(
            context=lambda x: format_docs(x["docs"]),
        )
        | RunnablePassthrough.assign(
            respuesta=generation,
        )
    )

    return chain


def _build_sources(docs) -> list[Fuente]:
    """Construye las fuentes desde los metadatos reales de Chroma.

    No le pedimos al LLM que invente las fuentes: las tomamos de los
    documentos que realmente se recuperaron. Así las citas son verificables.
    """
    fuentes = []

    for doc in docs:
        fuentes.append(
            Fuente(
                archivo=doc.metadata.get("source", "desconocido"),
                # Guardamos solo un extracto para que la respuesta no sea
                # enorme. Reemplazamos saltos de línea por espacios.
                fragmento=doc.page_content[:200].replace("\n", " ").strip(),
                chunk_index=int(doc.metadata.get("chunk_index", 0)),
            )
        )

    return fuentes


async def get_rag_response(query: str) -> RAGResponse:
    """Responde una consulta usando exclusivamente los documentos indexados.

    Pasos:
    1. Valida la consulta.
    2. Ejecuta la cadena LCEL de forma asíncrona.
    3. Si el modelo no encontró la respuesta, devuelve "No lo sé." sin fuentes.
    4. Si encontró, adjunta las fuentes reales de Chroma.
    """
    if not query or not query.strip():
        raise ValueError("La consulta no puede estar vacía.")

    chain = build_chain()

    try:
        # ainvoke es la versión asíncrona de invoke.
        # No bloquea el event loop mientras el LLM genera la respuesta.
        result = await chain.ainvoke({"question": query.strip()})
    except OutputParserException as exc:
        # Si el LLM devuelve un JSON inválido, no rompemos la aplicación:
        # registramos el problema y devolvemos una respuesta segura.
        logger.error("El LLM devolvió un formato inválido: %s", exc)
        return RAGResponse(
            respuesta="No lo sé.",
            encontrado=False,
            fuentes=[],
        )

    respuesta_llm: RespuestaLLM = result["respuesta"]
    docs = result["docs"]

    # Si el modelo no encontró la respuesta, no tiene sentido citar fuentes.
    if not respuesta_llm.encontrado:
        return RAGResponse(
            respuesta=respuesta_llm.respuesta,
            encontrado=False,
            fuentes=[],
        )

    return RAGResponse(
        respuesta=respuesta_llm.respuesta,
        encontrado=True,
        fuentes=_build_sources(docs),
    )
