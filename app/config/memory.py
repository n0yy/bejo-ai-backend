import os

# Hanya set GEMINI_API_KEY jika GOOGLE_API_KEY ada
google_api_key = os.getenv("GOOGLE_API_KEY")
if google_api_key is not None:
    os.environ["GEMINI_API_KEY"] = google_api_key


def mem0_config():
    return {
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "collection_name": "memory",
                "host": "localhost",
                "port": 6333,
                "embedding_model_dims": 768,
            },
        },
        "llm": {
            "provider": "gemini",
            "config": {
                "model": "gemini-2.0-flash",
                "temperature": 0.2,
                "max_tokens": 2000,
            },
        },
        "embedder": {
            "provider": "ollama",
            "config": {
                "model": "nomic-embed-text:latest",
                "ollama_base_url": "http://localhost:11434",
            },
        },
    }
