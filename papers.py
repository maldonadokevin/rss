# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

import html
import json
import socket
import urllib.request
from datetime import datetime
from pathlib import Path

API_URL = "https://huggingface.co/api/papers"
MAX_SUMMARY_LEN = 400


def truncate(text, max_len=MAX_SUMMARY_LEN):
    text = " ".join(text.split())
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0] + "…"


def fetch_papers():
    print(f"  fetching {API_URL}")
    with urllib.request.urlopen(API_URL) as r:
        return json.loads(r.read())


def format_authors(authors):
    names = [a["name"] for a in authors[:4]]
    if len(authors) > 4:
        names.append("et al.")
    return ", ".join(names)


def render_entry(paper):
    upvotes = paper.get("upvotes", 0)
    title = html.escape(paper.get("title", "Untitled"))
    summary = html.escape(truncate(paper.get("summary", "")))
    arxiv_id = paper.get("id", "")
    hf_link = html.escape(f"https://huggingface.co/papers/{arxiv_id}")
    arxiv_link = html.escape(f"https://arxiv.org/abs/{arxiv_id}")
    authors = html.escape(format_authors(paper.get("authors", [])))
    summary_block = f'            <p class="summary">{summary}</p>\n' if summary else ""
    return (
        f'      <div class="entry">\n'
        f'        <div class="date">↑ {upvotes}</div>\n'
        f'        <div class="content">\n'
        f'          <details>\n'
        f'            <summary>{title}<span class="feed-name">{authors}</span></summary>\n'
        f"{summary_block}"
        f'            <p class="link-line"><a href="{hf_link}">huggingface</a> &middot; <a href="{arxiv_link}">arxiv</a></p>\n'
        f'          </details>\n'
        f"        </div>\n"
        f"      </div>\n"
    )


def render_page(papers):
    today = datetime.now().strftime("%Y-%m-%d")
    items = "".join(render_entry(p) for p in papers)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Kevin&#x27;s Papers FrontPage</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div class="container">
    <nav>
      <a href="index.html">Blogs</a>
      <a href="papers.html" class="active">Papers</a>
    </nav>
    <h1>Kevin&#x27;s Papers FrontPage</h1>
    <p class="generated">Generated on {today}.</p>
    <p class="description">Today&#x27;s most upvoted ML papers on Hugging Face, sorted by community votes.</p>
    <section>
{items}    </section>
  </div>
</body>
</html>"""


def main():
    socket.setdefaulttimeout(10)
    print("Fetching HuggingFace Papers...")
    papers = fetch_papers()
    papers.sort(key=lambda p: p.get("upvotes", 0), reverse=True)
    page = render_page(papers)
    Path("papers.html").write_text(page, encoding="utf-8")
    print(f"Done — wrote papers.html with {len(papers)} papers.")


if __name__ == "__main__":
    main()
