from config.llm import get_llm
from state.types import State
from prompts.query_prompt import ANSWER_GENERATION_PROMPT
from utils.memory import use_memory, get_user_memories


def generate_answer(state: State):
    """
    Generate an answer based on the given state.

    If the result query is empty, returns a fallback answer.
    Otherwise, generates an answer based on the result query and other
    information in the state, and saves the answer to the state.

    Args:
        state (State): The current state of the workflow, which should contain
            the result query and other relevant information.

    Returns:
        dict: A dictionary containing the generated answer, or a fallback
            answer if there was an error.
    """
    llm = get_llm()

    # Get thread_id and user_id from state
    thread_id = state.get("thread_id", "session-id")
    user_id = state.get("user_id", "user_id_1")

    if not state["result_query"].strip():
        return {
            "answer": "Oops! 😅 It looks like there's no data matching that request right now. Please check the filters or try a different question. Bejo's always here to help! 💡"
        }
    else:
        try:
            prompt = ANSWER_GENERATION_PROMPT.format(
                question=state["question"],
                user_memories=get_user_memories(
                    user_id=user_id, search=True, question=state["question"]
                ),
                conversation_history=get_user_memories(
                    user_id=user_id, session_id=thread_id, is_session=True
                ),
                result_query=state["result_query"],
            )

            answer = llm.invoke(prompt).content
            state["answer"] = answer
            return {"answer": answer}
        except Exception as e:
            print(f"Error generating answer: {e}")
            fallback_answer = "Oops! 😅 Something went wrong. Please try again. Bejo's always here to help! 💡"
            state["answer"] = fallback_answer
            return {"answer": fallback_answer}
        finally:
            use_memory(state, user_id=user_id, session_id=thread_id)
