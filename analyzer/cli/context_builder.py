# context_builder.py
# ─────────────────────────────────────────────────────────────
# Build LLM context from tweets for different analysis modes.
# ─────────────────────────────────────────────────────────────

import random
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analyzer import config as analyzer_config
from analyzer import metrics, data_loader


def build_voice_clone_context(tweets: list[dict], n_examples: int = None) -> str:
    """
    Build context for few-shot voice cloning.

    Selects best examples prioritizing high-engagement tweets
    and mixing in recent content for freshness.

    Args:
        tweets: Full list of tweets
        n_examples: Number of examples to include

    Returns:
        Formatted string of example tweets
    """
    n_examples = n_examples or analyzer_config.VOICE_CLONE_EXAMPLES

    # Filter to original tweets only (no RTs)
    original = [t for t in tweets if not t.get("is_retweet")]

    if not original:
        return "No original tweets found."

    # Prioritize top-engaged tweets as voice examples
    top_engaged = sorted(
        original,
        key=lambda t: t.get("likes", 0),
        reverse=True
    )[:n_examples - 5]

    # Mix in recent tweets
    recent = sorted(
        original,
        key=lambda t: t.get("created_at_dt") or "",
        reverse=True
    )[:5]

    # Combine and deduplicate
    seen_ids = set()
    examples = []

    for t in top_engaged + recent:
        if t["tweet_id"] not in seen_ids:
            seen_ids.add(t["tweet_id"])
            examples.append(t)

    examples = examples[:n_examples]

    # Format examples
    lines = []
    for t in examples:
        likes = t.get("likes", 0)
        text = t.get("text", "").strip()
        lines.append(f"Tweet ({likes} likes):\n{text}")

    return "\n\n---\n\n".join(lines)


def build_analysis_context(tweets: list[dict], max_tweets: int = None) -> str:
    """
    Build context for general writing analysis.

    For small datasets, includes all tweets.
    For large datasets, samples strategically.

    Args:
        tweets: Full list of tweets
        max_tweets: Maximum tweets to include

    Returns:
        Formatted string of tweets for analysis
    """
    max_tweets = max_tweets or analyzer_config.MAX_CONTEXT_TWEETS

    original = [t for t in tweets if not t.get("is_retweet")]

    if not original:
        return "No original tweets found."

    # If small dataset, use all
    if len(original) <= max_tweets:
        selected = original
    else:
        # Strategic sampling
        selected = _sample_tweets(
            original,
            top_engaged=analyzer_config.TOP_ENGAGED_SAMPLE,
            recent=analyzer_config.RECENT_SAMPLE,
            random_n=analyzer_config.RANDOM_SAMPLE,
        )

    # Format for context
    lines = []
    for t in selected:
        likes = t.get("likes", 0)
        rts = t.get("retweets", 0)
        text = t.get("text", "").strip()
        lines.append(f"[{likes} likes, {rts} RTs]\n{text}")

    return "\n\n---\n\n".join(lines)


def build_engagement_context(tweets: list[dict]) -> dict:
    """
    Build context for engagement correlation analysis.

    Returns structured data comparing top vs low performers.

    Args:
        tweets: Full list of tweets

    Returns:
        Dict with top_tweets, bottom_tweets, and stats
    """
    correlations = metrics.analyze_engagement_correlations(tweets)

    # Format top performers
    top_hooks = correlations.get("top_hooks", [])[:10]
    top_formatted = "\n\n".join([
        f"[{h['likes']} likes]\n{h['full_text']}"
        for h in top_hooks
    ])

    # Get bottom performers for comparison
    original = [t for t in tweets if not t.get("is_retweet")]
    by_engagement = sorted(
        original,
        key=metrics.calc_weighted_engagement,
        reverse=True
    )
    bottom_tweets = by_engagement[-10:] if len(by_engagement) > 10 else []

    bottom_formatted = "\n\n".join([
        f"[{t.get('likes', 0)} likes]\n{t.get('text', '')}"
        for t in bottom_tweets
    ])

    # Format stats comparison
    top_stats = correlations.get("top_performers", {})
    low_stats = correlations.get("low_performers", {})

    stats_lines = [
        "METRIC | TOP 10% | BOTTOM 50%",
        "-" * 40,
        f"Avg length | {top_stats.get('avg_length', 0):.0f} | {low_stats.get('avg_length', 0):.0f}",
        f"Has media | {top_stats.get('has_media_pct', 0):.0f}% | {low_stats.get('has_media_pct', 0):.0f}%",
        f"Has links | {top_stats.get('has_links_pct', 0):.0f}% | {low_stats.get('has_links_pct', 0):.0f}%",
        f"Questions | {top_stats.get('question_pct', 0):.0f}% | {low_stats.get('question_pct', 0):.0f}%",
    ]

    return {
        "top_tweets": top_formatted,
        "bottom_tweets": bottom_formatted,
        "stats_comparison": "\n".join(stats_lines),
        "total_analyzed": correlations.get("total_analyzed", 0),
    }


