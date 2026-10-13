#!/usr/bin/env python3
"""
out/html の全ページから rename_map.csv の下書きを作るスクリプト (一度きり)。

使い方:
    uv run python draft_rename_map.py

カテゴリはメニューの区分と、どの一覧ページからリンクされているかで決める。
英語スラッグは SLUGS に手で書く。ゲーム英語版の名称が分からず意訳したものは note に「要確認」を付ける。
SLUGS に無いページは仮に p<id> とし、note に「要命名」を付ける。
"""
import csv
import re
from collections import defaultdict
from pathlib import Path

from bs4 import BeautifulSoup

OUT = Path("out")
PAGE_RE = re.compile(r"//w\.atwiki\.jp/magicsurvival/pages/(\d+)\.html")
MENU = 2

# メニューの区分 → ディレクトリ ("" は docs/ 直下)
MENU_SECTIONS = {"メニュー": "", "お役立ち情報": "guide", "データベース": "database", "編集者向け": "editors"}

# 一覧ページ → そこからリンクされる個別ページのディレクトリ (先に書いたものを優先する)
INDEXES = {
    15: "magic",       # 魔法(紹介&tier)
    34: "artifacts",   # アーティファクト(紹介&tier)
    8: "classes",      # クラス
    195: "subjects",   # 実験体
    47: "research",    # 研究
    53: "stages",      # 基礎情報 (ステージ)
    185: "stages",     # 深層区域
    172: "builds",     # 参考記録・ビルド構築解説
}

# 上の規則で決まるカテゴリを上書きする
CATEGORY = {
    186: "builds",  # 融合を1つも取らないプレイ (深層区域からリンクされるがプレイ記録)
    242: "artifacts",  # 怪しいポーション (一覧の表からはリンクされていない)
    243: "artifacts",  # 平和条約 (同上)
    **{pid: "synergies" for pid in range(266, 271)},  # AF 一覧のシナジーの表からリンクされる
    308: "guide",  # マジサバクイズ一覧 (どこからもリンクされていない)
    398: "guide",  # シナジー評価(melamain編) (サイドバーの更新履歴からのみ)
    401: "guide",  # 時間で変わるAF・シナジーの価値について (同上)
}

# 出力しないページ (test 系とコメントページは名前で判定する)
EXCLUDE = {
    3: "右メニュー (サイドバー)",
    6: "コメント欄の注意書き",
    174: "どこからもリンクされていないネタページ",
    200: "@wiki の記法の調査メモ",
}

