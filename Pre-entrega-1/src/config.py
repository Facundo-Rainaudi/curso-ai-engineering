#imports
import os
from dotenv import load_dotenv

#Cargamos las variables de entorno desde el archivo .env
load_dotenv()

def get_provider_config():

    #Recibimos el proveedor de LLM desde las variables de entorno
    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    #Validamos q el usuario elija el proveedor correcto
    if provider not in ["openai", "anthropic"]:
        raise ValueError(f"Proveedor no soportado: {provider}")

    #Obtenemos la API key correspondiente al proveedor seleccionado
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
    else:
        api_key = os.getenv("ANTHROPIC_API_KEY")

    #Validamos q la API key no este vacia o con un valor por defecto
    if not api_key or api_key.startswith("tu_api_key"):
        raise ValueError(f"Falta configurar la API key para {provider}")

    return {
        "provider": provider,
        "api_key": api_key
    }