from config.memory import mem0_config
from mem0 import Memory
from state.types import State


def use_memory(state: State):
    """
    Save the current state (question and answer) to memory.
    The current state will be added to the memory twice:
    - As a short-term memory for this session
    - As a long-term memory for the user
    This function is no-op if the state does not have an answer.
    """
    if "answer" not in state:
        print("[Memory] Skipped: No 'answer' in state.")
        return
    m = Memory.from_config(mem0_config())
    m.add(
        [
            {"role": "user", "content": state["question"]},
            {"role": "assistant", "content": state["answer"]},
        ],
        user_id="user_id_1",
        run_id="session-id",
    )

    # Long-term memory for user
    m.add(
        [
            {"role": "user", "content": state["question"]},
            {"role": "assistant", "content": state["answer"]},
        ],
        user_id="user_id_1",
    )


def get_user_memories(
    user_id: str,
    session_id: str = None,
    question: str = None,
    search: bool = False,
    is_session: bool = False,
) -> str:
    """
    Get all memories for a given user.

    Parameters
    ----------
    user_id : str
        The user ID to retrieve memories for.
    session_id : str
        The session ID to retrieve memories for (if is_session is True).
    question : str
        The question to search for (if search is True).
    search : bool, optional
        Whether to search for memories containing the question, by default False
    is_session : bool, optional
        Whether to retrieve memories for a given session, by default False

    Returns
    -------
    str
        A string containing all memories, one per line, in markdown format.
    """
    m = Memory.from_config(mem0_config())

    if search:
        response = m.search(query=question, user_id=user_id)
    elif is_session:
        response = m.get_all(user_id=user_id, run_id=session_id)
    else:
        response = m.get_all(user_id=user_id)

    memories = [f"- {item['memory']}" for item in response["results"]]
    return "\n".join(memories)
