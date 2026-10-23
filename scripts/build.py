#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""依存パッケージ不要の静的サイト生成。HTMLはJSなしでも閲覧できます。"""
import argparse
import datetime
import html
import json
import os
from pathlib import Path
import re
import shutil
from urllib.parse import quote, urlparse

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist"
E = lambda value: html.escape(str(value), quote=True)
parser = argparse.ArgumentParser()
parser.add_argument("--release", action="store_true", help="連絡先・ポリシー運用の未設定があれば公開用ビルドを中止")
args = parser.parse_args()
site = json.loads((ROOT / "data/site.json").read_text())
required = ("contactEmail", "supportMailProvider", "supportRetention", "supportAccess", "policyDate", "siteUrl")
missing = [key for key in required if not site.get(key, "").strip()]
if args.release and missing:
    parser.error("公開前に data/site.json を設定してください: " + ", ".join(missing))
if site["contactEmail"] and not re.fullmatch(r"[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+", site["contactEmail"]):
    parser.error("contactEmail の形式が正しくありません")
if site["policyDate"]:
    datetime.date.fromisoformat(site["policyDate"])
if site["siteUrl"] and (urlparse(site["siteUrl"]).scheme != "https" or not urlparse(site["siteUrl"]).netloc):
    parser.error("siteUrl は公開先の https URL を設定してください")
ids = [app["id"] for app in site["apps"]]
if not ids:
    parser.error("apps に少なくとも1件のアプリを登録してください")
if len(ids) != len(set(ids)) or any(not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) for slug in ids):
    parser.error("apps の id は重複しない英小文字・数字・ハイフンにしてください")
for app in site["apps"]:
    icon = (ROOT / app["icon"]).resolve()
    if ROOT / "assets" not in icon.parents or not icon.is_file():
        parser.error("アプリアイコンは assets 内のファイルを指定してください")
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir()
shutil.copytree(ROOT / "assets", OUT / "assets")
(OUT / ".nojekyll").touch()
routes = []


def page(route, title, description, content, active=""):
    target = OUT / route / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    def url(path=""):
        path, separator, fragment = path.partition("#")
        return E(os.path.relpath(OUT / path, target.parent)) + ("/" if not Path(path).suffix else "") + ("#" + E(fragment) if separator else "")
    # コンテンツ内リンクも各ページからの相対URLへ変換。Pagesのサブディレクトリに対応。
    content = re.sub(r'@@([^@]*)@@', lambda match: url(match[1]), content)
    nav = "".join(f'<a href="{url(path)}" {"aria-current=page" if active == key else ""}>{label}</a>' for key, label, path in [
        ("apps", "アプリ", "apps"), ("support", "サポート", "support"), ("contact", "お問い合わせ", "contact")])
    canonical = f'<link rel="canonical" href="{E(site["siteUrl"].rstrip("/") + "/" + (route + "/" if route else ""))}">' if site["siteUrl"] else ""
    banner = '<div class="draft">プレビュー版 · ポリシーの運用情報と公開URLを確認してから公開してください。</div>' if missing else ""
    doc = f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)} | {E(site['brand'])}</title><meta name="description" content="{E(description)}">
