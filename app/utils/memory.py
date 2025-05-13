"""
Memory utilities for BEJO SQL Assistant.
Handles saving and retrieving conversation memories.
"""

import logging
from typing import Dict, List, Any, Optional
from mem0 import Memory
from langchain_core.messages import HumanMessage, AIMessage

from config.memory import mem0_config

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def use_memory(state: Dict[str, str], user_id: str, config: Dict[str, Any]) -> None:
    """
    Save the current state (question and answer) to memory.
    The current state will be added to the memory twice:
    - As a short-term memory for this session
    - As a long-term memory for the user

    Args:
        state (dict): A dictionary containing 'question' and 'answer'.
        user_id (str): The user ID to associate the memory with.
        config (dict): Configuration containing session/thread information.
    """
    if "question" not in state or "answer" not in state:
        logger.warning("Skipped: Missing 'question' or 'answer' in state.")
        return

    try:
        # Extract session ID from config
        session_id = config.get("configurable", {}).get("thread_id", "unknown-session")

        m = Memory.from_config(mem0_config())

        # Session memory
        m.add(
            [
                {"role": "user", "content": state["question"]},
                {"role": "assistant", "content": state["answer"]},
            ],
            user_id=user_id,
            run_id=session_id,
        )

        # Long-term memory for user
        m.add(
            [
                {"role": "user", "content": state["question"]},
                {"role": "assistant", "content": state["answer"]},
            ],
            user_id=user_id,
        )
        logger.info(f"Memory saved for user {user_id} in session {session_id}")
    except Exception as e:
        logger.error(f"Error saving memory: {str(e)}")


def get_user_memories(
    user_id: str,
    session_id: Optional[str] = None,
    question: Optional[str] = None,
    search: bool = False,
    is_session: bool = False,
) -> str:
    """
    Get memories for a given user.

    Args:
        user_id (str): The user ID to retrieve memories for.
        session_id (str, optional): The session ID to retrieve memories for (if is_session is True).
        question (str, optional): The question to search for (if search is True).
        search (bool, optional): Whether to search for memories containing the question.
        is_session (bool, optional): Whether to retrieve memories for a given session.

    Returns:
        str: A string containing all memories, one per line, in markdown format.
    """
    try:
        m = Memory.from_config(mem0_config())

        if search and question:
            response = m.search(query=question, user_id=user_id)
        elif is_session and session_id:
            response = m.get_all(user_id=user_id, run_id=session_id)
        else:
            response = m.get_all(user_id=user_id)

        if not response or not response.get("results"):
            return ""

        formatted_memories = []
        for item in response["results"]:
            memory = item.get("memory", {})
            if isinstance(memory, dict):
                role = memory.get("role", "unknown")
                content = memory.get("content", "")
                if role == "user":
                    formatted_memories.append(f"Human: {content}")
                elif role == "assistant":
                    formatted_memories.append(f"BEJO: {content}")
            elif isinstance(memory, str):
                formatted_memories.append(f"- {memory}")

        return "\n".join(formatted_memories)
    except Exception as e:
        logger.error(f"Error retrieving user memories: {str(e)}")
        return ""


def format_chat_history(history: str) -> List[Dict[str, str]]:
    """
    Formats the chat history string into a list of message dictionaries.

    Args:
        history (str): The chat history as a string.

    Returns:
        List[Dict[str, str]]: A list of message dictionaries.
    """
    if not history:
        return []

    messages = []
    lines = history.split("\n")
    current_speaker = None
    current_message = ""

    for line in lines:
        if line.startswith("Human: "):
            # Save previous message if it exists
            if current_speaker and current_message:
                messages.append(
                    HumanMessage(content=current_message)
                    if current_speaker == "Human"
                    else AIMessage(content=current_message)
                )

            # Start new human message
            current_speaker = "Human"
            current_message = line[7:]  # Remove "Human: " prefix
        elif line.startswith("BEJO: "):
            # Save previous message if it exists
            if current_speaker and current_message:
                messages.append(
                    HumanMessage(content=current_message)
                    if current_speaker == "Human"
                    else AIMessage(content=current_message)
                )

            # Start new assistant message
            current_speaker = "BEJO"
            current_message = line[6:]  # Remove "BEJO: " prefix
        elif current_speaker:
            # Continue current message
            current_message += "\n" + line

    # Add the last message if it exists
    if current_speaker and current_message:
        messages.append(
            HumanMessage(content=current_message)
            if current_speaker == "Human"
            else AIMessage(content=current_message)
        )

    return messages
