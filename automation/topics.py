# -*- coding: utf-8 -*-
"""
記事テーマの選定ロジック

- 事前に用意したテーマ一覧(TOPICS)から、まだ使っていないものを順番に選ぶ。
- 一覧をすべて使い切ったら、Claudeにこれまでの記事タイトルを見せた上で
  重複しない新しいテーマを1つ提案してもらう(フォールバック)。

「使用済みかどうか」は content/posts/*.md の front matter にある `topic_id` で判定する
(generate_article.py が生成時に付与する)。
"""
import re

# ニッチ「離れて暮らす親のための防災ポータブル電源」に沿ったテーマ候補。
# 上から順番に使用し、使い切ったらClaudeに新しいテーマを提案してもらう。
TOPICS = [
    {"id": "typhoon-checklist", "hint": "台風シーズン前に実家の停電対策を点検するチェックリスト記事"},
    {"id": "earthquake-power-outage", "hint": "大規模地震による停電を想定した、実家の備えの見直し記事"},
    {"id": "solar-panel-combo", "hint": "ソーラーパネルと組み合わせて使うポータブル電源の選び方"},
    {"id": "budget-comparison", "hint": "価格帯別(1万円台〜10万円以上)で見るポータブル電源の選び方比較"},
    {"id": "winter-heavy-snow", "hint": "大雪による孤立・停電に備える、冬の実家向け防災グッズ特集"},
    {"id": "gift-guide-respect-elderly-day", "hint": "敬老の日や誕生日に贈る、防災グッズとしてのポータブル電源ギフトガイド"},
    {"id": "led-lantern-comparison", "hint": "停電時の照明について、LEDランタンとポータブル電源の使い分け方"},
    {"id": "smartphone-lifeline", "hint": "停電時にスマートフォンの充電を確保することの重要性と具体的な方法"},
    {"id": "solo-elderly-women", "hint": "一人暮らしの高齢女性向けに、軽量で扱いやすい防災グッズを選ぶポイント"},
    {"id": "cost-of-inaction", "hint": "「備えていなかった場合」に実際どんな困りごとが起きるかのケーススタディ記事"},
    {"id": "portable-fridge", "hint": "常備薬や食品の保存のために検討したい、ポータブル冷蔵庫という選択肢"},
    {"id": "simple-toilet", "hint": "断水時の備えとして、簡易トイレの選び方と使い方"},
    {"id": "emergency-food-elderly", "hint": "高齢者向けに、柔らかい・減塩などに配慮した非常食の選び方"},
    {"id": "capacity-calculator", "hint": "必要な容量(Wh)をどう見積もるか、簡単な目安表つきの解説記事"},
    {"id": "maintenance-tips", "hint": "ポータブル電源の劣化を防ぐための、正しい保管方法とメンテナンスの頻度"},
    {"id": "car-charging", "hint": "車のシガーソケットからも充電できるポータブル電源の活用法"},
    {"id": "multiple-devices", "hint": "スマホ・ラジオ・見守りカメラなど、複数機器を同時に給電する際の注意点"},
    {"id": "disaster-kit-checklist", "hint": "実家に用意しておきたい防災バッグの中身、総合チェックリスト"},
    {"id": "power-outage-duration-stats", "hint": "過去の災害事例から見る、実際の停電継続時間の目安"},
    {"id": "communication-plan", "hint": "停電時に離れた家族と連絡を取り合うための、電話以外の安否確認手段"},
]


def pick_next_topic(used_ids, existing_titles, call_claude_fn, site_context):
    """未使用のテーマを順番に返す。使い切っていればClaudeに新しいテーマを提案してもらう。"""
    for topic in TOPICS:
        if topic["id"] not in used_ids:
            return topic

    prompt = f"""{site_context}

これまでに公開した記事タイトル一覧:
{chr(10).join('- ' + t for t in existing_titles) if existing_titles else '(まだありません)'}

上記のどれとも内容が重複しない、新しい記事テーマを1つ提案してください。
次の形式で、他の文章を含めずに出力してください:

[ID]
(半角英数とハイフンのみの短い識別子。例: new-topic-idea)
[HINT]
(1文でのテーマの説明)
"""
    raw = call_claude_fn(prompt)
    id_match = re.search(r"\[ID\]\s*\n(.+)", raw)
    hint_match = re.search(r"\[HINT\]\s*\n(.+)", raw)
    new_id = id_match.group(1).strip() if id_match else f"auto-topic-{len(existing_titles) + 1}"
    new_id = re.sub(r"[^a-z0-9\-]", "", new_id.lower()) or f"auto-topic-{len(existing_titles) + 1}"
    hint = hint_match.group(1).strip() if hint_match else "防災ポータブル電源に関する新しい切り口の記事"
    return {"id": new_id, "hint": hint}