# id → (スラッグ, 要確認か)
SLUGS: dict[int, tuple[str, bool]] = {
    # メニュー
    1: ("index", False),
    52: ("game-overview", False),
    275: ("super-tutorial", False),
    5: ("faq", False),
    172: ("builds", False),
    189: ("tips", False),
    15: ("magic", False),
    34: ("artifacts", False),
    8: ("classes", False),
    195: ("test-subjects", False),
    47: ("research", False),
    53: ("basics", False),
    193: ("glossary", False),
    185: ("deep-zone", True),
    196: ("terra", True),
    282: ("terra-hard", True),
    273: ("join", False),
    # 魔法 (基本魔法は元 wiki の画像のファイル名が英語版の名称)
    16: ("magic-bolt", False),
    17: ("blizzard", False),
    18: ("frost-nova", False),
    19: ("satellite", False),
    20: ("thunderstorm", False),
    21: ("energy-bolt", False),
    22: ("meteor", False),
    23: ("incineration", False),
    24: ("tsunami", False),
    25: ("spirit", False),
    26: ("shield", False),
    27: ("fireball", False),
    28: ("cyclone", False),
    30: ("electric-shock", False),
    31: ("electric-zone", False),
    32: ("armageddon", False),
    33: ("cloaking", False),
    65: ("flash-shock", False),
    66: ("arcane-ray", False),
    67: ("lava-zone", False),
    69: ("magic-circle", False),
    # 融合魔法・究極魔法 (カタカナ名は英語版も同じ綴りとみなす。それ以外は意訳)
    58: ("wrath-of-the-heavens", True),
    71: ("flying-swords", True),
    72: ("light-barrage", True),
    73: ("tera-current", True),
    74: ("war-climate", True),
    75: ("demon-equation", True),
    76: ("frenzy", False),
    77: ("night-parade", True),
    78: ("reaction", True),
    79: ("vortex", False),
    80: ("fire-breath", True),
    81: ("ether-arson", True),
    82: ("orbital-bombardment", True),
    83: ("neutron-emission", True),
    84: ("winter-storm", True),
    85: ("plasma-ray", True),
    86: ("thunder-burst", True),
    87: ("quantum-explosion", True),
    88: ("inferno", False),
    89: ("thunder-attunement", True),
    90: ("furnace", True),
    91: ("power-surge", True),
    92: ("deluge", True),
    93: ("snowflake-bloom", True),
    94: ("storm-ruler", True),
    95: ("overmind", False),
    96: ("infinite-power", True),
    97: ("door-of-creation", True),
    98: ("origin-blast", True),
    99: ("prism-barrage", True),
    100: ("great-rift", True),
    101: ("hyperion-old", True),  # 153 ヒュペリオン の旧ページ
    102: ("avatar", False),
    103: ("heart-of-thunder-old", True),  # 154 雷の心臓 の旧ページ
    106: ("meissner-effect", False),
    107: ("energy-saturation", True),
    108: ("super-typhoon", False),
    109: ("teleport", False),
    110: ("firestorm", True),
    111: ("fireworks", True),
    112: ("spear-of-magic-old", True),  # 157 魔力の槍 の旧ページ (本文に「Spear of Magic」)
    152: ("hellfire", False),
    153: ("hyperion", False),
    154: ("heart-of-thunder", True),
    155: ("great-collision", True),
    156: ("heart-of-ice", True),
    157: ("spear-of-magic", False),
    158: ("gate", False),
    159: ("magnetic-field", True),
    160: ("black-death", True),
    161: ("thunder-breath", True),
    162: ("phoenix", True),
    163: ("brandish", False),
    164: ("black-hole", False),
    165: ("genesis", False),
    166: ("astrape", False),
    167: ("supernova", True),
    168: ("blaster", False),
    169: ("age-of-the-sun", True),
    170: ("destroyer", False),
    171: ("genocide", False),
    197: ("deus-ex-machina", False),
    198: ("excidium", False),
    # 究極魔法 (カタカナ名)
    288: ("stormbringer", False),
    289: ("aura-blade", False),
    290: ("nemesis", False),
    291: ("darkness", False),
    292: ("omega", False),
    293: ("quantum-laser", False),
    294: ("death-storm", False),
    295: ("inquisitor", False),
    296: ("mega-tsunami", False),
    297: ("zero-nova", False),
    298: ("blitz", False),
    299: ("equilibrium", False),
    300: ("ark", True),  # Arc の可能性もある
    301: ("giant-impact", False),
    302: ("hallucination", False),
    303: ("ascension", False),
    304: ("core", False),
    305: ("cosmos", False),
    306: ("overlord", False),
    307: ("terminator", False),
    # アーティファクト (カタカナ名は英語版も同じ綴りとみなす。それ以外は意訳)
    205: ("shadow-cloak", True),
    206: ("broom", True),
    207: ("fairy-tale-book", True),
    208: ("ancient-grimoire", True),
    209: ("meat", True),
    210: ("gear", True),
    211: ("hourglass", True),
    212: ("force-field", True),
    213: ("mutagen", True),
    214: ("lantern", False),
    215: ("bio-shield", True),
    216: ("breeze", True),
    217: ("masquerade-mask", True),
    218: ("stained-glass", False),
    219: ("carnival", False),
    220: ("world-tree-leaf", True),
    221: ("gravity-orb", True),
    222: ("moon-crystal", False),
    223: ("pocket-watch", True),
    224: ("clockwork", True),
    225: ("spider-web", True),
    226: ("second-heart", True),
    227: ("key-ring", True),
    228: ("black-cat", True),
    229: ("watchers-eye", True),
    230: ("aegis", False),
    231: ("soul", True),
    232: ("wizard-hat", True),
    233: ("mercury", False),
    234: ("unicorn", False),
    235: ("undead", False),
    236: ("ether", False),
    237: ("barrier", True),
    238: ("necronomicon", False),
    239: ("cube", False),
    240: ("toy-castle", True),
    241: ("treasure-map", True),
    242: ("suspicious-potion", True),
    243: ("peace-treaty", True),
    244: ("underworld", True),
    245: ("werewolf", False),
    246: ("golden-roulette", True),
    247: ("spear-of-longinus", True),
    248: ("abyss", False),
    249: ("bouquet", True),
    250: ("uranium", True),
    251: ("treasure", True),
    252: ("accelerator", False),
    253: ("dragon-magic", True),
    254: ("titans-authority", True),
    255: ("gaia", False),
    256: ("ark-of-the-covenant", True),
    257: ("ouroboros", False),
    309: ("blood-pack", False),  # TODO.md の例
    310: ("gunpowder", True),
    311: ("spell-backpack", True),
    312: ("specimen", True),
    313: ("ruby", True),
    314: ("target-paper", True),
    315: ("hp-potion", True),
    316: ("magic-scroll", True),
    317: ("rainbow", True),
    318: ("snowman", True),
    319: ("crow", True),
    320: ("sapphire", False),
    321: ("harp", False),
    322: ("virus", False),
    323: ("four-leaf-clover", True),
    324: ("rose", True),
    325: ("graduation-cap", True),
    326: ("cross", True),
    327: ("dragon-scale", True),
    328: ("mana-shield", False),
    329: ("aurora", False),
    330: ("golem-core", True),
    331: ("ancient-staff", True),
    332: ("harmony", False),
    333: ("mana-flame", False),
    334: ("spell-cloak", True),
    335: ("bomb", True),
    336: ("radar", False),
    337: ("mimic", False),
    338: ("owl", True),
    339: ("diamond", False),
    340: ("oculus", False),
    341: ("mana-crystal", True),
    342: ("tarot-card", False),
    343: ("siege-hammer", True),
    344: ("clairvoyance", True),
    345: ("mana-circuit", True),
    346: ("pyramid", False),
    347: ("mana-fountain", True),
    348: ("coin", False),
    349: ("asi", False),
    350: ("assassination", True),
    351: ("philosophers-stone", True),
    352: ("amplifier", True),
    353: ("death-bell", True),
    354: ("spacetime-circuit", True),
    355: ("merlins-cloak", True),
    356: ("singularity", True),
    357: ("brand", True),
    358: ("geometry", True),
    359: ("hunter", True),
    360: ("cyborg", False),
    361: ("domain-of-authority", True),
    362: ("ai-magic", True),
    363: ("predicate", True),
    364: ("halo", False),
    365: ("basilisk", False),
    366: ("jet-engine", False),
    367: ("matrix", False),
    368: ("plasma", False),
    369: ("occult", False),
    370: ("desperado", False),
    371: ("creation-art", True),
    372: ("demon-sword", True),
    373: ("transcendent", True),
    374: ("genome-map", False),
    375: ("reapers-scythe", True),
    376: ("iron-maiden", False),
    377: ("hydra", False),
    378: ("ballista", False),
    379: ("executioners-axe", True),
    380: ("akashic-records", False),
    381: ("dna", False),
    382: ("sanctuary", True),
    383: ("joker", False),
    384: ("crown", True),
    385: ("eclipse", False),
    386: ("excalibur", False),
    387: ("nexus", False),
    388: ("dragon-heart", True),
    389: ("countess", True),
    390: ("widowmaker", False),
    # シナジー (カタカナ名)
    266: ("red-dragon", False),
    267: ("archangel", False),
    268: ("wonderland", False),
    269: ("healing-factor", False),
    270: ("steampunk", False),
    # 読み物
    308: ("quiz", False),
    398: ("synergy-review-melamain", True),
    401: ("af-value-over-time", True),
    # ステージ
    14: ("array", True),
    37: ("laboratory", True),
    41: ("sewer", True),
    176: ("suburbs", True),
    177: ("arboretum", True),
    178: ("academy", True),
    179: ("power-plant", True),
    180: ("culture-room", True),
    181: ("reservoir", True),
    182: ("forest", True),
    183: ("city", True),
    184: ("virtual-ecosystem", True),
    # プレイ記録
    173: ("magic-scholar", True),
    186: ("no-fusion-run", True),
}


