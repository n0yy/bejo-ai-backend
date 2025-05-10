from config.llm import get_llm
from state.types import State
from utils.memory import use_memory
from utils.memory import get_user_memories


def handle_interactive(state: State):
    llm = get_llm()

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

=== Related User Memories ===
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
            user_id="user_id_1", session_id="session-id", is_session=True
        ),
    )

    try:
        answer = llm.invoke(prompt).content
        state["answer"] = answer
        return {"answer": answer}
    except Exception as e:
        print(e)
        fallback_answer = "Oops! 😅 Something went wrong. Please try again. Bejo’s always here to help! 💡"
        state["answer"] = fallback_answer
        return {"answer": fallback_answer}
    finally:
        use_memory(state)
