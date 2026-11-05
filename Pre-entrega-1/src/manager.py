#Imports
import openai
import anthropic
import asyncio

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

#Traemos la funcion get_provider_config desde el archivo config.py
from src.config import get_provider_config
#Traemos la clase LLMConfig desde el archivo schemas.py
from src.schemas import LLMConfig


class AsyncLLMManager:

    #Creamos el constructor de la clase, q recibe la configuracion del LLM como parametro
    def __init__(self, config: LLMConfig):

        #Obtenemos la configuracion del proveedor
        provider_config = get_provider_config()

        #Guardamos el proveedor seleccionado en una variable
        self.provider = provider_config["provider"]

        #Guardamos la configuracion del proveedor en una variable
        self.config = config

        #Creamos el cliente correspondiente al proveedor seleccionado
        if self.provider == "openai":
            self.client = AsyncOpenAI(
                api_key=provider_config["api_key"]
            )
        elif self.provider == "anthropic":
            self.client = AsyncAnthropic(
                api_key=provider_config["api_key"]
            )
        #self --> es una referencia a la instancia actual de la clase, y se utiliza para acceder
        # a las variables y metodos de la clase dentro de la misma. 
        
        # Una ventaja de usar self es q el resto de nuestra clase podra trabajar con "self.client" sin
        # tener q volver a consultar las variables de entorno.

    async def generate(self, prompt: str):
        try:
            if self.provider == "openai":

                async with asyncio.timeout(30):
                    stream = await self.client.chat.completions.create(
                        model=self.config.model,
                        messages=[
                            {"role": "user", "content": prompt}
                        ],
                        temperature=self.config.temperature,
                        max_tokens=self.config.max_tokens,
                        stream=True #Le decimos al proveedor q nos envie la respuesta progresivamente
                    )
                    #Recorremos los fragmentos q van llegando, no esperamos a q termine toda la generacion
                    async for chunk in stream:
                        #Recuperamos el contenido del fragmento
                        #Puede ser vacio o none.
                        fragmento = chunk.choices[0].delta.content

                        #Si el fragmento no es nulo, lo devolvemos al usuario
                        if fragmento:
                            yield fragmento

            elif self.provider == "anthropic":

                async with asyncio.timeout(30):
                    stream = await self.client.messages.create(
                        model=self.config.model,
                        messages=[
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=self.config.max_tokens,
                        stream=True
                    )
                    async for chunk in stream:
                        #Recibimos varios eventos, pero lo filtramos para quedarnos solo con los q contienen texto
                        if chunk.type == "content_block_delta":
                            #Accedemos al texto con "chunk.delta.text"
                            fragmento = chunk.delta.text

                            if fragmento:
                                yield fragmento    
            
        except (openai.RateLimitError, anthropic.RateLimitError):
            yield "Error: se supero el limite de solicitudes de la API. Por favor, intente nuevamente mas tarde."
        
        except (openai.APIConnectionError, anthropic.APIConnectionError):
            yield "Error: no se pudo establecer conexion con el proveedor de IA."

        except TimeoutError:
            yield "Error: se supero el tiempo maximo de espera"
        
        except (openai.APIError, anthropic.APIError) as e:
            yield f"Error de API: {str(e)}"