def load() -> tuple[dict[int, str], dict[int, set[int]], BeautifulSoup]:
    titles: dict[int, str] = {}
    links: dict[int, set[int]] = {}
    menu = None
    for f in (OUT / "html").glob("*.html"):
        pid = int(f.stem)
        soup = BeautifulSoup(f.read_bytes(), "html.parser")
        titles[pid] = soup.title.get_text().split(" - マジックサバイバル攻略wiki")[0].strip()
        body = soup.select_one("#wikibody")
        links[pid] = {int(m.group(1)) for a in body.select("a[href]") if (m := PAGE_RE.search(a["href"]))}
        if pid == MENU:
            menu = body
    titles[1] = "トップページ"
    return titles, links, menu


def menu_dirs(menu: BeautifulSoup) -> dict[int, str]:
    """メニューページの見出しごとに、その下のリンク先にディレクトリを割り当てる。"""
    dirs: dict[int, str] = {}
    section = ""
    for el in menu.find_all(["h2", "h3", "h4", "a"]):
        if el.name != "a":
            section = MENU_SECTIONS[el.get_text(strip=True)]
        elif m := PAGE_RE.search(el.get("href", "")):
            dirs[int(m.group(1))] = section
    return dirs


def excluded(pid: int, title: str) -> str:
    if pid in EXCLUDE:
        return EXCLUDE[pid]
    if title.startswith("コメント/"):
        return "コメントページ"
    if re.search(r"test|テスト", title, re.I):
        return "test 系ページ"
    return ""


