import requests

def fetch_news(api_key, query="AI", total_results=100):
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "contextualwebsearch-websearch-v1.p.rapidapi.com"
    }

    page_size = 50
    pages_needed = (total_results + page_size - 1) // page_size
    all_results = []

    for page in range(1, pages_needed + 1):
        params = {
            "q": query,
            "pageNumber": page,
            "pageSize": page_size,
            "autoCorrect": "true",
            "safeSearch": "true",
            "withThumbnails": "true"
        }

        response = requests.get(
            "https://contextualwebsearch-websearch-v1.p.rapidapi.com/api/Search/NewsSearchAPI",
            headers=headers,
            params=params
        )

        if response.status_code == 200:
            data = response.json()
            articles = data.get("value", [])
            all_results.extend(articles)
        else:
            print(f"Error fetching page {page}: {response.status_code}")
            break

    return all_results[:total_results]  # Trim in case of overshoot

# Example usage:
api_key = "YOUR_RAPIDAPI_KEY_HERE"
news_results = fetch_news(api_key, query="AI", total_results=100)

for idx, article in enumerate(news_results, 1):
    print(f"{idx}. {article['title']} — {article['url']}")
