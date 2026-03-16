# chat.py
# ─────────────────────────────────────────────────────────────
# Interactive chat loop for tweet analysis.
# ─────────────────────────────────────────────────────────────

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.live import Live
from rich.text import Text

from analyzer import data_loader, metrics
from analyzer.cli import llm_client, context_builder, prompts


console = Console()


def start_chat_session(tweets_file: str = "tweets.json"):
    """
    Start an interactive chat session for tweet analysis.

    Args:
        tweets_file: Path to tweets.json
    """
    console.print(Panel.fit(
        "[bold blue]xScraper Analytics CLI[/bold blue]\n"
        "Interactive tweet analysis with AI",
        border_style="blue"
    ))

    # Load tweets
    console.print("\n[dim]Loading tweets...[/dim]")
    tweets = data_loader.load_tweets(tweets_file)

    if not tweets:
        console.print("[red]No tweets found. Run the scraper first.[/red]")
        return

    author = data_loader.get_author_info(tweets)
    original = data_loader.get_original_tweets(tweets)

    console.print(f"[green]Loaded {len(tweets)} tweets from @{author['author_handle']}[/green]")
    console.print(f"[dim]({len(original)} original, {len(tweets) - len(original)} retweets)[/dim]\n")

    # Initialize LLM client
    try:
        client = llm_client.get_client()
        console.print(f"[dim]Using model: {client.model}[/dim]\n")
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        console.print("[yellow]Set OPENAI_API_KEY environment variable to enable AI features.[/yellow]")
        return

    # Show help
    _print_help()

    # Chat loop
    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]>[/bold cyan]").strip()

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "q"):
                console.print("[dim]Goodbye![/dim]")
                break

            if user_input.lower() == "help":
                _print_help()
                continue

            # Route command
            _handle_command(user_input, tweets, author, client)

        except KeyboardInterrupt:
            console.print("\n[dim]Goodbye![/dim]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def _handle_command(
    command: str,
    tweets: list[dict],
    author: dict,
    client: llm_client.LLMClient
):
    """Route and handle a user command."""

    cmd_lower = command.lower()

    if cmd_lower == "style":
        _run_style_analysis(tweets, client)

    elif cmd_lower == "hooks":
        _run_hooks_analysis(tweets, client)

    elif cmd_lower == "engagement":
        _run_engagement_analysis(tweets, client)

    elif cmd_lower == "profile":
        _run_profile_analysis(tweets, author, client)

    elif cmd_lower.startswith("generate "):
        topic = command[9:].strip()
        if topic:
            _run_generate(tweets, topic, client)
        else:
            console.print("[yellow]Usage: generate <topic>[/yellow]")

    elif cmd_lower.startswith("ask "):
        question = command[4:].strip()
        if question:
            _run_ask(tweets, author, question, client)
        else:
            console.print("[yellow]Usage: ask <question>[/yellow]")

    else:
        console.print(f"[yellow]Unknown command: {command}[/yellow]")
        console.print("[dim]Type 'help' for available commands.[/dim]")


def _run_style_analysis(tweets: list[dict], client: llm_client.LLMClient):
    """Run writing style analysis."""
    console.print("\n[dim]Analyzing writing style...[/dim]\n")

    context = context_builder.build_analysis_context(tweets)
    prompt = prompts.WRITING_ANALYSIS_PROMPT.format(tweet_samples=context)

    _stream_response(client, prompt, "Analyzing tweets...")


def _run_hooks_analysis(tweets: list[dict], client: llm_client.LLMClient):
    """Run hooks/opening lines analysis."""
    console.print("\n[dim]Analyzing hooks...[/dim]\n")

    context = context_builder.build_hooks_context(tweets)
    prompt = prompts.HOOKS_ANALYSIS_PROMPT.format(hooks=context)

    _stream_response(client, prompt, "Analyzing hooks...")


def _run_engagement_analysis(tweets: list[dict], client: llm_client.LLMClient):
    """Run engagement correlation analysis."""
    console.print("\n[dim]Analyzing engagement patterns...[/dim]\n")

    context = context_builder.build_engagement_context(tweets)
    prompt = prompts.ENGAGEMENT_ANALYSIS_PROMPT.format(
        top_tweets=context["top_tweets"],
        bottom_tweets=context["bottom_tweets"],
        stats_comparison=context["stats_comparison"],
        total_analyzed=context["total_analyzed"],
    )

    _stream_response(client, prompt, "Analyzing engagement...")


def _run_profile_analysis(
    tweets: list[dict],
    author: dict,
    client: llm_client.LLMClient
):
    """Run comprehensive user profile analysis."""
    console.print("\n[dim]Building user profile...[/dim]\n")

    context = context_builder.build_user_profile_context(tweets)
    prompt = prompts.USER_PROFILE_PROMPT.format(
        handle=author.get("author_handle", "unknown"),
        name=author.get("author_name", "Unknown"),
        tweet_samples=context["tweet_samples"],
        total_tweets=context["total_tweets"],
        topics=context["topics"],
        avg_engagement=context["avg_engagement"],
        reply_ratio=context["reply_ratio"],
    )

    _stream_response(client, prompt, "Building profile...")


