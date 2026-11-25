"""Resumo diário do Radar para o WhatsApp (via WuzAPI).

Escolhe até DIGEST_MAX notícias das últimas 24 h, por trilha editorial, com prioridade
para fontes primárias (campo "papel" do sources.json), no máximo uma por fonte e
DIGEST_PER_TRAIL por trilha. Monta a mensagem no formato do WhatsApp e envia.

Variáveis:
  RADAR_DATABASE_URL   banco do Radar
  WUZAPI_URL           ex.: http://10.1.30.144:8089
  WUZAPI_TOKEN         token da sessão (usuário) do WuzAPI que envia
  DIGEST_TO            número de destino, só dígitos com DDI (ex.: 55...)
  DIGEST_DRY_RUN=1     só imprime a mensagem, não envia (padrão quando faltar WUZAPI_*)
  DIGEST_MAX=10, DIGEST_PER_TRAIL=3, DIGEST_HOURS=24
Uso: python digest.py [--dry-run]
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
import psycopg

ROOT = os.path.dirname(__file__)
TZ = ZoneInfo("America/Sao_Paulo")

# Trilhas na ordem em que aparecem na mensagem; categoria do Radar -> trilha.
TRAILS = [
    ("🤖", "IA", lambda c: c.startswith("IA ·") and c != "IA · Saúde" or c == "Inteligência Artificial"),
    ("🛡️", "Cibersegurança", lambda c: c == "Cibersegurança"),
    ("🏥", "Saúde digital", lambda c: c in ("Saúde Digital", "IA · Saúde")),
    ("☁️", "Infra, cloud e SRE", lambda c: c in ("Infraestrutura & Cloud", "DevOps & SRE")),
    ("📋", "Governança e regulação", lambda c: c == "ITSM & Governança"),
    ("📈", "Mercado", lambda c: c == "Mercado & Estratégia"),
]
# Fontes de notas de versão: úteis no banco, ruído no resumo.
SKIP_SOURCES_SUFFIX = ("(versões)",)


def trail_of(category: str):
    for icon, name, match in TRAILS:
        if match(category or ""):
            return icon, name
    return None


def load_papel() -> dict[str, str]:
    with open(os.path.join(ROOT, "sources.json"), encoding="utf-8") as f:
        return {s["name"]: s.get("papel", "descoberta") for s in json.load(f)}


def pick(rows, papel, max_total: int, per_trail: int):
    """rows: (source_name, title, url, category, published_at) do mais novo ao mais velho."""
    ranked = sorted(rows, key=lambda r: (papel.get(r[0]) != "primaria", -(r[4].timestamp() if r[4] else 0)))
    used_sources, per, chosen = set(), {}, []
    for src, title, url, cat, pub in ranked:
        t = trail_of(cat)
        if not t or src in used_sources or src.endswith(SKIP_SOURCES_SUFFIX):
            continue
        if per.get(t[1], 0) >= per_trail:
            continue
        used_sources.add(src)
        per[t[1]] = per.get(t[1], 0) + 1
        chosen.append((t, src, title, url))
        if len(chosen) >= max_total:
            break
    return chosen


def render(chosen, total_24h: int, now: datetime) -> str:
    lines = [f"*VSA Radar — {now:%d/%m/%Y}*",
             f"_{len(chosen)} destaques entre {total_24h} notícias das últimas 24 h_", ""]
    for icon, name, _ in TRAILS:
        items = [c for c in chosen if c[0][1] == name]
        if not items:
            continue
        lines.append(f"{icon} *{name}*")
        for _, src, title, url in items:
            title = " ".join(title.split())
            lines.append(f"• {title[:140]}{'…' if len(title) > 140 else ''} — _{src}_")
            lines.append(f"  {url}")
        lines.append("")
    lines.append("Fontes primárias primeiro. Notícia é pista: confirme na fonte antes de publicar.")
    return "\n".join(lines).strip()


def build_message(dsn: str) -> str | None:
    hours = int(os.environ.get("DIGEST_HOURS", "24"))
    with psycopg.connect(dsn, connect_timeout=10) as conn:
        rows = conn.execute(
            """select source_name, title, canonical_url, category, published_at from news_items
               where created_at > now() - make_interval(hours => %s)
                 and (published_at is null or published_at > now() - make_interval(hours => %s))
               order by published_at desc nulls last""", (hours, hours * 2)).fetchall()
    if not rows:
        return None
    chosen = pick(rows, load_papel(), int(os.environ.get("DIGEST_MAX", "10")), int(os.environ.get("DIGEST_PER_TRAIL", "3")))
    return render(chosen, len(rows), datetime.now(TZ)) if chosen else None


def send(text: str) -> None:
    url, token, to = os.environ["WUZAPI_URL"].rstrip("/"), os.environ["WUZAPI_TOKEN"], os.environ["DIGEST_TO"]
    if not to.isdigit():
        raise ValueError("DIGEST_TO deve ter só dígitos, com DDI")
    resp = httpx.post(f"{url}/chat/send/text", headers={"Token": token},
                      json={"Phone": to, "Body": text}, timeout=30)
    resp.raise_for_status()
    body = resp.json()
    if not body.get("success", True):
        raise RuntimeError(f"WuzAPI recusou: {str(body)[:200]}")


def main() -> int:
    dry = "--dry-run" in sys.argv or os.environ.get("DIGEST_DRY_RUN") == "1" \
        or not all(os.environ.get(k) for k in ("WUZAPI_URL", "WUZAPI_TOKEN", "DIGEST_TO"))
    text = build_message(os.environ["RADAR_DATABASE_URL"])
    if not text:
        print("[digest] nada novo nas últimas horas; nenhuma mensagem")
        return 0
    if dry:
        print("[digest] SIMULAÇÃO (não enviado):\n" + text)
        return 0
    send(text)
    print(f"[digest] enviado ({len(text)} caracteres) para ...{os.environ['DIGEST_TO'][-4:]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
