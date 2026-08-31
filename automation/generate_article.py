#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
記事自動生成スクリプト

ニッチ「離れて暮らす親のための防災ポータブル電源」に沿った新しい記事テーマを選び、
Claude API(claude-opus-5)で本文を生成し、ARTICLE_TEMPLATE.md の構成に沿った
Markdownファイルとして content/posts/ に追加する。

生成後、簡易的な品質チェック(quality_checks.py)を行い、チェックを通過しなければ
記事を公開せず content/review-needed/ に保存して人の確認に回す。

環境変数:
    ANTHROPIC_API_KEY   Claude APIキー(必須。GitHub ActionsではSecretsから注入する)

使い方:
    python3 automation/generate_article.py            # 通常実行(実際にAPIを呼ぶ)
    python3 automation/generate_article.py --dry-run  # APIを呼ばず、配線だけを確認する
"""
import datetime
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from topics import pick_next_topic  # noqa: E402
from quality_checks import run_quality_checks  # noqa: E402

ROOT = Path(__file__).parent.parent
POSTS_DIR = ROOT / "content" / "posts"
REVIEW_DIR = ROOT / "content" / "review-needed"
TEMPLATE_PATH = ROOT / "ARTICLE_TEMPLATE.md"

MODEL = "claude-opus-5"
MAX_ATTEMPTS = 3

SITE_CONTEXT = """\
サイト名: 実家の防災ポータブル電源ガイド
読者: 実家に高齢の親がいる40〜50代の子世代
ニッチ: 離れて暮らす親のための防災ポータブル電源・停電対策グッズ
扱う商品カテゴリ例: ポータブル電源、停電時用の照明・ラジオ、見守りカメラ用の充電維持セット、簡易トイレ、高齢者向け非常食など
"""


def build_prompt(topic, feedback=None):
    template_text = TEMPLATE_PATH.read_text(encoding="utf-8")
    feedback_block = f"\n【前回の下書きの修正指示。必ず反映すること】\n{feedback}\n" if feedback else ""

    return f"""あなたはアフィリエイトサイトの編集者です。以下のニッチ・読者像に沿って、1本の記事を作成してください。

{SITE_CONTEXT}
今回の記事テーマ: {topic['hint']}

記事は必ず次のテンプレートの構成(見出し・アフィリエイトリンクの挿入位置)に従ってください。
テンプレート中のコメント(<!-- -->)や記入例の括弧書きはそのまま出力せず、実際の記事本文に置き換えてください。

--- テンプレートここから ---
{template_text}
--- テンプレートここまで ---

【厳守事項】
- 「命を守れます」「絶対に安全」など、効果や安全性を断定・保証する表現は一切使わないこと。
- 在宅酸素・人工呼吸器・ペースメーカーなどの医療機器に言及する場合は、必ず「メーカーに要確認」「メーカーまたは医療機関に確認」のような注記を近くに入れること。医療機器への給電可否を断定してはいけない。
- {{{{affiliate:商品名|差込ID}}}} の形式のプレースホルダーを、本文中に2〜3箇所入れること(実在のURLやASINは書かないこと)。
- 見出し記法は #, ##, ### のみ、箇条書きは「- 」、引用は「> 」、強調は **text** のみを使うこと(それ以外のMarkdown記法、表組み、番号付きリストは使わない)。
- 全体で1800〜2600文字程度の日本語本文にすること。
{feedback_block}
次の形式で、これ以外の文章を一切含めずに出力してください(前置きや挨拶、説明は不要です):

[TITLE]
(記事タイトル。32文字前後、1行のみ)
[DESCRIPTION]
(記事の要約。80〜120文字程度、1行のみ)
[SLUG]
(半角英数とハイフンのみのURLスラッグ。1行のみ)
[BODY]
(本文のMarkdown。ここに複数行で記述してよい)
"""


def call_claude(prompt):
    """Claude API(claude-opus-5)を1回呼び出し、テキストを返す。"""
    import anthropic

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


_DRY_RUN_SAMPLE = """[TITLE]
【ドライラン】台風前に見直す実家の停電対策チェックリスト
[DESCRIPTION]
これはドライラン用のサンプル記事です。APIを呼ばずに生成〜品質チェック〜保存までの配線を確認するために使います。
[SLUG]
dry-run-typhoon-checklist
[BODY]
## この記事でわかること

これはドライラン確認用のダミー本文です。台風シーズン前に実家の停電対策を見直すポイントを紹介します。

## こんな方におすすめ

- 実家の親が一人暮らしをしている
- 台風のたびに停電が心配になる

## 選び方のポイント

### 1. 操作のシンプルさ

ボタンが少なく、コンセントに挿すだけで使える機種が安心です。

