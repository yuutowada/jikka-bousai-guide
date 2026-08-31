#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
「実家の防災ポータブル電源ガイド」サイトジェネレーター

content/ 以下の Markdown(独自の軽量フォーマット)を docs/ に静的HTMLとして書き出す。
外部ライブラリ不要(Python標準ライブラリのみ)。GitHub Pages は docs/ を公開対象にする想定。

使い方:
    python3 build.py

新しい記事の追加方法は README.md を参照。
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
CONTENT_POSTS = ROOT / "content" / "posts"
CONTENT_PAGES = ROOT / "content" / "pages"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
DOCS = ROOT / "docs"

SITE_NAME = "実家の防災ポータブル電源ガイド"
SITE_DESC = "離れて暮らす親のために、停電・災害時の備えを考える子世代のためのサイト"

DISCLAIMER_SHORT = (
    "本記事は備えの一助を目的としており、効果を保証するものではありません。"
    "公的機関の情報も併せてご確認ください。"
)

AFFILIATE_RE = re.compile(r"^\{\{affiliate:(.+?)\|(.+?)\}\}$")


def read_front_matter(text):
    """--- で囲まれた簡易フロントマターと本文を分離する(key: value の単純な形式)"""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if not m:
        raise ValueError("front matter (---...---) が見つかりません")
    fm_text, body = m.group(1), m.group(2)
    meta = {}
    for line in fm_text.splitlines():
        if not line.strip():
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta, body


def inline_md(text):
    """1行内の **強調** と [文字](URL) だけを変換する簡易インライン変換"""
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', text)
    return text


def md_to_html(body):
    """見出し(#/##/###)・箇条書き(- )・引用(> )・段落・アフィリエイトプレースホルダーのみ対応した
    最小限の Markdown サブセット変換。対応記法は ARTICLE_TEMPLATE.md に明記している。
    """
    lines = body.strip("\n").split("\n")
    html_parts = []
    list_buffer = []
    paragraph_buffer = []

    def flush_list():
        nonlocal list_buffer
        if list_buffer:
            items = "\n".join(f"  <li>{inline_md(x)}</li>" for x in list_buffer)
            html_parts.append(f"<ul>\n{items}\n</ul>")
            list_buffer = []

    def flush_paragraph():
        nonlocal paragraph_buffer
        if paragraph_buffer:
            html_parts.append("<p>" + inline_md(" ".join(paragraph_buffer)) + "</p>")
            paragraph_buffer = []

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            flush_list()
            continue

        m_aff = AFFILIATE_RE.match(stripped)
        if m_aff:
            flush_paragraph()
            flush_list()
            product, value = m_aff.group(1), m_aff.group(2)
            if value.startswith("http://") or value.startswith("https://"):
                # 実リンクが差し込まれている商品:実際に遷移するボタンとして表示する
                html_parts.append(
                    '<div class="affiliate-link">\n'
                    f'  <p class="affiliate-link__product">{product}</p>\n'
                    f'  <a class="affiliate-link__button" href="{value}" '
                    'target="_blank" rel="nofollow sponsored noopener">Amazonで見る →</a>\n'
                    '  <p class="affiliate-link__disclosure">[PR] Amazon.co.jpの商品ページに移動します</p>\n'
                    "</div>"
                )
            else:
                # まだリンク未設置の商品:「設置予定」のプレースホルダー表示のまま。
                # 差込ID(value)は開発用の内部情報であり読者向け表示には出さず、
                # HTMLコメントとしてソース上にのみ残す(view-sourceでのみ確認可能)。
                safe_value = value.replace("--", "—")
                html_parts.append(
                    '<div class="affiliate-placeholder">\n'
                    '  <p class="affiliate-placeholder__label">🔧 アフィリエイトリンク設置予定</p>\n'
                    f'  <p class="affiliate-placeholder__product">{product}</p>\n'
                    '  <p class="affiliate-placeholder__note">(リンク設置準備中)</p>\n'
                    f"  <!-- 差込ID: {safe_value} -->\n"
                    "</div>"
                )
            continue

        if line.startswith("### "):
            flush_paragraph(); flush_list()
            html_parts.append(f"<h3>{inline_md(line[4:])}</h3>")
        elif line.startswith("## "):
            flush_paragraph(); flush_list()
            html_parts.append(f"<h2>{inline_md(line[3:])}</h2>")
        elif line.startswith("# "):
            flush_paragraph(); flush_list()
            html_parts.append(f"<h1>{inline_md(line[2:])}</h1>")
        elif line.startswith("> "):
            flush_paragraph(); flush_list()
            html_parts.append(f"<blockquote>{inline_md(line[2:])}</blockquote>")
        elif line.startswith("- "):
            flush_paragraph()
            list_buffer.append(line[2:])
        else:
            flush_list()
            paragraph_buffer.append(stripped)

    flush_paragraph()
    flush_list()
    return "\n".join(html_parts)


