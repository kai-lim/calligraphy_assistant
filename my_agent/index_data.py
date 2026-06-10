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

# Load env before any package imports to avoid agent.py running first via __init__.py
_current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _current_dir)

from dotenv import load_dotenv
load_dotenv(os.path.join(_current_dir, ".env"), override=True)

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from calligraphy_knowledge import KNOWLEDGE_DOCS  # direct import, skips __init__.py

INDEX_NAME = "calligraphy"


def build_es_client() -> Elasticsearch:
    url = os.environ["ELASTIC_URL"]
    api_key = os.environ["ELASTIC_API_KEY"]
    return Elasticsearch(url, api_key=api_key)


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
