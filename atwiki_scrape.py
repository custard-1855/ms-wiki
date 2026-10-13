#!/usr/bin/env python3
"""
マジックサバイバル攻略wiki (atwiki) の全ページの生 HTML と本文中の画像・添付ファイルを取得して保存するスクリプト。
Markdown への変換は convert.py が out/ だけを読んで行う (@wiki へは再アクセスしない)。

使い方:
    uv run python atwiki_scrape.py

出力 (out/ は git 管理外):
    out/html/<id>.html   … 各ページの生 HTML
    out/img/<path>       … 本文中の画像と添付ファイル (img.atwiki.jp/magicsurvival/ 以下のパスをそのまま使う)
    out/pages.json       … {id: タイトル} (一覧と本文リンクから見つけた全ページ)
    out/missing.json     … リンクはあるが存在しないページの id
    途中で止めても、再実行すれば取得済みのファイルは飛ばします。
"""
import json
import re
import sys
import time
from collections import deque
from pathlib import Path

import requests
from bs4 import BeautifulSoup

WIKI = "https://w.atwiki.jp/magicsurvival"
IMG_PREFIX = "//img.atwiki.jp/magicsurvival/"
OUT = Path("out")
DELAY = 2.0  # サーバー負荷を避けるため、1リクエストごとに待つ秒数
HEADERS = {"User-Agent": "Mozilla/5.0 (personal archive script; low rate)"}
PAGE_RE = re.compile(r"//w\.atwiki\.jp/magicsurvival/pages/(\d+)\.html")

session = requests.Session()
session.headers.update(HEADERS)


def get(url: str) -> requests.Response | None:
    """取得して返す。404 は None。"""
    for attempt in range(3):
        time.sleep(DELAY)
        try:
            r = session.get(url, timeout=30)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            print(f"  ! {url}: {e} (retry {attempt + 1}/3)", file=sys.stderr)
            time.sleep(DELAY * 3)
    raise RuntimeError(f"failed: {url}")


def page_links(soup: BeautifulSoup) -> dict[int, str]:
    """ページ内のリンクから {id: タイトル} を集める。"""
    found: dict[int, str] = {}
    for a in soup.select('a[href*="/magicsurvival/pages/"]'):
        m = PAGE_RE.search(a["href"])
        if not m:
            continue
        title = (a.get("title") or a.get_text()).strip()
        title = re.sub(r"\s*\(\d+[a-z]\)$", "", title)  # 末尾の "(91d)" などを除去
        found.setdefault(int(m.group(1)), title)
    return found


def collect_list() -> dict[int, str]:
    """全ページ一覧 (list?pp=1..N) からページ番号とタイトルを集める。"""
    pages: dict[int, str] = {}
    pp = 1
    while True:
        soup = BeautifulSoup(get(f"{WIKI}/list?pp={pp}").content, "html.parser")
        before = len(pages)
        for pid, title in page_links(soup).items():
            pages.setdefault(pid, title)
        print(f"list pp={pp}: +{len(pages) - before} (計 {len(pages)})")
        # ページ送りのリンクは "?pp=2" のような相対 URL
        if not soup.select_one(f'.atwiki_pagination a[href="?pp={pp + 1}"]'):
            break
        pp += 1
    return pages


def save_attachments(soup: BeautifulSoup) -> None:
    """本文中の画像と、リンクされた添付ファイル (PDF など) を保存する。"""
    body = soup.select_one("#wikibody")
    if body is None:
        return
    urls = [img.get("src", "") for img in body.select("img")]
    urls += [a["href"].removeprefix("https:") for a in body.select("a[href]")]
    for src in urls:
        if not src.startswith(IMG_PREFIX):
            continue
        dest = OUT / "img" / src.removeprefix(IMG_PREFIX)
        if dest.exists():
            continue
        r = get("https:" + src)
        if r is None:
            print(f"  ! image 404: {src}", file=sys.stderr)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(r.content)


def main():
    (OUT / "html").mkdir(parents=True, exist_ok=True)
    index_path = OUT / "pages.json"
    pages: dict[int, str] = {}
    if index_path.exists():
        pages = {int(k): v for k, v in json.loads(index_path.read_text()).items()}
    missing: set[int] = set()

    for pid, title in collect_list().items():
        pages.setdefault(pid, title)

    # 一覧のページから始めて、本文の内部リンクを辿って一覧に無いページも補完する
    queue = deque(sorted(pages))
    seen = set(queue)
    while queue:
        pid = queue.popleft()
        path = OUT / "html" / f"{pid}.html"
        if path.exists():
            html = path.read_bytes()
        else:
            r = get(f"{WIKI}/pages/{pid}.html")
            if r is None:
                print(f"  missing {pid} {pages.get(pid, '')}")
                missing.add(pid)
                continue
            html = r.content
            path.write_bytes(html)
            print(f"[{len(seen) - len(queue)}/{len(seen)}] {pid} {pages.get(pid, '')}")
        soup = BeautifulSoup(html, "html.parser")
        save_attachments(soup)
        body = soup.select_one("#wikibody")
        for linked, title in page_links(body).items() if body else []:
            pages.setdefault(linked, title)
            if linked not in seen:
                seen.add(linked)
                queue.append(linked)

    index_path.write_text(json.dumps(
        {str(k): v for k, v in sorted(pages.items())}, ensure_ascii=False, indent=1))
    (OUT / "missing.json").write_text(json.dumps(sorted(missing)))
    print(f"全 {len(pages)} ページ / 取得 {len(pages) - len(missing)} / 存在しない {len(missing)}")


if __name__ == "__main__":
    main()
