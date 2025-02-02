import tweepy
import feedparser
import requests
import schedule
import time
from flask import Flask
from newspaper import Article

import os

consumer_key = os.getenv("CONSUMER_KEY")
consumer_secret = os.getenv("CONSUMER_SECRET")
access_token = os.getenv("ACCESS_TOKEN")
access_token_secret = os.getenv("ACCESS_SECRET")

HF_API_KEY = os.getenv("HF_API_KEY")

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)


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
        json=payload)

    if response.status_code == 200:
        summary = response.json()[0]['summary_text']
    else:
        summary = title

    tweet = summary[:280]
    api.update_status(tweet)
    print("Tweet posted:", tweet)


schedule.every().hour.at(":00").do(fetch_news)

app = Flask(__name__)


@app.route('/')
def home():
    return "Bot is running!"


def run_schedule():
    """Keep the bot running."""
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == '__main__':
    from threading import Thread
    Thread(target=run_schedule).start()
    app.run(host="0.0.0.0", port=8080)