<meta name="theme-color" content="#f5f6f8"><meta property="og:title" content="{E(title)} | {E(site['brand'])}"><meta property="og:description" content="{E(description)}"><meta property="og:type" content="website">
{canonical}<link rel="icon" href="{url('assets/favicon.svg')}" type="image/svg+xml"><link rel="stylesheet" href="{url('assets/style.css')}"><link rel="stylesheet" href="{url('assets/home.css')}"><script src="{url('assets/site.js')}" defer></script></head>
<body class="{'home' if route == '' else 'inner-page'}"><a class="skip" href="#main">本文へスキップ</a>{banner}<header class="header"><a class="brand" href="{url()}"><span class="brand-mark" aria-hidden="true">t<span>·</span></span>{E(site['brand'])}<span class="brand-sub">Support Center</span></a><nav aria-label="メインナビゲーション">{nav}</nav></header>
<main id="main">{content}</main>
<footer><div><a class="footer-brand" href="{url()}">{E(site['brand'])}<span>日々に、小さな工夫を。</span></a><p>アプリの使い方や、お困りごとをサポートします。</p><a href="mailto:{E(quote(site['contactEmail'], safe='@.'))}">{E(site['contactEmail'])}</a></div><div class="footer-links"><a href="{url('apps')}">アプリ一覧</a><a href="{url('contact')}">お問い合わせ</a><a href="{url('privacy')}">プライバシーポリシー</a></div><small>© {datetime.date.today().year} {E(site['brand'])}</small></footer></body></html>'''
    target.write_text(doc, encoding="utf-8")
    routes.append(route)


def email_link(subject=""):
    email = site["contactEmail"]
    if not email:
        return '<p class="contact-pending">お問い合わせ先は公開準備中です。</p>'
    suffix = "?subject=" + quote(subject, safe="") if subject else ""
    return f'<a class="email-link" href="mailto:{E(quote(email, safe="@."))}{E(suffix)}">{E(email)} <span aria-hidden="true">↗</span></a>'


def support_management():
    fields = [("メールサービス", "supportMailProvider"), ("アクセスできる担当者", "supportAccess"), ("保管期間・削除方針", "supportRetention")]
    known = "<br>".join(f'{label}：{E(site[key])}' for label, key in fields if site[key])
    pending = [label for label, key in fields if not site[key]]
    note = '<aside class="policy-pending">公開前の確認事項：' + "、".join(pending) + 'を実際の運用に合わせて設定します。</aside>' if pending else ""
    return f'<section><h2>お問い合わせの管理</h2><p>{known}</p>{note}</section>'


def cards():
    return "".join(f'''<a class="selection-card" href="@@apps/{app['id']}/support@@" aria-label="{E(app['name'])}のサポートを見る"><img src="@@{E(app['icon'])}@@" width="96" height="96" alt=""><span class="selection-name">{E(app['name'])}</span><span class="selection-subtitle">{E(app['subtitle'])}</span><span class="selection-link">サポートを見る <span aria-hidden="true">→</span></span></a>''' for app in site["apps"])


page("", "サポートセンター", "toytoy labのアプリを選んで、使い方・FAQ・購入・プライバシーに関するサポート情報をご確認ください。", f'''
<section class="selection-hero" aria-labelledby="home-title">
  <p class="eyebrow">TOYTOY LAB SUPPORT</p>
  <h1 id="home-title">あなたのアプリを、<br class="mobile-break">もっと快適に。</h1>
  <p>ご利用中のアプリを選択して、<br class="mobile-break">サポート情報をご確認ください。</p>
  <a class="button" href="#apps">アプリを探す <span aria-hidden="true">↓</span></a>
</section>
<section class="selection-section" id="apps" aria-labelledby="apps-title">
  <div class="selection-heading"><h2 id="apps-title">アプリを選ぶ</h2><span>Applications</span></div>
  <div class="selection-grid">{cards()}
    <article class="selection-card selection-pending" aria-label="新しいアプリは準備中です">
      <span class="pending-icon" aria-hidden="true">＋</span><h3>Coming Soon</h3>
      <p>新しいアプリを追加予定</p><span class="pending-label">準備中</span>
    </article>
  </div>
