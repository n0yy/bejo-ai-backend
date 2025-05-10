from config.db import get_database
from config.llm import get_llm
from prompts.query_prompt import query_prompt_template
from state.types import State, QueryOutput


def write_query(state: State):
    db = get_database()
    llm = get_llm()

    # Buat prompt untuk menghasilkan query
    prompt = query_prompt_template.invoke(
        {
            "dialect": db.dialect,
            "top_k": 5,
            "input": state["question"],
            "table_context": db.get_context(),
        }
    )

    # Gunakan structured output untuk mendapatkan query yang terformat dengan benar
    structured_output = llm.with_structured_output(QueryOutput)
    result = structured_output.invoke(prompt)

    return {"sql_query": result["sql_query"]}