def _run_generate(
    tweets: list[dict],
    topic: str,
    client: llm_client.LLMClient,
    count: int = 3
):
    """Generate tweets in the author's voice."""
    console.print(f"\n[dim]Generating tweets about '{topic}'...[/dim]\n")

    examples = context_builder.build_voice_clone_context(tweets)
    prompt = prompts.VOICE_CLONE_PROMPT.format(
        examples=examples,
        topic=topic,
        count=count,
    )

    _stream_response(client, prompt, "Generating...")


def _run_ask(
    tweets: list[dict],
    author: dict,
    question: str,
    client: llm_client.LLMClient
):
    """Answer a free-form question about the tweets."""
    console.print("\n[dim]Thinking...[/dim]\n")

    context = context_builder.build_analysis_context(tweets, max_tweets=50)
    avg = metrics.calc_avg_engagement(data_loader.get_original_tweets(tweets))

    prompt = prompts.ASK_PROMPT.format(
        tweet_samples=context,
        handle=author.get("author_handle", "unknown"),
        total_tweets=len(tweets),
        avg_likes=avg.get("avg_likes", 0),
        question=question,
    )

    _stream_response(client, prompt, "Answering...")


def _stream_response(
    client: llm_client.LLMClient,
    user_message: str,
    thinking_text: str = "Thinking..."
):
    """Stream and display LLM response."""
    full_response = ""

    with Live(Text(thinking_text, style="dim"), refresh_per_second=10) as live:
        for chunk in client.chat_stream(
            system_prompt="You are a helpful Twitter/X content analyst.",
            user_message=user_message,
        ):
            full_response += chunk
            # Update display with markdown
            live.update(Markdown(full_response))

    console.print()  # Extra newline after response


def _print_help():
    """Print available commands."""
    help_text = """
[bold]Available Commands:[/bold]

  [cyan]style[/cyan]            Analyze voice, tone, sentence structure, vocabulary
  [cyan]hooks[/cyan]            Extract and rank opening lines by engagement
  [cyan]generate[/cyan] <topic> Create tweets in the author's voice
  [cyan]engagement[/cyan]       What content patterns drive engagement
  [cyan]profile[/cyan]          Generate comprehensive user profile
  [cyan]ask[/cyan] <question>   Ask any question about the writing style

  [dim]help[/dim]             Show this help message
  [dim]quit[/dim]             Exit the chat
"""
    console.print(Panel(help_text, title="Help", border_style="dim"))


# ── One-shot command runners ────────────────────────────────


def run_single_command(command: str, tweets_file: str = "tweets.json"):
    """
    Run a single analysis command without interactive mode.

    Args:
        command: Command to run (style, hooks, engagement, profile)
        tweets_file: Path to tweets.json
    """
    # Load tweets
    tweets = data_loader.load_tweets(tweets_file)

    if not tweets:
        console.print("[red]No tweets found. Run the scraper first.[/red]")
        return

    author = data_loader.get_author_info(tweets)

    console.print(f"[dim]Analyzing {len(tweets)} tweets from @{author['author_handle']}...[/dim]\n")

    # Initialize LLM client
    try:
        client = llm_client.get_client()
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        return

    # Route command
    if command == "style":
        _run_style_analysis(tweets, client)
    elif command == "hooks":
        _run_hooks_analysis(tweets, client)
    elif command == "engagement":
        _run_engagement_analysis(tweets, client)
    elif command == "profile":
        _run_profile_analysis(tweets, author, client)
    else:
        console.print(f"[red]Unknown command: {command}[/red]")


def run_generate_command(
    topic: str,
    tweets_file: str = "tweets.json",
    count: int = 3
):
    """
    Run tweet generation command.

    Args:
        topic: Topic to generate tweets about
        tweets_file: Path to tweets.json
        count: Number of tweets to generate
    """
    # Load tweets
    tweets = data_loader.load_tweets(tweets_file)

    if not tweets:
        console.print("[red]No tweets found. Run the scraper first.[/red]")
        return

    author = data_loader.get_author_info(tweets)

    console.print(f"[dim]Generating tweets in @{author['author_handle']}'s voice...[/dim]\n")

    # Initialize LLM client
    try:
        client = llm_client.get_client()
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        return

    # Generate
    examples = context_builder.build_voice_clone_context(tweets)
    prompt = prompts.VOICE_CLONE_PROMPT.format(
        examples=examples,
        topic=topic,
        count=count,
    )

    _stream_response(client, prompt, "Generating...")
