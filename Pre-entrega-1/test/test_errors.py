
import asyncio
import openai
import httpx2 as httpx

from src.manager import AsyncLLMManager
from src.schemas import LLMConfig, LLMError


async def test_api_error():
    config = LLMConfig(
        temperature=0.7,
        max_tokens=500,
        model="gpt-4o-mini"
    )

    manager = AsyncLLMManager(config)

    async def mock_generate(*args, **kwargs):
        raise openai.NotFoundError(
            message="Model not found",
            response=httpx.Response(
                status_code=404,
                request=httpx.Request(
                    "POST",
                    "https://api.openai.com"
                )
            ),
            body=None
        )

    manager.client.chat.completions.create = mock_generate

    print("Prueba de error general de API:")

    async for resultado in manager.generate("Hola"):
            if isinstance(resultado, LLMError):
                print(f"Tipo: {resultado.type}")
                print(f"Mensaje: {resultado.message}")

asyncio.run(test_api_error())