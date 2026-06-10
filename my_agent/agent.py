import os
import sys
from dotenv import load_dotenv
from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
from mcp import StdioServerParameters

current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(current_dir, ".env"))

instagram_mcp_tools = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=[os.path.join(current_dir, "instagram_mcp_server.py")],
            env={
                "INSTAGRAM_ACCOUNT_ID": os.environ.get("INSTAGRAM_ACCOUNT_ID", ""),
                "INSTAGRAM_ACCESS_TOKEN": os.environ.get("INSTAGRAM_ACCESS_TOKEN", ""),
            },
        ),
        timeout=60,
    )
)

elastic_mcp_tools = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=[os.path.join(current_dir, "elastic_mcp_server.py")],
            env={
                "ELASTIC_URL": os.environ.get("ELASTIC_URL", ""),
                "ELASTIC_API_KEY": os.environ.get("ELASTIC_API_KEY", ""),
            },
        ),
        timeout=60,
    )
)

root_agent = Agent(
    model="gemini-2.5-flash",
    name="calligraphy_assistant",
    description=(
        "A helpful assistant for @kai.ligraphy, a Chinese calligraphy Instagram account."
    ),
    instruction="""You are a helpful assistant for @kai.ligraphy, a Chinese calligraphy Instagram account.

You have two sources of information:
1. Instagram tools — for live data: recent posts, engagement statistics, hashtag trends, and other public Instagram profiles.
2. search_calligraphy tool — for semantic search: finding past @kai.ligraphy posts by topic, and answering questions about Chinese calligraphy styles (楷书, 行书, 草书, 隶书, 篆书), tools (文房四宝), techniques, and famous calligraphers.

Use the most appropriate source for each question. For questions that span both (e.g. "which calligraphy style appears most in your posts?"), combine both sources.

If a question is unrelated to @kai.ligraphy or Chinese calligraphy, politely decline to answer.""",
    tools=[instagram_mcp_tools, elastic_mcp_tools],
)