def build_user_profile_context(tweets: list[dict]) -> dict:
    """
    Build context for comprehensive user profiling.

    Args:
        tweets: Full list of tweets

    Returns:
        Dict with tweet_samples and computed statistics
    """
    original = [t for t in tweets if not t.get("is_retweet")]

    # Get author info
    author = data_loader.get_author_info(tweets)

    # Sample tweets
    sample = _sample_tweets(original, top_engaged=30, recent=20, random_n=0)
    samples_formatted = "\n\n---\n\n".join([
        t.get("text", "") for t in sample
    ])

    # Get topics from hashtags
    from collections import Counter
    all_hashtags = []
    for t in original:
        all_hashtags.extend(t.get("hashtags", []))
    topics = [tag for tag, _ in Counter(all_hashtags).most_common(10)]

    # Calculate stats
    avg_engagement = metrics.calc_avg_engagement(original)
    reply_ratio = sum(1 for t in original if t.get("is_reply")) / len(original) * 100 if original else 0

    return {
        "author": author,
        "tweet_samples": samples_formatted,
        "total_tweets": len(original),
        "topics": ", ".join(topics) if topics else "No hashtags found",
        "avg_engagement": avg_engagement.get("avg_likes", 0),
        "reply_ratio": round(reply_ratio, 1),
    }


def build_hooks_context(tweets: list[dict], top_n: int = 30) -> str:
    """
    Build context focused on opening hooks/lines.

    Args:
        tweets: Full list of tweets
        top_n: Number of top hooks to include

    Returns:
        Formatted string of hooks with engagement data
    """
    hooks = metrics.extract_hooks(tweets)[:top_n]

    if not hooks:
        return "No hooks found."

    lines = []
    for i, h in enumerate(hooks, 1):
        lines.append(
            f"{i}. [{h['likes']} likes, {h['views']:,} views]\n"
            f"   Hook: \"{h['hook']}\"\n"
            f"   Full: {h['full_text'][:200]}..."
        )

    return "\n\n".join(lines)


def _sample_tweets(
    tweets: list[dict],
    top_engaged: int = 50,
    recent: int = 30,
    random_n: int = 20,
) -> list[dict]:
    """
    Strategically sample tweets for context.

    Args:
        tweets: List of tweets to sample from
        top_engaged: Number of top-engaged tweets
        recent: Number of recent tweets
        random_n: Number of random tweets

    Returns:
        Sampled list of tweets
    """
    seen_ids = set()
    result = []

    # Top engaged
    by_likes = sorted(tweets, key=lambda t: t.get("likes", 0), reverse=True)
    for t in by_likes[:top_engaged]:
        if t["tweet_id"] not in seen_ids:
            seen_ids.add(t["tweet_id"])
            result.append(t)

    # Recent
    by_date = sorted(
        [t for t in tweets if t.get("created_at_dt")],
        key=lambda t: t["created_at_dt"],
        reverse=True
    )
    for t in by_date[:recent]:
        if t["tweet_id"] not in seen_ids:
            seen_ids.add(t["tweet_id"])
            result.append(t)

    # Random
    remaining = [t for t in tweets if t["tweet_id"] not in seen_ids]
    if remaining and random_n > 0:
        random_sample = random.sample(remaining, min(random_n, len(remaining)))
        result.extend(random_sample)

    return result


def format_tweet_for_context(tweet: dict, include_stats: bool = True) -> str:
    """
    Format a single tweet for LLM context.

    Args:
        tweet: Tweet dict
        include_stats: Whether to include engagement stats

    Returns:
        Formatted tweet string
    """
    text = tweet.get("text", "").strip()

    if include_stats:
        likes = tweet.get("likes", 0)
        rts = tweet.get("retweets", 0)
        views = tweet.get("views", 0)
        return f"[{likes} likes, {rts} RTs, {views:,} views]\n{text}"

    return text
