from langchain.chat_models import init_chat_model
import os


def get_llm():
    """
    Return an LLM object based on environment variables.

    The following environment variables are used, with default values if not present:
    - LLM_MODEL: the name of the LLM model, default "gemini-2.0-flash"
    - LLM_PROVIDER: the provider of the LLM model, default "google_genai"
    - LLM_TEMPERATURE: the temperature of the LLM model, default 0.3

    The LLM object is constructed in the form
    init_chat_model(model_name, model_provider, temperature).
    """
    model_name = os.getenv("LLM_MODEL", "gemini-2.0-flash")
    model_provider = os.getenv("LLM_PROVIDER", "google_genai")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))

    return init_chat_model(
        model_name, model_provider=model_provider, temperature=temperature
    )
