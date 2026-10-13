// 表の列ヘッダのクリックで並べ替える。tier 列は色付きバッジにし、S→× の順で並べ替える。

const TIERS = ["S", "A", "B", "C", "D", "E", "×"];
// 「A」「A(S)」(ゲーム終盤での評価を括弧で書く) の形。全角の括弧・× の異体字も受け付ける
const TIER_RE = /^([SABCDE×xX✕])\s*(?:[(（]\s*([SABCDE×xX✕])\s*[)）])?$/;

function tierRank(letter) {
  return TIERS.indexOf(/[xX✕]/.test(letter) ? "×" : letter);
}

function badge(letter, sub) {
  const rank = tierRank(letter);
  const span = document.createElement("span");
  span.className = `tier tier-${rank === 6 ? "x" : TIERS[rank].toLowerCase()}`;
  if (sub) span.classList.add("tier--sub");
  span.textContent = TIERS[rank];
  return span;
}

// 脚注の参照番号を除いたセルの文字列
function cellText(cell) {
  const clone = cell.cloneNode(true);
  clone.querySelectorAll("sup").forEach((sup) => sup.remove());
  return clone.textContent.trim();
}

function decorateTierColumn(table, col) {
  for (const row of table.tBodies[0]?.rows ?? []) {
    const cell = row.cells[col];
    const m = cell && cellText(cell).match(TIER_RE);
    if (!m) continue;
    const notes = [...cell.querySelectorAll("sup")];
    cell.replaceChildren(badge(m[1], false));
    if (m[2]) cell.append("(", badge(m[2], true), ")");
    cell.append(...notes);
    // 主評価で並べ、同じなら終盤評価で並べる
    const sub = m[2] ? tierRank(m[2]) : tierRank(m[1]);
    cell.dataset.sort = String(tierRank(m[1]) * 10 + sub);
  }
}

Tablesort.extend(
  "tier",
  () => false, // 自動判定はしない。tier 列には data-sort-method="tier" を付ける
  // tablesort は昇順のとき並べ替え結果を反転するので、大きい順に並べる関数を渡す
  (a, b) => Number(b) - Number(a),
);

document$.subscribe(() => {
  for (const table of document.querySelectorAll("article table:not([class])")) {
    const head = table.tHead?.rows[0];
    if (!head) continue;
    [...head.cells].forEach((th, col) => {
      if (/tier/i.test(th.textContent)) {
        th.dataset.sortMethod = "tier";
        decorateTierColumn(table, col);
      }
    });
    new Tablesort(table);
  }
});
