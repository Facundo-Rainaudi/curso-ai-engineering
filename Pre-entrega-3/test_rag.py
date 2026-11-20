"""Pruebas de humo del sistema RAG.

Se ejecutan con:

    python test_rag.py

No usamos pytest para mantener el proyecto simple: usamos assert de Python.
Si una condición no se cumple, el script falla con un mensaje claro.
"""

import asyncio
import unicodedata

from src.ingest import collection_count, get_chroma_client, ingest_documents
from src.rag import get_rag_response


def normalizar(texto: str) -> str:
    """Pasa a minúsculas y quita acentos para comparar frases.

    Ejemplo: "No lo sé." -> "no lo se."
    """
    texto = texto.lower()
    return "".join(
        caracter
        for caracter in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(caracter)
    )


async def test_pregunta_respondible() -> None:
    """La respuesta debe estar en 03_reembolsos.md y citar ese archivo."""
    pregunta = "¿Hasta cuándo puedo solicitar un reembolso total?"
    respuesta = await get_rag_response(pregunta)

    print("\n[PRUEBA 1] Pregunta respondible")
    print("Pregunta:", pregunta)
    print("Respuesta:", respuesta.respuesta)
    print("Encontrado:", respuesta.encontrado)
    print("Fuentes:", [fuente.archivo for fuente in respuesta.fuentes])

    assert respuesta.encontrado is True, (
        "El modelo no encontró una respuesta que sí existe en los documentos."
    )

    respuesta_normalizada = normalizar(respuesta.respuesta)

    assert "30" in respuesta.respuesta or "treinta" in respuesta_normalizada, (
        "La respuesta no menciona el plazo de 30 días."
    )

    assert respuesta.fuentes, (
        "La respuesta debe incluir al menos una fuente."
    )

    assert any(
        "03_reembolsos" in fuente.archivo for fuente in respuesta.fuentes
    ), "La fuente esperada (03_reembolsos.md) no aparece."


async def test_pregunta_trampa() -> None:
    """La base no habla de motores de base de datos: debe responder 'No lo sé.'"""
    pregunta = "¿Qué motor de base de datos usa PagoNube internamente?"
    respuesta = await get_rag_response(pregunta)

    print("\n[PRUEBA 2] Pregunta trampa")
    print("Pregunta:", pregunta)
    print("Respuesta:", respuesta.respuesta)
    print("Encontrado:", respuesta.encontrado)
    print("Fuentes:", [fuente.archivo for fuente in respuesta.fuentes])

    assert respuesta.encontrado is False, (
        "El modelo afirmó haber encontrado algo que no está en los documentos."
    )

    respuesta_normalizada = normalizar(respuesta.respuesta)

    # Aceptamos algunas variantes naturales de la negativa.
    frases_negativas = (
        "no lo se",
        "no tengo acceso",
        "no esta en el contexto",
        "no se menciona",
    )

    assert any(
        frase in respuesta_normalizada for frase in frases_negativas
    ), "El modelo no indicó que no tiene la información."

    # Verificamos que no haya alucinado un motor de base de datos.
    motores = ("postgres", "mysql", "mongo", "sqlite", "oracle", "sql server")

    for motor in motores:
        assert motor not in respuesta_normalizada, (
            f"El modelo alucinó el motor de base de datos: {motor}"
        )

    assert respuesta.fuentes == [], (
        "Una respuesta 'No lo sé.' no debe citar fuentes."
    )


def test_persistencia() -> None:
    """La segunda ingesta debe reutilizar la base y no duplicar fragmentos."""
    client = get_chroma_client()
    count_antes = collection_count(client)

    # Si ya hay datos, esta llamada debe omitir la indexación.
    ingest_documents()

    count_despues = collection_count(client)

    print("\n[PRUEBA 3] Persistencia")
    print("Fragmentos antes:", count_antes)
    print("Fragmentos después:", count_despues)

    assert count_antes == count_despues, (
        "La ingesta duplicó documentos en la base."
    )


async def main() -> None:
    """Ejecuta las tres pruebas en orden."""
    # Nos aseguramos de que la base exista antes de consultar.
    # Si ya existe, ingest_documents() no vuelve a indexar.
    ingest_documents()

    await test_pregunta_respondible()
    await test_pregunta_trampa()
    test_persistencia()

    print("\n✅ Todas las pruebas pasaron.")


if __name__ == "__main__":
    asyncio.run(main())
