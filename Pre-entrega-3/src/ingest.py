"""Ingesta de documentos: carga, chunking y persistencia en ChromaDB.

Flujo general:

    data/*.md|*.txt
          |
          v
    Document(page_content, metadata)
          |
          v
    chunks de 500 tokens (50 de overlap)
          |
          v
    ./vectorstore (Chroma persistente)

El script es idempotente: si la colección ya tiene documentos, no vuelve a
indexar. Eso ahorra tiempo y costo de embeddings. Si querés reconstruirla,
usá el flag --reindex.
"""

import argparse
import logging
from pathlib import Path

import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import (
    COLLECTION_NAME,
    DATA_DIR,
    VECTORSTORE_DIR,
    get_embeddings,
)

logger = logging.getLogger(__name__)

# Extensiones que aceptamos como documentos de entrada.
SUPPORTED_EXTENSIONS = {".md", ".txt"}

# La consigna pide mínimo 500 tokens con 50 de overlap.
# Estos valores se miden en TOKENS porque usamos from_tiktoken_encoder.
CHUNK_SIZE_TOKENS = 500
CHUNK_OVERLAP_TOKENS = 50


def load_documents(data_dir: Path = DATA_DIR) -> list[Document]:
    """Lee los archivos .md/.txt de data/ y los convierte en Documents.

    Un Document de LangChain tiene dos partes:
    - page_content: el texto del documento.
    - metadata: un diccionario con información extra. Acá guardamos el nombre
      del archivo para poder citarlo después como fuente.
    """
    if not data_dir.is_dir():
        raise FileNotFoundError(
            f"No existe la carpeta de documentos: {data_dir}. "
            "Creala y agregá archivos .md o .txt."
        )

    documents: list[Document] = []

    # rglob("*") recorre la carpeta y sus subcarpetas.
    # sorted() garantiza un orden estable entre ejecuciones.
    for path in sorted(data_dir.rglob("*")):
        if not path.is_file():
            continue

        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        # encoding="utf-8" evita problemas con tildes y eñes.
        content = path.read_text(encoding="utf-8").strip()

        if not content:
            logger.warning("Se omite %s porque está vacío.", path.name)
            continue

        # Guardamos la ruta relativa (ej. "03_reembolsos.md") para que la
        # cita sea corta y legible en la respuesta final.
        source = str(path.relative_to(data_dir))

        documents.append(
            Document(
                page_content=content,
                metadata={"source": source},
            )
        )
        logger.info("Documento cargado: %s", source)

    if not documents:
        raise ValueError(
            f"No se encontraron archivos .md o .txt con contenido en {data_dir}."
        )

    return documents


def split_documents(documents: list[Document]) -> list[Document]:
    """Divide los documentos en chunks que preservan contexto semántico.

    RecursiveCharacterTextSplitter intenta cortar primero por separadores
    "grandes" (secciones Markdown, párrafos) y solo si no alcanza baja a
    oraciones, palabras o caracteres. Así evita cortar una idea al medio.

    from_tiktoken_encoder hace que chunk_size y chunk_overlap se midan en
    TOKENS, no en caracteres. Es lo que exige la consigna.
    """
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        # cl100k_base es el tokenizador que usan los modelos de OpenAI.
        # tiktoken funciona offline: no consume API.
        encoding_name="cl100k_base",
        chunk_size=CHUNK_SIZE_TOKENS,
        chunk_overlap=CHUNK_OVERLAP_TOKENS,
        # El orden importa: de la unidad más grande a la más chica.
        separators=[
            "\n## ",   # secciones Markdown
            "\n### ",  # subsecciones
            "\n\n",    # párrafos
            "\n",      # líneas
            ". ",      # oraciones
            " ",       # palabras
            "",        # último recurso: caracteres
        ],
        # Agrega metadata["start_index"] con la posición del chunk.
        add_start_index=True,
    )

    chunks = splitter.split_documents(documents)

    # Numeramos los chunks para poder referenciarlos en la respuesta final.
    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = index

    logger.info(
        "Chunking completado: %s documentos -> %s fragmentos.",
        len(documents),
        len(chunks),
    )

    return chunks


def get_chroma_client() -> chromadb.PersistentClient:
    """Crea el cliente persistente de Chroma apuntando a ./vectorstore.

    PersistentClient guarda la base en disco, no en memoria. Si la carpeta
    no existe, la crea.
    """
    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(VECTORSTORE_DIR))


def get_vectorstore(client: chromadb.PersistentClient | None = None) -> Chroma:
    """Devuelve el vector store de LangChain conectado a la colección.

    Le pasamos la MISMA función de embeddings que se usa en la ingesta.
    Así indexación y consulta trabajan en el mismo espacio vectorial.
    """
    client = client or get_chroma_client()

    return Chroma(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding_function=get_embeddings(),
    )


def collection_count(client: chromadb.PersistentClient) -> int:
    """Cuenta cuántos fragmentos hay en la colección (0 si no existe)."""
    collection = client.get_or_create_collection(COLLECTION_NAME)
    return collection.count()


def ingest_documents(reindex: bool = False) -> Chroma:
    """Carga los documentos y los persiste en Chroma.

    Si la colección ya tiene datos y reindex=False, no hace nada.
    Esa verificación es la que evita reindexar en cada ejecución.
    """
    client = get_chroma_client()
    current_count = collection_count(client)

    # Caso 1: ya hay datos y no se pidió reindexar -> reutilizamos la base.
    if current_count > 0 and not reindex:
        logger.info(
            "La colección '%s' ya contiene %s fragmentos. "
            "Se omite la ingesta (usá --reindex para reconstruirla).",
            COLLECTION_NAME,
            current_count,
        )
        return get_vectorstore(client)

    # Caso 2: se pidió reindexar -> borramos la colección anterior.
    if current_count > 0 and reindex:
        logger.info("Reindexación solicitada: se elimina la colección anterior.")
        client.delete_collection(COLLECTION_NAME)

    # Caso 3: base vacía -> cargamos, dividimos e indexamos.
    documents = load_documents()
    chunks = split_documents(documents)

    # from_documents calcula el embedding de cada chunk y los guarda.
    # Al usar el cliente persistente, los datos quedan en disco.
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        client=client,
        collection_name=COLLECTION_NAME,
    )

    logger.info(
        "Ingesta finalizada. Fragmentos persistidos: %s",
        collection_count(client),
    )

    return vectorstore


def main() -> None:
    """Punto de entrada para ejecutar la ingesta desde la terminal.

    Uso:
        python -m src.ingest
        python -m src.ingest --reindex
    """
    parser = argparse.ArgumentParser(
        description="Carga los documentos de data/ en ChromaDB."
    )
    parser.add_argument(
        "--reindex",
        action="store_true",
        help="Borra la colección existente y vuelve a indexar todo.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    ingest_documents(reindex=args.reindex)


if __name__ == "__main__":
    main()
