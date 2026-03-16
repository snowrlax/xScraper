# charts.py
# ─────────────────────────────────────────────────────────────
# Plotly chart builders for tweet analytics dashboard.
# ─────────────────────────────────────────────────────────────

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime
from typing import Optional

from . import metrics


def engagement_over_time(tweets: list[dict], rolling_window: int = 7) -> go.Figure:
    """
    Line chart showing engagement metrics over time with rolling averages.

    Args:
        tweets: List of tweets with created_at_dt
        rolling_window: Window size for rolling average

    Returns:
        Plotly figure
    """
    data = metrics.get_engagement_over_time(tweets)

    if not data:
        return _empty_chart("No data available")

    df = pd.DataFrame(data)
    df = df.sort_values("date")

    # Calculate rolling averages
    for col in ["likes", "retweets", "views"]:
        df[f"{col}_rolling"] = df[col].rolling(window=rolling_window, min_periods=1).mean()

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        subplot_titles=("Likes & Retweets", "Views"),
        vertical_spacing=0.1,
    )

    # Likes
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["likes"],
            mode="markers",
            name="Likes",
            marker=dict(size=6, opacity=0.5),
            line=dict(color="#E91E63"),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["likes_rolling"],
            mode="lines",
            name=f"Likes ({rolling_window}d avg)",
            line=dict(color="#E91E63", width=2),
        ),
        row=1,
        col=1,
    )

    # Retweets
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["retweets"],
            mode="markers",
            name="Retweets",
            marker=dict(size=6, opacity=0.5),
            line=dict(color="#2196F3"),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["retweets_rolling"],
            mode="lines",
            name=f"Retweets ({rolling_window}d avg)",
            line=dict(color="#2196F3", width=2),
        ),
        row=1,
        col=1,
    )

    # Views
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["views"],
            mode="markers",
            name="Views",
            marker=dict(size=6, opacity=0.5),
            line=dict(color="#4CAF50"),
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["views_rolling"],
            mode="lines",
            name=f"Views ({rolling_window}d avg)",
            line=dict(color="#4CAF50", width=2),
        ),
        row=2,
        col=1,
    )

    fig.update_layout(
        title="Engagement Over Time",
        height=500,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig


def posting_time_heatmap(tweets: list[dict]) -> go.Figure:
    """
    Heatmap showing tweet frequency by hour and day of week.

    Args:
        tweets: List of tweets with created_at_dt

    Returns:
        Plotly figure
    """
    # Build hour x day matrix
    matrix = [[0 for _ in range(24)] for _ in range(7)]

    for t in tweets:
        dt = t.get("created_at_dt")
        if dt:
            matrix[dt.weekday()][dt.hour] += 1

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    hours = [f"{h:02d}:00" for h in range(24)]

    fig = go.Figure(
        data=go.Heatmap(
            z=matrix,
            x=hours,
            y=days,
            colorscale="Blues",
            hoverongaps=False,
            hovertemplate="Day: %{y}<br>Hour: %{x}<br>Tweets: %{z}<extra></extra>",
        )
    )

    fig.update_layout(
        title="Posting Time Heatmap (UTC)",
        xaxis_title="Hour of Day",
        yaxis_title="Day of Week",
        height=350,
    )

    return fig


def content_type_breakdown(tweets: list[dict]) -> go.Figure:
    """
    Pie chart showing distribution of content types.

    Args:
        tweets: List of tweets

    Returns:
        Plotly figure
    """
    # Count types
    original = 0
    replies = 0
    quotes = 0
    retweets = 0
    threads = 0

    for t in tweets:
        if t.get("is_retweet"):
            retweets += 1
        elif t.get("is_self_reply"):
            threads += 1
        elif t.get("is_reply"):
            replies += 1
        elif t.get("is_quote"):
            quotes += 1
        else:
            original += 1

    labels = ["Original", "Replies", "Quote Tweets", "Retweets", "Threads"]
    values = [original, replies, quotes, retweets, threads]
    colors = ["#4CAF50", "#2196F3", "#FF9800", "#9C27B0", "#00BCD4"]

    # Filter out zero values
    filtered = [(l, v, c) for l, v, c in zip(labels, values, colors) if v > 0]
    if not filtered:
        return _empty_chart("No data available")

    labels, values, colors = zip(*filtered)

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                marker=dict(colors=colors),
                textinfo="label+percent",
                textposition="outside",
            )
        ]
    )

    fig.update_layout(
        title="Content Type Distribution",
        height=400,
        showlegend=True,
    )

    return fig


