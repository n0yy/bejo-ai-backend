from app.config.llm import get_llm
from app.prompts.relevance_prompt import check_relevance_template
from app.state.types import State, RelevanceOutput


def check_relevance(state: State):
    """
    Determine if the question requires database access.

    If the question requires database access, branch to the DATABASE branch.
    Otherwise, branch to the INTERACTIVE branch and include an interactive response.
    """
    llm = get_llm()

    prompt = check_relevance_template.invoke({"question": state["question"]})

    structured_output = llm.with_structured_output(RelevanceOutput)
    result = structured_output.invoke(prompt)

    if result["requires_db"] == "DATABASE":
        return {"branch": "DATABASE"}
    else:
        return {
            "branch": "INTERACTIVE",
            "interactive_response": "This is a chat-type question.",
        }
