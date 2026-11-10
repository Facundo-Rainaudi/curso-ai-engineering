import asyncio
import openai
import httpx2 as httpx

from src.manager import AsyncLLMManager
from src.schemas import LLMConfig, LLMError


async def test_rate_limit():
    config = LLMConfig(
        temperature=0.7,
        max_tokens=500,
        model="gpt-4o-mini"
    )

    manager = AsyncLLMManager(config)

    async def mock_generate(*args, **kwargs):
        raise openai.RateLimitError(
            message="Rate limit exceeded",
            response=httpx.Response(
                status_code=429,
                request=httpx.Request(
                    "POST",
                    "https://api.openai.com"
                )
            ),
            body=None
        )

    manager.client.chat.completions.create = mock_generate

    print("Prueba Rate Limit:")

    
    async for resultado in manager.generate("Hola"):
        if isinstance(resultado, LLMError):
            print(f"Tipo: {resultado.type}")
            print(f"Mensaje: {resultado.message}")

    
asyncio.run(test_rate_limit())