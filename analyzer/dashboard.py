# dashboard.py
# ─────────────────────────────────────────────────────────────
# Streamlit analytics dashboard for tweet data visualization.
#
# Usage: streamlit run analyzer/dashboard.py
# ─────────────────────────────────────────────────────────────

import streamlit as st
import pandas as pd
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer import data_loader, metrics, charts


def main():
    st.set_page_config(
        page_title="xScraper Analytics",
        page_icon="📊",
        layout="wide",
    )

    st.title("xScraper Analytics Dashboard")

    # Load data
    tweets = data_loader.load_tweets()

    if not tweets:
        st.error("No tweets found. Run the scraper first to collect data.")
        st.info("Run `python main.py` to scrape tweets.")
        return

    # Get author info
    author = data_loader.get_author_info(tweets)
    original_tweets = data_loader.get_original_tweets(tweets)

    # Header metrics
    st.markdown(f"### @{author['author_handle']} - {author['author_name']}")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Tweets", len(tweets))
    with col2:
        st.metric("Original", len(original_tweets))
    with col3:
        avg_engagement = metrics.calc_avg_engagement(original_tweets)
        st.metric("Avg Likes", f"{avg_engagement.get('avg_likes', 0):.0f}")
    with col4:
        st.metric("Avg Retweets", f"{avg_engagement.get('avg_retweets', 0):.1f}")
    with col5:
        st.metric("Avg Views", f"{avg_engagement.get('avg_views', 0):,.0f}")

    st.divider()

    # Main content in tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Engagement",
        "🕐 Timing",
        "🏆 Top Content",
        "📊 Content Mix",
        "🏷️ Tags & Mentions",
    ])

    with tab1:
        st.subheader("Engagement Over Time")

        # Rolling window selector
        rolling_window = st.slider(
            "Rolling Average Window (days)",
            min_value=1,
            max_value=30,
            value=7,
        )

        fig = charts.engagement_over_time(tweets, rolling_window=rolling_window)
        st.plotly_chart(fig, use_container_width=True)

        # Engagement distribution
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Likes Distribution")
            fig = charts.engagement_distribution(tweets)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Engagement by Content Type")
            fig = charts.engagement_by_type(tweets)
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Posting Time Analysis")

        fig = charts.posting_time_heatmap(tweets)
        st.plotly_chart(fig, use_container_width=True)

        # Posting frequency stats
        freq = metrics.get_posting_frequency(tweets)
        if freq:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Days Analyzed", freq.get("span_days", 0))
            with col2:
                st.metric("Tweets/Day", f"{freq.get('tweets_per_day', 0):.1f}")
            with col3:
                st.metric("Tweets/Week", f"{freq.get('tweets_per_week', 0):.1f}")

        # Best times summary
        st.subheader("Best Posting Times")

        hourly = metrics.get_hourly_distribution(original_tweets)
        daily = metrics.get_daily_distribution(original_tweets)

        col1, col2 = st.columns(2)

        with col1:
            top_hours = sorted(hourly.items(), key=lambda x: x[1], reverse=True)[:3]
            st.write("**Top Hours (UTC)**")
            for hour, count in top_hours:
                st.write(f"- {hour:02d}:00 - {count} tweets")

        with col2:
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            top_days = sorted(daily.items(), key=lambda x: x[1], reverse=True)[:3]
            st.write("**Top Days**")
            for day, count in top_days:
                st.write(f"- {days[day]} - {count} tweets")

    with tab3:
        st.subheader("Top Performing Tweets")

        # Number of tweets to show
        n_tweets = st.slider("Number of tweets", min_value=5, max_value=50, value=10)

        df = charts.top_tweets_table(tweets, n=n_tweets)

        if not df.empty:
            # Make URLs clickable
            st.dataframe(
                df,
                column_config={
                    "URL": st.column_config.LinkColumn("Link"),
                    "Text": st.column_config.TextColumn("Tweet", width="large"),
                },
                hide_index=True,
                use_container_width=True,
            )

        # Top hooks
        st.subheader("Top Performing Hooks")

        hooks = metrics.extract_hooks(tweets)[:10]

        for i, hook in enumerate(hooks, 1):
            with st.expander(f"{i}. {hook['hook']}"):
                st.write(f"**Full tweet:** {hook['full_text']}")
                st.write(f"**Likes:** {hook['likes']} | **Views:** {hook['views']:,}")
                if hook.get("tweet_url"):
                    st.link_button("View Tweet", hook["tweet_url"])

    with tab4:
        st.subheader("Content Type Distribution")

        col1, col2 = st.columns(2)

        with col1:
            fig = charts.content_type_breakdown(tweets)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Content structure analysis
            st.write("**Content Structure Patterns**")

            patterns = metrics.analyze_writing_patterns(tweets)
            structures = patterns.get("structure_types", {})

            for struct, pct in sorted(structures.items(), key=lambda x: x[1], reverse=True):
                if pct > 0:
                    st.progress(pct / 100, text=f"{struct.title()}: {pct}%")

        # Writing patterns
        st.subheader("Writing Patterns")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Avg Tweet Length",
                f"{patterns.get('avg_tweet_length', 0):.0f} chars"
            )

        with col2:
            emoji_data = patterns.get("emoji_frequency", {})
            st.metric(
                "Emoji Usage",
                f"{emoji_data.get('pct_with_emoji', 0):.0f}%"
            )

        with col3:
            formatting = patterns.get("formatting", {})
            st.metric(
                "Line Breaks",
                f"{formatting.get('uses_line_breaks_pct', 0):.0f}%"
            )

    with tab5:
        st.subheader("Hashtags & Mentions")

        col1, col2 = st.columns(2)

        with col1:
            fig = charts.hashtag_frequency(tweets)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = charts.mention_frequency(tweets)
            st.plotly_chart(fig, use_container_width=True)

        # Common phrases
        st.subheader("Common Phrases")

        phrases = patterns.get("common_phrases", [])
        if phrases:
            phrase_df = pd.DataFrame(phrases, columns=["Phrase", "Count"])
            st.dataframe(phrase_df, hide_index=True)
        else:
            st.info("Not enough data to extract common phrases.")

    # Footer
    st.divider()
    st.caption("Built with xScraper Analytics | Data refreshes on page reload")


if __name__ == "__main__":
    main()
