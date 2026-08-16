import asyncio

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
import time

from api.schemas.chat import ChatStreamChunk
from api.services.chat import process_chat
from environment import BUILD_COMMIT_ID
from infrastructure.checkpointer.client import checkpointer_close, checkpointer_setup, get_checkpointer
from utils.embeddings import embedding_func, compressor

console = Console()

def get_bot_response(user_input: str) -> str:
    # Replace this mock function with your LLM API call (e.g., OpenAI, Gemini, Ollama)
    return (
        f"You asked: **{user_input}**\n\n"
        "Here is a code example:\n"
        "```python\n"
        "def greet(name):\n"
        "    return f'Hello, {name}!'\n"
        "```"
    )

async def main():
    await checkpointer_setup()

    console.print(Panel.fit(
        f"[bold cyan]🤖 Practce-Lang ({BUILD_COMMIT_ID})[/bold cyan]\nType 'exit' or 'quit' to end the session.",
        border_style="cyan"
    ))

    while True:
        try:
            user_input = console.input("\n[bold green]You:[/bold green] ")
            interrupt_id = None
            response = None

            if user_input.strip().lower() in ["exit", "quit"]:
                console.print("[yellow]Goodbye![/yellow]")
                break

            if not user_input.strip():
                continue

            def on_yield(message: str, is_summary: bool, interrupt: str | None) -> ChatStreamChunk:
                nonlocal interrupt_id
                nonlocal response
                interrupt_id = interrupt
                response = message
                return ChatStreamChunk(message=message, summary=message if is_summary else '')

            # Display a spinner while waiting for the LLM
            with console.status("[bold blue]Thinking...[/bold blue]"):
                # time.sleep(1) # Simulate network request latency
                # response = get_bot_response(user_input)
                async for _ in process_chat(
                    message=user_input.strip(),
                    embedding_func=embedding_func,
                    compressor=compressor,
                    checkpointer=get_checkpointer(),
                    interrupt_id=interrupt_id,
                    mcp_code="",
                    session_id="tui",
                    yield_formatter=on_yield,

                ):
                    pass
                

            # Render response as styled Markdown
            console.print("\n[bold magenta]Bot:[/bold magenta]")
            console.print(Markdown(response or "Empty response."))

        except (KeyboardInterrupt, EOFError):
            await checkpointer_close()
            console.print("\n[yellow]Goodbye![/yellow]")
            break

if __name__ == "__main__":
    asyncio.run(main())