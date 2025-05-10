from langgraph.graph import START, StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from state.types import State
from tools.relevance_checker import check_relevance
from tools.query_writer import write_query
from tools.query_executor import execute_query
from tools.answer_generator import generate_answer
from tools.interactive_handler import handle_interactive


def build_graph(memory: MemorySaver = None):
    """
    Build a StateGraph representing the workflow of generating an answer to a user query.

    The graph consists of the following nodes:

    - check_relevance: determine if the query requires database access
    - write_query: generate a SQL query based on the user query
    - execute_query: execute the SQL query and format the result
    - generate_answer: generate an answer based on the SQL result
    - handle_interactive: handle non-database queries

    The graph has the following edges:

    - START -> check_relevance
    - check_relevance -> write_query (if requires database access)
    - check_relevance -> handle_interactive (if does not require database access)
    - write_query -> execute_query
    - execute_query -> generate_answer
    - generate_answer -> END
    - handle_interactive -> END

    The graph is compiled with a memory checkpointer and an interrupt_before condition
    on the execute_query node to allow for cancellation of long-running queries.
    """
    if memory is None:
        memory = MemorySaver()

    graph_builder = StateGraph(State)

    graph_builder.add_node("check_relevance", check_relevance)
    graph_builder.add_node("write_query", write_query)
    graph_builder.add_node("execute_query", execute_query)
    graph_builder.add_node("generate_answer", generate_answer)
    graph_builder.add_node("handle_interactive", handle_interactive)

    graph_builder.add_edge(START, "check_relevance")

    graph_builder.add_conditional_edges(
        "check_relevance",
        lambda x: x["branch"],
        {"DATABASE": "write_query", "INTERACTIVE": "handle_interactive"},
    )

    graph_builder.add_edge("write_query", "execute_query")
    graph_builder.add_edge("execute_query", "generate_answer")
    graph_builder.add_edge("generate_answer", END)

    graph_builder.add_edge("handle_interactive", END)

    return graph_builder.compile(
        checkpointer=memory, interrupt_before=["execute_query"]
    )
