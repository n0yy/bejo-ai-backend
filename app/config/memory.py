import os

os.environ["GEMINI_API_KEY"] = os.getenv("GOOGLE_API_KEY")


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
