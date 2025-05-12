from langchain_core.tools import tool
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langgraph.checkpoint.memory import MemorySaver
from langchain import hub

prompt = hub.pull("hwchase17/openai-functions-agent")

memory = MemorySaver()
COLLECTION_NAME = "knowledge_layer_1"
qdrant = QdrantClient(host="localhost", port=6333)
embedding = OllamaEmbeddings(model="nomic-embed-text:latest")
vector_store = QdrantVectorStore(
    client=qdrant,
    collection_name=COLLECTION_NAME,
    embedding=embedding,
)
llm = init_chat_model(
    "gemini-2.0-flash", model_provider="google_genai", temperature=0.7
)


@tool(response_format="content")
def retrive(query: str):
    """
    Retrieves relevant documents from a knowledge base given a natural language query.

    Args:
    query (str): The natural language query to retrieve documents for.

    Returns:
    str: A serialized string containing the source and content of the retrieved documents.
    """
    retrieved_docs = vector_store.similarity_search(query, k=3)
    serialized = "\n\n".join(
        f"Source: {doc.metadata['source']}\nContent: {doc.page_content}"
        for doc in retrieved_docs
    )
    return serialized


config = {"configurable": {"thread_id": "session_id_1"}}

# system_prompt = ChatPromptTemplate.from_messages(
#     [
#         (
#             "system",
#             "You are an expert assistant for internal knowledge management. Be concise, professional, and only answer based on retrieved documents. Your name is BEJO.",
#         ),
#         ("human", "{{input}}"),
#     ]
# )

# agent_executor = create_react_agent(
#     llm,
#     tools=[retrive],
#     checkpointer=memory,
#     # prompt=system_prompt,
# )

agent = create_tool_calling_agent(llm, [retrive], prompt)
agent_executor = AgentExecutor(agent=agent, tools=[retrive])
while True:
    question = input("You : ")
    if question.lower() == "exit":
        break

    for event in agent_executor.stream(
        {"input": question},
        config=config,
    ):
        event["messages"][-1].pretty_print()
