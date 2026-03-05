import asyncio
from backend.web_search import WebSearch

async def test():
    ws = WebSearch()
    results = await ws.search("últimas notícias inteligência artificial", max_results=3)
    for r in results:
        print(f"Título: {r['title']}")
        print(f"URL: {r['url']}")
        print(f"Resumo: {r['snippet']}\n")

asyncio.run(test())