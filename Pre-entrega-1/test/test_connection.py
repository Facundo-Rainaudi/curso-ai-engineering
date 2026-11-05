import asyncio
import openai
import httpx2

from src.manager import AsyncLLMManager
from src.schemas import LLMConfig


async def test_connection():
    config = LLMConfig(
        temperature=0.7,
        max_tokens=500,
        model="gpt-4o-mini"
    )

    manager = AsyncLLMManager(config)

    async def mock_generate(*args, **kwargs):
        raise openai.APIConnectionError(
            request=httpx2.Request(
                "POST",
                "https://api.openai.com"
            )
        )

    manager.client.chat.completions.create = mock_generate

    print("Prueba de conexión:")
    
    async for fragmento in manager.generate("Hola"):
        print(fragmento)


asyncio.run(test_connection())