</section>
<section class="home-contact" aria-labelledby="help-title"><h2 id="help-title">お困りですか？</h2><p>解決しない問題やご要望がありましたら、<br class="mobile-break">お気軽にお問い合わせください。</p><a href="@@contact@@">お問い合わせ <span aria-hidden="true">↗</span></a></section>
''')

page("apps", "アプリ一覧", "toytoy labのアプリ別サポートとプライバシーポリシー。", f'<section class="page-head"><p class="eyebrow">OUR APPS</p><h1>アプリ一覧</h1><p>アプリごとの使い方と、データの取り扱いをご確認いただけます。</p></section><section class="selection-grid app-list">{cards()}</section>', "apps")

page("support", "共通サポート", "toytoy labの全アプリ共通のお問い合わせ窓口。不具合・操作方法・ご意見・機能要望を受け付けています。", f'''
<section class="page-head"><p class="eyebrow">SUPPORT</p><h1>アプリに関するサポート</h1><p>toytoy labが提供するすべてのアプリの、ご質問・不具合報告・ご要望を受け付けています。</p></section>
<section class="contact-callout common-contact"><div><h2>共通のお問い合わせ窓口</h2>{email_link()}<p>アプリの起動や操作、購入に関する問題、内容の誤り、機能のご要望などをご連絡ください。</p></div><a class="button" href="@@contact@@">問い合わせ内容を作成 ↗</a></section>
<section class="content-section"><h2>まずお試しください</h2><div class="faqs"><details class="faq"><summary><span class="question-mark">Q</span>アプリが正常に動作しません。<span class="expand" aria-hidden="true">＋</span></summary><div class="faq-answer"><p>アプリ・端末の再起動と、App Storeでのアップデートをご確認ください。改善しない場合は、端末名、OSとアプリのバージョン、発生する操作手順を添えてお問い合わせください。端末内の記録を失う場合があるため、保存方法やバックアップを確認するまではアプリを削除しないでください。</p></div></details><details class="faq"><summary><span class="question-mark">Q</span>機種変更した場合、データを引き継げますか？<span class="expand" aria-hidden="true">＋</span></summary><div class="faq-answer"><p>保存方法や引き継ぎ手順はアプリごとに異なります。下のアプリ別サポートをご確認ください。Nutriメモは旧端末でJSONバックアップを書き出し、新しい端末で復元します。復元は全置換です。</p></div></details><details class="faq"><summary><span class="question-mark">Q</span>購入や返金について相談したいです。<span class="expand" aria-hidden="true">＋</span></summary><div class="faq-answer"><p>購入に関する操作はアプリごとの案内をご確認ください。Nutriメモは買い切りで、アプリ内購入・サブスクリプションはありません。返金は<a href="https://reportaproblem.apple.com/">Appleの返金申請ページ</a>から申請でき、可否はAppleが判断します。詳しくは<a href="https://support.apple.com/ja-jp/118223">Apple公式の返金案内</a>をご覧ください。</p></div></details></div></section>
<section class="content-section"><p class="eyebrow">APP SUPPORT</p><h2>アプリごとの使い方・FAQ</h2><div class="selection-grid">{cards()}</div></section>''', "support")

policy_links = "".join(f'<li><a href="@@apps/{app["id"]}/privacy@@">{E(app["name"])}のプライバシーポリシー <span aria-hidden="true">↗</span></a></li>' for app in site["apps"])
page("privacy", "プライバシーポリシー", "toytoy labの共通方針とアプリごとのプライバシーポリシーをご案内します。", f'''
<article class="policy"><p class="eyebrow">PRIVACY</p><h1>プライバシーポリシー</h1><p class="policy-meta">運営：{E(site['brand'])}　／　適用日：{E(site['policyDate'] or '公開前・未確定')}</p><section><h2>利用者のプライバシーを尊重します</h2><p>toytoy labは、日々の学習や生活をより便利にするiOSアプリを開発・提供しています。適用される法令および各アプリのプライバシーポリシーに従って情報を取り扱います。扱う情報・利用目的・保存方法・外部サービスの利用状況はアプリごとに異なるため、各アプリの個別ポリシーをご確認ください。</p></section><section><h2>アプリ別プライバシーポリシー</h2><ul class="policy-list">{policy_links}</ul></section><section><h2>共通のお問い合わせ窓口で扱う情報</h2><p>お問い合わせの際に受け取るメールアドレス、本文、利用者が任意で送付した情報を、回答と問題の確認に使用します。広告や追跡には利用しません。問い合わせ情報の削除を希望する場合は、同じメール窓口へお申し出ください。</p></section>{support_management()}<section><h2>本サポートサイトについて</h2><p>このサイトには広告・アクセス解析SDKや追跡Cookieを組み込んでいません。検索内容やメール下書きの入力内容はサイトからサーバーへ送信しません。利用者がメールアプリで送信した場合に、メールサービスへ渡ります。GitHub Pagesの配信に伴い、GitHubがIPアドレスなどのアクセス情報を扱う場合があります。詳しくは<a href="https://docs.github.com/ja/site-policy/privacy-policies/github-general-privacy-statement">GitHubのプライバシーに関する声明</a>をご確認ください。</p></section><section><h2>変更とお問い合わせ</h2><p>取り扱いを変更した際は本ページを更新します。必要に応じて通知や同意の取得を行います。プライバシーに関するご質問・削除依頼は次の窓口へご連絡ください。</p>{email_link('プライバシーに関するお問い合わせ')}</section></article>''')

for app in site["apps"]:
    page(f"apps/{app['id']}", app["name"], app["description"], f'''
