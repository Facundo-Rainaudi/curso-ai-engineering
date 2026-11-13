import asyncio

from chain import process_text

texto = """
La API desarrollada con FastAPI presenta problemas de rendimiento
debido a un alto número de conexiones simultáneas a PostgreSQL.
El sistema utiliza Redis como caché, pero actualmente no está
respondiendo correctamente. Los usuarios experimentan demoras
y errores al intentar acceder a los servicios.
"""

async def main():
    #Ejecuta el pipeline 
    resultado = await process_text(texto)

    print("\nResultado del análisis:")
    #Convertimos el objeto Pydantic en JSON legible
    print(resultado.model_dump_json(indent=2))

if __name__ == "__main__":
    asyncio.run(main())