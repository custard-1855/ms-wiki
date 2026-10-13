#!/usr/bin/env python3
"""
atwiki_scrape.py が保存した out/ の生 HTML を docs/ の Markdown に一度だけ変換するスクリプト。

使い方:
    uv run python convert.py

入力:
    out/html/<id>.html, out/img/   … atwiki_scrape.py の出力
    rename_map.csv                  … id, 元タイトル, カテゴリ, 新パス (新パスが空のページは出力しない)
出力:
    docs/<新パス>                   … 各ページの Markdown
    docs/assets/images/<新パスから .md を除いたもの>/<ファイル名> … 本文中の画像
"""
import csv
import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

from bs4 import BeautifulSoup, Comment, NavigableString, Tag
from markdownify import MarkdownConverter

OUT = Path("out")
DOCS = Path("docs")
IMAGES = DOCS / "assets" / "images"
IMG_PREFIX = "//img.atwiki.jp/magicsurvival/"
PAGE_RE = re.compile(r"^(?:https?:)?//w\.atwiki\.jp/magicsurvival/pages/(\d+)\.html")
COMMENT_RE = re.compile(r"--\s*.*\(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\)$")
BARE_URL_RE = re.compile(r"https?://w\.atwiki\.jp/magicsurvival/pages/\d+\.html(?:#[\w-]+)?")
TITLE_LINK_RE = re.compile(r"^(?:https?:)?//w\.atwiki\.jp/magicsurvival/\?page=")


@dataclass
class Page:
    id: int
    title: str
    category: str
    path: str  # docs/ からの相対パス。空なら出力しない


def load_map() -> dict[int, Page]:
    with open("rename_map.csv", encoding="utf-8") as f:
        return {
            int(r["id"]): Page(int(r["id"]), r["title"], r["category"], r["path"])
            for r in csv.DictReader(f)
        }


def page_title(soup: BeautifulSoup) -> str:
    title = soup.title.get_text() if soup.title else ""
    return title.split(" - マジックサバイバル攻略wiki")[0].strip()


def top_level(el: Tag, body: Tag) -> Tag:
    """body 直下にある el の祖先 (el 自身を含む) を返す。"""
    while el.parent is not body:
        el = el.parent
    return el


def remove_with_trailing_br(el: Tag) -> None:
    """el と、その直後に続く <br> (と空白) を削除する。"""
    nxt = el.next_sibling
    while nxt is not None and (
        (isinstance(nxt, NavigableString) and not nxt.strip())
        or (isinstance(nxt, Tag) and nxt.name == "br")
    ):
        following = nxt.next_sibling
        nxt.extract()
        nxt = following
    el.decompose()


def remove_section(heading: Tag) -> None:
    """見出しと、次の同じかより上の階層の見出しまでの内容を削除する。"""
    level = int(heading.name[1])
    nxt = heading.next_sibling
    while nxt is not None and not (
        isinstance(nxt, Tag) and re.fullmatch(r"h[1-6]", nxt.name) and int(nxt.name[1]) <= level
    ):
        following = nxt.next_sibling
        nxt.extract()
        nxt = following
    heading.decompose()


def remove_boilerplate(body: Tag) -> None:
    """引っ越し案内・目次・コメント欄・ウィキ内検索リンクなど、移行先では不要な部分を削除する。"""
    for c in body.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()
    # #comment プラグインの過去のコメントは、フォームの直前の ul に「本文 -- 名前 (日時)」の形で並ぶ
    for form in body.select(".plugin_comment"):
        prev = form.find_previous_sibling()
        if prev is not None and prev.name == "ul" and all(
            COMMENT_RE.search(li.get_text(" ", strip=True)) for li in prev.find_all("li", recursive=False)
        ):
            prev.decompose()
    for el in body.select(
        "script, style, noscript, ins, form, .atwiki-ads, .atwiki-page-keyword, .atwiki-page-tags,"
        " #atwiki-liked-counter, .plugin_pcomment, .plugin_comment"
    ):
        el.decompose()
    top: list[Tag] = []
    # 「wiki引っ越しのご案内」の定型文 (body 直下の div 1 つ)
    for s in body.find_all(string=re.compile("wiki引っ越しのご案内")):
        top.append(top_level(s.parent, body))
    # 目次: 「目次」とだけ書かれた要素と、#contents プラグインの出力
    for el in body.select(".plugin_contents"):
        top.append(top_level(el, body))
    for s in body.find_all(string=re.compile(r"^\s*目次\s*$")):
        if s.parent is not body:
            top.append(top_level(s.parent, body))
    for el in dict.fromkeys(top):  # 重複を除き、順序は保つ
        remove_with_trailing_br(el)
    # コメント欄の見出しと、その下に残った過去のコメント
    for h in body.find_all(re.compile(r"^h[1-6]$"), string=re.compile(r"^\s*コメント(欄)?\s*$")):
        remove_section(h)
    # 目次用のアンカー (href の無い <a name/id>)
    for a in body.select("a[name], a[id]"):
        if not a.get("href"):
            a.unwrap()
    for a in body.find_all("a", string=re.compile("をウィキ内検索")):
        a.decompose()


