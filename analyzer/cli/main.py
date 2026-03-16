# main.py
# ─────────────────────────────────────────────────────────────
# CLI entry point for the tweet analyzer.
#
# Usage: python -m analyzer.cli chat
# ─────────────────────────────────────────────────────────────

import click
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@click.group()
@click.version_option(version="1.0.0", prog_name="xScraper Analyzer")
def cli():
    """xScraper Analytics CLI - Analyze tweets with AI."""
    pass


@cli.command()
@click.option(
    "--tweets-file",
    "-f",
    default="tweets.json",
    help="Path to tweets.json file",
)
def chat(tweets_file: str):
    """Start interactive chat session for tweet analysis."""
    from analyzer.cli.chat import start_chat_session

    start_chat_session(tweets_file)


@cli.command()
@click.option(
    "--tweets-file",
    "-f",
    default="tweets.json",
    help="Path to tweets.json file",
)
def style(tweets_file: str):
    """Analyze writing style (one-shot, no interactive chat)."""
    from analyzer.cli.chat import run_single_command

    run_single_command("style", tweets_file)


@cli.command()
@click.option(
    "--tweets-file",
    "-f",
    default="tweets.json",
    help="Path to tweets.json file",
)
def hooks(tweets_file: str):
    """Extract and rank opening hooks (one-shot)."""
    from analyzer.cli.chat import run_single_command

    run_single_command("hooks", tweets_file)


@cli.command()
@click.option(
    "--tweets-file",
    "-f",
    default="tweets.json",
    help="Path to tweets.json file",
)
def engagement(tweets_file: str):
    """Analyze engagement patterns (one-shot)."""
    from analyzer.cli.chat import run_single_command

    run_single_command("engagement", tweets_file)


@cli.command()
@click.option(
    "--tweets-file",
    "-f",
    default="tweets.json",
    help="Path to tweets.json file",
)
def profile(tweets_file: str):
    """Generate comprehensive user profile (one-shot)."""
    from analyzer.cli.chat import run_single_command

    run_single_command("profile", tweets_file)


@cli.command()
@click.argument("topic")
@click.option(
    "--tweets-file",
    "-f",
    default="tweets.json",
    help="Path to tweets.json file",
)
@click.option(
    "--count",
    "-n",
    default=3,
    help="Number of tweets to generate",
)
def generate(topic: str, tweets_file: str, count: int):
    """Generate tweets in the user's voice about a TOPIC."""
    from analyzer.cli.chat import run_generate_command

    run_generate_command(topic, tweets_file, count)


@cli.command()
def check():
    """Check if OpenAI API key is configured."""
    from rich.console import Console
    from analyzer import config as analyzer_config

    console = Console()

    api_key = analyzer_config.OPENAI_API_KEY

    if api_key:
        console.print("[green]OpenAI API key is configured.[/green]")
        console.print(f"Key: {api_key[:8]}...{api_key[-4:]}")
    else:
        console.print("[red]OpenAI API key is NOT configured.[/red]")
        console.print("Set it with: export OPENAI_API_KEY='your-key'")


if __name__ == "__main__":
    cli()
