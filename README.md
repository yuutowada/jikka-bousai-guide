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
├── automation/
│   ├── generate_article.py     # 記事自動生成スクリプト(Claude API)
│   ├── topics.py                # 記事テーマの選定ロジック
│   ├── quality_checks.py        # 生成記事の簡易品質チェック
│   └── requirements.txt         # automation用の依存パッケージ(anthropic)
├── content/
│   ├── posts/                 # 記事のMarkdown(ここに追加していく)
│   ├── review-needed/          # 品質チェックに落ちた記事の下書き(自動生成、通常は空)
│   └── pages/
│       └── about.md            # 「このサイトについて」ページの原稿
├── templates/                  # HTMLレイアウト断片(base / nav / card / article / index / posts_list)
├── static/
│   └── style.css               # サイト全体のスタイル
├── .github/workflows/
│   └── weekly-article.yml      # 毎週月曜に記事生成→ビルド→pushするワークフロー
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

> このリポジトリは既に GitHub Pages で公開済みです(`https://<ユーザー名>.github.io/jikka-bousai-guide/`)。以下は、別環境で最初からセットアップする場合や、手順を振り返りたい場合のための記録です。

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

## 記事の自動生成・自動公開(フェーズ3)

`automation/generate_article.py` が、Claude API(`claude-sonnet-5`)を使って記事を1本自動生成し、`content/posts/` に追加します。`.github/workflows/weekly-article.yml` により、**毎週月曜 06:00(JST)に自動実行 → ビルド → コミット・push** まで行われます。

### 仕組み

1. **テーマ選定**(`automation/topics.py`): あらかじめ用意した20個のテーマ候補から、まだ使っていないものを順番に選びます。使用済みかどうかは各記事の front matter の `topic_id` で判定します。候補を使い切った場合は、これまでの記事タイトル一覧をClaudeに見せて重複しない新しいテーマを1つ提案してもらいます。
2. **本文生成**: `ARTICLE_TEMPLATE.md` の構成(見出し・アフィリエイトリンクの挿入位置・免責文言の位置)をそのままプロンプトに埋め込み、その構成に従って本文を生成させます。
3. **品質チェック**(`automation/quality_checks.py`): 生成された本文に対して、以下を機械的にチェックします。
   - 「命を守れます」「絶対に安全」等、断定的な効能表現が含まれていないか
   - 在宅酸素・人工呼吸器などの医療機器に言及している場合、「メーカーに要確認」等の注記があるか
   - アフィリエイトリンクのプレースホルダーが入っているか
   - 「この記事でわかること」「まとめ」等の必須見出しがあるか、本文の長さが極端でないか
   - チェックに落ちた場合は、その理由をフィードバックとして添えて**最大3回まで再生成**します。
4. **公開 or レビュー行き**: 3回すべて失敗した場合は記事を公開せず、`content/review-needed/` に下書きを保存して人の確認に委ねます(このときは `content/posts/` に追加されないため、サイトには反映されません)。

> **注意**: このチェックはあくまで簡易的な文字列マッチングです。内容の事実確認や薬機法・景品表示法上の適切性まで保証するものではありません。定期的に生成記事に目を通すことをおすすめします。

### ローカルでの動作確認

実際にAPIを呼ばずに配線(テーマ選定→生成→品質チェック→保存)だけを確認したい場合:

```bash
cd jikka-bousai-guide
python3 automation/generate_article.py --dry-run
```

実際にClaude APIを呼んで1本生成する場合(要 `ANTHROPIC_API_KEY`):

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
pip install -r automation/requirements.txt
python3 automation/generate_article.py
python3 build.py   # 生成された記事をサイトに反映
```

生成された `content/posts/*.md` を確認し、問題なければ通常どおり `git add / commit / push` してください。

### GitHub Actionsでの動作確認

1. GitHubに `ANTHROPIC_API_KEY` をSecretsとして登録する(登録手順は次のセクション)
2. GitHubリポジトリの `Actions` タブ → `週次記事自動生成・公開` → `Run workflow` で手動実行できます(`workflow_dispatch` に対応済み)
3. 実行後、`Actions` の実行ログで `RESULT: PUBLISHED ...` または `RESULT: REVIEW_NEEDED ...` を確認できます
4. `PUBLISHED` の場合は数分後に GitHub Pages にも反映されます。`REVIEW_NEEDED` の場合は `content/review-needed/` にファイルが追加されますが、サイト自体は変わりません

### GitHub Secretsへの登録手順(あなたに行っていただく部分)

1. Anthropic Console(https://console.anthropic.com/ )でAPIキーを発行する
2. GitHubの対象リポジトリページで `Settings` → `Secrets and variables` → `Actions` を開く
3. `New repository secret` をクリック
4. `Name` に `ANTHROPIC_API_KEY`、`Secret` に発行したAPIキーの値を入力して `Add secret`

これでワークフロー内の `${{ secrets.ANTHROPIC_API_KEY }}` からキーが参照されます。コード中にキーを直書きすることはありません。

### コストについて

`claude-sonnet-5` は $2.00 / $10.00(入力 / 出力 100万トークンあたり)の料金です(コスト効率を優先し、`claude-opus-5` から変更)。1回の記事生成(最大3回まで再試行)にかかるトークン数の目安から、1回の週次実行あたり数円〜十数円程度のAPI利用料が発生します。毎週自動実行されるため、月間のAnthropic APIの請求額は定期的に確認することをおすすめします。生成記事の品質に問題が見られる場合は `automation/generate_article.py` の `MODEL` を `claude-opus-5` に戻すことも検討してください。

## Amazonアソシエイト承認後にやること

- `content/posts/*.md` 内の `{{affiliate:商品名|ASIN_PLACEHOLDER_xx}}` を、実際のアフィリエイトリンクに置き換える(`build.py` の `AFFILIATE_RE` 部分を、リンク生成に変更する形でも対応可能)
- `templates/base.html` の「Amazonアソシエイト・プログラムへの参加を予定していますが…」の文言を、正式な開示文言に更新する
- `content/pages/about.md` のアフィリエイトプログラムについての節を更新する
