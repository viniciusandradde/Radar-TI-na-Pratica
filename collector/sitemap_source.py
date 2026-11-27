"""Fonte do tipo "sitemap": para sites oficiais que não publicam RSS.

Lê o sitemap.xml do próprio site (o mesmo que ele entrega aos buscadores), pega as
URLs mais recentes pelo <lastmod> dentro de um caminho (ex.: /news/) e abre só as
URLs que ainda não estão no banco, para tirar título, data e resumo dos metadados
da página (og:*, JSON-LD). Respeita o robots.txt.

Campos da fonte em sources.json:
  "type": "sitemap",
  "sitemap_url": "https://x.ai/sitemap.xml",
  "path_prefix": "/news/",            # obrigatório
  "exclude": ["/tag/"],               # opcional: trechos de caminho a ignorar
  "max_age_days": 30,                 # opcional (padrão 30)
  "max_new": 10                       # opcional: páginas abertas por coleta (padrão 10)
"""
from __future__ import annotations

import zlib
import json
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from defusedxml import ElementTree as ET  # XML de terceiros: sem entidades externas

from bs4 import BeautifulSoup
from dateutil import parser as date_parser

LOCAL_HOSTS = {"127.0.0.1", "localhost", "0.0.0.0"}
_robots_cache: dict[str, RobotFileParser] = {}


def _tag(el) -> str:
    return el.tag.rsplit("}", 1)[-1]


def _parse_dt(value: str | None):
    if not value:
        return None
    try:
        dt = date_parser.parse(value)
        return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
    except (ValueError, OverflowError):
        return None


def _allowed(client, url: str, user_agent: str) -> bool:
    parts = urlparse(url)
    base = f"{parts.scheme}://{parts.netloc}"
    rp = _robots_cache.get(base)
    if rp is None:
        rp = RobotFileParser()
        try:
            resp = client.get(base + "/robots.txt", follow_redirects=True)
            rp.parse(resp.text.splitlines() if resp.status_code == 200 else [])
        except Exception:
            rp.parse([])
        _robots_cache[base] = rp
    return rp.can_fetch(user_agent, url)


MAX_SITEMAP_BYTES = 20 * 1024 * 1024  # sitemaps grandes reais ficam bem abaixo disso


def _download_capped(client, url: str) -> bytes:
    chunks, size = [], 0
    with client.stream("GET", url, follow_redirects=True) as resp:
        resp.raise_for_status()
        for chunk in resp.iter_raw():
            size += len(chunk)
            if size > MAX_SITEMAP_BYTES:
                raise ValueError("sitemap maior que 20 MB")
            chunks.append(chunk)
    body = b"".join(chunks)
    if body[:2] == b"\x1f\x8b":
        inflater = zlib.decompressobj(16 + zlib.MAX_WBITS)
        body = inflater.decompress(body, MAX_SITEMAP_BYTES)
        if inflater.unconsumed_tail:
            raise ValueError("sitemap descompactado maior que 20 MB")
    return body


def _read_sitemap(client, url: str) -> list[tuple[str, str]]:
    body = _download_capped(client, url)
    root = ET.fromstring(body)
    if _tag(root) == "sitemapindex":
        raise ValueError("sitemap_url aponta para um índice; informe o sitemap filho")
    out = []
    for node in root:
        fields = {_tag(child): (child.text or "").strip() for child in node}
        if fields.get("loc"):
            out.append((fields["loc"], fields.get("lastmod", "")))
    return out


def _fix_host(loc: str, homepage: str) -> str:
    """Alguns sites publicam o sitemap com host interno (ex.: 127.0.0.1); troca pelo público."""
    parts = urlparse(loc)
    if parts.hostname in LOCAL_HOSTS:
        home = urlparse(homepage)
        return parts._replace(scheme=home.scheme, netloc=home.netloc).geturl()
    return loc


def _same_site(url: str, allowed_hosts: set[str]) -> bool:
    """Só segue URLs http(s) do próprio site da fonte (evita SSRF via sitemap de terceiros)."""
    parts = urlparse(url)
    host = (parts.hostname or "").rstrip(".").lower()
    return parts.scheme in ("http", "https") and host in allowed_hosts


def _get_same_site(client, url: str, allowed_hosts: set[str], max_hops: int = 3):
    """GET seguindo redirecionamentos só enquanto continuarem no mesmo site."""
    for _ in range(max_hops + 1):
        resp = client.get(url, follow_redirects=False)
        if resp.is_redirect:
            url = str(resp.next_request.url) if resp.next_request else ""
            if not _same_site(url, allowed_hosts):
                return None
            continue
        return resp
    return None


def _page_metadata(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    def meta(*keys):
        for key in keys:
            tag = soup.find("meta", attrs={"property": key}) or soup.find("meta", attrs={"name": key})
            if tag and tag.get("content"):
                return tag["content"].strip()
        return None

    published = meta("article:published_time", "og:published_time", "date", "pubdate")
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except (ValueError, TypeError):
            continue
        for item in data if isinstance(data, list) else data.get("@graph", [data]):
            if isinstance(item, dict) and item.get("datePublished"):
                published = published or item["datePublished"]
    title = meta("og:title", "twitter:title") or (soup.title.get_text(strip=True) if soup.title else "")
    site = meta("og:site_name") or ""
    if site:
        # "Título | Stanford HAI" -> "Título"; página cujo título é só o nome do site não é artigo.
        title = re.sub(rf"\s*[|\-–—]\s*{re.escape(site)}\s*$", "", title).strip()
        if title.lower() == site.lower():
            title = ""
    summary = meta("og:description", "description", "twitter:description") or ""
    return {"title": title, "summary": re.sub(r"\s+", " ", summary)[:700], "published": published}


def sitemap_entries(client, source: dict, store, user_agent: str, clean_url) -> dict:
    """Devolve {"records": [...], "duplicate": n, "blocked": n} para uma fonte sitemap."""
    homepage = source["homepage_url"]
    prefix = source["path_prefix"]
    exclude = source.get("exclude", [])
    max_age = timedelta(days=source.get("max_age_days", 30))
    max_new = source.get("max_new", 10)
    now = datetime.now(timezone.utc)

    allowed_hosts = {(urlparse(u).hostname or "").rstrip(".").lower() for u in (homepage, source["sitemap_url"])}
    candidates = []
    for loc, lastmod in _read_sitemap(client, source["sitemap_url"]):
        loc = _fix_host(loc, homepage)
        if not _same_site(loc, allowed_hosts):
            continue
        path = urlparse(loc).path
        if not path.startswith(prefix) or path.rstrip("/") == prefix.rstrip("/"):
            continue
        if any(part in path for part in exclude):
            continue
        when = _parse_dt(lastmod)
        if when and now - when > max_age:
            continue
        candidates.append((when or now, clean_url(loc)))
    candidates.sort(reverse=True)

    records, duplicate, blocked = [], 0, 0
    for when, url in candidates[:25]:
        if store.exists(url):
            duplicate += 1
            continue
        if len(records) >= max_new:
            break
        if not _allowed(client, url, user_agent):
            blocked += 1
            continue
        resp = _get_same_site(client, url, allowed_hosts)
        if resp is None or resp.status_code != 200:
            continue
        info = _page_metadata(resp.text)
        if not info["title"]:
            continue
        published = _parse_dt(info["published"]) or when
        records.append({"title": info["title"], "link": url, "summary": info["summary"],
                        "published_at": published.isoformat()})
    return {"records": records, "duplicate": duplicate, "blocked": blocked}
