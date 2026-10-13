"""convert.py: atwiki の HTML → Markdown 変換のテスト。

実際の atwiki の HTML から必要な部分だけを抜き出した断片を入力にしている。
"""
from pathlib import Path

import pytest

from convert import Page, convert_html

WIKI = "//w.atwiki.jp/magicsurvival/pages"

PAGES = {
    15: Page(15, "魔法(紹介&tier)", "database", "database/magic.md"),
    16: Page(16, "魔力弾", "magic", "magic/magic-bolt.md"),
    151: Page(151, "test", "除外", ""),
}


def page_html(body: str, footnotes: str = "") -> str:
    """atwiki のページ全体の形に包む。注釈は本文 (#wikibody) の外に出る。"""
    return f"""<html><head><title>魔法(紹介&amp;tier) - マジックサバイバル攻略wiki | マジサバwiki</title></head>
<body><div class="atwiki-contents" id="wikibody">
<!--@@@@@-->{body}
</div>
<div class="atwiki-footnote"><div id="note"><hr class="note_hr"/>{footnotes}</div></div>
</body></html>"""


def convert(body: str, footnotes: str = "", page: int = 15, images: dict | None = None) -> str:
    return convert_html(page_html(body, footnotes), PAGES[page], PAGES, {} if images is None else images)


# --- ページ全体 -----------------------------------------------------------------


def test_h1_is_the_japanese_title():
    assert convert("<p>本文</p>").startswith("# 魔法(紹介&tier)\n\n本文\n")


# --- 除去する定型部分 -----------------------------------------------------------


def test_removes_moving_notice():
    md = convert("""<div>
<span style="font-weight: bold;"><!--@@@@@-->wiki引っ越しのご案内</span>
<br/>
@wiki記法で書くのが手間なので、discordに完全に移行する予定です。
<br/>
攻略情報など要望があればこちらへどうぞ→<a href="https://discord.gg/scXvWqmCZG" rel="nofollow">https://discord.gg/scXvWqmCZG</a>
</div>
<br/>
<div>本文</div>""")
    assert "引っ越し" not in md
    assert "discord" not in md
    assert "本文" in md


def test_removes_table_of_contents():
    md = convert("""<div><big>目次</big></div>
<div class="plugin_contents"><!--@@@@@--><ul><li><a href="#id_d7425aa6">魔法の種類について</a></li></ul></div>
<h2 id="id_d7425aa6">魔法の種類について</h2>""")
    assert "目次" not in md
    assert "#id_" not in md
    assert md.count("魔法の種類について") == 1
    assert "## 魔法の種類について" in md


def test_removes_comment_section_with_its_heading():
    md = convert("""<h2 id="id_1">コメント欄</h2>
<div class="plugin_pcomment"><form action="//w.atwiki.jp/magicsurvival/?plugin=pcomment">
<label for="comment_name">名前:</label><input type="submit" value="書き込む"/></form></div>
<ul><li>過去のコメント -- 名無しさん (2024-04-22 15:12:45)</li></ul>
<h2 id="id_2">次の節</h2>""")
    assert "コメント" not in md
    assert "名無しさん" not in md
    assert "## 次の節" in md


def test_removes_past_comments_before_comment_form():
    md = convert("""<p>本文</p>
<ul><li> 爆竹と分裂の違い  -- 名無しさん  (2024-04-22 15:12:45)</li></ul>
<div class="plugin_comment"><form><input name="name"/><input type="submit" value="投稿"/></form></div>""")
    assert "爆竹" not in md
    assert "投稿" not in md


def test_keeps_ordinary_list_before_comment_form():
    md = convert("""<ul><li>普通の箇条書き</li></ul>
<div class="plugin_comment"><form><input type="submit" value="投稿"/></form></div>""")
    assert "- 普通の箇条書き" in md


def test_removes_tags_like_button_and_search_link():
    md = convert("""<p>本文</p>
<div class="atwiki-page-tags"><p class="atwiki-tag-notation">タグ：</p>
<a class="atwiki-tag-frame" href="/magicsurvival/tag/x">データベース</a></div>
<div id="atwiki-liked-counter"><button class="liked-btn">いいね！</button></div>
<div class="atwiki-page-keyword">
<a href="//w.atwiki.jp/magicsurvival/search?keyword=x" rel="nofollow">「魔法(紹介&amp;tier)」をウィキ内検索</a>
</div>""")
    assert md == "# 魔法(紹介&tier)\n\n本文\n"


# --- リンク ---------------------------------------------------------------------


def test_internal_link_becomes_relative_path_without_title():
    md = convert(f'<p><a href="{WIKI}/16.html" title="魔力弾 (654d)">魔力弾</a></p>')
    assert "[魔力弾](../magic/magic-bolt.md)" in md
    assert "654d" not in md


def test_link_to_excluded_or_unknown_page_keeps_only_text():
    md = convert(f'<p><a href="{WIKI}/151.html">test</a> と <a href="{WIKI}/999.html">無いページ</a></p>')
    assert "test と 無いページ" in md
    assert "](" not in md


