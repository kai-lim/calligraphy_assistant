# 🖌️ Kai.ligraphy AI Assistant

An AI-powered assistant for [@kai.ligraphy](https://www.instagram.com/kai.ligraphy/), a Chinese calligraphy Instagram account. Built for the **Google Cloud Rapid Agent Hackathon** on the **Elastic partner track**.

## What It Does

The assistant combines two live data sources to answer questions about Chinese calligraphy and the @kai.ligraphy account:

| Capability | Source |
|---|---|
| Live post data, engagement stats, hashtag trends | Instagram Graph API (MCP) |
| Semantic search over 307 historical posts | Elasticsearch (MCP) |
| Chinese calligraphy knowledge base (styles, tools, masters) | Elasticsearch (MCP) |

**Example questions:**
- "What are your 3 most recent posts?"
- "Find your posts related to ink brushwork"
- "What is 草书 and how does it differ from 楷书?"
- "Tell me about the 文房四宝 (Four Treasures)"
- "Which calligraphy style appears most in your posts?"

## Tech Stack

| Component | Technology |
|---|---|
| Agent framework | [Google ADK](https://google.github.io/adk-docs/) (Agent Development Kit) |
| LLM | Gemini 2.5 Flash |
| Search & knowledge base | Elastic Cloud Serverless (ELSER semantic search) |
| Live social data | Instagram Graph API |
| MCP servers | Custom FastMCP stdio servers (Instagram + Elasticsearch) |
| Deployment | Google Cloud Run |

## Architecture

```
User
 │
 ▼
Google ADK Agent (Gemini 2.5 Flash) — Cloud Run
 ├── instagram_mcp_server.py (stdio MCP)
 │    └── Instagram Graph API → live posts, stats, hashtags
 └── elastic_mcp_server.py (stdio MCP)
      └── Elastic Cloud Serverless → semantic search
           ├── 307 @kai.ligraphy Instagram posts
           └── 13 Chinese calligraphy knowledge articles
```

## Setup & Run

### Prerequisites

- Python 3.11+
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
- Elastic Cloud Serverless account ([free trial](https://cloud.elastic.co))
- Instagram Graph API credentials (Business/Creator account)

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/calligraphy_assistant.git
cd calligraphy_assistant

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment variables

Create `my_agent/.env`:

```
INSTAGRAM_ACCOUNT_ID=your_instagram_account_id
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token
ELASTIC_URL=https://your-project.es.region.gcp.elastic.cloud:443
ELASTIC_API_KEY=your_elastic_api_key
```

### 3. Index data into Elasticsearch (one-time)

This script fetches all your Instagram posts and indexes them alongside the built-in Chinese calligraphy knowledge base into Elastic:

```bash
python -m my_agent.index_data
```

### 4. Run locally

```bash
# Terminal chat
.venv/bin/adk run my_agent

# Web UI (development only)
.venv/bin/adk web
```

### 5. Deploy to Google Cloud Run

```bash
.venv/bin/adk deploy cloud_run --with_ui my_agent
```

## Knowledge Base

The Elasticsearch index contains 13 hand-curated Chinese calligraphy knowledge articles covering:

- **Five main styles**: 楷书 (Kǎishū), 行书 (Xíngshū), 草书 (Cǎoshū), 隶书 (Lìshū), 篆书 (Zhuànshū)
- **Four Treasures (文房四宝)**: 笔 brush, 墨 ink, 纸 paper, 砚 inkstone
- **Famous calligraphers**: 王羲之 (Wang Xizhi), 颜真卿 (Yan Zhenqing)
- **Techniques**: basic brushwork (基本笔法), copying practice (临摹)

Semantic search is powered by Elastic's ELSER model, enabling meaning-based retrieval in both English and Chinese.

## Learnings

- Google ADK's `MCPToolset` makes it straightforward to wire multiple MCP servers into a single agent, with each server running as a subprocess over stdio.
- Elastic Cloud Serverless's `semantic_text` field type handles ELSER embedding generation automatically on ingest — no separate ML pipeline needed.
- Combining live API data (Instagram) with a persistent semantic search layer (Elasticsearch) gives the agent a much richer context than either source alone.

## License

MIT