def render(template_name, **ctx):
    text = (TEMPLATES / template_name).read_text(encoding="utf-8")
    for key, value in ctx.items():
        text = text.replace(f"<!--{key}-->", value)
    return text


def load_posts():
    posts = []
    for path in sorted(CONTENT_POSTS.glob("*.md")):
        meta, body = read_front_matter(path.read_text(encoding="utf-8"))
        meta["_html"] = md_to_html(body)
        meta.setdefault("slug", path.stem)
        posts.append(meta)
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def render_card(post):
    return render(
        "card.html",
        TITLE=post["title"],
        DESCRIPTION=post.get("description", ""),
        DATE=post["date"],
        SLUG=post["slug"],
    )


def build():
    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir(parents=True)
    (DOCS / "posts").mkdir()
    (DOCS / ".nojekyll").touch()  # GitHub PagesにJekyll処理をさせず、生成済みHTMLをそのまま配信させる
    if STATIC.exists():
        shutil.copytree(STATIC, DOCS / "static")

    posts = load_posts()

    nav_root = render("nav.html", DEPTH="")
    nav_post = render("nav.html", DEPTH="../")

    # --- 記事詳細ページ ---
    for post in posts:
        article_html = render(
            "article.html",
            TITLE=post["title"],
            DATE=post["date"],
            BODY=post["_html"],
            DISCLAIMER=DISCLAIMER_SHORT,
        )
        page = render(
            "base.html",
            DEPTH="../",
            SITE_NAME=SITE_NAME,
            NAV=nav_post,
            PAGE_TITLE=f"{post['title']} | {SITE_NAME}",
            CONTENT=article_html,
        )
        (DOCS / "posts" / f"{post['slug']}.html").write_text(page, encoding="utf-8")

    # --- 記事一覧ページ ---
    cards = "\n".join(render_card(p) for p in posts) or "<p>準備中です。</p>"
    posts_page = render("posts_list.html", CARDS=cards)
    page = render(
        "base.html",
        DEPTH="",
        SITE_NAME=SITE_NAME,
        NAV=nav_root,
        PAGE_TITLE=f"記事一覧 | {SITE_NAME}",
        CONTENT=posts_page,
    )
    (DOCS / "posts.html").write_text(page, encoding="utf-8")

    # --- トップページ ---
    latest_cards = "\n".join(render_card(p) for p in posts[:3]) or "<p>準備中です。</p>"
    index_content = render(
        "index.html", SITE_NAME=SITE_NAME, SITE_DESC=SITE_DESC, LATEST_CARDS=latest_cards
    )
    page = render(
        "base.html",
        DEPTH="",
        SITE_NAME=SITE_NAME,
        NAV=nav_root,
        PAGE_TITLE=SITE_NAME,
        CONTENT=index_content,
    )
    (DOCS / "index.html").write_text(page, encoding="utf-8")

    # --- このサイトについて ---
    about_meta, about_body = read_front_matter(
        (CONTENT_PAGES / "about.md").read_text(encoding="utf-8")
    )
    about_html = md_to_html(about_body)
    page = render(
        "base.html",
        DEPTH="",
        SITE_NAME=SITE_NAME,
        NAV=nav_root,
        PAGE_TITLE=f"{about_meta['title']} | {SITE_NAME}",
        CONTENT=f"<article class=\"page\">{about_html}</article>",
    )
    (DOCS / "about.html").write_text(page, encoding="utf-8")

    print(f"Built {len(posts)} posts -> {DOCS}")


if __name__ == "__main__":
    build()
