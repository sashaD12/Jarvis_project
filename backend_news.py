import requests

class NewsBackend:
    NEWS_API_URL = 'https://newsapi.org/v2/top-headlines?category=business&apiKey=984a385872e24689b1f01ad8fc9d1167'

    def fetch_news(self):
        try:
            resp = requests.get(self.NEWS_API_URL, timeout=5)
            data = resp.json()
            articles = data.get("articles", [])
            if not articles:
                return "Нет новостей."

            news_list = []
            for i, art in enumerate(articles[:]):
                title = art.get("title", "Без заголовка")
                desc = art.get("description", "")
                news_list.append(f"{i+1}. {title}\n{desc}\n")
            return "\n".join(news_list)
        except Exception as e:
            return f"Ошибка загрузки новостей:\n{str(e)}"