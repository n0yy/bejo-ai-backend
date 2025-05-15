# 📊 BEJO SQL Assistant Documentation

BEJO is a friendly, interactive SQL assistant that helps users access and analyze data through natural language queries. This document provides a comprehensive overview of the project architecture, components, and usage instructions.

## 🌟 Overview

BEJO is designed to be a joyful, friendly SQL assistant that simplifies database interactions through natural language processing. It combines advanced AI capabilities with database utilities to provide accurate and helpful responses to user queries.

## 🏗️ Architecture

The system is built using a modular architecture that integrates several key components:

1. **Agent System** - Manages the conversation flow and tool orchestration
2. **Memory System** - Stores and retrieves conversation history
3. **Knowledge Base** - Provides access to relevant information
4. **Database Connector** - Handles SQL query execution
5. **LLM Integration** - Powers the natural language understanding

## 🧩 Key Components

### 🤖 Agent Module (`app/agent.py`)

The agent module is the core of BEJO's functionality:

- Implements an agentic AI approach that orchestrates all tools
- Provides tools for database interaction, knowledge retrieval, and memory management
- Manages user and session context throughout conversations

### 🗄️ Database Configuration (`app/config/db.py`)

- Establishes connections to MySQL databases
- Configurable through environment variables
- Provides a standardized interface for database operations

### 🧠 LLM Integration (`app/config/llm.py`)

- Connects to Google's Gemini models (default: gemini-2.0-flash)
- Configurable temperature and model settings
- Abstracted interface for easy LLM switching

### 💾 Memory System (`app/utils/memory.py`)

- Uses Mem0 for conversation memory storage
- Supports both session-based and long-term memory
- Provides search capabilities for relevant memories

### 🔍 Knowledge Retrieval (`app/utils/retrieved.py`)

- Integrates with Google Drive for document loading
- Processes and chunks documents for efficient retrieval
- Uses Qdrant vector store for similarity search

### 🚀 Main Application (`app/main.py`)

- Entry point for the command-line interface
- Handles user interactions and display formatting
- Configures session management and logging

## 💻 Usage Instructions

### Prerequisites

- Python 3.8+
- MySQL database
- Ollama with nomic-embed-text model
- Qdrant vector database
- Google API credentials (for Drive integration)

### Environment Setup

1. Create a `.env` file with the following variables:
   ```
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_HOST=localhost
   DB_PORT=3306
   DB_NAME=your_db_name
   GOOGLE_API_KEY=your_google_api_key
   LLM_MODEL=gemini-2.0-flash
   LLM_PROVIDER=google_genai
   LLM_TEMPERATURE=0.3
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the Qdrant server:
   ```bash
   docker run -p 6333:6333 qdrant/qdrant
   ```

4. Start the Ollama server:
   ```bash
   ollama run nomic-embed-text:latest
   ```

### Running BEJO

Launch the application:

```bash
python app/main.py --user <your_user_id>
```

Optional flags:
- `--verbose` or `-v`: Enable detailed logging
- `--user` or `-u`: Specify user ID

### Interacting with BEJO

Once running, BEJO provides a command-line interface where you can:

1. Ask database-related questions in natural language
2. Request knowledge from indexed documents
3. Explore data through SQL queries
4. Type 'exit' to quit the application

## 🧰 Tools and Capabilities

### Database Interaction

- Schema retrieval and exploration
- SQL query execution
- Result formatting in markdown tables

### Knowledge Access

- Document similarity search
- Relevant information retrieval
- Context-aware responses

### Memory Management

- Session-based conversation tracking
- Long-term user memory
- Contextual memory search

## 🔧 Development and Customization

### Adding New Tools

To add new tools to BEJO, create a new tool function in `agent.py`:

```python
@tool(response_format="content")
def your_tool_name(param1: str, param2: str) -> str:
    """
    Document your tool's functionality here.
    
    Args:
        param1 (str): Description of parameter 1
        param2 (str): Description of parameter 2
        
    Returns:
        str: Description of return value
    """
    # Your implementation here
    return result
```

Then add it to the tools list in the `create_bejo_agent` function.

### Customizing the LLM

To use a different LLM model or provider, update the environment variables:

```
LLM_MODEL=your_model_name
LLM_PROVIDER=your_provider
LLM_TEMPERATURE=0.5
```
