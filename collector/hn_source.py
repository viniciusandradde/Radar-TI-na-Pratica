"""Fonte do tipo "hn_api": Hacker News pela API oficial de busca (Algolia).

Substitui o hnrss.org (serviço de terceiros que às vezes cai) para pegar as
histórias com muitos pontos sobre os termos escolhidos.

Campos da fonte em sources.json:
  "type": "hn_api",
  "queries": ["AI", "LLM", "agents"],   # uma busca por termo; resultados unidos
  "min_points": 150,                     # opcional (padrão 150)
  "max_age_days": 3                      # opcional (padrão 3)
"""
from __future__ import annotations

import time

API = "https://hn.algolia.com/api/v1/search_by_date"


def hn_entries(client, source: dict, store, clean_url) -> dict:
    min_points = source.get("min_points", 150)
    since = int(time.time()) - source.get("max_age_days", 3) * 86400
    seen, records, duplicate = set(), [], 0
    for query in source.get("queries", ["AI"]):
        resp = client.get(API, params={"query": query, "tags": "story", "hitsPerPage": 25,
                                       "numericFilters": f"points>={min_points},created_at_i>={since}"})
        resp.raise_for_status()
        for hit in resp.json().get("hits", []):
            item_url = f"https://news.ycombinator.com/item?id={hit['objectID']}"
            link = clean_url(hit.get("url") or item_url)
            if link in seen or not hit.get("title"):
                continue
            seen.add(link)
            if store.exists(link):
                duplicate += 1
                continue
            records.append({
                "title": hit["title"],
                "link": link,
                "summary": f"{hit.get('points', 0)} pontos e {hit.get('num_comments', 0)} comentários no Hacker News: {item_url}",
                "published_at": hit["created_at"],
            })
    return {"records": records, "duplicate": duplicate, "blocked": 0}
