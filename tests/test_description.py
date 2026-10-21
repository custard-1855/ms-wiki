import importlib.util
from pathlib import Path
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location(
    "description", Path(__file__).parent.parent / "hooks" / "description.py"
)
description = importlib.util.module_from_spec(spec)
spec.loader.exec_module(description)


def page(title="アビス", meta=None, home=False):
    return SimpleNamespace(title=title, meta=meta or {}, is_homepage=home)


def test_first_paragraph_with_title():
    p = page()
    description.on_page_content("<h1>x</h1><p>要らない<b>です</b></p>", p, None, None)
    assert p.meta["description"] == "アビス | Magic Survival (マジサバ) 攻略wiki。要らないです"


def test_front_matter_wins():
    p = page(meta={"description": "手書き"})
    description.on_page_content("<p>本文</p>", p, None, None)
    assert p.meta["description"] == "手書き"


def test_escaped_and_truncated():
    p = page(title='A&B')
    description.on_page_content('<p>"' + "あ" * 200 + "</p>", p, None, None)
    d = p.meta["description"]
    assert "A&amp;B" in d and "&quot;" in d and d.endswith("…")
