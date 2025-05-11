from typing_extensions import TypedDict, Annotated, Literal


class State(TypedDict):
    question: str
    user_id: str
    thread_id: str
    requires_db: bool
    interactive_response: str
    sql_query: str
    result_query: str
    answer: str


class RelevanceOutput(TypedDict):
    requires_db: Annotated[
        Literal["DATABASE", "INTERACTIVE"],
        "Whether the question requires database access",
    ]


class QueryOutput(TypedDict):
    sql_query: Annotated[str, "Syntactically correct SQL Query"]
