# /// script
# requires-python = ">=3.12"
# dependencies = ["feedparser"]
# ///

import feedparser
import html
import json
import re
import socket
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from pathlib import Path

MAX_SUMMARY_LEN = 400


def load_config(path="feeds.json"):
    with open(path) as f:
        return json.load(f)


def strip_html(text):
    return html.unescape(re.sub(r"<[^>]+>", "", text or "").strip())


def truncate(text, max_len=MAX_SUMMARY_LEN):
    text = " ".join(text.split())
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0] + "…"


def fetch_feed(cfg, cutoff):
    url = cfg["url"]
    print(f"  fetching {url}")
    parsed = feedparser.parse(url)
    name = cfg.get("name") or parsed.feed.get("title", url)
    entries = []
    for entry in parsed.entries:
        pt = entry.get("published_parsed") or entry.get("updated_parsed")
        date = datetime(*pt[:6], tzinfo=timezone.utc) if pt else datetime.now(timezone.utc)
        if date < cutoff:
            continue
        raw = entry.get("summary") or entry.get("description") or ""
        entries.append({
            "date": date,
            "title": strip_html(entry.get("title", "Untitled")),
            "summary": truncate(strip_html(raw)),
            "link": entry.get("link", "#"),
            "feed": name,
        })
    return entries


def fetch_all(feeds, max_age_days):
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    with ThreadPoolExecutor() as executor:
        batches = list(executor.map(lambda cfg: fetch_feed(cfg, cutoff), feeds))
    entries = [e for batch in batches for e in batch]
    entries.sort(key=lambda e: e["date"], reverse=True)
    return entries


def render_entry(e):
    date = e["date"].strftime("%Y-%m-%d")
    title = html.escape(e["title"])
    summary = html.escape(e["summary"])
    link = html.escape(e["link"])
    feed = html.escape(e["feed"])
    summary_block = f'            <p class="summary">{summary}</p>\n' if summary else ""
    return (
        f'      <div class="entry">\n'
        f'        <div class="date">{date}</div>\n'
        f'        <div class="content">\n'
        f'          <details>\n'
        f'            <summary>{title}<span class="feed-name">{feed}</span></summary>\n'
        f"{summary_block}"
        f'            <p class="link-line"><a href="{link}">link</a></p>\n'
        f'          </details>\n'
        f"        </div>\n"
        f"      </div>\n"
    )


def render_page(config, entries):
    today = datetime.now().strftime("%Y-%m-%d")
    title = html.escape(config.get("title", "My Blog FrontPage"))
    desc = config.get("description", "")
    desc_block = f'    <p class="description">{html.escape(desc)}</p>\n' if desc else ""
    items = "".join(render_entry(e) for e in entries)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div class="container">
    <nav>
      <a href="index.html" class="active">Blogs</a>
      <a href="papers.html">Papers</a>
    </nav>
    <h1>{title}</h1>
    <p class="generated">Generated on {today}.</p>
{desc_block}    <section>
{items}    </section>
  </div>
</body>
</html>"""


def main():
    socket.setdefaulttimeout(10)
    config = load_config()
    max_age = config.get("max_age_days", 60)
    print(f"Fetching feeds (max age: {max_age} days)...")
    entries = fetch_all(config["feeds"], max_age)
    page = render_page(config, entries)
    Path("index.html").write_text(page, encoding="utf-8")
    print(f"Done — wrote index.html with {len(entries)} entries.")


if __name__ == "__main__":
    main()
