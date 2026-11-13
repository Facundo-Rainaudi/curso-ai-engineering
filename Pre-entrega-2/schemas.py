#Importamos 'Enum' nos permite definir un conjunto cerrado de valores
from enum import Enum
from pydantic import BaseModel, Field

#Creamos la clase 'NivelCriticidad' q hereda de 'str' y 'Enum', lo q nos permite definir un conjunto cerrado de valores
class NivelCriticidad(str, Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"

class EntidadTecnica(BaseModel):
    #'list[str] -> indica q esperamos una lista de cadenas
    #Field -> nos permite definir restricciones, en este caso exige q haya al menos una tecnologia
    tecnologias: list[str] = Field(
        min_length=1,
        description="Lista de tecnologías, herramientas o lenguajes identificados."
    )

    nivel_de_criticidad: NivelCriticidad

    #En este caso con 'Field' exigimos q el resumen sea de al menos 10 caracteres
    resumen_tecnico: str = Field(
        min_length=10,
        description="Resumen técnico del texto analizado."
    )