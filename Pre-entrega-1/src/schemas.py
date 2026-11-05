#imports
from pydantic import BaseModel, Field

#Creamos el esquema para la configuracion del LLM
class LLMConfig(BaseModel):

    temperature: float = Field(
        default=0.7, #valor por defecto
        ge=0, #mayor o igual a 0
        le=2 #menor o igual a 2
    )

    max_tokens: int = Field(
        default=1000,
        gt=0 #mayor a 0
    )

    model: str = Field(
        min_length=1 #longitud minima de 1
    )