def main():
    titles, links, menu = load()
    top = menu_dirs(menu)
    parents: dict[int, set[int]] = defaultdict(set)
    for src, targets in links.items():
        for t in targets:
            parents[t].add(src)

    # カテゴリ: メニューにあるページはその区分、それ以外はリンク元の一覧ページで決める。
    # 一覧から直接リンクされていないページ (ステージの続きなど) は、リンク元のページのカテゴリに合わせる
    category: dict[int, str] = dict(CATEGORY)
    for pid in titles:
        if pid in category:
            continue
        if pid in top:
            category[pid] = top[pid]
        elif d := next((d for idx, d in INDEXES.items() if idx in parents[pid]), None):
            category[pid] = d
    for _ in range(len(titles)):
        for pid in titles:
            if pid not in category:
                d = next((category[p] for p in sorted(parents[pid]) if p in category and p not in top), None)
                if d is not None:
                    category[pid] = d

    rows = []
    for pid in sorted(titles):
        title = titles[pid]
        reason = "メニュー (mkdocs.yml の nav に移す)" if pid == MENU else excluded(pid, title)
        if reason:
            rows.append({"id": pid, "title": title, "category": "除外", "path": "", "note": reason})
            continue
        cat = category.get(pid, "")
        slug, unsure = SLUGS.get(pid, (f"p{pid}", None))
        note = "要命名" if unsure is None else "要確認" if unsure else ""
        if not cat and pid not in top:
            note = (note + " カテゴリ不明").strip()
        rows.append({"id": pid, "title": title, "category": cat or "(直下)",
                     "path": f"{cat}/{slug}.md" if cat else f"{slug}.md", "note": note})

    paths = [r["path"] for r in rows if r["path"]]
    dup = {p for p in paths if paths.count(p) > 1}
    if dup:
        raise SystemExit(f"パスが重複: {sorted(dup)}")
    with open("rename_map.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "title", "category", "path", "note"])
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} 行 (除外 {sum(r['category'] == '除外' for r in rows)}, "
          f"要命名 {sum(r['note'] == '要命名' for r in rows)}, 要確認 {sum(r['note'] == '要確認' for r in rows)})")


if __name__ == "__main__":
    main()
