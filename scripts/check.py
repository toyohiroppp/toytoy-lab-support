#!/usr/bin/env python3
"""生成された全ページのリンク・画像・フラグメントを実ファイルと照合。"""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

OUT = Path(__file__).resolve().parents[1] / 'dist'


class Document(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.links = []
        self.ids = set()
        self.feed(path.read_text())

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if attrs.get('id'):
            self.ids.add(attrs['id'])
        for key in ('href', 'src'):
            if key in attrs:
                self.links.append(attrs[key])


docs = {path: Document(path) for path in OUT.rglob('*.html')}
assert docs, '先に scripts/build.py を実行してください'
errors = []
count = 0
for path, doc in docs.items():
    if '@@' in path.read_text():
        errors.append(f'{path}: 未解決のテンプレート')
    for link in doc.links:
        url = urlsplit(link)
        if url.scheme or url.netloc:
            continue
        count += 1
        target = (OUT / unquote(url.path).lstrip('/') if url.path.startswith('/') else path.parent / unquote(url.path)).resolve() if url.path else path
        if target.is_dir():
            target /= 'index.html'
        # 404.html は公開URLのサブパスを使用するため、別途本番URLで確認する。
        if path == OUT / '404.html' and url.path.startswith('/'):
            continue
        if not target.is_relative_to(OUT) or not target.is_file():
            errors.append(f'{path.relative_to(OUT)}: 見つからないリンク {link}')
        elif url.fragment and target in docs and unquote(url.fragment) not in docs[target].ids:
            errors.append(f'{path.relative_to(OUT)}: 見つからないアンカー {link}')
if errors:
    raise SystemExit('\n'.join(errors))
print(f'検証成功: {len(docs)} HTML / {count} 内部参照。リンク・画像・アンカーの欠損なし。')
