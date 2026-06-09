# Elasticsearch Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Elasticsearch as a second MCP data source to the @kai.ligraphy agent, enabling semantic search over historical Instagram posts and a Chinese calligraphy knowledge base.

**Architecture:** A one-time Python script indexes Instagram posts and curated Chinese calligraphy knowledge documents into an Elasticsearch Serverless index using `semantic_text` for ELSER embeddings. A tool defined in Elastic Agent Builder (Kibana) exposes semantic search over that index via a built-in MCP server. The existing Google ADK agent is updated to connect to this MCP endpoint alongside the existing Instagram MCP server.

**Tech Stack:** Python 3.13, Google ADK 2.0.0, `elasticsearch` Python client, Elastic Cloud Serverless, Elastic Agent Builder MCP, `SseConnectionParams` (google-adk)

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `my_agent/calligraphy_knowledge.py` | Create | Chinese calligraphy knowledge documents as a Python list |
| `my_agent/index_data.py` | Create | One-time script: create ES index + bulk index posts + knowledge docs |
| `my_agent/agent.py` | Modify | Add Elastic MCP toolset + update agent instruction |
| `my_agent/.env` | Modify (manual) | Add `ELASTIC_CLOUD_ID`, `ELASTIC_API_KEY`, `ELASTIC_MCP_URL` |
| Cloud Run service | Modify (UI) | Add same three env vars |

---

## Task 1: Install the Elasticsearch Python client

**Files:**
- No file changes — installs into `.venv`

- [ ] **Step 1: Install into the project venv**

```bash
.venv/bin/pip install elasticsearch
```

Expected output includes: `Successfully installed elasticsearch-8.x.x`

- [ ] **Step 2: Verify it imported correctly**

```bash
.venv/bin/python -c "from elasticsearch import Elasticsearch; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "chore: no file changes — elasticsearch client installed in venv"
```

> Note: If the project has no `requirements.txt`, skip the commit. The venv is gitignored.

---

## Task 2: Create the Chinese calligraphy knowledge documents

**Files:**
- Create: `my_agent/calligraphy_knowledge.py`

- [ ] **Step 1: Create the file with 13 knowledge documents**