<section class="page-head"><p class="eyebrow">OUR APPS</p><img class="overview-icon" src="@@{E(app['icon'])}@@" width="96" height="96" alt=""><h1>{E(app['name'])}<br><small>{E(app['subtitle'])}</small></h1><p>{E(app['description'])}</p><p>{E(app['platform'])}</p><a class="button" href="@@apps/{app['id']}/support@@">使い方・よくある質問 →</a></section><section class="content-section"><div class="privacy-lead"><span class="shield" aria-hidden="true">✓</span><p>{E(app['privacySummary'])}</p></div><a class="back-link" href="@@apps/{app['id']}/privacy@@">プライバシーポリシーを見る →</a></section>''', "apps")
    slug = app["id"]
    name = E(app["name"])
    categories = list(dict.fromkeys(faq["category"] for faq in app["faqs"]))
    filters = '<button class="filter active" type="button" data-filter="all" aria-pressed="true">すべて</button>' + "".join(f'<button class="filter" type="button" data-filter="{E(cat)}" aria-pressed="false">{E(cat)}</button>' for cat in categories)
    faqs = "".join(f'<details class="faq" data-category="{E(faq["category"])}"><summary><span class="question-mark">Q</span>{E(faq["q"])}<span class="expand" aria-hidden="true">＋</span></summary><div class="faq-answer"><span class="faq-category">{E(faq["category"])}</span><p>{E(faq["a"])}</p></div></details>' for faq in app["faqs"])
    steps = "".join(f'<li><span class="step-number">{i:02d}</span><h3>{E(title)}</h3><p>{E(body)}</p></li>' for i, (title, body) in enumerate(app["quickStart"], 1))
    reqs = "".join(f'<div><dt>{E(key)}</dt><dd>{E(value)}</dd></div>' for key, value in app["requirements"])
    purchases = ""
    if app.get("purchaseLinks"):
        links = "".join(f'<li><a href="{E(url)}">{E(label)} ↗</a></li>' for label, url in app["purchaseLinks"])
        purchases = f'<section class="content-section" id="purchase"><p class="eyebrow">PURCHASE SUPPORT</p><h2>購入に関する案内</h2><p>購入・再ダウンロード・返金の操作については、Apple公式の案内をご確認ください。</p><ul class="policy-list">{links}</ul></section>'
    page(f"apps/{slug}/support", f"{app['name']} サポート", app["description"], f'''
