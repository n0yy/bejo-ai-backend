from dotenv import load_dotenv
from graph.builder import build_graph
from langgraph.checkpoint.memory import MemorySaver


def main():
    load_dotenv()

    memory = MemorySaver()
    graph = build_graph(memory)

    config = {"configurable": {"thread_id": "session_id_1"}}

    print("BEJO SQL Assistant - Type 'exit' to quit")
    print("-------------------------------------")

    while True:
        question = input("You : ")
        if question.lower() == "exit":
            break

        for step in graph.stream({"question": question}, config, stream_mode="updates"):
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
