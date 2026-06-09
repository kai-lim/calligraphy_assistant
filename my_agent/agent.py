import os
import sys
from dotenv import load_dotenv
from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
from mcp import StdioServerParameters

# Load environment variables from the .env file in this directory
current_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(current_dir, ".env")
load_dotenv(dotenv_path)

server_path = os.path.join(current_dir, "instagram_mcp_server.py")

# Configure connection using standard input/output (stdio)
server_params = StdioServerParameters(
    command=sys.executable,
    args=[server_path],
    env={
        # Automatically propagate environment variables if present
        "INSTAGRAM_ACCOUNT_ID": os.environ.get("INSTAGRAM_ACCOUNT_ID", ""),
        "INSTAGRAM_ACCESS_TOKEN": os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")
    }
)

connection_params = StdioConnectionParams(
    server_params=server_params,
    timeout=60
)

# Initialize MCP Toolset containing Instagram API tools
instagram_mcp_tools = MCPToolset(connection_params=connection_params)

root_agent = Agent(
    model='gemini-2.5-flash',
    name='social_media_agent',
    description='A helpful social media assistant for questions about @kai.ligraphy, a social media account on Instagram.',
    instruction="""Answer user questions about @kai.ligraphy on Instagram. 
    If the question is not about @kai.ligraphy on Instagram, politely decline to answer and suggest the user visit @kai.ligraphy on Instagram to learn more.""",
    tools=[instagram_mcp_tools]
)