def hashtag_frequency(tweets: list[dict], top_n: int = 15) -> go.Figure:
    """
    Bar chart of most frequently used hashtags.

    Args:
        tweets: List of tweets
        top_n: Number of top hashtags to show

    Returns:
        Plotly figure
    """
    from collections import Counter

    all_hashtags = []
    for t in tweets:
        all_hashtags.extend(t.get("hashtags", []))

    if not all_hashtags:
        return _empty_chart("No hashtags found")

    counts = Counter(all_hashtags).most_common(top_n)
    hashtags, freqs = zip(*counts)

    fig = go.Figure(
        data=[
            go.Bar(
                x=list(freqs),
                y=[f"#{h}" for h in hashtags],
                orientation="h",
                marker=dict(color="#1DA1F2"),
            )
        ]
    )

    fig.update_layout(
        title=f"Top {top_n} Hashtags",
        xaxis_title="Frequency",
        yaxis=dict(autorange="reversed"),
        height=max(300, top_n * 25),
    )

    return fig


def mention_frequency(tweets: list[dict], top_n: int = 15) -> go.Figure:
    """
    Bar chart of most frequently mentioned users.

    Args:
        tweets: List of tweets
        top_n: Number of top mentions to show

    Returns:
        Plotly figure
    """
    from collections import Counter

    all_mentions = []
    for t in tweets:
        all_mentions.extend(t.get("mentions", []))

    if not all_mentions:
        return _empty_chart("No mentions found")

    counts = Counter(all_mentions).most_common(top_n)
    mentions, freqs = zip(*counts)

    fig = go.Figure(
        data=[
            go.Bar(
                x=list(freqs),
                y=[f"@{m}" for m in mentions],
                orientation="h",
                marker=dict(color="#794BC4"),
            )
        ]
    )

    fig.update_layout(
        title=f"Top {top_n} Mentions",
        xaxis_title="Frequency",
        yaxis=dict(autorange="reversed"),
        height=max(300, top_n * 25),
    )

    return fig


def engagement_distribution(tweets: list[dict]) -> go.Figure:
    """
    Histogram showing distribution of engagement (likes).

    Args:
        tweets: List of tweets

    Returns:
        Plotly figure
    """
    original = [t for t in tweets if not t.get("is_retweet")]
    likes = [t.get("likes", 0) for t in original]

    if not likes:
        return _empty_chart("No data available")

    fig = go.Figure(
        data=[
            go.Histogram(
                x=likes,
                nbinsx=30,
                marker=dict(color="#E91E63"),
            )
        ]
    )

    fig.update_layout(
        title="Likes Distribution",
        xaxis_title="Likes",
        yaxis_title="Number of Tweets",
        height=350,
    )

    return fig


def top_tweets_table(tweets: list[dict], n: int = 10) -> pd.DataFrame:
    """
    Create a DataFrame of top performing tweets.

    Args:
        tweets: List of tweets
        n: Number of top tweets

    Returns:
        DataFrame with top tweets
    """
    original = [t for t in tweets if not t.get("is_retweet")]
    sorted_tweets = sorted(original, key=lambda t: t.get("likes", 0), reverse=True)[:n]

    data = []
    for t in sorted_tweets:
        data.append(
            {
                "Text": t.get("text", "")[:100] + "..." if len(t.get("text", "")) > 100 else t.get("text", ""),
                "Likes": t.get("likes", 0),
                "Retweets": t.get("retweets", 0),
                "Replies": t.get("replies", 0),
                "Views": t.get("views", 0),
                "Engagement %": f"{metrics.calc_engagement_rate(t):.2f}%",
                "Date": t.get("created_at_dt").strftime("%Y-%m-%d") if t.get("created_at_dt") else "",
                "URL": t.get("tweet_url", ""),
            }
        )

    return pd.DataFrame(data)


def engagement_by_type(tweets: list[dict]) -> go.Figure:
    """
    Bar chart comparing average engagement across content types.

    Args:
        tweets: List of tweets

    Returns:
        Plotly figure
    """
    types = {
        "Original": [t for t in tweets if not t.get("is_retweet") and not t.get("is_reply") and not t.get("is_quote")],
        "Replies": [t for t in tweets if t.get("is_reply") and not t.get("is_self_reply")],
        "Quote Tweets": [t for t in tweets if t.get("is_quote")],
        "Threads": [t for t in tweets if t.get("is_self_reply")],
    }

    labels = []
    avg_likes = []
    avg_views = []

    for label, type_tweets in types.items():
        if type_tweets:
            labels.append(label)
            avg_likes.append(sum(t.get("likes", 0) for t in type_tweets) / len(type_tweets))
            avg_views.append(sum(t.get("views", 0) for t in type_tweets) / len(type_tweets))

    if not labels:
        return _empty_chart("No data available")

    fig = make_subplots(rows=1, cols=2, subplot_titles=("Avg Likes", "Avg Views"))

    fig.add_trace(
        go.Bar(x=labels, y=avg_likes, marker=dict(color="#E91E63"), name="Likes"),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(x=labels, y=avg_views, marker=dict(color="#4CAF50"), name="Views"),
        row=1,
        col=2,
    )

    fig.update_layout(
        title="Average Engagement by Content Type",
        height=350,
        showlegend=False,
    )

    return fig


def _empty_chart(message: str) -> go.Figure:
    """Create an empty chart with a message."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=16),
    )
    fig.update_layout(
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=300,
    )
    return fig