```python
# my_agent/calligraphy_knowledge.py

KNOWLEDGE_DOCS = [
    {
        "title": "楷书 (Kǎishū — Regular Script)",
        "content": (
            "楷书, or Regular Script, is the most standard and widely taught Chinese calligraphy style. "
            "Each stroke is written separately and clearly, making it the foundation for beginners. "
            "It developed during the Han dynasty and matured in the Tang dynasty. "
            "Famous practitioners include 欧阳询 (Ouyang Xun), 颜真卿 (Yan Zhenqing), and 柳公权 (Liu Gongquan). "
            "It is used in print typefaces and is the style most people learn first."
        ),
    },
    {
        "title": "行书 (Xíngshū — Running Script)",
        "content": (
            "行书, or Running Script, is a semi-cursive style that flows between the formality of 楷书 and the "
            "freedom of 草书. Strokes are connected but still legible. It is the most practical style for everyday "
            "handwriting. 王羲之 (Wang Xizhi) is considered its greatest master; his 《兰亭序》 (Preface to the "
            "Orchid Pavilion) is called the 'number one running script under heaven' (天下第一行书)."
        ),
    },
    {
        "title": "草书 (Cǎoshū — Cursive Script)",
        "content": (
            "草书, or Cursive Script, is the most expressive and abstract of the five styles. Strokes are heavily "
            "abbreviated and connected, prioritising speed and artistic expression over legibility. "
            "狂草 (wild cursive) is the most extreme form. It requires a deep understanding of all other styles "
            "before it can be practised meaningfully. 张旭 (Zhang Xu) and 怀素 (Huaisu) are celebrated masters."
        ),
    },
    {
        "title": "隶书 (Lìshū — Clerical Script)",
        "content": (
            "隶书, or Clerical Script, emerged during the Qin dynasty and became the dominant style of the Han "
            "dynasty. It is characterised by its horizontal emphasis and the distinctive 蚕头燕尾 (silkworm head, "
            "swallow tail) stroke ending. It was the script used by government clerks, hence the name. "
            "It is considered the ancestor of modern Chinese script forms."
        ),
    },
    {
        "title": "篆书 (Zhuànshū — Seal Script)",
        "content": (
            "篆书, or Seal Script, is the oldest surviving major calligraphy style, with roots in oracle bone "
            "script. 大篆 (Greater Seal) predates the Qin dynasty; 小篆 (Lesser Seal) was standardised by the "
            "first Qin emperor. The strokes are round and uniform in width, with a very structured, archaic "
            "appearance. It is still used today in personal seals (印章) and artistic contexts."
        ),
    },
    {
        "title": "笔 (Bǐ — The Brush)",
        "content": (
            "The brush is one of the 文房四宝 (Four Treasures of the Study). Chinese calligraphy brushes have a "
            "tapered tip made from animal hair — wolf hair (狼毫) for firm, precise strokes; goat hair (羊毫) for "
            "soft, absorbent strokes; and mixed hair (兼毫) for a balance of both. "
            "Brush size ranges from tiny detail brushes to large brushes for bold character work. "
            "Proper brush grip (执笔法) and posture are fundamental to control."
        ),
    },
    {
        "title": "墨 (Mò — The Ink)",
        "content": (
            "Ink is one of the 文房四宝. Traditional Chinese ink is made from pine soot or oil soot bound with "
            "animal glue and formed into 墨条 (ink sticks). The stick is ground against a wet 砚台 (inkstone) to "
            "produce liquid ink. The concentration of ink — thick (浓墨) or diluted (淡墨) — dramatically affects "
            "the character of brushstrokes. Bottled liquid ink (墨汁) is widely used today for convenience."
        ),
    },
    {
        "title": "纸 (Zhǐ — The Paper)",
        "content": (
            "Paper is one of the 文房四宝. 宣纸 (Xuan paper, also called rice paper) from Anhui province is the "
            "traditional calligraphy paper. It is prized for its absorbency, which allows ink to spread naturally "
            "and produce subtle tonal variations (墨韵). 生宣 (raw Xuan) is highly absorbent and used for expressive "
            "work; 熟宣 (sized Xuan) is less absorbent and allows more control, suitable for fine detail."
        ),
    },
    {
        "title": "砚 (Yàn — The Inkstone)",
        "content": (
            "The inkstone is one of the 文房四宝. It is a flat stone used to grind ink sticks with water to "
            "produce liquid ink. Famous types include 端砚 (from Guangdong) and 歙砚 (from Anhui). "
            "A good inkstone has a smooth grinding surface that produces fine ink without excessive friction, "
            "and a shallow well to hold the resulting liquid."
        ),
    },
    {
        "title": "王羲之 (Wáng Xīzhī — The Sage of Calligraphy)",
        "content": (
            "王羲之 (303–361 AD) is regarded as the greatest Chinese calligrapher of all time and is honoured "
            "with the title 书圣 (Sage of Calligraphy). He mastered all scripts but is most celebrated for his "
            "行书 (Running Script). His masterpiece 《兰亭序》 (Preface to the Orchid Pavilion, 353 AD) is considered "
            "the finest example of Chinese calligraphy ever created. The original was said to have been buried "
            "with Emperor Taizong of Tang."
        ),
    },
    {
        "title": "颜真卿 (Yán Zhēnqīng)",
        "content": (
            "颜真卿 (709–785 AD) was a Tang dynasty official and calligrapher renowned for his 楷书 (Regular Script). "
            "His style, called 颜体 (Yan style), is characterised by bold, powerful strokes with a strong sense "
            "of structure and moral uprightness — reflecting his own character as a loyal official. "
            "《多宝塔碑》 and 《颜勤礼碑》 are among his most studied works."
        ),
    },
    {
        "title": "基本笔法 (Jīběn Bǐfǎ — Basic Brush Techniques)",
        "content": (
            "Fundamental brushwork includes: 中锋 (centred tip) — the brush tip travels along the centre of the "
            "stroke, producing smooth, even lines; 侧锋 (side tip) — the brush tilts to create textured, expressive "
            "marks. Key strokes include: 横 (horizontal), 竖 (vertical), 撇 (left-falling), 捺 (right-falling), "
            "点 (dot), 折 (turning), 钩 (hook). Mastering these eight strokes (永字八法, the Eight Principles of "
            "the character 永) is the foundation of all calligraphy practice."
        ),
    },
    {
        "title": "临摹 (Línmó — Copying Practice)",
        "content": (
            "临摹 is the traditional method of learning calligraphy by closely copying the work of master "
            "calligraphers. 临 means tracing over a model placed underneath; 摹 means copying by observing. "
            "Practitioners spend years copying classic works (帖) to internalise stroke order, proportion, "
            "rhythm, and spirit before developing their own style. Well-known practice texts include "
            "《九成宫醴泉铭》 by 欧阳询 and 《玄秘塔碑》 by 柳公权."
        ),
    },
]
```

