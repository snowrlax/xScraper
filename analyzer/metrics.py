# metrics.py
# ─────────────────────────────────────────────────────────────
# Engagement calculations, writing pattern analysis, and
# statistical aggregations for tweet data.
# ─────────────────────────────────────────────────────────────

import re
from collections import Counter
from datetime import datetime
from typing import Optional


# ── Engagement Calculations ─────────────────────────────────────


def calc_weighted_engagement(tweet: dict) -> float:
    """
    Calculate engagement using X's algorithm weights.

    Weights based on X's known ranking factors:
    - Retweets: 20x (high value - amplification)
    - Replies: 13.5x (conversation starters)
    - Quotes: 10x (engaged commentary)
    - Bookmarks: 10x (save for later)
    - Likes: 1x (baseline)
    """
    return (
        tweet.get("likes", 0) * 1
        + tweet.get("retweets", 0) * 20
        + tweet.get("replies", 0) * 13.5
        + tweet.get("quotes", 0) * 10
        + tweet.get("bookmarks", 0) * 10
    )


def calc_engagement_rate(tweet: dict) -> float:
    """
    Engagement rate = (interactions / views) * 100.

    Returns:
        Percentage engagement rate
    """
    views = tweet.get("views", 0)
    if views == 0:
        return 0.0

    interactions = (
        tweet.get("likes", 0)
        + tweet.get("retweets", 0)
        + tweet.get("replies", 0)
        + tweet.get("quotes", 0)
    )
    return (interactions / views) * 100


def calc_avg_engagement(tweets: list[dict]) -> dict:
    """
    Calculate average engagement metrics across tweets.
    """
    if not tweets:
        return {}

    n = len(tweets)
    return {
        "avg_likes": round(sum(t.get("likes", 0) for t in tweets) / n, 1),
        "avg_retweets": round(sum(t.get("retweets", 0) for t in tweets) / n, 1),
        "avg_replies": round(sum(t.get("replies", 0) for t in tweets) / n, 1),
        "avg_quotes": round(sum(t.get("quotes", 0) for t in tweets) / n, 1),
        "avg_bookmarks": round(sum(t.get("bookmarks", 0) for t in tweets) / n, 1),
        "avg_views": round(sum(t.get("views", 0) for t in tweets) / n, 1),
        "avg_engagement_rate": round(
            sum(calc_engagement_rate(t) for t in tweets) / n, 2
        ),
        "avg_weighted_engagement": round(
            sum(calc_weighted_engagement(t) for t in tweets) / n, 1
        ),
    }


# ── Writing Pattern Analysis ─────────────────────────────────────


def extract_hooks(tweets: list[dict]) -> list[dict]:
    """
    Extract opening lines (hooks) with engagement data.
    """
    hooks = []
    original = [t for t in tweets if not t.get("is_retweet")]

    for t in original:
        text = t.get("text", "")
        if not text:
            continue

        # Get first line, strip mentions at start
        first_line = text.split("\n")[0].strip()
        first_line = re.sub(r"^@\w+\s*", "", first_line).strip()

        if not first_line:
            continue

        hooks.append(
            {
                "hook": first_line[:100],
                "full_text": text,
                "likes": t.get("likes", 0),
                "views": t.get("views", 0),
                "engagement_rate": calc_engagement_rate(t),
                "weighted_engagement": calc_weighted_engagement(t),
                "tweet_url": t.get("tweet_url"),
            }
        )

    return sorted(hooks, key=lambda h: h["likes"], reverse=True)


def analyze_writing_patterns(tweets: list[dict]) -> dict:
    """
    Deep analysis of writing patterns in tweet corpus.
    """
    original = [t for t in tweets if not t.get("is_retweet")]

    if not original:
        return {}

    texts = [t.get("text", "") for t in original if t.get("text")]

    return {
        "hooks": extract_hooks(original)[:20],
        "avg_tweet_length": calc_avg_text_length(original),
        "avg_sentence_length": calc_avg_sentence_length(texts),
        "emoji_frequency": count_emoji_usage(texts),
        "formatting": {
            "uses_line_breaks_pct": pct_with_line_breaks(texts),
            "uses_bullets_pct": pct_with_bullets(texts),
            "uses_threads_pct": pct_self_replies(original),
        },
        "structure_types": classify_structures(original),
        "common_phrases": extract_common_phrases(texts),
    }


