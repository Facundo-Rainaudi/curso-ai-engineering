from src.schemas import LLMConfig


config = LLMConfig(
    temperature=0.7,
    max_tokens=1000,
    model="gpt-4.1-mini"
)

print(config)