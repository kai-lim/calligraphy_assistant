import os
import sys
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from mcp.server.fastmcp import FastMCP

current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(current_dir, ".env"))

mcp = FastMCP("elasticsearch")


def get_es_client() -> Elasticsearch:
    return Elasticsearch(
        os.environ["ELASTIC_URL"],
        api_key=os.environ["ELASTIC_API_KEY"],
    )


@mcp.tool()
def search_calligraphy(query: str, limit: int = 5) -> str:
    """Searches the Chinese calligraphy knowledge base and @kai.ligraphy's historical
    Instagram posts by meaning. Use this for questions about calligraphy styles
    (楷书, 行书, 草书, 隶书, 篆书), tools (文房四宝), techniques, famous calligraphers,
    or to find past posts by topic.

    Args:
        query: The search query in English or Chinese.
        limit: Maximum number of results to return (default 5).
    """
    es = get_es_client()
    resp = es.search(
        index="calligraphy",
        body={
            "query": {
                "semantic": {
                    "field": "searchable_text",
                    "query": query,
                }
            },
            "size": limit,
        },
    )

    hits = resp["hits"]["hits"]
    if not hits:
        return f"No results found for '{query}'."

    results = []
    for hit in hits:
        src = hit["_source"]
        if src.get("doc_type") == "knowledge":
            results.append(
                f"[Knowledge] **{src.get('title')}**\n{src.get('content')}\n"
            )
        else:
            results.append(
                f"[Post] **Caption**: {src.get('caption', 'No caption')}\n"
                f"  Likes: {src.get('like_count', 0)} | Comments: {src.get('comments_count', 0)}\n"
                f"  Hashtags: {', '.join(src.get('hashtags', []))}\n"
                f"  Link: {src.get('permalink')}\n"
            )

    return "\n---\n".join(results)


if __name__ == "__main__":
    mcp.run(transport="stdio")