def calc_avg_text_length(tweets: list[dict]) -> float:
    """Average character length of tweet text."""
    texts = [t.get("text", "") for t in tweets]
    if not texts:
        return 0
    return round(sum(len(t) for t in texts) / len(texts), 1)


def calc_avg_sentence_length(texts: list[str]) -> float:
    """Average words per sentence."""
    all_sentences = []
    for text in texts:
        sentences = re.split(r"[.!?\n]+", text)
        all_sentences.extend([s.strip() for s in sentences if s.strip()])

    if not all_sentences:
        return 0

    word_counts = [len(s.split()) for s in all_sentences]
    return round(sum(word_counts) / len(word_counts), 1)


def count_emoji_usage(texts: list[str]) -> dict:
    """Count emoji frequency and common emojis."""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE,
    )

    all_emojis = []
    tweets_with_emoji = 0

    for text in texts:
        emojis = emoji_pattern.findall(text)
        if emojis:
            tweets_with_emoji += 1
            all_emojis.extend(emojis)

    emoji_counts = Counter(all_emojis)

    return {
        "pct_with_emoji": round((tweets_with_emoji / len(texts)) * 100, 1)
        if texts
        else 0,
        "avg_per_tweet": round(len(all_emojis) / len(texts), 2) if texts else 0,
        "top_emojis": emoji_counts.most_common(10),
    }


def pct_with_line_breaks(texts: list[str]) -> float:
    """Percentage of tweets using line breaks."""
    if not texts:
        return 0
    with_breaks = sum(1 for t in texts if "\n" in t)
    return round((with_breaks / len(texts)) * 100, 1)


def pct_with_bullets(texts: list[str]) -> float:
    """Percentage of tweets using bullet-style formatting."""
    if not texts:
        return 0
    bullet_pattern = re.compile(r"[•→\-\d]+[.\)]\s")
    with_bullets = sum(1 for t in texts if bullet_pattern.search(t))
    return round((with_bullets / len(texts)) * 100, 1)


def pct_self_replies(tweets: list[dict]) -> float:
    """Percentage of tweets that are self-replies (threads)."""
    if not tweets:
        return 0
    self_replies = sum(1 for t in tweets if t.get("is_self_reply"))
    return round((self_replies / len(tweets)) * 100, 1)


def classify_structures(tweets: list[dict]) -> dict:
    """Identify recurring content structure patterns."""
    structures = {
        "question": 0,
        "list": 0,
        "story": 0,
        "announcement": 0,
        "thread": 0,
        "call_to_action": 0,
    }

    for t in tweets:
        text = t.get("text", "")

        # Questions
        if text.strip().endswith("?") or "?" in text[:100]:
            structures["question"] += 1

        # Lists
        if any(marker in text for marker in ["1.", "2.", "•", "→", "- "]):
            structures["list"] += 1

        # Threads (self-replies)
        if t.get("is_self_reply"):
            structures["thread"] += 1

        # Call to action
        cta_patterns = ["comment", "reply", "retweet", "share", "follow", "check out"]
        if any(p in text.lower() for p in cta_patterns):
            structures["call_to_action"] += 1

        # Announcements
        announcement_patterns = ["launching", "announcing", "introducing", "new:", "🚀"]
        if any(p in text.lower() for p in announcement_patterns):
            structures["announcement"] += 1

    # Convert to percentages
    total = len(tweets)
    if total > 0:
        for key in structures:
            structures[key] = round((structures[key] / total) * 100, 1)

    return structures


def extract_common_phrases(texts: list[str], min_words: int = 2, max_words: int = 4) -> list[tuple]:
    """Extract commonly used multi-word phrases."""
    phrase_counter = Counter()

    for text in texts:
        # Clean and tokenize
        clean = re.sub(r"https?://\S+", "", text)  # Remove URLs
        clean = re.sub(r"@\w+", "", clean)  # Remove mentions
        clean = re.sub(r"[^\w\s]", " ", clean)  # Remove punctuation
        words = clean.lower().split()

        # Extract n-grams
        for n in range(min_words, max_words + 1):
            for i in range(len(words) - n + 1):
                phrase = " ".join(words[i : i + n])
                if len(phrase) > 5:  # Skip very short phrases
                    phrase_counter[phrase] += 1

    # Filter to phrases appearing multiple times
    return [(p, c) for p, c in phrase_counter.most_common(20) if c > 1]


# ── Engagement Correlation Analysis ─────────────────────────────────