> 医療機器を使用中のご家庭は、機種によって給電の可否が異なります。使用中の機器がある場合は必ずメーカーまたは医療機関に要確認としてください。

## おすすめタイプ2選

### タイプA:小型モデル

{{affiliate:小型ポータブル電源|ASIN_PLACEHOLDER_DRYRUN_01}}

### タイプB:大容量モデル

{{affiliate:大容量ポータブル電源|ASIN_PLACEHOLDER_DRYRUN_02}}

## まとめ

これはドライラン確認用のダミーまとめ文です。
"""


def call_claude_dry_run(prompt):
    """APIを呼ばず、配線確認用の固定サンプルを返す(--dry-run 用)。"""
    return _DRY_RUN_SAMPLE


def load_used_topic_ids():
    used = set()
    for path in POSTS_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        m = re.search(r"^topic_id:\s*(.+)$", text, re.M)
        if m:
            used.add(m.group(1).strip())
    return used


def load_existing_titles():
    titles = []
    for path in POSTS_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        m = re.search(r"^title:\s*(.+)$", text, re.M)
        if m:
            titles.append(m.group(1).strip())
    return titles


def parse_response(text):
    def extract(tag, next_tag=None):
        if next_tag:
            pattern = rf"\[{tag}\]\s*\n(.*?)(?=\n\[{next_tag}\]|\Z)"
        else:
            pattern = rf"\[{tag}\]\s*\n(.*)\Z"
        m = re.search(pattern, text, re.S)
        return m.group(1).strip() if m else ""

    title = extract("TITLE", "DESCRIPTION")
    description = extract("DESCRIPTION", "SLUG")
    slug = extract("SLUG", "BODY")
    body = extract("BODY")

    slug = re.sub(r"[^a-z0-9\-]", "", slug.lower().strip())
    return title, description, slug, body


def generate_once(topic, call_claude_fn, feedback=None):
    prompt = build_prompt(topic, feedback)
    raw = call_claude_fn(prompt)
    return parse_response(raw)


def write_front_matter(title, date_str, description, slug, topic_id, extra_lines=None):
    lines = [
        "---",
        f"title: {title}",
        f"date: {date_str}",
        f"description: {description}",
        f"slug: {slug}",
        f"topic_id: {topic_id}",
    ]
    if extra_lines:
        lines.extend(extra_lines)
    lines.append("---")
    return "\n".join(lines) + "\n"


def main():
    dry_run = "--dry-run" in sys.argv or os.environ.get("DRY_RUN") == "1"
    call_claude_fn = call_claude_dry_run if dry_run else call_claude

    if not dry_run and not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY が設定されていません", file=sys.stderr)
        sys.exit(1)

    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)

    used_ids = load_used_topic_ids()
    existing_titles = load_existing_titles()
    topic = pick_next_topic(used_ids, existing_titles, call_claude_fn, SITE_CONTEXT)
    print(f"選定テーマ: {topic['id']} - {topic['hint']}")

    feedback = None
    last_result = ("", "", "", "")
    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"--- 生成試行 {attempt}/{MAX_ATTEMPTS} ---")
        title, description, slug, body = generate_once(topic, call_claude_fn, feedback)
        last_result = (title, description, slug, body)

        if not (title and description and slug and body):
            feedback = "出力形式が正しくありませんでした。[TITLE]/[DESCRIPTION]/[SLUG]/[BODY] の形式を厳密に守ってください。"
            print("出力形式エラー。再試行します。")
            continue

        ok, problems = run_quality_checks(body)
        if ok:
            date_str = datetime.date.today().isoformat()
            filename = f"{date_str}-{slug}.md"
            content = write_front_matter(title, date_str, description, slug, topic["id"]) + body.strip() + "\n"
            (POSTS_DIR / filename).write_text(content, encoding="utf-8")
            print(f"RESULT: PUBLISHED content/posts/{filename}")
            return

        print("品質チェックNG: " + " / ".join(problems))
        feedback = "前回の下書きは次の理由で公開できませんでした。修正して書き直してください。\n- " + "\n- ".join(problems)

    # 全ての試行が失敗した場合は公開せず、レビュー用に保存する
    title, description, slug, body = last_result
    date_str = datetime.date.today().isoformat()
    review_filename = f"{date_str}-{slug or 'draft'}.review.md"
    content = (
        write_front_matter(
            title or "(タイトル未生成)",
            date_str,
            description or "(説明未生成)",
            slug or "draft",
            topic["id"],
            extra_lines=["status: needs-review"],
        )
        + (body or "(本文の生成に失敗しました)").strip()
        + "\n"
    )
    (REVIEW_DIR / review_filename).write_text(content, encoding="utf-8")
    print(f"RESULT: REVIEW_NEEDED content/review-needed/{review_filename}")


if __name__ == "__main__":
    main()
