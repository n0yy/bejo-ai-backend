from tabulate import tabulate
from config.db import get_database
from state.types import State
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool


def execute_query(state: State):
    """
    Execute SQL query and return result as markdown table.

    The result of the query is returned as a markdown table if the result is a list of tuples.
    Otherwise, the result is returned as a string.
    """
    db = get_database()
    execute_query_tool = QuerySQLDatabaseTool(db=db)

    result = execute_query_tool.invoke(state["sql_query"])

    if isinstance(result, list) and len(result) > 0 and isinstance(result[0], tuple):
        headers = [f"Column {i+1}" for i in range(len(result[0]))]
        markdown_table = tabulate(result, headers=headers, tablefmt="github")
    else:
        markdown_table = str(result)

    return {
        "result_query": markdown_table,
    }
