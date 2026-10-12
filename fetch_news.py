#!/usr/bin/env python3
"""Собирает заголовки из русскоязычных изданий, работающих за пределами России,
и сохраняет их в news.json для страницы index.html."""
import json
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

FEEDS = [
    ("Meduza", "https://meduza.io/rss/all"),
    ("BBC", "https://feeds.bbci.co.uk/russian/rss.xml"),
    ("DW", "https://rss.dw.com/rdf/rss-ru-all"),
    ("Euronews", "https://ru.euronews.com/rss"),
    ("The Insider", "https://theins.ru/feed"),
    ("Медиазона", "https://zona.media/rss"),
    ("Новая газета Европа", "https://novayagazeta.eu/feed/rss"),
    ("Холод", "https://holod.media/feed/"),
]

PER_SOURCE = 12          # сколько последних заголовков брать у каждого издания
MAX_AGE_HOURS = 48       # старше этого возраста новости отбрасываются
OUT_FILE = Path(__file__).with_name("news.json")


def local(tag):
    return tag.rsplit("}", 1)[-1]


def child_text(el, name):
    for c in el:
        if local(c.tag) == name and c.text:
            return c.text.strip()
    return ""


def parse_date(s):
    if not s:
        return None
    try:
        d = parsedate_to_datetime(s)
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)


def fetch(name, url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        root = ET.fromstring(r.read())
    items = []
    for el in root.iter():
        if local(el.tag) != "item":
            continue
        title = child_text(el, "title")
        date = parse_date(child_text(el, "pubDate") or child_text(el, "date"))
        if not title or not date:
            continue
        items.append({"source": name, "title": title,
                      "link": child_text(el, "link"), "ts": int(date.timestamp())})
    items.sort(key=lambda x: x["ts"], reverse=True)
    return items[:PER_SOURCE]


def build():
    now = datetime.now(timezone.utc).timestamp()
    all_items, errors = [], []
    for name, url in FEEDS:
        try:
            all_items += fetch(name, url)
        except Exception as e:  # одна упавшая лента не должна ломать остальные
            errors.append(f"{name}: {e}")
    all_items = [i for i in all_items if now - i["ts"] < MAX_AGE_HOURS * 3600]
    all_items.sort(key=lambda x: x["ts"], reverse=True)
    OUT_FILE.write_text(json.dumps(
        {"updated": int(now), "items": all_items}, ensure_ascii=False), encoding="utf-8")
    return len(all_items), errors


if __name__ == "__main__":
    n, errs = build()
    print(f"Сохранено заголовков: {n}")
    for e in errs:
        print("Ошибка:", e, file=sys.stderr)