def convert_footnotes(soup: BeautifulSoup, body: Tag) -> list[tuple[str, Tag]]:
    """本文中の atwiki の注釈を Markdown の脚注 ([^N]) にし、(番号, 注釈の本文) を返す。"""
    for span in body.select(".link_atwiki_footnote"):
        a = span.select_one("a[id^=footnote_body_]")
        span.replace_with(f"[^{a['id'].removeprefix('footnote_body_')}]")
    defs = []
    for p in soup.select(".atwiki-footnote #note p"):
        a = p.select_one("a[id^=footnote_foot_]")
        if a is None:
            continue
        n = a["id"].removeprefix("footnote_foot_")
        a.decompose()
        defs.append((n, p))
    return defs


def rel_link(target: str, current: str) -> str:
    return os.path.relpath(target, os.path.dirname(current) or ".").replace(os.sep, "/")


def link_bare_urls(body: Tag) -> None:
    """本文に文字として書かれた wiki 内の URL を <a> にする (rewrite_links で新しいパスに直すため)。"""
    for s in body.find_all(string=BARE_URL_RE):
        if s.find_parent("a") is not None:
            continue
        parts = []
        last = 0
        for m in BARE_URL_RE.finditer(s):
            parts.append(s[last:m.start()])
            a = Tag(name="a", attrs={"href": m.group(0)})
            a.string = m.group(0)
            parts.append(a)
            last = m.end()
        parts.append(s[last:])
        s.replace_with(*[p for p in parts if p != ""])


def rewrite_links(body: Tag, current: Page, pages: dict[int, Page]) -> None:
    for a in body.select("a[href]"):
        href = a["href"]
        if "title" in a.attrs:
            del a["title"]
        m = PAGE_RE.match(href)
        if m:
            target = pages.get(int(m.group(1)))
            if target is None or not target.path:
                a.unwrap()  # 除外・存在しないページへのリンクはテキストだけ残す
                continue
            a["href"] = rel_link(target.path, current.path)
            if BARE_URL_RE.fullmatch(a.get_text(strip=True)):
                a.string = target.title  # URL がそのままリンク文字列になっているものはタイトルにする
        elif TITLE_LINK_RE.match(href) or href.startswith("#"):
            a.unwrap()  # ?page=タイトル はすべて存在しないページ、#id は見出し id を引き継がない
        elif href.startswith("//"):
            a["href"] = "https:" + href


def local_asset(url: str, current: Page, used: dict[str, Path]) -> tuple[str, Path]:
    """atwiki に添付されたファイルの URL を、ページごとのディレクトリに置いたときの相対パスにする。

    例: magic/magic-bolt.md の "Magic%20Bolt.n.png" → assets/images/magic/magic-bolt/magic-bolt.n.png
    使ったファイルは used に {docs/assets/images/ からのパス: out/ のファイル} として足す。
    """
    local = OUT / "img" / url.removeprefix("https:").removeprefix(IMG_PREFIX)
    name = re.sub(r"\s+", "-", unquote(local.name).strip()).lower()
    rel = f"{current.path.removesuffix('.md')}/{name}"
    if used.setdefault(rel, local) != local:
        raise RuntimeError(f"画像のファイル名が重複: {rel}")
    return rel_link(f"assets/images/{rel}", current.path), local


def rewrite_attachments(body: Tag, current: Page, used: dict[str, Path]) -> None:
    """本文中の画像と、リンクされた添付ファイル (PDF など) を docs/assets/images/ を指すようにする。"""
    for source in body.select("picture source"):
        source.decompose()
    for img in body.select("img"):
        src = img.get("src", "")
        if not src.startswith(IMG_PREFIX):
            print(f"  ! {current.id}: 外部画像 {src}", file=sys.stderr)
            continue
        path, local = local_asset(src, current, used)
        alt = img.get("alt") or img.get("title") or Path(unquote(local.name)).stem
        attrs = {"src": path, "alt": alt}
        for k in ("width", "height"):
            if img.get(k):
                attrs[k] = img[k]
        img.attrs = attrs
    for a in body.select("a[href]"):
        if a["href"].removeprefix("https:").startswith(IMG_PREFIX):
            a["href"], _ = local_asset(a["href"], current, used)


