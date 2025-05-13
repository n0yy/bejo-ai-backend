"""
Agentic AI implementation for BEJO SQL Assistant.
This replaces the previous chain-based approach with a single agent that orchestrates all tools.
"""

import logging
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from tabulate import tabulate
import traceback
from uuid import uuid4

from config.db import get_database
from config.llm import get_llm
from utils.memory import use_memory, get_user_memories

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@tool(response_format="content")
def retrieve_knowledge(query: str) -> str:
    """
    Retrieves relevant documents from the knowledge base given a natural language query.

    Args:
        query (str): The natural language query to retrieve documents for.

    Returns:
        str: A serialized string containing the retrieved documents.
    """
    try:
        # Initialize the vector store
        qdrant = QdrantClient(host="localhost", port=6333)
        embedding = OllamaEmbeddings(model="nomic-embed-text:latest")
        vector_store = QdrantVectorStore(
            client=qdrant,
            collection_name="knowledge_layer_1",
            embedding=embedding,
        )

        # Retrieve documents
        retrieved_docs = vector_store.similarity_search(query, k=3)

        # Serialize the results
        serialized = "\n\n".join(
            f"Source: {doc.metadata.get('source', 'Unknown')}\nContent: {doc.page_content}"
            for doc in retrieved_docs
        )
        return serialized if serialized else "No relevant documents found."
    except Exception as e:
        logger.error(f"Error retrieving documents: {str(e)}")
        logger.debug(traceback.format_exc())
        return f"Error retrieving documents: {str(e)}"


@tool(response_format="content")
def execute_sql_query(query: str) -> str:
    """
    Executes a SQL query and returns the results as a formatted table.

    Args:
        query (str): SQL query to execute.

    Returns:
        str: Results formatted as a markdown table.
    """
    try:
        db = get_database()
        result = db.run(query)

        if not result:
            return "Query executed successfully, but returned no results."

        if isinstance(result, list) and len(result) > 0:
            if isinstance(result[0], dict):
                # If results are dictionaries, extract headers from keys
                headers = list(result[0].keys())
                rows = [[row.get(header, "") for header in headers] for row in result]
                markdown_table = tabulate(rows, headers=headers, tablefmt="github")
            elif isinstance(result[0], tuple):
                # If results are tuples, use generic column names
                headers = [f"Column {i+1}" for i in range(len(result[0]))]
                markdown_table = tabulate(result, headers=headers, tablefmt="github")
            else:
                markdown_table = str(result)
        else:
            markdown_table = str(result)

        return f"```\n{markdown_table}\n```"
    except Exception as e:
        logger.error(f"Error executing SQL query: {str(e)}")
        logger.debug(traceback.format_exc())
        return f"Error executing SQL query: {str(e)}"


@tool(response_format="content")
def get_db_schema() -> str:
    """
    Returns the database schema information.

    Returns:
        str: The database schema information.
    """
    try:
        db = get_database()
        schema = db.get_context()
        return f"### Database Schema\n\n{schema}"
    except Exception as e:
        logger.error(f"Error retrieving database schema: {str(e)}")
        logger.debug(traceback.format_exc())
        return f"Error retrieving database schema: {str(e)}"


# Keep track of the current user and session throughout the conversation
_CURRENT_USER_ID = None
_CURRENT_SESSION_ID = None


def set_current_user(user_id: str) -> None:
    """
    Sets the current user ID for the session.

    Args:
        user_id (str): The user ID to set as current.
    """
    global _CURRENT_USER_ID
    _CURRENT_USER_ID = user_id
    logger.info(f"Current user set to: {user_id}")


def set_current_session(session_id: str) -> None:
    """
    Sets the current session ID.

    Args:
        session_id (str): The session ID to set as current.
    """
    global _CURRENT_SESSION_ID
    _CURRENT_SESSION_ID = session_id
    logger.info(f"Current session set to: {session_id}")


def get_current_user() -> str:
    """
    Gets the current user ID.

    Returns:
        str: The current user ID or a placeholder if not set.
    """
    return _CURRENT_USER_ID or "unknown_user"


def get_current_session() -> str:
    """
    Gets the current session ID.

    Returns:
        str: The current session ID or a placeholder if not set.
    """
    return _CURRENT_SESSION_ID or "unknown_session"


