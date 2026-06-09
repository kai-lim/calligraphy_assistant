import sys
import os

from instagram_mcp_server import search_instagram_profile

# Test the search_instagram_profile function with 'instagram'
print("Testing search_instagram_profile with 'instagram':")
result = search_instagram_profile("instagram", limit=3)
print(result)
