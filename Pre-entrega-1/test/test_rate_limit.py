import asyncio
import openai
import httpx2

from src.manager import AsyncLLMManager
from src.schemas import LLMConfig


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
            response=httpx2.Response(
                status_code=429,
                request=httpx2.Request(
                    "POST",
                    "https://api.openai.com"
                )
            ),
            body=None
        )

    manager.client.chat.completions.create = mock_generate

    print("Prueba Rate Limit:")

    async for fragmento in manager.generate("Hola"):
        print(fragmento)
    
asyncio.run(test_rate_limit())