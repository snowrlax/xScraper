# xScraper Data Engineering Plan

## Session Date: 2026-03-16

---

## Original Problem

All tweets have `user_handle: "unknown"` and `user_name: ""` because the user extraction path in `interceptor.py` is returning empty data.

**Root Cause**: X/Twitter changed their GraphQL response structure. The code was looking for user data at:
```
core.user_results.result.legacy.screen_name  ← WRONG (empty)
```

But X moved it to:
```
core.user_results.result.core.screen_name    ← CORRECT
core.user_results.result.core.name           ← CORRECT
```

---

## Discussion: Data Engineering Approach

### Initial Questions Asked

**Q1: Flat vs Nested data model?**
- Fully flat: one row per tweet, all fields at top level
- Nested JSON: one row per tweet, with nested objects for media, entities, user
- Normalized: separate files for tweets, users, media, threads

**Q2: Quoted/Retweeted Content - extract full data or just reference ID?**

**Q3: User Deduplication - inline in each tweet or separate users.json?**

**Q4: Thread Grouping - store thread_position or compute post-hoc?**

**Q5: Historical Data - add scraped_at timestamp?**

### User Responses

- **Q1**: User asked for comparison between Normalized vs Enriched Flat. Final decision: **Enriched Flat** suffices for current use case, but may need a post-processing `normalize.py` script later.
- **Q2**: Extract the quoted tweet's full data if available. **Yes, extract fully.**
- **Q3**: Discussed further - decided on **Hybrid approach** (inline basic + separate users.json)
- **Q4**: Discussed further - decided on **Raw storage, post-processing computation**
- **Q5**: **Yes**, add scraped_at timestamp

---

## Decision: Enriched Flat with Selective Nesting

### Why Enriched Flat over Normalized

| Factor | Enriched Flat | Normalized Multi-File |
|--------|---------------|----------------------|
| **File count** | 2-3 files | 5-6 files |
| **Read one tweet** | Single lookup | Join 3-4 files |
| **Storage size** | ~15-20% larger | Minimal redundancy |
| **Pandas analysis** | `pd.read_json()` done | Multiple reads + merge |
| **SQL import** | Needs flattening | Direct table import |
| **Add new tweet** | Append to 1 file | Append to 3-4 files |
| **Update user bio** | Update N tweets | Update 1 record |
| **Partial scrape resume** | Simple | Need FK consistency |
| **Scale (10K tweets)** | Fine | Overkill |
| **Scale (1M+ tweets)** | Gets slow | Shines here |

### When Normalized Wins
- Scraping millions of tweets
- Building a production data pipeline
- Need to update user data independently
- Multiple consumers with different needs
- Storage costs are a concern

### When Enriched Flat Wins
- Moderate scale (under 50K tweets) - likely range for this project
- Ad-hoc analysis - Jupyter notebooks, quick pandas exploration
- Simplicity - One file to understand, share, backup
- Self-contained records - Each tweet makes sense alone
- Faster iteration - Change schema without migration headaches

---

## Decision: User Deduplication (Hybrid Approach)

**Structure**:
```
tweets.json (inline, denormalized):
{
  "tweet_id": "123",
  "author_id": "2311987360",
  "author_handle": "marclou",
  "author_name": "Marc Lou",
  "author_verified": true,
  ...
}

users.json (normalized, deduplicated):
{
  "2311987360": {
    "handle": "marclou",
    "name": "Marc Lou",
    "bio": "...",
    "followers": 318020,
    "following": 1190,
    "verified": true,
    "profile_image": "https://...",
    "created_at": "Wed Jan 29 13:56:31 +0000 2014",
    "first_seen": "2026-03-16T23:22:28Z"
  }
}
```

**Benefits**:
1. Tweets stay self-contained - Basic analysis doesn't need joins
2. No redundancy for full profiles - One user's 500 tweets don't repeat 500x of the same bio
3. Captures ALL users - Target user + anyone quoted/retweeted/replied-to
4. Scales to multi-user scraping - users.json becomes a growing index

---

## Decision: Thread Grouping (Raw Storage, Post-Processing Computation)

**Store in tweets.json**:
```json
{
  "tweet_id": "789",
  "conversation_id": "123",
  "in_reply_to_tweet_id": "456",
  "in_reply_to_user_id": "2311987360",
  "is_self_reply": true
}
```

**Compute later (NOT stored)**:
- `thread_position` - computed by grouping by conversation_id, sorting by created_at

**Why**:
1. Scraper stays simple - Just extract what API gives us
2. No ordering assumptions - Tweets may arrive out of order during scrolling
3. Post-processing flexibility - Thread position computed by:
   ```python
   threads = tweets.groupby('conversation_id').apply(
       lambda x: x.sort_values('created_at').assign(
           thread_position=range(1, len(x)+1)
       )
   )
   ```

---

## Tweet Type Classification