<div class="breadcrumb"><a href="@@@@">ホーム</a><span>/</span><a href="@@apps@@">アプリ</a><span>/</span>{name}</div>
<section class="product-head"><img src="@@{E(app['icon'])}@@" width="96" height="96" alt="{name}のアイコン"><div><p class="eyebrow">APP SUPPORT</p><h1>{name}<span>サポート</span></h1><p>{E(app['description'])}</p></div></section>
<div class="support-layout"><aside class="side-nav"><p>このページの内容</p><a href="#start">はじめての使い方 <span>↘</span></a><a href="#faq">よくある質問 <span>↘</span></a><a href="#requirements">対応環境 <span>↘</span></a><a href="@@apps/{slug}/privacy@@">プライバシー <span>↗</span></a><a href="@@contact@@">お問い合わせ <span>↗</span></a><div class="side-tip"><span class="status-dot"></span> 記録はあなたの端末に<p>{E(app['privacySummary'])}</p></div></aside>
<div class="support-content"><section class="content-section" id="start"><p class="eyebrow">GETTING STARTED</p><h2>まずは、ひとつ記録してみる。</h2><p>目標を設定せず、記録だけで始めることもできます。</p><ol class="steps">{steps}</ol></section>
<section class="content-section" id="faq"><p class="eyebrow">FREQUENTLY ASKED QUESTIONS</p><h2>よくある質問</h2><div class="faq-tools" hidden><label class="search"><span aria-hidden="true">⌕</span><span class="sr-only">よくある質問を検索</span><input type="search" id="faq-search" placeholder="キーワードで検索（例：バックアップ）" autocomplete="off"></label><div class="filters" role="group" aria-label="質問のカテゴリ">{filters}</div><p id="faq-result" class="result-count" role="status" aria-live="polite"></p></div><div class="faqs">{faqs}</div><p id="no-results" class="empty" hidden>一致する質問がありません。検索する言葉やカテゴリを変えるか、お問い合わせください。</p></section>
<section class="content-section" id="requirements"><p class="eyebrow">REQUIREMENTS</p><h2>対応環境</h2><dl class="requirements">{reqs}</dl><p class="small">栄養値は食品データや登録内容に基づく概算です。食品データの出典は、文部科学省「日本食品標準成分表（八訂）増補2023年」（2026年3月27日訂正反映）。本アプリは診断・治療・疾病別の栄養指導を提供しません。</p></section>
{purchases}<section class="contact-callout"><div><h2>見つからない答えは、こちらへ。</h2><p>不具合や使い方について、お問い合わせいただけます。</p>{email_link(app["name"] + "に関するお問い合わせ")}</div><a class="button" href="@@contact@@">お問い合わせ <span aria-hidden="true">↗</span></a></section></div></div>''', "support")

    policy_sections = "".join(f'<section id="policy-{i}"><h2><span>{i:02d}</span>{E(title)}</h2><p>{E(body)}</p></section>' for i, (title, body) in enumerate(app["privacy"], 1))
    policy_sections += support_management()
    policy_sections += f'<section><h2>本サポートサイトについて</h2><p>このサイトのコードには広告・アクセス解析SDK、Cookieによる追跡を組み込んでいません。FAQの検索内容やお問い合わせの入力内容を、このサイトからサーバーへ送信することはありません。メールアプリを開き、利用者が送信した場合にメールサービスへ渡ります。公開先のホスティング事業者は、サイト配信のためIPアドレスなどのアクセス情報を扱う場合があります。</p></section>'
    page(f"apps/{slug}/privacy", f"{app['name']} プライバシーポリシー", f"{app['name']}で取り扱う情報、端末内処理、バックアップと削除、お問い合わせの取り扱い。", f'''
