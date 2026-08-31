# 実家の防災ポータブル電源ガイド(仮称)

離れて暮らす高齢の親を持つ40〜50代の子世代に向けて、停電・災害時の備え(ポータブル電源、停電時の照明・ラジオ、見守り家電の電源維持、簡易トイレ、非常食など)の選び方を紹介するアフィリエイトサイトです。

> **注意**: サイト名・リポジトリ名は仮のものです。正式名称が決まったら README・`build.py` 内の `SITE_NAME` を書き換えてください。

## なぜこの構成にしたか

- この開発環境に Node.js / Ruby が入っていなかったため、Eleventy や Jekyll ではなく **Python標準ライブラリのみで動く自作ジェネレーター(`build.py`)** を採用しました。
- 依存パッケージが一切ないため、`git clone` して `python3 build.py` を叩くだけでどの環境でも同じようにビルドできます。
- 出力(`docs/`)はビルド済みの静的HTMLをそのままリポジトリにコミットする方式です。GitHub Pages 側でのビルド処理が不要なため、GitHub Actions の設定やNode環境が無くても公開できます。
- 今後、記事を自動生成する仕組みを組む場合も「`content/posts/` に決まったフォーマットのMarkdownファイルを置いて `python3 build.py` を実行する」というシンプルなインターフェースなので、スクリプトからの自動投稿と相性が良い構成にしています。

## ディレクトリ構成

```
jikka-bousai-guide/
├── build.py                  # サイトジェネレーター本体(標準ライブラリのみ)
├── ARTICLE_TEMPLATE.md        # 新規記事を書くときにコピーするテンプレート
├── content/
│   ├── posts/                 # 記事のMarkdown(ここに追加していく)
│   └── pages/
│       └── about.md            # 「このサイトについて」ページの原稿
├── templates/                  # HTMLレイアウト断片(base / nav / card / article / index / posts_list)
├── static/
│   └── style.css               # サイト全体のスタイル
└── docs/                       # ビルド結果(GitHub Pagesの公開対象)
    ├── index.html
    ├── posts.html
    ├── about.html
    ├── static/style.css
    └── posts/*.html
```

`docs/` は `build.py` が自動生成するフォルダです。手動で編集せず、必ず `content/` 側を編集してから再ビルドしてください。

## ローカルでの使い方

### サイトをビルドする

```bash
cd jikka-bousai-guide
python3 build.py
```

`docs/` フォルダが再生成されます。

### ローカルでプレビューする

```bash
cd jikka-bousai-guide/docs
python3 -m http.server 8000
```

ブラウザで `http://localhost:8000/index.html` を開くと確認できます。

## 新しい記事を追加する手順

1. `ARTICLE_TEMPLATE.md` を `content/posts/YYYY-MM-DD-記事スラッグ.md` としてコピー
2. フロントマター(title / date / description / slug)と本文を書く
3. アフィリエイトリンクを入れたい場所に `{{affiliate:商品名|差込ID}}` を記述(Amazon未承認の間はこのままでOK)
4. `python3 build.py` を実行してビルド
5. ローカルプレビューで見た目を確認
6. `git add . && git commit -m "記事追加: ○○"` してから push

対応しているMarkdown記法の詳細は `ARTICLE_TEMPLATE.md` 冒頭のコメントを参照してください。

## GitHub Pagesでの公開手順

このリポジトリはまだGitHub上に作成されていません。以下の手順で公開してください(`gh` CLIが未インストールのため、Web UIまたは個別コマンドでの手順を記載します)。

### 1. GitHubで新規リポジトリを作成

GitHub上で `New repository` から作成します(READMEやライセンスは追加しない「空のリポジトリ」で作成してください)。

### 2. ローカルリポジトリをリモートに接続してpush

```bash
cd ~/jikka-bousai-guide
git remote add origin https://github.com/<あなたのユーザー名>/<リポジトリ名>.git
git branch -M main
git push -u origin main
```

### 3. GitHub PagesをOnにする

1. GitHubのリポジトリページで `Settings` → `Pages` を開く
2. `Build and deployment` の `Source` を `Deploy from a branch` にする
3. `Branch` を `main` / `/docs` に設定して `Save`
4. 数分待つと `https://<あなたのユーザー名>.github.io/<リポジトリ名>/` で公開されます

### 4. 記事を追加・更新するたび

```bash
python3 build.py
git add .
git commit -m "記事更新: ○○"
git push
```

pushすると数十秒〜数分でGitHub Pages側にも反映されます。

## Amazonアソシエイト承認後にやること

- `content/posts/*.md` 内の `{{affiliate:商品名|ASIN_PLACEHOLDER_xx}}` を、実際のアフィリエイトリンクに置き換える(`build.py` の `AFFILIATE_RE` 部分を、リンク生成に変更する形でも対応可能)
- `templates/base.html` の「Amazonアソシエイト・プログラムへの参加を予定していますが…」の文言を、正式な開示文言に更新する
- `content/pages/about.md` のアフィリエイトプログラムについての節を更新する
