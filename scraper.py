

import os
from curl_cffi import requests
from supabase import create_client, Client

# Initialize Supabase using GitHub Secrets / Environment Variables
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

def scrape_reddit_leads():
    # Combine subreddits using + syntax
    url = "https://old.reddit.com/r/shopify+webflow+freelance_forhire/new.json?limit=25"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    # Fetch using Chrome TLS impersonation to bypass 403 blocks
    response = requests.get(url, headers=headers, impersonate="chrome120")

    if response.status_code != 200:
        print(f"Failed to fetch posts. Status code: {response.status_code}")
        return

    posts = response.json()["data"]["children"]
    
    for item in posts:
        post = item["data"]
        lead_data = {
            "post_id": post["id"],
            "title": post["title"],
            "url": f"https://reddit.com{post['permalink']}",
            "author": post["author"],
            "subreddit": post["subreddit"],
            "created_utc": post["created_utc"],
            "selftext": post["selftext"][:500]  # First 500 chars of body
        }

        # Upsert into Supabase to prevent duplicate key errors
        supabase.table("leads").upsert(lead_data, on_conflict="post_id").execute()
        print(f"Saved lead: {lead_data['title']}")

if __name__ == "__main__":
    scrape_reddit_leads()