def analyze_engagement_correlations(tweets: list[dict]) -> dict:
    """
    Find patterns that correlate with high vs low engagement.
    """
    original = [t for t in tweets if not t.get("is_retweet")]

    if not original:
        return {}

    # Sort by weighted engagement
    by_engagement = sorted(original, key=calc_weighted_engagement, reverse=True)

    # Top 10% vs bottom 50%
    top_10_pct = by_engagement[: max(1, len(by_engagement) // 10)]
    bottom_50_pct = by_engagement[len(by_engagement) // 2 :]

    return {
        "total_analyzed": len(original),
        "top_performers": _analyze_cohort(top_10_pct, "Top 10%"),
        "low_performers": _analyze_cohort(bottom_50_pct, "Bottom 50%"),
        "top_hooks": extract_hooks(original)[:10],
    }


def _analyze_cohort(tweets: list[dict], label: str) -> dict:
    """Analyze a cohort of tweets."""
    texts = [t.get("text", "") for t in tweets]

    return {
        "label": label,
        "count": len(tweets),
        "avg_length": calc_avg_text_length(tweets),
        "has_media_pct": pct_with_media(tweets),
        "has_links_pct": pct_with_links(tweets),
        "question_pct": pct_questions(texts),
        "avg_engagement": calc_avg_engagement(tweets),
        "posting_hours": most_common_hours(tweets),
    }


def pct_with_media(tweets: list[dict]) -> float:
    """Percentage of tweets with media attachments."""
    if not tweets:
        return 0
    with_media = sum(1 for t in tweets if t.get("media"))
    return round((with_media / len(tweets)) * 100, 1)


def pct_with_links(tweets: list[dict]) -> float:
    """Percentage of tweets with URLs."""
    if not tweets:
        return 0
    with_links = sum(1 for t in tweets if t.get("urls"))
    return round((with_links / len(tweets)) * 100, 1)


def pct_questions(texts: list[str]) -> float:
    """Percentage of texts ending with or containing questions."""
    if not texts:
        return 0
    questions = sum(1 for t in texts if "?" in t)
    return round((questions / len(texts)) * 100, 1)


def most_common_hours(tweets: list[dict]) -> list[int]:
    """Find most common posting hours (UTC)."""
    hours = []
    for t in tweets:
        dt = t.get("created_at_dt")
        if dt:
            hours.append(dt.hour)

    if not hours:
        return []

    hour_counts = Counter(hours)
    return [h for h, _ in hour_counts.most_common(3)]


# ── Time-based Analytics ─────────────────────────────────────


def get_posting_frequency(tweets: list[dict]) -> dict:
    """Calculate posting frequency statistics."""
    with_dates = [t for t in tweets if t.get("created_at_dt")]

    if len(with_dates) < 2:
        return {}

    dates = sorted([t["created_at_dt"] for t in with_dates])
    span_days = (dates[-1] - dates[0]).days or 1

    return {
        "total_tweets": len(with_dates),
        "span_days": span_days,
        "tweets_per_day": round(len(with_dates) / span_days, 2),
        "tweets_per_week": round((len(with_dates) / span_days) * 7, 1),
    }


def get_hourly_distribution(tweets: list[dict]) -> dict[int, int]:
    """Get tweet count by hour of day (UTC)."""
    hourly = {h: 0 for h in range(24)}

    for t in tweets:
        dt = t.get("created_at_dt")
        if dt:
            hourly[dt.hour] += 1

    return hourly


def get_daily_distribution(tweets: list[dict]) -> dict[int, int]:
    """Get tweet count by day of week (0=Monday, 6=Sunday)."""
    daily = {d: 0 for d in range(7)}

    for t in tweets:
        dt = t.get("created_at_dt")
        if dt:
            daily[dt.weekday()] += 1

    return daily


def get_engagement_over_time(tweets: list[dict]) -> list[dict]:
    """
    Get engagement metrics over time for charting.
    Returns list sorted by date with rolling averages.
    """
    with_dates = [t for t in tweets if t.get("created_at_dt")]
    sorted_tweets = sorted(with_dates, key=lambda t: t["created_at_dt"])

    result = []
    for t in sorted_tweets:
        result.append(
            {
                "date": t["created_at_dt"],
                "likes": t.get("likes", 0),
                "retweets": t.get("retweets", 0),
                "replies": t.get("replies", 0),
                "views": t.get("views", 0),
                "engagement_rate": calc_engagement_rate(t),
            }
        )

    return result
