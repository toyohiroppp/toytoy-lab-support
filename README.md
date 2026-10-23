# toytoy lab サポートサイト

Nutriメモから始める、アプリ共通のサポートセンター。静的HTMLなので、外部ライブラリのインストールやAPIキーは不要です。FAQの検索とメール下書きの作成だけブラウザ内のJavaScriptで行います。JavaScriptが無効でも原稿・FAQ・メールアドレスを閲覧できます。

問い合わせ先は `sako.business.15716@gmail.com`、メールサービスはGoogle（Gmail）に設定済みです。共通サポートの対象はtoytoy labのすべてのアプリ。今回の掲載アプリは、実装を確認できるNutriメモです。参考チャットに登場するEMT-LABは、仕様・データの取り扱いが未確認のため、このサイトには追加していません。

| ページ | パス |
| --- | --- |
| ブランドトップ | `/` |
| 共通サポート | `/support/` |
| 共通お問い合わせ | `/contact/` |
| 共通方針・アプリ別ポリシー一覧 | `/privacy/` |
| アプリ一覧 | `/apps/` |
| Nutriメモの概要 | `/apps/nutri-memo/` |
| Nutriメモの使い方・FAQ・購入案内 | `/apps/nutri-memo/support/` |
| Nutriメモのプライバシーポリシー | `/apps/nutri-memo/privacy/` |

## プレビュー

```sh
cd toytoy-lab-support
python3 scripts/build.py
python3 scripts/check.py
python3 -m http.server 4173 --directory dist --bind 127.0.0.1
```

ブラウザで http://127.0.0.1:4173/ を開きます。

## 公開前の設定

`data/site.json` の次の項目を実際の運用に合わせて設定します。未設定ならプレビューの上部に案内が出ます。GitHub Actionsの公開用ビルドは未設定を検出して停止します。

| 項目 | 設定内容 |
| --- | --- |
| `brand` | 設定済み：toytoy lab |
| `contactEmail` | 設定済み：sako.business.15716@gmail.com。受信・返信を実際に確認する |
| `supportMailProvider` | 設定済み：Google（Gmail） |
| `supportRetention` | 設定済み：対応完了後1年を目安に削除。削除依頼は共通窓口へ |
| `supportAccess` | 設定済み：toytoy labの開発者本人のみ |
| `policyDate` | 設定済み：2026-10-23 |
| `siteUrl` | 公開予定：`https://toyohiroppp.github.io/toytoy-lab-support`。実際の公開成功は別途確認 |

`siteUrl` はドメイン未決定でもプレビュー用ビルドができます。公開用ビルドでは設定が必要です。canonical・sitemap・robotsと404ページのリンクを公開先に合わせて生成します。未設定のプレビューでは独自404ページのリンクはドメイン直下を想定します。

問い合わせフォームは送信サーバーを持たず、メールアプリに下書きを開きます。利用者がメールを送信するまで問い合わせは届きません。メールアプリ未設定の場合は表示されたアドレスに直接連絡できます。返信までの日数は未確定のため約束していません。

公開する前に、メールの受信・返信、問い合わせ情報の管理方針、ポリシーの内容が実際の運用と一致していることを確認します。プライバシー原稿はアプリの現行コードと既存原稿に基づきます。アプリの仕様・SDKを変えたときは個別ポリシーも更新してください。

## GitHub Pagesへの公開

このフォルダだけを専用の `toytoy-lab-support` リポジトリのルートに配置してください。親の栄養管理アプリフォルダをそのまま公開しないでください。サイトのファイルにアプリ本体、Archive、食事データ、審査情報は含めていません。

1. GitHubにサイト専用リポジトリを作成し、このフォルダの内容を `main` にpushします。隠しフォルダ `.github` と `.gitignore` も含めます。
2. Settings → Pages → Build and deployment → Source を **GitHub Actions** にします。
3. `data/site.json` の公開前設定と `siteUrl` を設定してpushします。
4. Actionsの「Publish support site」が成功すると、GitHub Pagesの公開URLが表示されます。Sourceを後から切り替えた場合はActionsから手動実行できます。

公開URLの例（ユーザー名は実際のものに置き換え）：

```text
https://USERNAME.github.io/toytoy-lab-support/
https://USERNAME.github.io/toytoy-lab-support/apps/nutri-memo/support/
https://USERNAME.github.io/toytoy-lab-support/apps/nutri-memo/privacy/
https://USERNAME.github.io/toytoy-lab-support/contact/
```

ワークフローはビルド・内部リンク検証後、生成した `dist` だけを配信します。日常の更新はJSON・CSS・生成スクリプトの変更をpushすれば反映されます。

GitHub公式：[カスタムワークフローでのPages公開](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)。独自ドメインを使う場合はPagesのSettingsで指定し、`siteUrl` も変更してください。GitHub以外の静的ホスティングにも `dist` を配置できます。

## App Store Connectとアプリへの反映

全アプリ共通のサポートURLには `/support/` を使用できます。Nutriメモの個別サポートを直接登録する場合は `/apps/nutri-memo/support/` を使用します。プライバシーポリシーURLには `/apps/nutri-memo/privacy/` の公開済みHTTPS URLを設定します。共通の `/privacy/` はアプリ別ポリシーへの案内ページです。

アプリ側は `Nutri-stage/Nutri/Resources/ReleaseConfiguration.json` の `supportEmail`・`supportURL`・`privacyURL` に同じ値を反映します。この作業では公開URLへの配信が未完了のため、アプリ側の設定は変更していません。実際に公開・表示できたURLをストアへ登録してください。

## アプリを追加する

`data/site.json` の `apps` に既存アプリと同じ形のオブジェクトを追加し、アイコンを `assets` に置きます。

- `id` はURL用の重複しない英小文字・数字・ハイフン。
- `quickStart` は操作手順、`requirements` は対応環境、`faqs` はカテゴリ・質問・回答。
- `privacy` はアプリ固有の実際の情報処理に合わせた見出し・本文。Nutriメモの端末内処理を別アプリへ無条件に使い回さないでください。

トップ・アプリ一覧・アプリ概要・サポート・プライバシー・問い合わせの選択肢を自動生成します。ヘッダーのサポート導線は共通サポートを表示します。トップはアプリ選択専用の画面です。カード全体を選択すると、そのアプリの専用サポートへ直接移動します。「Coming Soon」はリンクのない準備中カードです。スマートフォンではカードを縦並びにします。`purchaseLinks` を設定するとアプリの購入に関する案内リンクを表示します。

## 検証

```sh
python3 scripts/build.py
python3 scripts/check.py
node --check assets/site.js
python3 scripts/build.py --release
```

最後のコマンドは連絡先・運用方針・適用日が未設定の間は失敗するのが正常です。公開前にPCとスマートフォンで表示、FAQ検索とカテゴリ切替、メール下書き、メールの受信・返信、公開URLの直接表示を確認してください。
