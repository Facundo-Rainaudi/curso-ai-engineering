import asyncio

from src.manager import AsyncLLMManager
from src.schemas import LLMConfig, LLMError
from src.config import get_provider_config

async def main():
    #Obtenemos la configuracion del proveedor y el modelo
    provider_config = get_provider_config()

    #Creamos la configuracion del LLM
    config = LLMConfig(
        temperature = 0.7,
        max_tokens = 500,
        model = provider_config["model"]
    )

    #Inicializamos el administrador
    manager = AsyncLLMManager(config)

    print(f"Respuesta del modelo {provider_config['model']}:")

    async for fragmento in manager.generate(
        "Explicame brevemente qué es Python."
    ):
        #Comprobamos si lo q recibimos es un objeto 'LLMError',
        #Si es un error, mostramos un tipo y msj, y detenemos el consumo con break.
        #Si no es un error, significa q recibimos un fragmento de texto y lo imprimimo normal.
        if isinstance(fragmento, LLMError):
            print(f"\nError [{fragmento.type}]: {fragmento.message}")
            break

        #Imprimimos el fragmento, 'end=""' evitamos q los fragmentos se impriman en lineas diferentes
        #flush= True --> fuerza a mostrar el texto en la terminal inmediatamente
        print(fragmento, end="", flush=True)

    print()

if __name__ == "__main__":
    asyncio.run(main())