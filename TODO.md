# GitHub Pages 移行タスク

@wiki (マジサバwiki) を MkDocs Material で GitHub Pages に移す。
変換は一度だけ行い、以後は `docs/` の Markdown を直接編集する。

## 決定事項

| 項目 | 決定 |
| --- | --- |
| サイト名 | マジサバwiki |
| 公開 URL | `<user>.github.io/ms-wiki` (独自ドメインなし) |
| 権利 | 自分が元 wiki の管理者。公開して問題なし |
| 見た目 | MkDocs Material + `origin.css` の配色 (ライト/ダーク) |
| 運用 | 変換後は `docs/` の Markdown が正。数人のメンバーが編集 |
| 編集フロー | PR 必須 + CI (`mkdocs build --strict`)、main はブランチ保護 |
| 取得範囲 | 取得漏れ (本文から 273 ページにリンク、取得済み 110) を再取得して全部載せる |
| 除外 | test 系ページ / コメントページ / 各ページ冒頭の「wiki引っ越しのご案内」定型文 |
| ファイル名 | 英語スラッグ。ゲーム英語版の名称に合わせる (例: `artifacts/excalibur.md`) |
| サイドバー | 元の「メニュー」の構成のみ。個別ページ (AF 等) は一覧の表のリンクと検索から辿る |
| 本文中の目次 | 削除 (Material の右側の目次で代わりになる)。見出し id は引き継がない |
| tier 表 | tier の色分け + 列クリックで並べ替え |
| 鮮度表示 | 各ページに最終更新日 (git 履歴から) |
| コメント欄 | 置かない。Discord への誘導をヘッダーのアイコンとフッターに置く |
| 旧 ID の URL | リダイレクトしない |

## タスク

### 1. スクレイパー修正・再取得
- [x] 163 ページ漏れの原因調査 (`list?pp=` のページ送り判定を疑う)
- [x] 一覧に無いページは本文の内部リンクを辿って補完
- [x] Markdown に加えて生 HTML も `out/html/<id>.html` に保存 (`out/` は全体が git 管理外。再変換時に @wiki へ再アクセスしない)
- [x] 表の結合セル (rowspan/colspan) を展開してから Markdown にする (今は空欄になっている。例: `0015_魔法(紹介&tier).md:207`)
- [x] 画像の扱いを決める (今は `strip=["img"]` で捨てている)。残すならダウンロードして `docs/assets/` に置く
  - 残す。ページごとに `docs/assets/images/<ページのパス>/` に置く (添付 PDF も同じ)
- [x] 再取得の実行 (1 リクエスト 2 秒間隔)
  - 339 ページ取得。うち除外 61、出力 278

### 2. ページ名の変換
- [x] 再取得後のページ一覧を見てカテゴリを確定
  - トップページ → `docs/index.md`
  - 「メニュー」の区分でディレクトリを分ける (例: `guide/` お役立ち情報、`database/` データベース、`artifacts/` AF 個別ページ)
- [x] `rename_map.csv` (id, 元タイトル, カテゴリ, 新パス) を下書き
  - スラッグはゲーム英語版の名称を小文字にし、単語をハイフンでつなぐ (例: `blood-pack`)
  - 英語版の名称が分からないものは意訳し、印を付けて確認を頼む
- [>] `rename_map.csv` を確認してもらい、確定版を変換に使う
  - 後回し. 他のメンバに委譲する

### 3. Markdown 変換 (一度きり)
- [x] 内部リンク `//w.atwiki.jp/magicsurvival/pages/N.html` → `rename_map.csv` を使った相対リンク
- [x] リンクの title 属性 (「血液パック (212d)」の類) を削除
- [x] 本文中の「目次」リストと、目次用のアンカーを削除
- [x] 表の空ヘッダ行を削除し、1 行目をヘッダにする
- [x] 「『〇〇』をウィキ内検索」リンクを削除
- [x] 「wiki引っ越しのご案内」定型文を削除
- [x] 除外ページを出力しない。除外ページへのリンクはテキストだけ残す
- [x] 各ページの H1 は日本語タイトル (ファイル名だけ英語)

