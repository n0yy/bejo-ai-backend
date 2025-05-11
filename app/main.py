from dotenv import load_dotenv
from graph.builder import build_graph
from langgraph.checkpoint.memory import MemorySaver


def main():
    load_dotenv()

    memory = MemorySaver()
    graph = build_graph(memory)

    # Set up session and user info
    session_id = "session_id_1"
    user_id = input("Enter user ID (or press Enter for default): ") or "user_id_1"

    config = {"configurable": {"thread_id": session_id}}

    print(f"BEJO SQL Assistant - User: {user_id} - Type 'exit' to quit")
    print("-------------------------------------")

    while True:
        question = input("You: ")
        if question.lower() == "exit":
            break

        # Pass both question, thread_id, and user_id to the graph
        for step in graph.stream(
            {"question": question, "thread_id": session_id, "user_id": user_id},
            config,
            stream_mode="updates",
        ):
            print(step)

        if "__interrupt__" in step:
            try:
                user_approval = input("Do you want execute this query? (y/n): ")
            except Exception:
                user_approval = "n"

            if user_approval.lower() == "y":
                for step in graph.stream(None, config, stream_mode="updates"):
                    print(step)
            else:
                print("Operation cancelled by user.")


if __name__ == "__main__":
    main()