| Type | How to Detect |
|------|---------------|
| Original | No RT prefix, no `in_reply_to`, no `quoted_status` |
| Retweet | `full_text.startswith("RT @")` or `retweeted_status_result` exists |
| Quote Tweet | `quoted_status_result` exists |
| Reply | `in_reply_to_status_id_str` is not null |
| Thread (self-reply) | Reply where `in_reply_to_user_id == author_user_id` |
| Pinned | Context from parent shows "pinned" |

---

## X's Actual GraphQL Structure (from scraper.log analysis)

```
tweet_results.result
├── __typename: "Tweet" | "TweetWithVisibilityResults"
├── rest_id: "1234567890"
├── core
│   └── user_results
│       └── result
│           ├── __typename: "User"
│           ├── rest_id: "2311987360"
│           ├── core                          ← USER BASIC INFO HERE
│           │   ├── screen_name: "marclou"
│           │   ├── name: "Marc Lou"
│           │   └── created_at: "Wed Jan 29..."
│           ├── legacy                        ← USER EXTENDED INFO
│           │   ├── description
│           │   ├── followers_count: 318020
│           │   ├── friends_count: 1190
│           │   ├── statuses_count: 32648
│           │   ├── profile_banner_url
│           │   └── ...
│           ├── is_blue_verified: true
│           ├── avatar.image_url
│           └── ...
├── legacy                                    ← TWEET DATA HERE
│   ├── id_str
│   ├── full_text
│   ├── created_at
│   ├── favorite_count (likes)
│   ├── retweet_count
│   ├── reply_count
│   ├── lang
│   ├── in_reply_to_status_id_str
│   ├── in_reply_to_user_id_str
│   ├── conversation_id_str
│   ├── entities (hashtags, mentions, urls, media)
│   └── ...
├── views.count
├── source: "<a href=...>Twitter Web App</a>"
├── quoted_status_result (if quote tweet)
├── note_tweet (for long tweets)
└── edit_control
```

---

## Complete Field Mapping

### Tweet Fields
| X GraphQL Path | Our Field | Type |
|----------------|-----------|------|
| `rest_id` | tweet_id | string |
| `legacy.full_text` | text | string |
| `note_tweet.note_tweet_results.result.text` | full_text | string (long tweets) |
| `legacy.created_at` | created_at | string |
| `legacy.favorite_count` | likes | int |
| `legacy.retweet_count` | retweets | int |
| `legacy.reply_count` | replies | int |
| `views.count` | views | int |
| `legacy.quote_count` | quotes | int |
| `legacy.bookmark_count` | bookmarks | int |
| `legacy.lang` | lang | string |
| `source` | source | string (needs HTML strip) |
| `legacy.conversation_id_str` | conversation_id | string |
| `legacy.in_reply_to_status_id_str` | in_reply_to_tweet_id | string |
| `legacy.in_reply_to_user_id_str` | in_reply_to_user_id | string |
| `legacy.in_reply_to_screen_name` | in_reply_to_handle | string |

### Author Fields (inline in tweets.json)
| X GraphQL Path | Our Field | Type |
|----------------|-----------|------|
| `core.user_results.result.rest_id` | author_id | string |
| `core.user_results.result.core.screen_name` | author_handle | string |
| `core.user_results.result.core.name` | author_name | string |
| `core.user_results.result.is_blue_verified` | author_verified | bool |

### User Profile (for users.json)
| X GraphQL Path | Our Field |
|----------------|-----------|
| `core.user_results.result.rest_id` | user_id |
| `core.user_results.result.core.screen_name` | handle |
| `core.user_results.result.core.name` | name |
| `core.user_results.result.core.created_at` | created_at |
| `core.user_results.result.legacy.description` | bio |
| `core.user_results.result.legacy.followers_count` | followers |
| `core.user_results.result.legacy.friends_count` | following |
| `core.user_results.result.legacy.statuses_count` | tweet_count |
| `core.user_results.result.is_blue_verified` | verified |
| `core.user_results.result.avatar.image_url` | avatar_url |
| `core.user_results.result.legacy.profile_banner_url` | banner_url |

### Entities (arrays)
| X GraphQL Path | Our Field |
|----------------|-----------|
| `legacy.entities.hashtags[].text` | hashtags[] |
| `legacy.entities.user_mentions[].screen_name` | mentions[] |
| `legacy.entities.urls[]` | urls[] (display_url, expanded_url) |
| `legacy.entities.media[]` | media[] (type, media_url_https) |

### Linked Content
| X GraphQL Path | Our Field |
|----------------|-----------|
| `quoted_status_result.result` | quoted_tweet (full object) |
| `legacy.retweeted_status_result.result` | retweeted_tweet (full object) |

### Derived Fields (computed)
| Logic | Our Field |
|-------|-----------|
| `text.startswith("RT @")` | is_retweet |
| `in_reply_to_tweet_id is not None` | is_reply |
| `quoted_tweet is not None` | is_quote |
| `in_reply_to_user_id == author_id` | is_self_reply |
| `socialContext.contextType == "Pin"` | is_pinned |
| Current timestamp | scraped_at |

---

## Final Schema: tweets.json

