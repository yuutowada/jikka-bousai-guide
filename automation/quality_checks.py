# -*- coding: utf-8 -*-
"""
生成された記事本文に対する簡易品質チェック。

ここを通過しない記事は自動公開せず、content/review-needed/ に保存して人の確認に回す
(generate_article.py 側の制御)。あくまで簡易的な文字列チェックであり、
最終的な内容の妥当性を保証するものではない点に注意。
"""

# 効果・安全性を断定・保証する表現(このニッチはYMYL寄りのため特に注意)
DEFAULT_FORBIDDEN_PHRASES = [
    "命を守れます",
    "命を守ります",
    "必ず助かります",
    "絶対に安全",
    "完全に防げます",
    "100%安全",
    "確実に助かります",
    "必ず安全",
    "絶対安心",
    "完全に安心",
    "何があっても安心",
]

# これらの語に言及している場合は「要確認」等の注記が必須
DEFAULT_MEDICAL_KEYWORDS = [
    "在宅酸素",
    "酸素濃縮器",
    "人工呼吸器",
    "医療機器",
    "ペースメーカー",
    "電動ベッド",
    "吸引器",
    "透析",
]

DEFAULT_REQUIRED_CAUTION_SNIPPET = "要確認"

REQUIRED_HEADINGS = ["この記事でわかること", "まとめ"]


def run_quality_checks(
    body,
    forbidden_phrases=None,
    medical_keywords=None,
    required_caution_snippet=None,
):
    """本文(Markdown)を検査し、(合格したか, 問題点のリスト) を返す。"""
    forbidden_phrases = forbidden_phrases or DEFAULT_FORBIDDEN_PHRASES
    medical_keywords = medical_keywords or DEFAULT_MEDICAL_KEYWORDS
    required_caution_snippet = required_caution_snippet or DEFAULT_REQUIRED_CAUTION_SNIPPET

    problems = []

    # 1. 断定的な効能表現のチェック
    found_forbidden = [p for p in forbidden_phrases if p in body]
    if found_forbidden:
        problems.append("断定的な効能表現が含まれています: " + "、".join(found_forbidden))

    # 2. 医療機器に言及している場合、「要確認」等の注記があるかチェック
    mentions_medical = any(kw in body for kw in medical_keywords)
    if mentions_medical and required_caution_snippet not in body:
        problems.append(
            "医療機器(在宅酸素・人工呼吸器等)への言及がありますが、"
            "「メーカーに要確認」等の注記が見当たりません"
        )

    # 3. アフィリエイトプレースホルダーが最低1つあるか
    if "{{affiliate:" not in body:
        problems.append("アフィリエイトリンクのプレースホルダー({{affiliate:商品名|ID}})が見つかりません")

    # 4. 必須見出しの有無(テンプレート構成に沿っているかの簡易チェック)
    for heading in REQUIRED_HEADINGS:
        if heading not in body:
            problems.append(f"必須の見出し「{heading}」が見つかりません")

    # 5. 極端に短い/長い本文でないか(生成崩れの簡易検知)
    length = len(body)
    if length < 500:
        problems.append(f"本文が短すぎます({length}文字)")
    elif length > 6000:
        problems.append(f"本文が長すぎます({length}文字)")

    return (len(problems) == 0, problems)
