import asyncio

from src.manager import AsyncLLMManager
from src.schemas import LLMConfig, LLMError


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

    
    async for resultado in manager.generate("Hola"):
        if isinstance(resultado, LLMError):
            print(f"Tipo: {resultado.type}")
            print(f"Mensaje: {resultado.message}")



asyncio.run(test_timeout())