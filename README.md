# マジサバwiki

Magic Survival (マジックサバイバル) の非公式攻略wiki。@wiki から移行し、MkDocs Material で GitHub Pages に公開している。

- サイト: https://custard-1855.github.io/ms-wiki/
- 編集のしかた: [CONTRIBUTING.md](CONTRIBUTING.md)

## 構成

| パス | 内容 |
| --- | --- |
| `docs/` | ページの Markdown (これが正) |
| `mkdocs.yml` | サイトの設定とサイドバー (`nav`) |
| `overrides/` | Material のテンプレートの上書き (ヘッダーの Discord アイコン) |
| `.github/workflows/pages.yml` | PR でテストとビルド確認、main への push でデプロイ |
| `tests/` | 変換スクリプト (pytest) と `docs/javascripts/tables.js` (node:test + jsdom) のテスト |

## ライセンス

文章 (`docs/` の Markdown) は CC BY-SA 4.0、コードは MIT。ゲームの画像・ゲーム内テキスト・データの権利は LEME に帰属し、対象外。詳しくは [LICENSE](LICENSE)。

## テスト

```sh
uv run pytest     # convert.py
npm ci && npm test  # docs/javascripts/tables.js (tier バッジと並べ替え)
```

## @wiki からの移行 (一度きり)

移行に使ったスクリプトを残している。`docs/` を手で編集し始めた後は再実行しないこと (上書きされる)。

```sh
uv run python atwiki_scrape.py      # @wiki の生 HTML と画像を out/ に保存 (1 リクエスト 2 秒間隔)
uv run python draft_rename_map.py   # rename_map.csv (id, 元タイトル, カテゴリ, 新パス) の下書きを作る
uv run python convert.py            # out/ と rename_map.csv から docs/ の Markdown を作る
```