```json
{
  "tweet_id": "1234567890",
  "text": "Just launched ShipFast!",
  "full_text": null,
  "created_at": "Mon Mar 15 10:30:00 +0000 2026",
  "scraped_at": "2026-03-16T23:22:28Z",

  "likes": 500,
  "retweets": 120,
  "replies": 45,
  "quotes": 12,
  "bookmarks": 30,
  "views": 50000,

  "lang": "en",
  "source": "Twitter Web App",

  "conversation_id": "1234567890",
  "in_reply_to_tweet_id": null,
  "in_reply_to_user_id": null,
  "in_reply_to_handle": null,

  "author_id": "2311987360",
  "author_handle": "marclou",
  "author_name": "Marc Lou",
  "author_verified": true,

  "is_retweet": false,
  "is_reply": false,
  "is_quote": true,
  "is_self_reply": false,
  "is_pinned": false,

  "hashtags": ["buildinpublic", "indiehacker"],
  "mentions": ["elonmusk"],
  "urls": [
    {"display": "shipfa.st", "expanded": "https://shipfa.st"}
  ],
  "media": [
    {"type": "photo", "url": "https://pbs.twimg.com/..."}
  ],

  "quoted_tweet": { /* full tweet object, same schema */ },
  "retweeted_tweet": null,

  "tweet_url": "https://x.com/marclou/status/1234567890"
}
```

---

## Final Schema: users.json

```json
{
  "2311987360": {
    "user_id": "2311987360",
    "handle": "marclou",
    "name": "Marc Lou",
    "bio": "⭐️ https://t.co/MZc8tGa5LQ $33K/m...",
    "followers": 318020,
    "following": 1190,
    "tweet_count": 32648,
    "verified": true,
    "avatar_url": "https://pbs.twimg.com/profile_images/...",
    "banner_url": "https://pbs.twimg.com/profile_banners/...",
    "created_at": "Wed Jan 29 13:56:31 +0000 2014",
    "first_seen": "2026-03-16T23:22:28Z",
    "last_updated": "2026-03-16T23:22:28Z"
  }
}
```

---

## Output Files Structure

```
xScraper/
├── tweets.json           # All tweets, enriched flat format
├── tweets.csv            # Core fields only, for spreadsheets
├── users.json            # Deduplicated user profiles
├── scraper.log           # Debug/audit trail
└── session_cookies.json  # Browser session
```

---

## Implementation Tasks

### Phase 1: Fix the Bug
1. Update `_parse_tweet_node()` in `interceptor.py` to use correct path:
   - `core.user_results.result.core.screen_name` (not legacy)
   - `core.user_results.result.core.name` (not legacy)

### Phase 2: Expand Schema
1. Update `_parse_tweet_node()` to extract all fields from mapping above
2. Add `_parse_user_node()` function for user extraction
3. Add `_extract_entities()` function for hashtags, mentions, urls, media
4. Handle `quoted_status_result` and `retweeted_status_result`
5. Add `scraped_at` timestamp
6. Compute derived fields (is_retweet, is_reply, is_quote, is_self_reply)

### Phase 3: Storage Updates
1. Update `storage.py` to handle new schema
2. Add `users.json` writing with deduplication
3. Update CSV export for core fields

### Phase 4: Future (Optional)
1. Create `normalize.py` post-processing script
2. Add thread position computation
3. Add media downloading option

---

## Files to Modify

| File | Changes |
|------|---------|
| `interceptor.py` | Fix user path, expand extraction, add user/entity parsing |
| `storage.py` | Add users.json, update tweet schema, CSV columns |
| `config.py` | Add OUTPUT_USERS path |

---

## Verification Steps

1. Run with `MAX_TWEETS=5`
2. Check `tweets.json` shows `author_handle: "marclou"` (not "unknown")
3. Check `users.json` contains user profile with all fields
4. Verify all new fields are populated correctly
5. Test with quote tweets and replies to verify linked content extraction
6. Confirm `scraped_at` timestamp is present
7. Verify derived fields (`is_reply`, `is_quote`, `is_self_reply`) are computed correctly

---

## Debug Logging Added (Step 1 - Complete)

The following debug logging was added to `interceptor.py` to diagnose the issue:

```python
# In _extract_tweets():
raw_json = json.dumps(data, indent=2)
log.debug(f"[RAW RESPONSE] (truncated):\n{raw_json[:5000]}")

# In _parse_tweet_node():
log.debug(f"[TWEET NODE] __typename: {result.get('__typename')}")
log.debug(f"[TWEET NODE] All keys: {list(result.keys())}")
log.debug(f"[TWEET NODE] core: {json.dumps(core, indent=2) if core else 'EMPTY'}")

for alt_key in ["author", "user", "author_results", "user_result"]:
    if alt_key in result:
        log.debug(f"[TWEET NODE] Found '{alt_key}': {json.dumps(result[alt_key], indent=2)[:500]}")
```

This logging confirmed the root cause: user data is in `core.user_results.result.core`, not `core.user_results.result.legacy`.