def test_link_by_title_is_unwrapped():
    # ?page=タイトル の形は @wiki 上で存在しないページへのリンク
    md = convert('<p><a href="//w.atwiki.jp/magicsurvival/?page=%E3%82%A2">アーティファクト</a></p>')
    assert md.endswith("\nアーティファクト\n")


def test_link_fragment_is_dropped():
    md = convert(f'<p><a href="{WIKI}/16.html#id_61159139">魔力弾の派生</a></p>')
    assert "[魔力弾の派生](../magic/magic-bolt.md)" in md


def test_bare_url_in_text_becomes_link_with_page_title():
    md = convert("<p>詳しくはここへhttps://w.atwiki.jp/magicsurvival/pages/16.html#id_351e3e41)を参照</p>")
    assert "詳しくはここへ[魔力弾](../magic/magic-bolt.md))を参照" in md


def test_link_whose_text_is_the_url_uses_page_title():
    url = "https://w.atwiki.jp/magicsurvival/pages/16.html#id_61159139"
    md = convert(f'<p>ここ→<a href="{url}">{url}</a></p>')
    assert "ここ→[魔力弾](../magic/magic-bolt.md)" in md


def test_protocol_relative_external_link_gets_https():
    md = convert('<p><a href="//example.com/x">外部</a></p>')
    assert "[外部](https://example.com/x)" in md


# --- 表 -------------------------------------------------------------------------


def table_lines(md: str) -> list[str]:
    return [line for line in md.splitlines() if line.startswith("|")]


def test_first_row_becomes_header_without_empty_header_row():
    md = convert("""<table>
<tr><td style="background-color:#666666;"><span style="color: #ffffff;">魔法名</span></td>
<td style="background-color:#666666;"><span style="color: #ffffff;">tier</span></td></tr>
<tr><td>魔力弾</td><td>B</td></tr>
</table>""")
    assert table_lines(md) == ["| 魔法名 | tier |", "| --- | --- |", "| 魔力弾 | B |"]


def test_rowspan_is_copied_to_each_row():
    md = convert("""<table>
<tr><td>魔法名</td><td>特性</td><td>tier</td><td>対応AF</td></tr>
<tr><td rowspan="3">魔力弾</td><td>魔力の矢</td><td>B</td><td rowspan="3">手裏剣</td></tr>
<tr><td>花火</td><td>C</td></tr>
<tr><td>分裂</td><td>D</td></tr>
<tr><td>火炎球</td><td>大爆発</td><td>D</td><td>たいまつ</td></tr>
</table>""")
    assert table_lines(md)[2:] == [
        "| 魔力弾 | 魔力の矢 | B | 手裏剣 |",
        "| 魔力弾 | 花火 | C | 手裏剣 |",
        "| 魔力弾 | 分裂 | D | 手裏剣 |",
        "| 火炎球 | 大爆発 | D | たいまつ |",
    ]


def test_colspan_leaves_following_cells_empty():
    md = convert("""<table>
<tr><td colspan="4">lv毎のステータス</td></tr>
<tr><td>1</td><td colspan="3">基本発射体を強化する。</td></tr>
<tr><td>2</td><td>数+1</td><td>4</td><td>特性1習得</td></tr>
</table>""")
    assert table_lines(md) == [
        "| lv毎のステータス |  |  |  |",
        "| --- | --- | --- | --- |",
        "| 1 | 基本発射体を強化する。 |  |  |",
        "| 2 | 数+1 | 4 | 特性1習得 |",
    ]


def test_rowspan_and_colspan_together():
    md = convert("""<table>
<tr><td>a</td><td>b</td><td>c</td></tr>
<tr><td rowspan="2" colspan="2">結合</td><td>1</td></tr>
<tr><td>2</td></tr>
</table>""")
    assert table_lines(md)[2:] == ["| 結合 |  | 1 |", "| 結合 |  | 2 |"]


def test_line_breaks_lists_and_pipes_inside_cells():
    md = convert("""<table>
<tr><td>名前</td><td>効果</td></tr>
<tr><td>花火</td><td>魔力弾が3発に分散する。<br/>ダメージ+50%<ul><li>A|B</li><li>C</li></ul></td></tr>
</table>""")
    assert table_lines(md)[2] == "| 花火 | 魔力弾が3発に分散する。<br>ダメージ+50%・A\\|B<br>・C |"


# --- 文字の装飾・脚注・埋め込み ---------------------------------------------------


def test_colored_and_bold_spans():
    md = convert("""<p><span style="color: #0068b7;"><!--@@@@@--><span style="font-weight: bold;"><!--@@@@@-->A</span></span>
(<span style="color: #ffffff;">白は消える</span>)</p>""")
    assert '<span style="color: #0068b7">**A**</span>' in md
    assert "(白は消える)" in md


