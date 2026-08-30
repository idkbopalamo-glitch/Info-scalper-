
import os
import xml.etree.ElementTree as ET
from curl_cffi import requests
from supabase import create_client, Client

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# 1. Fetch Reddit Leads
def fetch_reddit():
    leads = []
    url = "https://old.reddit.com/r/shopify+webflow+freelance_forhire/new.json?limit=15"
    response = requests.get(url, headers=HEADERS, impersonate="chrome120")
    
    if response.status_code == 200:
        posts = response.json().get("data", {}).get("children", [])
        for item in posts:
            post = item["data"]
            leads.append({
                "post_id": f"reddit_{post.get('id')}",
                "title": post.get("title"),
                "url": f"https://reddit.com{post.get('permalink')}",
                "author": post.get("author"),
                "source": f"Reddit (r/{post.get('subreddit')})",
                "created_utc": post.get("created_utc"),
                "selftext": post.get("selftext", "")[:500]
            })
    return leads

# 2. Fetch Hacker News (Who Is Hiring / Ask HN Leads)
def fetch_hacker_news():
    leads = []
    # Hacker News Firebase API endpoint for newest stories
    url = "https://hacker-news.firebaseio.com/v0/newstories.json"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        story_ids = response.json()[:15]  # Get latest 15 stories
        for s_id in story_ids:
            item_url = f"https://hacker-news.firebaseio.com/v0/item/{s_id}.json"
            res = requests.get(item_url, headers=HEADERS)
            if res.status_code == 200:
                item = res.json()
                title = item.get("title", "")
                # Filter for hiring or freelance related posts
                if any(k in title.lower() for k in ["hiring", "freelance", "contract", "looking for"]):
                    leads.append({
                        "post_id": f"hn_{item.get('id')}",
                        "title": title,
                        "url": item.get("url") or f"https://news.ycombinator.com/item?id={item.get('id')}",
                        "author": item.get("by"),
                        "source": "Hacker News",
                        "created_utc": item.get("time"),
                        "selftext": item.get("text", "")[:500] if item.get("text") else title
                    })
    return leads

# 3. Fetch Upwork / Remote Job RSS Feeds
def fetch_rss_feed(feed_url, source_name):
    leads = []
    response = requests.get(feed_url, headers=HEADERS)
    if response.status_code == 200:
        try:
            root = ET.fromstring(response.content)
            for item in root.findall("./channel/item")[:10]:
                guid = item.find("guid").text if item.find("guid") is not None else item.find("link").text
                leads.append({
                    "post_id": f"rss_{hash(guid)}",
                    "title": item.find("title").text if item.find("title") is not None else "No Title",
                    "url": item.find("link").text if item.find("link") is not None else "",
                    "author": "RSS Feed",
                    "source": source_name,
                    "created_utc": None,
                    "selftext": item.find("description").text[:500] if item.find("description") is not None else ""
                })
        except Exception as e:
            print(f"Error parsing RSS feed from {source_name}: {e}")
    return leads

# Main Orchestrator
def main():
    all_leads = []

    print("Fetching Reddit...")
    all_leads.extend(fetch_reddit())

    print("Fetching Hacker News...")
    all_leads.extend(fetch_hacker_news())

    print("Fetching Remote Job RSS Feeds...")
    all_leads.extend(fetch_rss_feed("https://weworkremotely.com/categories/remote-programming-jobs.rss", "WeWorkRemotely"))

    print(f"Total leads collected across all web sources: {len(all_leads)}")

    if all_leads:
        # Save to Supabase
        supabase.table("leads").upsert(all_leads, on_conflict="post_id").execute()
        print("Successfully written to Supabase database.")

if __name__ == "__main__":
    main()
