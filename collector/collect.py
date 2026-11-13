"""Collect public RSS/Atom feeds and insert source-linked items into the Radar database.
No scraping of paywalled pages, social networks, or newsletter content.

Storage backends (chosen by environment):
- RADAR_DATABASE_URL set  -> own PostgreSQL (postgres/schema.sql), ADR-001.
- otherwise               -> Supabase (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, VSA_OWNER_ID), legacy.
"""
from __future__ import annotations
import json, os, re, sys, hashlib
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin, urldefrag, urlparse
import feedparser
import httpx
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

ROOT = os.path.dirname(__file__)
USER_AGENT = "VSA-Radar/1.0 (+https://github.com/viniciusandradde/Radar-TI-na-Pratica-)"
TIMEOUT = 18

def clean_url(url: str) -> str:
    url = urldefrag((url or "").strip())[0]
    return re.sub(r"[?&](utm_[^=]+|fbclid|gclid)=[^&]*", "", url).rstrip("?&")

def discover_feed(client: httpx.Client, homepage: str) -> str | None:
    try:
        response = client.get(homepage, follow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for link in soup.find_all("link", href=True):
            rel = " ".join(link.get("rel", [])).lower()
            typ = (link.get("type") or "").lower()
            if "alternate" in rel and ("rss" in typ or "atom" in typ or "xml" in typ):
                return urljoin(str(response.url), link["href"])
        # Conservative common feed paths only; validate by parsing before accepting.
        base = f"{urlparse(str(response.url)).scheme}://{urlparse(str(response.url)).netloc}"
        for suffix in ("/feed/", "/feed", "/rss", "/rss.xml", "/atom.xml"):
            candidate = urljoin(base, suffix)
            parsed = feedparser.parse(candidate)
            if parsed.entries:
                return candidate
    except Exception as exc:
        print(f"[WARN] discovery failed for {homepage}: {exc}")
    return None

def parse_date(entry):
    for key in ("published", "updated", "created"):
        value = entry.get(key)
        if value:
            try:
                dt = date_parser.parse(value)
                if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc).isoformat()
            except Exception:
                pass
    return datetime.now(timezone.utc).isoformat()

