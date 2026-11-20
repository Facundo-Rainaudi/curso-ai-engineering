# Pre-entrega 3 — Sistema de recuperación semántica local (RAG)

Implementación End-to-End de un sistema RAG (Retrieval-Augmented Generation)
con LangChain, ChromaDB y OpenAI. El sistema indexa documentos locales, recupera
los fragmentos más relevantes para una consulta y genera una respuesta usando
**exclusivamente** ese contexto.

Si la respuesta no está en los documentos, el sistema responde `No lo sé.` y no
inventa información.

## Cumplimiento de la consigna

| Criterio de evaluación | Dónde se cumple |
|---|---|
| **Chunking e ingesta (25%)** | `src/ingest.py`: carga de `data/`, `RecursiveCharacterTextSplitter.from_tiktoken_encoder` con `chunk_size=500` tokens y `chunk_overlap=50`, metadatos por fragmento y persistencia en Chroma. |
| **Arquitectura asíncrona y recuperación (35%)** | `src/rag.py`: retriever de Chroma con `top_k=4`, cadena LCEL con retriever + formateo + LLM + parser, y `get_rag_response` con `await chain.ainvoke(...)`. |
| **Validación Pydantic (20%)** | `src/schemas.py`: `RespuestaLLM` parseada con `PydanticOutputParser`, `Fuente` y `RAGResponse` final con texto + referencias. |
| **Robustez y pruebas (20%)** | `test_rag.py`: pregunta respondible, pregunta trampa con `assert`, prueba de persistencia y manejo de `OutputParserException`. `.env` excluido por `.gitignore`. |

## Arquitectura

```text
data/*.md
   │
   ▼
[src/ingest.py]
   ├─ leer archivos → Document(page_content, metadata={"source": ...})
   ├─ RecursiveCharacterTextSplitter (500 tokens / 50 overlap)
   ├─ verificar si Chroma ya tiene documentos
   └─ Chroma.from_documents(...) → ./vectorstore
                                        │
consulta del usuario ───────────────────┘
   │
   ▼
[src/rag.py: get_rag_response]
   ├─ retriever.ainvoke(query)          → top 4 chunks
   ├─ format_docs(docs)                 → contexto delimitado
   ├─ prompt | llm | parser             → RespuestaLLM
   └─ RAGResponse(respuesta, encontrado, fuentes)
```

## Estructura del proyecto

```text
Pre-entrega-3/
├── data/
│   ├── 01_autenticacion.md
│   ├── 02_pagos.md
│   ├── 03_reembolsos.md
│   └── 04_limites_y_errores.md
├── src/
│   ├── __init__.py
│   ├── config.py       # entorno, modelo de chat y embeddings
│   ├── schemas.py      # Fuente, RespuestaLLM, RAGResponse
│   ├── ingest.py       # carga, chunking y persistencia
│   └── rag.py          # prompt, cadena LCEL y get_rag_response
├── main.py             # demo de las dos consultas
├── test_rag.py         # pruebas con asserts
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Requisitos

- Python 3.12 o superior.
- Una API key de OpenAI. La misma clave se usa para el modelo de chat y para
  los embeddings.
- Conexión a internet para la primera indexación y para consultar el LLM.

> **Nota sobre Python 3.15:** ChromaDB depende de `onnxruntime`, que al momento
> de la entrega no tiene wheel para Python 3.15. El proyecto fue probado con
> **Python 3.14**. Si tu `python3` es 3.15, creá el entorno con `python3.14`.

## Instalación

```bash
cd Pre-entrega-3

# Crear el entorno virtual (usar 3.14 si 3.15 falla por onnxruntime)
python3.14 -m venv .venv

# Activarlo
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# Instalar dependencias
pip install -r requirements.txt
```

## Configuración de variables de entorno

Copiar el archivo de ejemplo:

```bash
cp .env.example .env
```

Editar `.env` y completar la clave:

```env
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

OPENAI_API_KEY=sk-...
```

Opcionalmente se pueden cambiar las rutas:

```env
DATA_DIR=data
VECTORSTORE_DIR=vectorstore
COLLECTION_NAME=curso_ai_docs
```

**Importante:** `.env` está incluido en `.gitignore`. No se debe subir al
repositorio.

## Ingesta de documentos

La primera vez, o cuando cambien los documentos:

```bash
python -m src.ingest
```

El script:

1. Lee los archivos `.md` y `.txt` de `data/`.
2. Los divide en fragmentos de hasta 500 tokens con 50 de overlap.
3. Verifica si la colección de Chroma ya tiene documentos.
4. Si está vacía, calcula los embeddings y persiste todo en `./vectorstore`.

Para forzar la reconstrucción de la base:

```bash
python -m src.ingest --reindex
```

La segunda ejecución sin `--reindex` debe mostrar:

```text
La colección 'curso_ai_docs' ya contiene 12 fragmentos. Se omite la ingesta...
```

## Ejecución

```bash
python main.py
```

El programa ejecuta dos consultas:

1. `¿Hasta cuándo puedo solicitar un reembolso total?`
2. `¿Qué motor de base de datos usa PagoNube internamente?`

La primera debe responder con el plazo de 30 días y citar `03_reembolsos.md`.
La segunda debe responder `No lo sé.` sin fuentes.

## Pruebas

```bash
python test_rag.py
```

El script usa `assert` de Python, sin dependencias extra. Verifica:

1. **Pregunta respondible:** `encontrado=True`, mención de 30 días y fuente
   `03_reembolsos.md`.
2. **Pregunta trampa:** `encontrado=False`, respuesta negativa y ausencia de
   motores de base de datos inventados.
3. **Persistencia:** la segunda ingesta no duplica fragmentos.

Resultado obtenido en la entrega:

```text
[PRUEBA 1] Pregunta respondible
Pregunta: ¿Hasta cuándo puedo solicitar un reembolso total?
Respuesta: Hasta **30 días corridos** desde la aprobación.
Encontrado: True
Fuentes: ['03_reembolsos.md', '03_reembolsos.md', '03_reembolsos.md', '04_limites_y_errores.md']