def test_footnotes_become_markdown_footnotes():
    md = convert(
        """<p>融合し<span class="link_atwiki_footnote"><span class="hidden">(</span>
<a href="#footnote_foot_1" id="footnote_body_1" title="パッシブ魔法等">*1</a><span class="hidden">)</span></span>、強力な魔法を習得</p>""",
        footnotes=f'<p><a href="#footnote_body_1" id="footnote_foot_1">*1</a> パッシブ魔法等は<a href="{WIKI}/16.html">魔力弾</a>参照</p>',
    )
    assert "融合し[^1]、強力な魔法を習得" in md
    assert md.endswith("\n\n[^1]: パッシブ魔法等は[魔力弾](../magic/magic-bolt.md)参照\n")


def test_youtube_iframe_is_kept_without_query():
    md = convert("""<div class="plugin_video plugin_youtube"><iframe allowfullscreen="" frameborder="0" height="360"
src="https://www.youtube.com/embed/2u78nk3HDYw?controls=1&amp;rel=0" width="640"></iframe></div>""")
    assert '<iframe class="video" src="https://www.youtube.com/embed/2u78nk3HDYw" allowfullscreen loading="lazy"></iframe>' in md


def video(src: str) -> str:
    return f'<iframe class="video" src="{src}" allowfullscreen loading="lazy"></iframe>'


def test_youtube_link_gets_player_after_its_block():
    md = convert("""<div>動画はこちら→<a href="https://youtu.be/uwgu8EKbEYQ?feature=shared" rel="nofollow">https://youtu.be/uwgu8EKbEYQ?feature=shared</a>
<br/>次の行</div><div>次のブロック</div>""")
    assert md.endswith(
        "動画はこちら→<https://youtu.be/uwgu8EKbEYQ?feature=shared>\n\n次の行\n\n"
        f"{video('https://www.youtube.com/embed/uwgu8EKbEYQ')}\n\n次のブロック\n"
    )


def test_youtube_links_in_one_block_keep_their_order():
    md = convert("""<ul><li><a href="https://youtube.com/shorts/lZF2hS89kK8?si=x">ショート</a></li>
<li><a href="https://www.youtube.com/watch?v=0007NV4duu4&amp;t=10">通常</a></li></ul>""")
    shorts = video("https://www.youtube.com/embed/lZF2hS89kK8")
    watch = video("https://www.youtube.com/embed/0007NV4duu4")
    assert md.index("[通常]") < md.index(shorts) < md.index(watch)


def test_youtube_playlist_link_gets_playlist_player():
    md = convert('<div><a href="https://youtube.com/playlist?list=PL7Nm7vv8wC9mSUN_1PhO3AauzegWQ5RgN&amp;si=x">再生リスト</a></div>')
    assert video("https://www.youtube.com/embed/videoseries?list=PL7Nm7vv8wC9mSUN_1PhO3AauzegWQ5RgN") in md


def test_youtube_channel_link_gets_no_player():
    md = convert('<div><a href="https://www.youtube.com/@leme">チャンネル</a></div>')
    assert "<iframe" not in md


# --- 画像 -----------------------------------------------------------------------


def test_image_goes_to_per_page_directory():
    images: dict = {}
    md = convert(
        """<picture><source srcset="x.webp"/><img class="atwiki_plugin_image" width="30" height="35"
src="//img.atwiki.jp/magicsurvival/attach/16/1/Magic%20Bolt.n.png"></picture>""",
        page=16,
        images=images,
    )
    assert '![Magic Bolt.n](../assets/images/magic/magic-bolt/magic-bolt.n.png){ width="30" height="35" }' in md
    assert images == {"magic/magic-bolt/magic-bolt.n.png": Path("out/img/attach/16/1/Magic%20Bolt.n.png")}


def test_image_without_size_and_markdown_chars_in_alt():
    md = convert('<img src="//img.atwiki.jp/magicsurvival/attach/15/1/a.png" alt="[tier]_表|*">')
    assert r"![\[tier\]\_表\|\*](../assets/images/database/magic/a.png)" in md
    assert "{" not in md


def test_two_different_images_with_same_name_on_one_page_is_an_error():
    with pytest.raises(RuntimeError, match="重複"):
        convert("""<img src="//img.atwiki.jp/magicsurvival/attach/15/1/1.png">
<img src="//img.atwiki.jp/magicsurvival/attach/15/2/1.png">""")


def test_linked_attachment_goes_to_per_page_directory():
    images: dict = {}
    md = convert(
        '<p><a href="//img.atwiki.jp/magicsurvival/attach/16/3480/%E6%AD%BB%E3%81%AE%E9%90%98.pdf">問題pdf</a></p>',
        page=16,
        images=images,
    )
    assert "[問題pdf](../assets/images/magic/magic-bolt/死の鐘.pdf)" in md
    assert images == {"magic/magic-bolt/死の鐘.pdf": Path("out/img/attach/16/3480/%E6%AD%BB%E3%81%AE%E9%90%98.pdf")}
