"""Demo de la Pre-entrega 3.

Ejecuta dos consultas:

1. Una pregunta cuya respuesta SÍ está en los documentos.
2. Una pregunta trampa cuya respuesta NO está.

Antes de ejecutar, la base vectorial tiene que existir:

    python -m src.ingest

Después:

    python main.py
"""

import asyncio
import logging

from src.rag import get_rag_response


# Las dos consultas de prueba que pide la consigna.
PREGUNTAS = [
    # Respondible: está en data/03_reembolsos.md.
    "¿Hasta cuándo puedo solicitar un reembolso total?",
    # Trampa: ningún documento habla de motores de base de datos.
    "¿Qué motor de base de datos usa PagoNube internamente?",
]


async def main() -> None:
    """Ejecuta las consultas de forma secuencial y muestra el JSON final."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    for numero, pregunta in enumerate(PREGUNTAS, start=1):
        print(f"\n{'=' * 70}")
        print(f"Consulta {numero}: {pregunta}")
        print("=" * 70)

        # await espera la respuesta sin bloquear el event loop.
        respuesta = await get_rag_response(pregunta)

        # model_dump_json convierte el modelo Pydantic a JSON legible.
        print(respuesta.model_dump_json(indent=2))


if __name__ == "__main__":
    # asyncio.run crea el event loop, ejecuta main() y lo cierra.
    asyncio.run(main())
