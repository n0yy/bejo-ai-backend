"""
BEJO SQL Assistant - Main Application Entry Point
"""

import os
import sys
import logging
import signal
import argparse
from dotenv import load_dotenv
from uuid import uuid4
import traceback
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress

from agent import create_bejo_agent
from utils.memory import use_memory, get_user_memories, format_chat_history

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("bejo.log"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Rich console for better output formatting
console = Console()


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    console.print(
        "\n\n[bold yellow]Exiting BEJO SQL Assistant. Have a great day! 👋[/bold yellow]"
    )
    sys.exit(0)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="BEJO SQL Assistant")
    parser.add_argument("--user", "-u", type=str, help="User ID")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    return parser.parse_args()


def display_welcome():
    """Display welcome message"""
    console.print(
        Panel.fit(
            "[bold blue]BEJO SQL Assistant[/bold blue] - Type 'exit' to quit\n"
            "A friendly AI assistant to help with your database queries 🔍",
            border_style="blue",
            title="Welcome",
            subtitle="v1.0.0",
        )
    )


def main():
    """
    Main entry point for the BEJO SQL Assistant application.
    """
    # Handle Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # Load environment variables
    load_dotenv()

    # Parse arguments
    args = parse_arguments()

    # Set logging level based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Display welcome message
    display_welcome()

    # Create the agent
    try:
        with Progress() as progress:
            task = progress.add_task("[green]Initializing BEJO...", total=100)
            progress.update(task, advance=30)
            agent = create_bejo_agent()
            progress.update(task, advance=70)
    except Exception as e:
        console.print(f"[bold red]Failed to initialize BEJO:[/bold red] {str(e)}")
        logger.error(f"Initialization error: {str(e)}")
        logger.debug(traceback.format_exc())
        return

    # Set up the config for agent
    thread_id = str(uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # Get user ID
    user_id = (
        args.user
        if args.user
        else console.input("[bold cyan]Enter your user_id:[/bold cyan] ")
    )
    console.print(f"[green]Session started for user:[/green] {user_id}")
    console.print(f"[dim]Session ID: {thread_id}[/dim]")

    # Set the current user and session in the agent module
    from agent import set_current_user, set_current_session

    set_current_user(user_id)
    set_current_session(thread_id)

    # Main interaction loop
    while True:
        try:
            # Get user input
            question = console.input("\n[bold white]You:[/bold white] ")

            # Check for exit command
            if question.lower() in ["exit", "quit", "bye"]:
                console.print(
                    "\n[bold yellow]Thank you for using BEJO SQL Assistant! Have a great day! 👋[/bold yellow]"
                )
                break

            # Get chat history
            raw_history = get_user_memories(
                user_id=user_id, session_id=thread_id, is_session=True
            )
            chat_history = format_chat_history(raw_history)

            # Process the question
            console.print("\n[bold cyan]BEJO:[/bold cyan] ", end="")

            # Stream the response
            final_answer = ""
            response = agent.stream({"input": question}, config=config)

            for chunk in response:
                for msg in chunk.get("messages", []):
                    content = getattr(msg, "content", None)
                    if content:
                        console.print(content, end="", highlight=False)
                        final_answer += content

            console.print()  # Add a newline after the response

            # Save the interaction
            use_memory({"question": question, "answer": final_answer}, user_id, config)

        except KeyboardInterrupt:
            console.print(
                "\n\n[bold yellow]Exiting BEJO SQL Assistant. Have a great day! 👋[/bold yellow]"
            )
            break
        except Exception as e:
            error_msg = str(e)
            console.print(f"\n[bold red]Error:[/bold red] {error_msg}")
            logger.error(f"Runtime error: {error_msg}")
            logger.debug(traceback.format_exc())
            console.print(
                "\n[italic cyan]Oops! 😅 Something went wrong. Please try again. Bejo's always here to help! 💡[/italic cyan]"
            )


if __name__ == "__main__":
    main()