<div class="breadcrumb"><a href="@@@@">ホーム</a><span>/</span><a href="@@apps/{slug}/support@@">{name}</a><span>/</span>プライバシー</div>
<article class="policy"><p class="eyebrow">PRIVACY POLICY</p><h1>{name}<br>プライバシーポリシー</h1><p class="policy-meta">提供者：{E(site['brand'])}　／　適用日：{E(site['policyDate'] or '公開前・未確定')}</p><div class="privacy-lead"><span class="shield" aria-hidden="true">✓</span><div><h2>あなたの記録は、あなたの端末に。</h2><p>{E(app['privacySummary'])}</p></div></div>{policy_sections}<section><h2>お問い合わせ窓口</h2><p>このポリシーに関するご質問・問い合わせ情報の削除依頼は、<a href="@@contact@@">お問い合わせ窓口</a>へご連絡ください。</p>{email_link(app["name"] + "のプライバシーに関するお問い合わせ")}</section><a class="back-link" href="@@apps/{slug}/support@@">← {name}のサポートに戻る</a></article>''')

email = site["contactEmail"]
options = "".join(f'<option value="{E(app["name"])}">{E(app["name"])}</option>' for app in site["apps"])
mail = email_link()
form = f'''<form id="contact-form" data-email="{E(email)}" hidden><div class="form-grid"><label>アプリ<select name="app">{options}<option>その他</option></select></label><label>お問い合わせの種類<select name="kind"><option>使い方について</option><option>不具合の報告</option><option>購入について</option><option>プライバシー・削除依頼</option><option>内容の誤り・機能要望</option><option>ご意見・その他</option></select></label><label>端末名 <span>任意</span><input name="device" placeholder="例：iPhone 17"></label><label>iOS / アプリバージョン <span>任意</span><input name="version" placeholder="例：iOS 27 / 1.0"></label></div><label>お問い合わせ内容<textarea name="message" rows="6" required maxlength="5000" placeholder="お困りのことや、問題が起きるまでの手順をお書きください。"></textarea></label><button class="button" type="submit">メールアプリを開く <span aria-hidden="true">↗</span></button><p class="small">入力内容をメールの下書きにします。メールアプリで確認し、送信してください。サイト上からは送信されません。</p><p id="mail-status" role="status" aria-live="polite"></p></form>''' if email else ""
page("contact", "お問い合わせ", "toytoy labのアプリに関するお問い合わせ窓口。", f'''
<section class="page-head"><p class="eyebrow">CONTACT</p><h1>お気軽に、ご相談ください。</h1><p>アプリの使い方や、不具合についてのお問い合わせはこちらへ。</p></section><div class="contact-layout"><aside class="contact-guide"><h2>お問い合わせの前に</h2><p>よくある質問で、すぐに解決できることもあります。</p><a href="@@support@@">よくある質問を見る →</a><div class="privacy-note"><h3>大切な情報は、送らずに。</h3><p>健康情報・私的な写真・バックアップ全体は不要です。パスワード、認証コード、クレジットカード番号も送らないでください。スクリーンショットを添える場合は、個人情報を隠してください。</p></div><p class="small">お問い合わせでお預かりする情報は、回答と問題の確認のために使用します。<a href="@@privacy@@">詳しい取り扱い</a></p></aside><section class="contact-panel"><p class="eyebrow">EMAIL SUPPORT</p><h2>メールでお問い合わせ</h2>{mail}<p>アプリ名・端末名・iOSとアプリのバージョン・問題の再現手順やエラーメッセージをお知らせください。内容を確認のうえ、必要に応じて返信いたします。回答までに時間をいただく場合があります。</p>{form}<noscript><p>上のメールアドレス宛に、アプリ名とご相談内容を記載してご連絡ください。</p></noscript></section></div>''', "contact")

page("404", "ページが見つかりません", "お探しのページが見つかりませんでした。", '<section class="page-head"><p class="eyebrow">404 / PAGE NOT FOUND</p><h1>お探しのページが<br>見つかりませんでした。</h1><p>ホームからアプリを選んで、もう一度ご確認ください。</p><a class="button" href="@@@@">サポートセンターへ →</a></section>')
# Pagesは404.htmlを使用。存在しないURLの深さに依存しないリンクを設定。
not_found = (OUT / "404/index.html").read_text()
base_path = urlparse(site["siteUrl"]).path.rstrip("/") if site["siteUrl"] else ""
not_found = re.sub(r'(href|src)="\.\./([^"\n]*)"', lambda m: m[1] + '="' + base_path + '/' + m[2] + '"', not_found)
(OUT / "404.html").write_text(not_found)
if site["siteUrl"]:
    base = site["siteUrl"].rstrip("/")
    entries = "".join(f'<url><loc>{E(base + "/" + (route + "/" if route else ""))}</loc></url>' for route in routes if route != "404")
    (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{entries}</urlset>')
    (OUT / "robots.txt").write_text(f'User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n')
print(f"生成完了: {len(routes)}ページ → {OUT}")
if missing:
    print("プレビュー用ビルド。公開前の設定: " + ", ".join(missing))
