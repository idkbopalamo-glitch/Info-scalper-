

import os
import requests
from supabase import create_client, Client

# Fetch environment variables from GitHub Secrets
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase URL or Service Role Key.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def scrape_reddit_leads():
    # Search Reddit API for e-commerce hiring posts
    url = "https://www.reddit.com/r/hireaghostwriter+forhire+freelance/new.json?limit=15"
    headers = {"User-Agent": "Mozilla/5.0 (E-commerce Lead Aggregator Bot v1.0)"}
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch Reddit data: {response.status_code}")
        return

    data = response.json()
    posts = data.get("data", {}).get("children", [])

    for post in posts:
        post_data = post["data"]
        title = post_data.get("title", "")
        permalink = f"https://www.reddit.com{post_data.get('permalink', '')}"
        selftext = post_data.get("selftext", "")

        # Filter for hiring/e-commerce keywords
        if "[hiring]" in title.lower() or "e-commerce" in title.lower() or "shopify" in title.lower():
            lead_data = {
                "title": title,
                "source_url": permalink,
                "description": selftext[:500],
                "platform": "Reddit",
                "status": "active"
            }

            try:
                # Insert into Supabase (prevents duplicate entries)
                supabase.table("leads").upsert(lead_data, on_conflict="source_url").execute()
                print(f"Added lead: {title}")
            except Exception as e:
                print(f"Error inserting lead: {e}")

if __name__ == "__main__":
    scrape_reddit_leads()
