import os
import requests
import json
import sys
import re
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables from the .env file in this directory if present
current_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(current_dir, ".env")
load_dotenv(dotenv_path)

# Create the FastMCP server instance
mcp = FastMCP("instagram")

# Helper function to get credentials
def get_credentials():
    account_id = os.environ.get("INSTAGRAM_ACCOUNT_ID")
    access_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")
    return account_id, access_token

@mcp.tool()
def get_instagram_posts(limit: int = 5) -> str:
    """Fetches the latest posts published by the user on Instagram.
    
    Args:
        limit: The maximum number of posts to return (default 5).
    """
    account_id, access_token = get_credentials()
    if not account_id or not access_token:
        return "Error: INSTAGRAM_ACCOUNT_ID and INSTAGRAM_ACCESS_TOKEN must be configured in environment variables."

    url = f"https://graph.facebook.com/v19.0/{account_id}/media"
    params = {
        "fields": "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count",
        "limit": limit,
        "access_token": access_token
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json().get("data", [])
        if not data:
            return "No posts found on this account."
        
        # Format the result nicely for the LLM
        result = []
        for post in data:
            result.append(
                f"- **Post ID**: {post.get('id')}\n"
                f"  **Type**: {post.get('media_type')}\n"
                f"  **Caption**: {post.get('caption', 'No caption')}\n"
                f"  **Timestamp**: {post.get('timestamp')}\n"
                f"  **Likes**: {post.get('like_count', 0)} | **Comments**: {post.get('comments_count', 0)}\n"
                f"  **Link**: {post.get('permalink')}\n"
            )
        return "\n".join(result)
    except Exception as e:
        return f"Error fetching posts: {str(e)}"

@mcp.tool()
def get_hashtag_recent_media(hashtag_name: str) -> str:
    """Finds recent public media tagged with a specific hashtag.
    
    Args:
        hashtag_name: The name of the hashtag to search (without the '#' symbol).
    """
    account_id, access_token = get_credentials()
    if not account_id or not access_token:
        return "Error: INSTAGRAM_ACCOUNT_ID and INSTAGRAM_ACCESS_TOKEN must be configured in environment variables."

    # Remove '#' prefix if provided by accident
    hashtag_name = hashtag_name.lstrip('#')

    # Step 1: Search for the hashtag ID
    search_url = "https://graph.facebook.com/v19.0/ig_hashtag_search"
    search_params = {
        "user_id": account_id,
        "q": hashtag_name,
        "access_token": access_token
    }

    try:
        search_res = requests.get(search_url, params=search_params)
        search_res.raise_for_status()
        search_data = search_res.json().get("data", [])
        if not search_data:
            return f"Error: Hashtag '{hashtag_name}' could not be resolved."
        
        hashtag_id = search_data[0].get("id")
        
        # Step 2: Fetch recent media for this hashtag ID
        media_url = f"https://graph.facebook.com/v19.0/{hashtag_id}/recent_media"
        media_params = {
            "user_id": account_id,
            "fields": "id,media_type,media_url,permalink,like_count,comments_count",
            "access_token": access_token
        }
        
        media_res = requests.get(media_url, params=media_params)
        media_res.raise_for_status()
        media_data = media_res.json().get("data", [])
        
        if not media_data:
            return f"No recent public media found for #{hashtag_name}."
            
        result = [f"### Recent media for #{hashtag_name}:"]
        for media in media_data:
            result.append(
                f"- **Media ID**: {media.get('id')}\n"
                f"  **Type**: {media.get('media_type')}\n"
                f"  **Likes**: {media.get('like_count', 0)} | **Comments**: {media.get('comments_count', 0)}\n"
                f"  **Link**: {media.get('permalink')}\n"
            )
        return "\n".join(result)
    except Exception as e:
        return f"Error searching hashtag: {str(e)}"

@mcp.tool()
def search_instagram_profile(username: str, limit: int = 5) -> str:
    """Searches for public information of another public Instagram Business or Creator profile.
    
    This retrieves metadata about the account (such as username, biography, followers count)
    as well as their recent media posts, including the caption (with hashtags), posted time,
    likes, comments, and post link.
    
    Args:
        username: The Instagram username of the public profile (without the '@' symbol).
        limit: The maximum number of recent media posts to retrieve (default 5).
    """
    account_id, access_token = get_credentials()
    if not account_id or not access_token:
        return "Error: INSTAGRAM_ACCOUNT_ID and INSTAGRAM_ACCESS_TOKEN must be configured in environment variables."

    # Normalize username: remove leading '@' and trim whitespace
    username = username.strip().lstrip('@')
    if not username:
        return "Error: A valid username must be provided."

    # Using the Facebook Graph API Business Discovery endpoint
    url = f"https://graph.facebook.com/v19.0/{account_id}"
    params = {
        "fields": f"business_discovery.username({username}){{id,username,name,biography,followers_count,media_count,website,media.limit({limit}){{id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count}}}}",
        "access_token": access_token
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        discovery_data = response.json().get("business_discovery", {})
        if not discovery_data:
            return f"Error: No business discovery data returned for user '{username}'."

        result = [
            f"### Instagram Profile: @{discovery_data.get('username')}",
            f"**Name**: {discovery_data.get('name')}",
            f"**Biography**: {discovery_data.get('biography', 'N/A')}",
            f"**Followers**: {discovery_data.get('followers_count', 0)} | **Media Count**: {discovery_data.get('media_count', 0)}",
            f"**Website**: {discovery_data.get('website', 'N/A')}\n",
            f"#### Recent Posts:"
        ]
        
        media_list = discovery_data.get("media", {}).get("data", [])
        if not media_list:
            result.append("No posts found for this user.")
        else:
            for post in media_list:
                caption = post.get('caption', '')
                timestamp = post.get('timestamp')
                likes = post.get('like_count', 0)
                comments = post.get('comments_count', 0)
                permalink = post.get('permalink')
                media_type = post.get('media_type')
                
                # Extract hashtags
                hashtags = re.findall(r'#\w+', caption)
                hashtags_str = ", ".join(hashtags) if hashtags else "None"
                
                result.append(
                    f"- **Post ID**: {post.get('id')}\n"
                    f"  **Type**: {media_type}\n"
                    f"  **Posted At**: {timestamp}\n"
                    f"  **Likes**: {likes} | **Comments**: {comments}\n"
                    f"  **Hashtags**: {hashtags_str}\n"
                    f"  **Caption**: {caption}\n"
                    f"  **Link**: {permalink}\n"
                )
        return "\n".join(result)
    except requests.exceptions.HTTPError as he:
        try:
            err_json = he.response.json()
            err_msg = err_json.get("error", {}).get("message", str(he))
            return f"API Error searching profile @{username}: {err_msg}"
        except Exception:
            return f"HTTP Error searching profile @{username}: {str(he)}"
    except Exception as e:
        return f"Error searching profile @{username}: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
