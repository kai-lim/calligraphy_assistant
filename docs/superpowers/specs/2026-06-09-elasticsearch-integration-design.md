# Elasticsearch Integration Design
Date: 2026-06-09

## Goal

Extend the existing `@kai.ligraphy` calligraphy assistant (Google ADK + Gemini 2.5 Flash, deployed on Cloud Run) with Elasticsearch as a second MCP data source. This adds semantic search over historical Instagram posts and a Chinese calligraphy knowledge base — capabilities the live Instagram API alone cannot provide.

Hackathon constraint: proof-of-concept in under 24 hours.

---

## Architecture

```
User question
     │
     ▼
Google ADK Agent (Gemini 2.5 Flash) — deployed on Cloud Run
     ├── Instagram MCP (stdio subprocess)   ← live, real-time data
     └── Elastic MCP (SSE/HTTP)             ← semantic search
              │
              ▼
         Elasticsearch index: "calligraphy"
              ├── doc_type: "post"       — @kai.ligraphy Instagram posts
              └── doc_type: "knowledge"  — Chinese calligraphy reference docs
```

The agent draws from both sources autonomously. Live questions ("how many likes did your last post get?") hit Instagram. Semantic or historical questions ("show me posts about ink consistency" or "what is 草书?") hit Elasticsearch.

---

## Components

### 1. One-time Indexing Script (`my_agent/index_data.py`)

Runs locally once to populate Elasticsearch. Does two things:

**A. Index Instagram posts**
- Reuses Instagram API credentials already in `.env`
- Fetches all available posts (paginating until exhausted)
- Each document shape:
  ```json
  {
    "doc_type": "post",
    "post_id": "...",
    "caption": "...",
    "hashtags": ["#calligraphy", "..."],
    "media_type": "IMAGE",
    "timestamp": "2024-01-15T10:00:00Z",
    "like_count": 42,
    "comments_count": 5,
    "permalink": "https://www.instagram.com/p/..."
  }
  ```

**B. Index calligraphy knowledge documents**
- Hand-written Python list of ~10-15 documents covering:
  - Five main styles: 楷书 (Kǎishū), 行书 (Xíngshū), 草书 (Cǎoshū), 隶书 (Lìshū), 篆书 (Zhuànshū)
  - Four Treasures (文房四宝): brush (笔), ink (墨), paper (纸), inkstone (砚)
  - Famous calligraphers: 王羲之, 颜真卿, 柳公权
  - Basic techniques: brush grip, ink dilution, stroke order
- Each document shape:
  ```json
  {
    "doc_type": "knowledge",
    "title": "草书 (Cursive Script)",
    "content": "草书 is the most fluid and expressive of the five styles..."
  }
  ```

Uses the `elasticsearch` Python client with bulk indexing. ELSER semantic embeddings are applied automatically by Elastic on ingest (configured via the index mapping).

### 2. Elastic Agent Builder Tool (Kibana UI)

In Kibana Agent Builder, define one tool:

- **Name**: `search_calligraphy`
- **Description**: "Searches the calligraphy knowledge base and historical Instagram posts by meaning. Use this for questions about Chinese calligraphy styles, techniques, tools, or to find past posts by topic."
- **Backend**: Semantic search over the `calligraphy` index using ELSER
- **Returns**: Top-k matching documents (caption/content + metadata)

The MCP server endpoint and API key are provided by Kibana in the Tools UI.

### 3. Agent Update (`my_agent/agent.py`)

Add a second `MCPToolset` using SSE connection params (exact class name to confirm from ADK docs — likely `SseConnectionParams` or `StreamableHTTPConnectionParams`):

```python
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseConnectionParams

elastic_mcp_tools = MCPToolset(
    connection_params=SseConnectionParams(
        url=os.environ.get("ELASTIC_MCP_URL"),
        headers={"Authorization": f"ApiKey {os.environ.get('ELASTIC_API_KEY')}"}
    )
)

root_agent = Agent(
    ...
    tools=[instagram_mcp_tools, elastic_mcp_tools]
)
```

Update the agent's instruction to describe both capabilities.

### 4. Environment Variables

Add to `.env` (local) and Cloud Run service config:

| Variable | Source |
|---|---|
| `ELASTIC_MCP_URL` | Kibana Agent Builder → Tools UI |
| `ELASTIC_API_KEY` | Elastic Cloud → API Keys |

---

## Updated Agent Instruction

```
You are a helpful assistant for @kai.ligraphy, a Chinese calligraphy Instagram account.

You have two sources of information:
1. Instagram tools — for live data: recent posts, engagement stats, hashtag trends, other profiles.
2. Elastic search tool — for semantic search: finding past posts by topic, and answering questions about Chinese calligraphy styles (楷书, 行书, 草书, 隶书, 篆书), tools (文房四宝), techniques, and famous calligraphers.

Use the most appropriate source for each question. For questions about both ("which calligraphy style appears most in your recent posts?"), combine both sources.

If a question is unrelated to @kai.ligraphy or Chinese calligraphy, politely decline.
```

---

## Demo Flow (for the 3-minute video)

1. "What are your 3 most recent posts?" → Instagram API (live)
2. "Find your posts related to ink brushwork" → Elastic semantic search over indexed posts
3. "What is 草书 and how does it differ from 楷书?" → Elastic knowledge base
4. "Which style do you use most often in your Instagram posts?" → Agent combines both sources

---

## Out of Scope (time constraint)

- ES|QL analytics queries (engagement trends, best posting times)
- Automatic write-back of new posts to Elastic on each fetch
- Real-time index sync with Instagram

---

## Deployment Steps Summary

1. Run `index_data.py` locally to populate Elastic (one-time)
2. Configure Agent Builder tool in Kibana UI
3. Copy MCP endpoint URL + API key from Kibana
4. Update `agent.py` with Elastic MCP toolset
5. Add env vars to Cloud Run service
6. Redeploy to Cloud Run