[PRUEBA 2] Pregunta trampa
Pregunta: ¿Qué motor de base de datos usa PagoNube internamente?
Respuesta: No lo sé.
Encontrado: False
Fuentes: []

[PRUEBA 3] Persistencia
Fragmentos antes: 12
Fragmentos después: 12

✅ Todas las pruebas pasaron.
```

## Decisiones de diseño

### Chunking en tokens, no en caracteres

`RecursiveCharacterTextSplitter` mide en caracteres por defecto. Para cumplir
la consigna se usa `from_tiktoken_encoder`, que hace que `chunk_size=500` y
`chunk_overlap=50` se midan en tokens.

Los separadores están ordenados de mayor a menor unidad semántica: secciones
Markdown, subsecciones, párrafos, líneas, oraciones, palabras y, como último
recurso, caracteres. Así se evita cortar una idea al medio.

El overlap de 50 tokens mantiene continuidad entre fragmentos vecinos.

### Un único modelo de embeddings

`src/config.py` expone `get_embeddings()`. Esa misma función se usa para
indexar (`Chroma.from_documents`) y para consultar (`get_vectorstore`). Si se
usaran modelos distintos, los vectores vivirían en espacios diferentes y la
búsqueda por similitud sería aleatoria.

Se usa `text-embedding-3-small` de OpenAI, que se factura con la misma
`OPENAI_API_KEY` y tiene un costo muy bajo para este volumen.

### Persistencia verificada

`src/ingest.py` usa `chromadb.PersistentClient(path="./vectorstore")` y consulta
`collection.count()` antes de indexar. Si ya hay documentos, no vuelve a
calcular embeddings. Esto evita duplicados y ahorra tiempo y costo.

### Recuperación con `top_k=4`

El retriever usa búsqueda por similitud y recupera 4 fragmentos. Es un valor
dentro del rango 3–5 recomendado: suficiente contexto sin caer en el problema
de "Lost in the Middle" ni en límites de tokens.

### Prompt de veracidad

El prompt de sistema obliga al modelo a:

- Responder solo con el contenido de `<contexto>`.
- Responder exactamente `No lo sé.` si la respuesta no está.
- No inventar datos, endpoints, plazos ni fuentes.
- Marcar `encontrado=False` cuando no puede responder.

### Dos modelos Pydantic

- `RespuestaLLM` es lo que parsea `PydanticOutputParser`: `respuesta` y
  `encontrado`.
- `RAGResponse` hereda de `RespuestaLLM` y agrega `fuentes`.
- Las fuentes se construyen desde los metadatos reales de Chroma (`source`,
  `chunk_index`), no desde lo que diga el LLM. Así las citas son verificables y
  no se pueden alucinar.

### Cadena LCEL y asincronía

La cadena incluye el retriever, el formateo de documentos, el LLM y el parser:

```python
chain = (
    RunnablePassthrough.assign(
        docs=itemgetter("question") | retriever
    )
    | RunnablePassthrough.assign(
        context=lambda x: format_docs(x["docs"])
    )
    | RunnablePassthrough.assign(
        respuesta=prompt | llm | parser
    )
)
```

`get_rag_response` es `async` y usa `await chain.ainvoke(...)`, por lo que la
recuperación y la llamada al LLM no bloquean el event loop.

### Manejo de errores

- Consulta vacía → `ValueError`.
- Base vectorial vacía → `RuntimeError` con instrucción para ejecutar la ingesta.
- JSON inválido del LLM → se captura `OutputParserException` y se devuelve una
  respuesta segura (`No lo sé.`, sin fuentes).
- Errores transitorios → la generación usa `.with_retry(stop_after_attempt=2)`.

## Seguridad

- `.env` está en `.gitignore`.
- `.env.example` solo contiene placeholders.
- No se incluyen claves en el código ni en el README.
- `vectorstore/` también está ignorado: es un artefacto generado localmente.

## Posibles mejoras

- Búsqueda MMR para reducir fragmentos redundantes.
- Reranking con un modelo dedicado.
- Búsqueda híbrida (embeddings + BM25).
- Streaming de la respuesta final.
- Evaluación automática con un conjunto de preguntas y respuestas esperadas.

## Autor

**Facundo Rainaudi**  
GitHub: [Facundo-Rainaudi](https://github.com/Facundo-Rainaudi)

Proyecto desarrollado como parte de la pre-entrega 3 del curso de AI Engineering.