def get_conversation_history(user_id: str = None, session_id: str = None) -> str:
    """
    Retrieves the conversation history for a specific user and session.

    Args:
        user_id (str, optional): The user ID. If None, uses the current user ID.
        session_id (str, optional): The session ID. If None, uses the current session ID.

    Returns:
        str: The conversation history.
    """
    try:
        # Use provided values or fall back to current context
        effective_user_id = user_id or get_current_user()
        effective_session_id = session_id or get_current_session()

        logger.info(
            f"Retrieving conversation history for user: {effective_user_id}, session: {effective_session_id}"
        )

        history = get_user_memories(
            user_id=effective_user_id, session_id=effective_session_id, is_session=True
        )
        return history if history else "No conversation history found."
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {str(e)}")
        logger.debug(traceback.format_exc())
        return f"Error retrieving conversation history: {str(e)}"


@tool(response_format="content")
def get_user_context(user_id: str = None, query: str = "") -> str:
    """
    Retrieves relevant user context based on a query.

    Args:
        user_id (str, optional): The user ID. If None, uses the current user ID.
        query (str): The query to search for relevant context.

    Returns:
        str: The relevant user context.
    """
    try:
        # Use provided user_id or fall back to current user
        effective_user_id = user_id or get_current_user()

        logger.info(
            f"Retrieving user context for user: {effective_user_id}, query: {query}"
        )

        context = get_user_memories(
            user_id=effective_user_id, search=True, question=query
        )
        return context if context else "No relevant user context found."
    except Exception as e:
        logger.error(f"Error retrieving user context: {str(e)}")
        logger.debug(traceback.format_exc())
        return f"Error retrieving user context: {str(e)}"


@tool(response_format="content")
def get_conversation_history_tool() -> str:
    """
    Retrieves the conversation history for the CURRENT user & session.
    (No parameters needed; uses global state.)
    """
    # Panggil fungsi asal dengan explicit globals
    return get_conversation_history(
        user_id=get_current_user(),
        session_id=get_current_session(),
    )


def create_bejo_agent() -> AgentExecutor:
    """
    Creates and returns the BEJO agent with all tools.

    Returns:
        AgentExecutor: The configured agent executor.
    """
    # Get the LLM
    llm = get_llm()

    # Define the tools
    tools = [
        get_user_context,
        retrieve_knowledge,
        get_db_schema,
        execute_sql_query,
        get_conversation_history_tool,
    ]

    # Define the agent prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
    You are BEJO, a joyful, friendly, and highly informative SQL assistant. 
    Your job is to help users access and analyze data by answering their questions clearly, accurately, and warmly 😊

    ## First Step
    - Use get schema tool to decide the user question is related to interact with database
    - If the question is related to database, use `execute_sql_query` tool to get the result
    - If the question is not related to database, use `retrieve_knowledge` tool to get the result
    - You must have ability to decide is the question is related to last conversation?
    - And you must use `get_conversation_history` tool to get the conversation history to understand the context of next question.

    ## Personality & Communication Style
    - Refer to yourself only as “Bejo”, never use “I”, “me”, or “my”
    - Use emojis sparingly and naturally to enhance friendliness
    - Be warm, humble, and supportive — never robotic or overly technical
    - Never explain how you know things — act as if Bejo naturally understands the user
    - Never mention or describe tools, memory, or system processes

    ## Interaction Behavior
    - Use context and conversation history silently — personalize without stating how
    - Always write clean, well-formatted answers
    - Use markdown tables when presenting data
    - When questions are complex, explain your reasoning step by step

    ## Tool Usage (internal-only)
    - Use `get_conversation_history` and `get_user_context` early for grounding
    - Use `get_db_schema` before SQL execution
    - Use `retrieve_knowledge` for internal knowledge
    - Never mention tools or intermediate steps to the user

    ## SQL Guidelines
    - Always inspect the schema before writing queries
    - Never use SELECT * — prefer explicit columns
    - Use JOINs with clear aliases and WHERE clauses
    - Add comments for non-trivial logic
    - Avoid unnecessary complexity and ensure queries are performant

    ## Summary
    Be friendly, professional, and smart.
    Focus on clarity and helpfulness.
    Bejo is a helpful companion, not a machine.
                """,
            ),
            # MESSAGE PLACEHOLDERS
            MessagesPlaceholder(variable_name="agent_scratchpad"),
            ("human", "{input}"),
        ]
    )

    agent = create_tool_calling_agent(llm, tools, prompt=prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)


# Expose these functions at the module level so they can be imported directly from agent.py
__all__ = [
    "create_bejo_agent",
    "set_current_user",
    "set_current_session",
    "get_current_user",
    "get_current_session",
]
