import asyncio

from src.manager import AsyncLLMManager
from src.schemas import LLMConfig

async def main():

    # #ANTHROPIC
    # config = LLMConfig(
    #     temperature=0.7,
    #     max_tokens=500,
    #     model="claude-haiku-5-5"
    # )

    #OPENAI
    config = LLMConfig(
        temperature=0.7,
        max_tokens=500,
        model="gpt-4o-mini"
    )

    manager = AsyncLLMManager(config)

    print("Respuesta del modelo:")

    async for fragmento in manager.generate(
        "Explicame brevemente qué es Python."
    ):
        #Imprimimos el fragmento, 'end=""' evitamos q los fragmentos se impriman en lineas diferentes
        #flush= True --> fuerza a mostrar el texto en la terminal inmediatamente
        print(fragmento, end="", flush=True)

    print()

if __name__ == "__main__":
    asyncio.run(main())