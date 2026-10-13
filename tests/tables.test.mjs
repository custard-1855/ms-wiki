// docs/javascripts/tables.js (tier バッジと並べ替え) のテスト。
// MkDocs Material が出力する表の形の HTML を jsdom に読ませて、サイトと同じ順にスクリプトを実行する。
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { JSDOM } from "jsdom";

const tablesort = readFileSync(new URL("../node_modules/tablesort/dist/tablesort.min.js", import.meta.url), "utf8");
const tables = readFileSync(new URL("../docs/javascripts/tables.js", import.meta.url), "utf8");

function render(headers, rows) {
  const th = headers.map((h) => `<th>${h}</th>`).join("");
  const tr = rows.map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join("")}</tr>`).join("");
  const dom = new JSDOM(`<article><table><thead><tr>${th}</tr></thead><tbody>${tr}</tbody></table></article>`, {
    runScripts: "outside-only",
  });
  // Material は document$ (ページ表示ごとに流れる Observable) を用意している
  dom.window.eval("var document$ = { subscribe: (f) => f() };");
  dom.window.eval(tablesort);
  dom.window.eval(tables);
  return dom.window;
}

const column = (w, i) => [...w.document.querySelectorAll("tbody tr")].map((r) => r.cells[i].textContent);
const click = (w, i) => w.document.querySelectorAll("th")[i].dispatchEvent(new w.MouseEvent("click", { bubbles: true }));

test("tier 列のセルを色付きバッジにする", () => {
  const w = render(["魔法", "tier"], [["a", "S"], ["b", "×"], ["c", "B"]]);
  const badges = [...w.document.querySelectorAll("tbody td:nth-child(2) .tier")];
  assert.deepEqual(badges.map((b) => b.className), ["tier tier-s", "tier tier-x", "tier tier-b"]);
});

test("元 wiki の色付き太字 (<span style><strong>) もバッジにする", () => {
  const w = render(["tier"], [['<span style="color: #0068b7"><strong>A</strong></span>']]);
  assert.equal(w.document.querySelector("td").innerHTML, '<span class="tier tier-a">A</span>');
});

test("A(S) は主評価と終盤評価の 2 つのバッジにする", () => {
  const w = render(["tier"], [["A(S)"], ["B（A）"]]);
  const cells = [...w.document.querySelectorAll("td")].map((td) => td.innerHTML);
  assert.deepEqual(cells, [
    '<span class="tier tier-a">A</span>(<span class="tier tier-s tier--sub">S</span>)',
    '<span class="tier tier-b">B</span>(<span class="tier tier-a tier--sub">A</span>)',
  ]);
});

test("脚注の参照番号はバッジの後ろに残す", () => {
  const w = render(["tier"], [['C<sup id="fnref:3"><a class="footnote-ref" href="#fn:3">3</a></sup>']]);
  const td = w.document.querySelector("td");
  assert.equal(td.querySelector(".tier").textContent, "C");
  assert.equal(td.querySelector("sup a").getAttribute("href"), "#fn:3");
});

test("tier 以外の列や tier でない値はそのまま", () => {
  const w = render(["魔法", "tier"], [["S", "-"], ["A", "調査中"]]);
  assert.equal(w.document.querySelectorAll(".tier").length, 0);
  assert.deepEqual(column(w, 1), ["-", "調査中"]);
});

test("tier 列は 1 回目のクリックで S→×、2 回目で逆順に並べる", () => {
  const w = render(["魔法", "tier"], [["c", "C"], ["x", "×"], ["s", "S"], ["e", "E"], ["a", "A"]]);
  click(w, 1);
  assert.deepEqual(column(w, 0), ["s", "a", "c", "e", "x"]);
  click(w, 1);
  assert.deepEqual(column(w, 0), ["x", "e", "c", "a", "s"]);
});

test("主評価が同じなら終盤評価の高い方を先に並べる", () => {
  const w = render(["魔法", "tier"], [["a", "A"], ["as", "A(S)"], ["ab", "A(B)"], ["s", "S"]]);
  click(w, 1);
  assert.deepEqual(column(w, 0), ["s", "as", "a", "ab"]);
});

test("tier 以外の列も見出しのクリックで並べ替えられる", () => {
  const w = render(["優先度", "tier"], [["3", "A"], ["1", "B"], ["2", "C"]]);
  click(w, 0);
  assert.deepEqual(column(w, 0), ["1", "2", "3"]);
});
