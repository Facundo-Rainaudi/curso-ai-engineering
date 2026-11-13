#Permite leer variables de entorno
import os
import logging

#Carga variables de entorno desde un archivo .env
from dotenv import load_dotenv

#Nos permite utilizar los modelos de OpenAI y Anthropic
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
#Es una herramienta de LangChain q nos permite crear prompts de chat reutilizables y estructurados
from langchain_core.prompts import ChatPromptTemplate
#Es la clase q nos permite crear un controlador de eventos.
#Con esto vamos a detectar cada reintento y registrarlo en los logs
from langchain_core.callbacks import BaseCallbackHandler

from schemas import EntidadTecnica

load_dotenv()

#Determina qué proveedor vamos a utilizar. Si no encuentra la variable, usa OpenAI por defecto
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
#Obtiene el nombre del modelo que queremos utilizar
LLM_MODEL = os.getenv("LLM_MODEL")

if not LLM_MODEL:
    raise ValueError("La variable LLM_MODEL no está configurada.")

def get_model():
    if LLM_PROVIDER == "openai":
        return ChatOpenAI(
            model=LLM_MODEL,
            temperature=0
        )

    elif LLM_PROVIDER == "anthropic":
        return ChatAnthropic(
            model=LLM_MODEL,
            temperature=0
        )

    else:
        raise ValueError(f"Proveedor no soportado: {LLM_PROVIDER}")
    
#Creamos el cliente del proveedor q configuramos en '.env'
model = get_model()
#Le indicamos a LangChain q queremos recibir la respuesta siguiendo nuestro esquema Pydantic
structured_model = model.with_structured_output(EntidadTecnica)

#Esto es importante: en lugar de pedirle al modelo que devuelva un JSON y después intentar convertirlo manualmente, 
# LangChain se encarga de solicitar una salida estructurada y validarla con nuestro esquema.

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        Sos un analista técnico especializado en arquitectura de software.

        Tu tarea es analizar el texto recibido y extraer información técnica.

        Debés identificar:
        - Las tecnologías mencionadas.
        - El nivel de criticidad: baja, media o alta.
        - Un resumen técnico claro y conciso.

        Si el texto describe un error o problema que afecta la disponibilidad,
        seguridad o funcionamiento del sistema, evaluá su criticidad.

        No inventes tecnologías que no estén respaldadas por el texto.
        Si no hay tecnologías identificables, devolvé una lista con una
        tecnología genérica como "No identificada".

        Respondé siguiendo estrictamente el esquema solicitado.
        """
    ),
    (
        "human",
        "Analizá el siguiente texto:\n\n{texto}"
    )
])

#Creamos la cadena de procesamiento q combina el prompt y el modelo estructurado.
#Esto nos permite enviar un texto al modelo y recibir una respuesta validada segun nuestro esquema Pydantic.
chain = prompt | structured_model

chain = chain.with_retry(
    #Esto nos permine hacer tres intentos, uno inicial y dos reintentos en caso de error
    stop_after_attempt=3,
    #Introduce una espera creciente entre cada intento, con una variacion aleatoria para evitar reintentos simultaneos
    wait_exponential_jitter=True
)

#Configuramos el logging para q nos muestre informacion sobre el procesamiento del texto
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)
class RetryLogger(BaseCallbackHandler):

    def on_chain_start(self, serialized, inputs, **kwargs):
        run_id = kwargs.get("run_id")

        if run_id:
            tags = kwargs.get("tags", [])

            for tag in tags:
                if tag.startswith("retry:attempt:"):
                    intento = tag.split(":")[-1]

                    logger.warning(
                        "Reintentando ejecución. Intento: %s",
                        intento
                    )

#Esta funcion recibe un texto como entrada, lo procesa a traves de la cadena y 
# devuelve un objeto 'EntidadTecnica' con la informacion extraida y validada
async def process_text(text: str) -> EntidadTecnica:
    logger.info("Iniciando procesamiento del texto")

    logger.info(
        "Proveedor: %s | Modelo: %s",
        LLM_PROVIDER,
        LLM_MODEL
    )
    
    try:
        #Ejecutamos la cadena de forma asincrona
        resultado = await chain.ainvoke(
            {"texto": text},
            config={"callbacks": [RetryLogger()]}
        )

        logger.info("Procesamiento y validación completados correctamente")

        return resultado

    except Exception:
        logger.exception("Error durante el procesamiento del texto")
        raise