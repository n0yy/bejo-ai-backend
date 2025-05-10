from langchain_core.prompts import ChatPromptTemplate


RELEVANCE_PROMPT_TEMPLATE = """
You are an intelligent assistant that helps determine if a user question requires 
database access to answer properly.

If the user is:
1. Asking a general greeting or chat message (like "hi", "hello", "how are you")
2. Making a statement rather than asking a question
3. Asking a question that clearly doesn't require database access
4. Asking a philosophical, personal, or non-data related question

Then respond with "INTERACTIVE" only.

If the user is requesting data or information that could be in a database, 
respond with "DATABASE" only.

User Query: {question}
"""

check_relevance_template = ChatPromptTemplate.from_template(RELEVANCE_PROMPT_TEMPLATE)