def summarize(entry):
    raw = entry.get("summary") or entry.get("description") or ""
    text = BeautifulSoup(raw, "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text)[:700]

class SupabaseStore:
    """Legacy backend: unchanged behaviour (upsert ignoring duplicates)."""
    name = "supabase"

    def __init__(self):
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        self.owner_id = os.environ.get("VSA_OWNER_ID")
        if not all((url, key, self.owner_id)):
            sys.exit("Missing SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY or VSA_OWNER_ID")
        from supabase import create_client  # imported only when this backend is used
        self.client = create_client(url, key)

    def insert(self, record) -> bool | None:
        self.client.table("news_items").upsert(record, on_conflict="owner_id,canonical_url", ignore_duplicates=True).execute()
        return None  # Supabase upsert does not report whether the row was new

    def finish(self, stats, details):
        pass


class PostgresStore:
    """Own PostgreSQL backend (postgres/schema.sql). Records each run in collector_runs."""
    name = "postgres"

    def __init__(self, dsn: str):
        import psycopg  # imported only when this backend is used
        self.conn = psycopg.connect(dsn, autocommit=True, connect_timeout=10)
        owner = os.environ.get("VSA_OWNER_ID")
        if not owner:
            row = self.conn.execute("select id from app_users where role = 'owner' order by created_at limit 1").fetchone()
            if not row:
                sys.exit("No owner in app_users: apply postgres/schema.sql or set VSA_OWNER_ID")
            owner = row[0]
        self.owner_id = str(owner)
        self.run_id = self.conn.execute("insert into collector_runs default values returning id").fetchone()[0]

    def insert(self, record) -> bool:
        # unique(owner_id, canonical_url) keeps repeated runs idempotent; RETURNING tells new vs duplicate.
        row = self.conn.execute(
            """insert into news_items (owner_id, source_name, source_url, canonical_url, title, summary, published_at, category, status)
               values (%(owner_id)s, %(source_name)s, %(source_url)s, %(canonical_url)s, %(title)s, %(summary)s, %(published_at)s, %(category)s, %(status)s)
               on conflict (owner_id, canonical_url) do nothing returning id""",
            record,
        ).fetchone()
        return row is not None

    def finish(self, stats, details):
        status = "success" if stats["errors"] == 0 else ("partial" if stats["feeds_ok"] else "failed")
        self.conn.execute(
            """update collector_runs set finished_at = now(), status = %s, feeds_ok = %s, items_seen = %s, items_new = %s,
               items_duplicate = %s, sources_skipped = %s, errors = %s, details = %s::jsonb where id = %s""",
            (status, stats["feeds_ok"], stats["seen"], stats["new"], stats["duplicate"], stats["skipped"], stats["errors"],
             json.dumps(details, ensure_ascii=False), self.run_id),
        )
        self.conn.close()


def open_store():
    dsn = os.environ.get("RADAR_DATABASE_URL")
    return PostgresStore(dsn) if dsn else SupabaseStore()


def main():
    store = open_store()
    owner_id = store.owner_id
    with open(os.path.join(ROOT, "sources.json"), encoding="utf-8") as f:
        sources = json.load(f)
    headers = {"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, text/html"}
    inserted = skipped = errors = 0
    stats = {"feeds_ok": 0, "seen": 0, "new": 0, "duplicate": 0, "skipped": 0, "errors": 0}
    details = []
    with httpx.Client(headers=headers, timeout=TIMEOUT) as client:
        for source in sources:
            if not source.get("enabled", True): continue
            homepage = source["homepage_url"]
            feed_url = source.get("feed_url") or discover_feed(client, homepage)
            if not feed_url:
                print(f"[SKIP] no RSS/Atom discovered: {source['name']}")
                skipped += 1
                details.append({"source": source["name"], "result": "skipped", "reason": "no RSS/Atom discovered"})
                continue
            parsed = feedparser.parse(feed_url)
            if parsed.bozo and not parsed.entries:
                print(f"[WARN] invalid feed {source['name']}: {parsed.bozo_exception}")
                errors += 1
                details.append({"source": source["name"], "result": "error", "feed_url": feed_url, "reason": str(parsed.bozo_exception)[:300]})
                continue
            print(f"[FEED] {source['name']} -> {feed_url} ({len(parsed.entries)} entries)")
            stats["feeds_ok"] += 1
            src_new = src_dup = 0
            for entry in parsed.entries[:25]:
                title = (entry.get("title") or "").strip()
                link = clean_url(entry.get("link") or "")
                if not title or not link or urlparse(link).scheme not in ("http", "https"): continue
                record = {
                    "owner_id": owner_id,
                    "source_name": source["name"],
                    "source_url": homepage,
                    "canonical_url": link,
                    "title": title[:500],
                    "summary": summarize(entry),
                    "published_at": parse_date(entry),
                    "category": source.get("category", "Mercado & Estratégia"),
                    "status": "new"
                }
                try:
                    # Unique(owner_id, canonical_url) makes repeated runs idempotent.
                    is_new = store.insert(record)
                    inserted += 1
                    if is_new is True: src_new += 1
                    elif is_new is False: src_dup += 1
                except Exception as exc:
                    print(f"[ERROR] {source['name']} / {title[:80]}: {exc}")
                    errors += 1
            stats["new"] += src_new; stats["duplicate"] += src_dup
            details.append({"source": source["name"], "result": "ok", "feed_url": feed_url, "new": src_new, "duplicate": src_dup})
    stats.update(seen=inserted, skipped=skipped, errors=errors)
    store.finish(stats, details)
    print(f"Finished [{store.name}]. processed={inserted} new={stats['new']} duplicate={stats['duplicate']} undiscovered={skipped} errors={errors}")

if __name__ == "__main__":
    main()
