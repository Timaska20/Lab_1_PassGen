# src/anime_api.py
import requests
from typing import Dict, Optional

ANILIST_ENDPOINT = "https://graphql.anilist.co"
HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}

# 1) Поиск аниме по названию (Media)
QUERY_MEDIA = """
query($search: String) {
  Media(search: $search, type: ANIME) {
    id
    title { romaji english native }
    genres
    characters(perPage: 10) {
      nodes { name { full } }
    }
  }
}
"""

# 2) Поиск персонажа по имени (Character)
QUERY_CHARACTER = """
query($search: String) {
  Character(search: $search) {
    id
    name { full native }
    media(perPage: 5) {
      nodes {
        title { romaji english native }
      }
    }
  }
}
"""

def _post(query: str, variables: Dict) -> Dict:
    resp = requests.post(ANILIST_ENDPOINT, headers=HEADERS, json={"query": query, "variables": variables}, timeout=15)
    # Если GraphQL вернул ошибки, покажем их явно
    data = resp.json() if resp.headers.get("content-type","").startswith("application/json") else {}
    if resp.status_code >= 400:
        # попытаемся извлечь полезную ошибку из GraphQL
        err = None
        try:
            err = data.get("errors", [{}])[0].get("message")
        except Exception:
            pass
        raise requests.HTTPError(err or f"{resp.status_code} {resp.reason} for url: {resp.url}")
    # GraphQL-ошибки без HTTP 4xx тоже возможны
    if "errors" in data:
        raise requests.HTTPError(data["errors"][0].get("message", "GraphQL error"))
    return data

def fetch_anime_bundle(title: Optional[str] = None, character: Optional[str] = None) -> Dict:
    """
    Возвращает словарь:
      {
        "title": "...",
        "genres": "...",
        "characters": "...",
        "seed_text": "title | genres | characters | character_only"
      }
    Работает, если задан title и/или character (хватает и одного).
    """
    title_info = {}
    char_info = {}

    if title:
        d = _post(QUERY_MEDIA, {"search": title})
        media = (d.get("data") or {}).get("Media")
        if media:
            title_all = " / ".join(filter(None, [
                (media.get("title") or {}).get("english"),
                (media.get("title") or {}).get("romaji"),
                (media.get("title") or {}).get("native"),
            ]))
            genres = ", ".join(media.get("genres") or [])
            char_nodes = ((media.get("characters") or {}).get("nodes") or [])
            chars = ", ".join([(n.get("name") or {}).get("full", "") for n in char_nodes if n])
            title_info = {
                "title": title_all,
                "genres": genres,
                "characters": chars,
            }

    if character:
        d = _post(QUERY_CHARACTER, {"search": character})
        ch = (d.get("data") or {}).get("Character")
        if ch:
            # имя персонажа
            char_name = (ch.get("name") or {}).get("full") or (ch.get("name") or {}).get("native") or character
            # привяжем несколько тайтлов, если есть
            media_nodes = ((ch.get("media") or {}).get("nodes") or [])
            m_titles = []
            for m in media_nodes:
                t = (m.get("title") or {})
                m_titles.append(t.get("english") or t.get("romaji") or t.get("native"))
            m_titles = ", ".join(filter(None, m_titles))
            char_info = {
                "character": char_name,
                "character_media": m_titles
            }

    # Если пусто – ничего не нашли
    if not title_info and not char_info:
        return {}

    # seed собираем из всего, что нашли
    seed_parts = []
    if title_info:
        seed_parts += [title_info.get("title",""), title_info.get("genres",""), title_info.get("characters","")]
    if char_info:
        seed_parts += [char_info.get("character",""), char_info.get("character_media","")]

    return {
        "title": title_info.get("title",""),
        "genres": title_info.get("genres",""),
        "characters": title_info.get("characters",""),
        "character": char_info.get("character",""),
        "character_media": char_info.get("character_media",""),
        "seed_text": " | ".join(filter(None, seed_parts)).strip(" |"),
    }