def expand_spans(table: Tag) -> None:
    """結合セルを展開する。縦 (rowspan) は同じ内容を複製し、横 (colspan) は空のセルで埋める。"""
    rows = table.find_all("tr")
    pending: dict[int, tuple[Tag, int]] = {}  # 列番号 -> (元セル, 残り行数)
    for tr in rows:
        cells = tr.find_all(["td", "th"], recursive=False)
        out: list[Tag] = []
        col = 0
        it = iter(cells)
        cell = next(it, None)
        while cell is not None or any(c >= col for c in pending):
            if col in pending:
                src, left = pending[col]
                clone = BeautifulSoup(str(src), "html.parser").find(src.name)
                del clone["rowspan"]
                out.append(clone)
                if left > 1:
                    pending[col] = (src, left - 1)
                else:
                    del pending[col]
                col += 1
                continue
            if cell is None:
                break
            colspan = int(cell.get("colspan", 1) or 1)
            rowspan = int(cell.get("rowspan", 1) or 1)
            for attr in ("colspan", "rowspan"):
                if attr in cell.attrs:
                    del cell[attr]
            for i in range(colspan):
                # 横の結合は先頭のセルにだけ内容を残す (行の見出しが全列に並ぶのを避ける)
                c = cell if i == 0 else Tag(name=cell.name)
                out.append(c)
                if rowspan > 1:
                    pending[col] = (c, rowspan - 1)
                col += 1
            cell = next(it, None)
        tr.clear()
        for c in out:
            tr.append(c)


class Converter(MarkdownConverter):
    def convert_br(self, el, text, parent_tags):
        if "td" in parent_tags or "th" in parent_tags:
            return "<br>"
        return super().convert_br(el, text, parent_tags)

    def convert_td(self, el, text, parent_tags):
        text = re.sub(r"(?<!\\)\|", r"\\|", text.strip())
        text = re.sub(r"\s*\n\s*", " ", text)
        text = re.sub(r"^(<br>\s*)+|(\s*<br>)+$", "", text)
        return " " + text + " |"

    convert_th = convert_td

    def convert_li(self, el, text, parent_tags):
        if "td" in parent_tags or "th" in parent_tags:
            return "・" + text.strip() + "<br>"
        return super().convert_li(el, text, parent_tags)

    def convert_ul(self, el, text, parent_tags):
        if "td" in parent_tags or "th" in parent_tags:
            return text
        return super().convert_ul(el, text, parent_tags)

    convert_ol = convert_ul

    def convert_span(self, el, text, parent_tags):
        style = el.get("style", "")
        if not text.strip():
            return text
        m = re.search(r"(?<![-\w])color:\s*([^;]+)", style)
        # 白文字は元の表ヘッダの濃い背景用。背景色は引き継がないので色も落とす
        if m and not re.fullmatch(r"#f{3}(f{3})?|white", m.group(1).strip(), re.I):
            text = f'<span style="color: {m.group(1).strip()}">{text}</span>'
        if re.search(r"font-weight:\s*bold", style):
            text = self.convert_b(el, text, parent_tags)
        return text

    def convert_iframe(self, el, text, parent_tags):
        src = el.get("src", "")
        if "youtube.com/embed/" in src:
            src = src.split("?")[0]
            return f'\n\n<iframe class="video" src="{src}" allowfullscreen loading="lazy"></iframe>\n\n'
        print(f"  ! iframe {src}", file=sys.stderr)
        return ""

    def convert_img(self, el, text, parent_tags):
        # 生の <img> だと MkDocs が相対パスを書き換えず、ページの URL (guide/faq/) からずれて表示されない。
        # Markdown 記法にして、width/height は attr_list で残す。
        alt = re.sub(r"([\\\[\]_*`|])", r"\\\1", el.get("alt", ""))
        size = " ".join(f'{k}="{el[k]}"' for k in ("width", "height") if el.get(k))
        return f"![{alt}]({el['src']})" + (f"{{ {size} }}" if size else "")


def to_markdown(body: Tag | BeautifulSoup) -> str:
    md = Converter(heading_style="ATX", bullets="-", table_infer_header=True).convert_soup(body)
    md = re.sub(r"[ \t]+\n", "\n", md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


def convert_html(html: str | bytes, page: Page, pages: dict[int, Page], used_images: dict[str, Path]) -> str:
    """1 ページ分の atwiki の HTML を Markdown にする。使った画像を used_images に足す。"""
    soup = BeautifulSoup(html, "html.parser")
    body = soup.select_one("#wikibody")
    remove_boilerplate(body)
    notes = convert_footnotes(soup, body)
    for el in [body] + [p for _, p in notes]:
        link_bare_urls(el)
        rewrite_attachments(el, page, used_images)
        rewrite_links(el, page, pages)
    for table in body.select("table"):
        expand_spans(table)
    md = f"# {page.title}\n\n{to_markdown(body)}\n"
    if notes:
        md += "\n" + "".join(f"[^{n}]: {to_markdown(p)}\n" for n, p in notes)
    return md


def main():
    pages = load_map()
    used_images: dict[str, Path] = {}
    for pid, page in sorted(pages.items()):
        if not page.path:
            continue
        dest = DOCS / page.path
        dest.parent.mkdir(parents=True, exist_ok=True)
        html = (OUT / "html" / f"{pid}.html").read_bytes()
        dest.write_text(convert_html(html, page, pages, used_images), encoding="utf-8")
        print(f"{pid} → {page.path}")
    for rel, src in used_images.items():
        (IMAGES / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, IMAGES / rel)
    print(f"{len([p for p in pages.values() if p.path])} ページ / 画像 {len(used_images)}")


if __name__ == "__main__":
    main()
