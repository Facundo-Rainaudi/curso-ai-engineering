import asyncio

from src.manager import AsyncLLMManager
from src.schemas import LLMConfig


async def test_timeout():
    config = LLMConfig(
        temperature=0.7,
        max_tokens=500,
        model="gpt-4o-mini"
    )

    manager = AsyncLLMManager(config)

    # Simulamos una operación que tarda demasiado
    async def mock_generate(*args, **kwargs):
        await asyncio.sleep(35)

    manager.client.chat.completions.create = mock_generate

    print("Iniciando prueba de timeout...")

    async for fragmento in manager.generate("Hola"):
        print(fragmento)


asyncio.run(test_timeout())