### 4. MkDocs 構築
- [x] `mkdocs-material` / `mkdocs-git-revision-date-localized-plugin` を依存に追加 (uv)
- [x] `mkdocs.yml`
  - `site_name: マジサバwiki`、`language: ja`、検索の言語を `ja` に
  - 「メニュー」ページの構成から `nav` を作る (個別ページは入れない)
  - `repo_url` / `edit_uri` で各ページに編集ボタン
  - `extra.social` にヘッダーの Discord アイコン、フッターにも Discord リンク
  - 最終更新日の表示 (git-revision-date-localized。Actions では `fetch-depth: 0`)
- [x] `docs/stylesheets/extra.css`: `origin.css` の色を Material の CSS 変数に移植 (ライト/ダーク)
- [x] tier 表
  - tier セル (S/A/B/C/D/E/×、`A(S)` 表記を含む) を色付きバッジにする
  - 列ヘッダのクリックで並べ替え (tablesort など)。tier 列は S→× の順で並べ替える
- [x] `mkdocs build --strict` でリンク切れが無いことを確認
  - 最終更新日のプラグインは git の履歴が要るので、初回コミット後にもう一度確認する

### 5. 公開・運用
- [ ] GitHub リポジトリ `ms-wiki` を作成して push
- [x] GitHub Actions: `main` への push でビルド・デプロイ (Pages の Source は GitHub Actions)
- [x] GitHub Actions: PR で `mkdocs build --strict` を実行 (テストも実行)
- [x] テスト: `convert.py` (pytest)、`docs/javascripts/tables.js` (node:test + jsdom)
- [ ] main のブランチ保護 (PR 必須、CI 成功を必須)
- [ ] メンバーを collaborator に追加
- [x] `CONTRIBUTING.md`: ブランチ作成 → 編集 → PR の手順、ページ追加時のファイル名規則、ローカルでのプレビュー方法 (`uv run mkdocs serve`)

## 将来タスク

### 6. 英語版ページの AI 自動生成
日本語ページを正とし、英語版は AI で生成する (人は直接編集しない)。

- [ ] 多言語化の構成: `mkdocs-static-i18n` を使う。ファイルは `docs/artifacts/excalibur.md` と `docs/artifacts/excalibur.en.md` のように並べ、ヘッダーに言語切り替えを付ける
- [ ] 用語集 `glossary.csv` (日本語, 英語): `rename_map.csv` の英語名称から作り、ゲーム用語の訳を統一する
- [ ] 翻訳スクリプト (Claude API)
  - 入力: 日本語ページ + 用語集。Markdown の構造 (見出し・表・リンク・tier 表記) は変えずに本文だけ訳す
  - 出力の front matter に `source_hash` (元の日本語ページのハッシュ) と `machine_translated: true` を書く
  - `source_hash` が一致するページは飛ばし、変更されたページだけ訳し直す
- [ ] 英語版ページに「機械翻訳です」の注記を出す (テンプレートの override)
- [ ] GitHub Actions: main で日本語ページが変わったら翻訳を実行し、結果を PR として出す (直接 push しない)
- [ ] `CONTRIBUTING.md` に「`*.en.md` は手で編集しない」と追記

### 7. 英語版の Lint
CI で PR ごとに実行する。翻訳 PR だけでなく、日本語ページを変更した PR でも古くなった訳を検出する。

- [ ] 鮮度: 各 `*.en.md` の `source_hash` が日本語ページの現在のハッシュと一致するか (不一致は警告)
- [ ] 欠落: 日本語ページに対応する `*.en.md` があるか (無いものは警告)
- [ ] 構造の一致: 見出しの数・階層、表の行数・列数、リンク数とリンク先が日本語版と同じか (不一致はエラー)
- [ ] 訳し残し: 本文に日本語 (ひらがな・カタカナ・漢字) が残っていないか (コードや固有名詞の例外リストあり)
- [ ] 用語の統一: 用語集の日本語に対応する英語が使われているか
- [ ] tier 表記 (S/A/B/C/D/E/×、`A(S)`) が日本語版と一致するか
- [ ] 一般的な Markdown の lint (markdownlint-cli2) を日英両方にかける