- [ ] **Step 2: Verify the file loads without errors**

```bash
.venv/bin/python -c "from my_agent.calligraphy_knowledge import KNOWLEDGE_DOCS; print(f'{len(KNOWLEDGE_DOCS)} docs loaded')"
```

Expected: `13 docs loaded`

- [ ] **Step 3: Commit**

```bash
git add my_agent/calligraphy_knowledge.py
git commit -m "feat: add Chinese calligraphy knowledge documents"
```

---

## Task 3: Add Elastic credentials to .env

**Files:**
- Modify: `my_agent/.env` (manual step — do not commit)

- [ ] **Step 1: Collect credentials from Elastic Cloud**

  1. Go to [cloud.elastic.co](https://cloud.elastic.co) → your Serverless project
  2. Go to **Kibana → Stack Management → API Keys** → Create a new API key with `all` cluster/index privileges. Copy the key value (shown once).
  3. From the project overview, copy the **Cloud ID** (format: `my-project:base64string==`)
  4. Go to **Kibana → Agent Builder → Tools** → copy the **MCP server endpoint URL**

- [ ] **Step 2: Add to `my_agent/.env`**

  Add these three lines to `my_agent/.env` (alongside existing Instagram vars):

  ```
  ELASTIC_CLOUD_ID=your-cloud-id-here
  ELASTIC_API_KEY=your-api-key-here
  ELASTIC_MCP_URL=https://your-elastic-mcp-endpoint-url-here
  ```

  > Do not commit `.env`. It is already in `.gitignore`.

---

## Task 4: Create the one-time indexing script

**Files:**
- Create: `my_agent/index_data.py`

- [ ] **Step 1: Create the indexing script**

```python
# my_agent/index_data.py
"""
One-time script: creates 'calligraphy' index in Elasticsearch and indexes
Instagram posts + calligraphy knowledge documents.

Run once from the project root:
    .venv/bin/python -m my_agent.index_data
"""

import os
import re
import sys
import requests
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from my_agent.calligraphy_knowledge import KNOWLEDGE_DOCS

current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(current_dir, ".env"))

INDEX_NAME = "calligraphy"


def build_es_client() -> Elasticsearch:
    cloud_id = os.environ["ELASTIC_CLOUD_ID"]
    api_key = os.environ["ELASTIC_API_KEY"]
    return Elasticsearch(cloud_id=cloud_id, api_key=api_key)


def create_index(es: Elasticsearch) -> None:
    if es.indices.exists(index=INDEX_NAME):
        print(f"Index '{INDEX_NAME}' already exists — skipping creation.")
        return

    es.indices.create(
        index=INDEX_NAME,
        body={
            "mappings": {
                "properties": {
                    "doc_type":       {"type": "keyword"},
                    "searchable_text": {"type": "semantic_text"},
                    "title":          {"type": "text"},
                    "content":        {"type": "text"},
                    "caption":        {"type": "text"},
                    "hashtags":       {"type": "keyword"},
                    "timestamp":      {"type": "date"},
                    "like_count":     {"type": "integer"},
                    "comments_count": {"type": "integer"},
                    "permalink":      {"type": "keyword"},
                    "post_id":        {"type": "keyword"},
                    "media_type":     {"type": "keyword"},
                }
            }
        },
    )
    print(f"Index '{INDEX_NAME}' created.")


def fetch_all_instagram_posts() -> list[dict]:
    account_id = os.environ["INSTAGRAM_ACCOUNT_ID"]
    access_token = os.environ["INSTAGRAM_ACCESS_TOKEN"]

    posts = []
    url = f"https://graph.facebook.com/v19.0/{account_id}/media"
    params = {
        "fields": "id,caption,media_type,permalink,timestamp,like_count,comments_count",
        "limit": 100,
        "access_token": access_token,
    }

    while url:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        posts.extend(data.get("data", []))
        next_page = data.get("paging", {}).get("next")
        url = next_page
        params = {}  # next_page URL already contains params

    print(f"Fetched {len(posts)} Instagram posts.")
    return posts


def posts_to_docs(posts: list[dict]) -> list[dict]:
    docs = []
    for post in posts:
        caption = post.get("caption", "") or ""
        hashtags = re.findall(r"#\w+", caption)
        docs.append({
            "_index": INDEX_NAME,
            "_source": {
                "doc_type": "post",
                "searchable_text": caption,
                "caption": caption,
                "hashtags": hashtags,
                "post_id": post.get("id"),
                "media_type": post.get("media_type"),
                "timestamp": post.get("timestamp"),
                "like_count": post.get("like_count", 0),
                "comments_count": post.get("comments_count", 0),
                "permalink": post.get("permalink"),
            },
        })
    return docs


def knowledge_to_docs() -> list[dict]:
    docs = []
    for doc in KNOWLEDGE_DOCS:
        docs.append({
            "_index": INDEX_NAME,
            "_source": {
                "doc_type": "knowledge",
                "searchable_text": f"{doc['title']}: {doc['content']}",
                "title": doc["title"],
                "content": doc["content"],
            },
        })
    return docs


def main() -> None:
    es = build_es_client()
    create_index(es)

    posts = fetch_all_instagram_posts()
    post_docs = posts_to_docs(posts)
    knowledge_docs = knowledge_to_docs()
    all_docs = post_docs + knowledge_docs

    success, failed = bulk(es, all_docs)
    print(f"Indexed {success} documents. Failed: {failed}.")

    count = es.count(index=INDEX_NAME)["count"]
    print(f"Total documents in '{INDEX_NAME}': {count}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the indexing script**

```bash
.venv/bin/python -m my_agent.index_data
```

Expected output (numbers will vary):
```
Index 'calligraphy' created.
Fetched 42 Instagram posts.
Indexed 55 documents. Failed: [].
Total documents in 'calligraphy': 55
```

- [ ] **Step 3: Verify in Kibana**

  In Kibana → Dev Tools, run:
  ```
  GET calligraphy/_count
  ```
  Confirm the count matches what the script reported.

- [ ] **Step 4: Commit the script (not .env)**

```bash
git add my_agent/index_data.py
git commit -m "feat: add one-time Elasticsearch indexing script for posts and knowledge docs"
```

---

## Task 5: Configure the search tool in Elastic Agent Builder (Kibana UI)

**Files:** None — this is a Kibana UI step.

- [ ] **Step 1: Open Agent Builder**

  Kibana → left sidebar → **Agent Builder**

- [ ] **Step 2: Create a new tool**

  Click **+ Add tool** (or equivalent). Fill in:

  | Field | Value |
  |---|---|
  | Name | `search_calligraphy` |
  | Description | `Searches the calligraphy knowledge base and @kai.ligraphy's historical Instagram posts by meaning. Use for questions about Chinese calligraphy styles, techniques, tools, calligraphers, or to find past posts by topic.` |
  | Type | Semantic search |
  | Index | `calligraphy` |
  | Search field | `searchable_text` |
  | Return fields | `doc_type, title, caption, content, hashtags, like_count, comments_count, permalink, timestamp` |

- [ ] **Step 3: Save the tool and copy the MCP endpoint URL**

  After saving, go to the **Tools** tab in Agent Builder. Copy the **MCP server URL** shown there. This is your `ELASTIC_MCP_URL` value.

  If you haven't added it to `.env` yet, add it now (see Task 3).

---

## Task 6: Update the agent to use both MCP servers

**Files:**
- Modify: `my_agent/agent.py`

- [ ] **Step 1: Replace `my_agent/agent.py` with the updated version**

```python
import os
import sys
from dotenv import load_dotenv
from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams, SseConnectionParams
from mcp import StdioServerParameters

current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(current_dir, ".env"))

server_path = os.path.join(current_dir, "instagram_mcp_server.py")

server_params = StdioServerParameters(
    command=sys.executable,
    args=[server_path],
    env={
        "INSTAGRAM_ACCOUNT_ID": os.environ.get("INSTAGRAM_ACCOUNT_ID", ""),
        "INSTAGRAM_ACCESS_TOKEN": os.environ.get("INSTAGRAM_ACCESS_TOKEN", ""),
    },
)

instagram_mcp_tools = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=server_params,
        timeout=60,
    )
)

elastic_mcp_tools = MCPToolset(
    connection_params=SseConnectionParams(
        url=os.environ.get("ELASTIC_MCP_URL", ""),
        headers={"Authorization": f"ApiKey {os.environ.get('ELASTIC_API_KEY', '')}"},
    )
)
# Note: If SseConnectionParams fails to connect (connection refused or protocol error),
# Elastic's MCP server may use the newer StreamableHTTP transport instead. In that case,
# replace SseConnectionParams with StreamableHTTPConnectionParams — same url/headers args,
# also importable from google.adk.tools.mcp_tool.mcp_toolset.

root_agent = Agent(
    model="gemini-2.5-flash",
    name="calligraphy_assistant",
    description=(
        "A helpful assistant for @kai.ligraphy, a Chinese calligraphy Instagram account."
    ),
    instruction="""You are a helpful assistant for @kai.ligraphy, a Chinese calligraphy Instagram account.

You have two sources of information:
1. Instagram tools — for live data: recent posts, engagement statistics, hashtag trends, and other public Instagram profiles.
2. Elastic search tool (search_calligraphy) — for semantic search: finding past @kai.ligraphy posts by topic, and answering questions about Chinese calligraphy styles (楷书, 行书, 草书, 隶书, 篆书), tools (文房四宝), techniques, and famous calligraphers.

Use the most appropriate source for each question. For questions that span both (e.g. "which calligraphy style appears most in your posts?"), combine both sources.

If a question is unrelated to @kai.ligraphy or Chinese calligraphy, politely decline to answer.""",
    tools=[instagram_mcp_tools, elastic_mcp_tools],
)
```

- [ ] **Step 2: Test locally with ADK web**

```bash
.venv/bin/adk web
```

Open the browser UI and test these four queries:
1. "What are your 3 most recent posts?" → should use Instagram tool
2. "Find your posts related to ink brushwork" → should use Elastic search tool
3. "What is 草书 and how is it different from 楷书?" → should use Elastic knowledge docs
4. "Which calligraphy style do you use most in your posts?" → should combine both

Confirm the agent responds sensibly for each.

- [ ] **Step 3: Commit**

```bash
git add my_agent/agent.py
git commit -m "feat: add Elastic MCP toolset and update agent instruction for dual-source search"
```

---

## Task 7: Add env vars to Cloud Run and redeploy

**Files:** None — Cloud Run configuration via `gcloud` CLI.

- [ ] **Step 1: Update the Cloud Run service with the new env vars**

  Replace `YOUR_SERVICE_NAME` and `YOUR_REGION` with your actual values:

```bash
gcloud run services update YOUR_SERVICE_NAME \
  --region YOUR_REGION \
  --update-env-vars ELASTIC_CLOUD_ID="$(grep ELASTIC_CLOUD_ID my_agent/.env | cut -d= -f2)" \
  --update-env-vars ELASTIC_API_KEY="$(grep ELASTIC_API_KEY my_agent/.env | cut -d= -f2)" \
  --update-env-vars ELASTIC_MCP_URL="$(grep ELASTIC_MCP_URL my_agent/.env | cut -d= -f2)"
```

  Or set them manually in the Cloud Run console: **Cloud Run → your service → Edit & Deploy → Variables & Secrets**.

- [ ] **Step 2: Trigger a new deployment**

  If you used `gcloud run services update`, a new revision is deployed automatically. Otherwise:

```bash
gcloud run deploy YOUR_SERVICE_NAME --region YOUR_REGION --source .
```

- [ ] **Step 3: Smoke test the deployed agent**

  Open your Cloud Run service URL and run the same four test queries from Task 6, Step 2. Confirm all four work correctly in the live deployment.

---

## Demo Script (for the 3-minute video)

Run these four questions in order to show the full capability:

1. **"What are your 3 most recent posts?"** — shows live Instagram data
2. **"Find your posts related to ink brushwork"** — shows Elastic semantic search over post history
3. **"What is 草书 and how does it differ from 楷书?"** — shows Elastic knowledge base
4. **"Which Chinese calligraphy style appears most often in your posts?"** — shows agent combining both sources
