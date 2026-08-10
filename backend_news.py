import os
import requests
from dotenv import load_dotenv

from config_loader import BASE_DIR

load_dotenv(os.path.join(BASE_DIR, ".env"))


class NewsBackend:
    def __init__(self):
        self.api_key = os.getenv("NEWS_API_KEY", "").strip()

    def fetch_news(self) -> str:
        if not self.api_key:
            return "NEWS_API_KEY не задано. Додайте ключ у файл .env (див. .env.example)."
        url = f"https://newsapi.org/v2/top-headlines?category=business&apiKey={self.api_key}"
        try:
            resp = requests.get(url, timeout=5)
            data = resp.json()
            if data.get("status") == "error":
                return f"Помилка NewsAPI: {data.get('message', 'unknown')}"
            articles = data.get("articles", [])
            if not articles:
                return "Немає новин."

            news_list = []
            for i, art in enumerate(articles[:10]):
                title = art.get("title", "Без заголовка")
                desc = art.get("description", "") or ""
                news_list.append(f"{i + 1}. {title}\n{desc}\n")
            return "\n".join(news_list)
        except Exception as e:
            return f"Помилка завантаження новин:\n{str(e)}"
