# 編集のしかた

ページは `docs/` 以下の Markdown ファイルです。main ブランチには直接 push できないので、ブランチを作って Pull Request (PR) を出してください。PR のビルド (`mkdocs build --strict`) が通ると main にマージできます。マージすると数分でサイトに反映されます。

## 小さな修正 (ブラウザだけで済ませる)

1. サイトの各ページ右上の鉛筆アイコンを押す (GitHub の編集画面が開く)
2. 書き換えて「Commit changes...」→「Create a new branch for this commit and start a pull request」を選ぶ
3. PR を作る

## 手元で編集する

```sh
git switch -c <ブランチ名>      # 例: update-magic-tier
# docs/ 以下を編集
uv run mkdocs serve              # http://127.0.0.1:8000/ms-wiki/ でプレビュー
uv run mkdocs build --strict     # リンク切れなどが無いか確認 (CI と同じ)
git commit -am "魔法 tier を v0.99 に更新"
git push -u origin <ブランチ名>
gh pr create
```

初回だけ [uv](https://docs.astral.sh/uv/) を入れて `uv sync` を実行してください。

## ページを追加するとき

- ファイル名は英語のスラッグにします。ゲーム英語版の名称を小文字にし、単語をハイフンでつなぎます。
  - 例: アーティファクト「エクスカリバー」→ `docs/artifacts/excalibur.md`
  - 英語版の名称が分からないときは意訳で構いません。PR にその旨を書いてください。
- 置き場所 (ディレクトリ) は次のとおりです。

  | ディレクトリ | 内容 |
  | --- | --- |
  | `docs/guide/` | お役立ち情報・読み物 |
  | `docs/database/` | データベース (一覧・tier 表など) |
  | `docs/magic/` | 魔法 (基本・融合・究極) の個別ページ |
  | `docs/artifacts/` | アーティファクトの個別ページ |
  | `docs/synergies/` | シナジーの個別ページ |
  | `docs/stages/` | ステージの個別ページ |
  | `docs/builds/` | プレイ記録・ビルド |
  | `docs/editors/` | 編集者向け |

- ファイルの 1 行目は日本語のタイトルを `# タイトル` で書きます。
- 個別ページはサイドバーには載せません。一覧ページの表からリンクしてください。サイドバーの構成は `mkdocs.yml` の `nav` にあります。
- 他のページへのリンクは相対パスで書きます (例: `[エクスカリバー](../artifacts/excalibur.md)`)。
- 画像は `docs/assets/images/<ページのパス>/` に置きます (例: `docs/artifacts/excalibur.md` の画像は `docs/assets/images/artifacts/excalibur/`)。

## 書き方のメモ

- tier 表: 列見出しに「tier」を含む列は、`S` `A` `B` `C` `D` `E` `×` と `A(S)` (ゲーム終盤での評価を括弧に書く) が色付きのバッジになり、S→× の順で並べ替えられます。
- 表の列見出しをクリックすると、その列で並べ替えられます。
- 文字色は `<span style="color: #b33e5c">文字</span>` のように HTML で書きます。
- 注釈は脚注で書きます: 本文に `[^1]`、ページ末尾に `[^1]: 注釈の内容`。
- 最終更新日は git の履歴から自動で入ります。
- まだ書いていないページは、空の `.md` の先頭に次の front matter を書くと「準備中」の画面になります。本文を書いたらこの 3 行を消します。

  ```markdown
  ---
  template: coming-soon.html
  ---
  ```

### 叫び (おふざけ用)

漫画の集中線つきの極太文字で叫べます (例: スーパーチュートリアルの「ドチュートリアルだっ！！！」)。ここぞという所でたまに使ってください。

```html
<div class="ms-shout">
  <p class="ms-shout__lead">前置きの小さい文 (なくてもよい)</p>
  <p class="ms-shout__text"><span>1行目</span><span>2行目</span></p>
</div>
```

- `<span>` 1 つが 1 行です。2 行目は少し右にずれます。
- 叫びの文字は、使う文字だけをフォントとして読み込んでいます。新しい文字を使うときは、`docs/stylesheets/extra.css` の先頭にある Dela Gothic One の `@import` の `text=` に、その文字を足してください (足さないと、その文字だけ普通の太字になります)。

## ライセンス

PR で追加・変更した内容は [LICENSE](LICENSE) のとおり、文章は CC BY-SA 4.0、コードは MIT で公開されます。PR を出すと、これに同意したことになります。

- 他のサイトや本から文章をコピーしないでください (自分で書いた文章だけを載せる)。
- ゲームの画像 (スクリーンショットを含む)・ゲーム内テキスト・データの権利は LEME にあり、ライセンスの対象外です。
