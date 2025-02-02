import tweepy
import feedparser
import requests
import os
from newspaper import Article

bearer_token = os.getenv("BEARER_TOKEN")
consumer_key = os.getenv("CONSUMER_KEY")
consumer_secret = os.getenv("CONSUMER_SECRET")
access_token = os.getenv("ACCESS_TOKEN")
access_token_secret = os.getenv("ACCESS_SECRET")
HF_API_KEY = os.getenv("HF_API_KEY")

client = tweepy.Client(
    bearer_token=bearer_token,
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    access_token=access_token,
    access_token_secret=access_token_secret
)

RSS_URL = "https://seekingalpha.com/tag/market-outlook/feed"

def fetch_news():
    """Fetch news, summarize using Hugging Face, and post to Twitter."""
    feed = feedparser.parse(RSS_URL)
    latest_entry = feed.entries[0]

    title = latest_entry.title
    url = latest_entry.link

    try:
        article = Article(url)
        article.download()
        article.parse()
        full_text = article.text
    except:
        full_text = "No full text available."

    input_text = title + ": " + full_text[:2000]

    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {
        "inputs": input_text,
        "parameters": {
            "max_length": 200,
            "min_length": 50,
            "do_sample": False
        }
    }

    response = requests.post(
        "https://api-inference.huggingface.co/models/facebook/bart-large-cnn",
        headers=headers,
        json=payload
    )

    if response.status_code == 200:
        summary = response.json()[0]['summary_text']
    else:
        summary = title

    tweet = summary[:280]
    post_tweet(tweet)

def post_tweet(tweet):
    """Post a tweet using Twitter API v2"""
    try:
        response = client.create_tweet(text=tweet)
        print("Tweet posted successfully:", response.data)
    except tweepy.TweepyException as e:
        print("Error posting tweet:", e)

if __name__ == '__main__':
    fetch_news()
