"""各ページの meta description を本文から作る。

front matter に description が無いページは、全ページ共通の site_description
になってしまい、検索結果の説明文が同じになる。そこで本文の最初の段落から
説明文を作る (front matter に書いたものが優先)。
"""

import html
import re

MAX_LEN = 110
TAG = re.compile(r"<[^>]+>")
SPACE = re.compile(r"\s+")
PARAGRAPH = re.compile(r"<p[\s>].*?</p>", re.S)


def _text(fragment: str) -> str:
    return SPACE.sub(" ", html.unescape(TAG.sub("", fragment))).strip()


def on_page_content(content, page, config, files):
    if page.meta.get("description"):
        return content
    body = ""
    for p in PARAGRAPH.findall(content):
        text = _text(p)
        if text:
            body += text + " "
        if len(body) >= MAX_LEN:
            break
    body = body.strip()
    if len(body) > MAX_LEN:
        body = body[: MAX_LEN - 1] + "…"
    title = page.title or ""
    if page.is_homepage or not title:
        prefix = "Magic Survival (マジックサバイバル) の非公式攻略wiki。"
    else:
        prefix = f"{title} | Magic Survival (マジサバ) 攻略wiki。"
    # Material のテンプレートは description をエスケープせずに出すので、ここでエスケープする
    page.meta["description"] = html.escape(prefix + body, quote=True)
    return content
