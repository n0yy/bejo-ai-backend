from config.llm import get_llm
from state.types import State
from utils.memory import use_memory, get_user_memories


def handle_interactive(state: State):
    """
    Handle non-database queries by generating a response using the LLM.

    Args:
        state (State): The current state containing the question

    Returns:
        dict: A dictionary containing the generated answer
    """
    llm = get_llm()

    # Get thread_id from config if available
    thread_id = state.get("thread_id", "session-id")

    prompt = """
You are BEJO, a joyful, friendly, and highly informative assistant for an internal company chatbot.

Your job is to help users by answering their questions in a warm, friendly, and conversational tone.
Always:
- Replace any use of "I", "me", or "my" with "Bejo"
- Use emojis naturally to maintain a positive and helpful tone 😊
- Be brief, but complete — answer only based on the context provided

Below is the information you can use:

=== Question ===
{question}

=== Related User Memories ===s
{user_memories}

=== Conversation History in This Session ===
{conversation_history}

Generate a concise and helpful response to the question above, using the memories and history when relevant.
""".format(
        question=state["question"],
        user_memories=get_user_memories(
            user_id="user_id_1", search=True, question=state["question"]
        ),
        conversation_history=get_user_memories(
            user_id="user_id_1", session_id=thread_id, is_session=True
        ),
    )

    try:
        answer = llm.invoke(prompt).content
        state["answer"] = answer
        return {"answer": answer}
    except Exception as e:
        print(f"Error handling interactive query: {e}")
        fallback_answer = "Oops! 😅 Something went wrong. Please try again. Bejo's always here to help! 💡"
        state["answer"] = fallback_answer
        return {"answer": fallback_answer}
    finally:
        use_memory(state, session_id=thread_id)
