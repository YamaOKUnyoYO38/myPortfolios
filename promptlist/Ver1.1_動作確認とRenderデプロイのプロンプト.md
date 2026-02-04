# High-Dividend Hunter Ver.1.1 — 動作確認と Render デプロイ用プロンプト

以下をそのままコピーして、ターミナルまたは AI に貼り付けて実行できます。

---

## 1. 動作確認手順（ローカルで実行）

プロジェクトルートで次を順に実行してください。

```bash
cd "c:\Users\Kape7\Desktop\Cursor_projects\High-Dividend Hunter"
pip install -r requirements.txt
streamlit run src/app.py
```

ブラウザで http://localhost:8501 を開き、次を確認してください。

- **ランキング取得**: サイト名で選ぶ / URL入力 → 取得件数 1〜999 → 「ランキングを取得」→ テーブル表示・CSVダウンロード
- **条件で絞り込み**: 「条件で絞り込み」を開き、配当利回り・決算年月などで絞り込みができること
- **ポートフォリオ**: サイドバー「ポートフォリオ」→ 新規リスト作成・編集・削除ができること
- **リストに保存**: ランキング取得後、「リストに保存」で銘柄と追加先ポートフォリオを選んで追加できること

確認後、Streamlit は Ctrl+C で停止してください。

---

## 2. Ver.1.1 としてタグ付けし、main をプッシュする

動作確認が問題なければ、以下でバージョンタグを打ち、リモートに反映します。

```bash
cd "c:\Users\Kape7\Desktop\Cursor_projects\High-Dividend Hunter"
git tag -a v1.1 -m "High-Dividend Hunter Ver.1.1 (機能5件追加)"
git push origin main
git push origin v1.1
```

---

## 3. Render でデプロイして使用できる状態にする（コピー用プロンプト）

以下を **人または AI への依頼文** としてそのままコピーして使えます。

```
【依頼】
アプリ「High-Dividend Hunter」を Ver.1.1 として Render でデプロイし、使用できる状態にしてください。

【前提】
- リポジトリは GitHub にあり、Render と連携済み（YamaOKUnyoYO38/myPortfolios または当該リポジトリ）
- main ブランチに 5 機能（取得件数指定・サイト名取得・条件絞り込み・ポートフォリオ・リストに保存）がマージ済み

【手順】
1. 上記「1. 動作確認手順」を実行し、ローカルでアプリが正常に動くことを確認する。
2. 問題なければ「2. Ver.1.1 としてタグ付けし、main をプッシュする」のコマンドを実行する。
3. Render のダッシュボードで、対象 Web サービスが main のプッシュにより自動デプロイされることを確認する（Auto-Deploy が On の場合）。
4. デプロイが成功したら、表示された URL（例: https://xxxx.onrender.com）で以下を確認する。
   - ランキング取得（サイト名・URL・件数指定）
   - 条件で絞り込み
   - ポートフォリオページでのリスト作成・編集・削除
   - ランキング結果から「リストに保存」でポートフォリオに追加
5. 以上が問題なければ、「High-Dividend Hunter Ver.1.1 が Render で使用できる状態になった」と報告する。

【補足】
- ポートフォリオデータは data/portfolios.json に保存される。Render の無料プランでは再デプロイでデータはリセットされる可能性がある。
- エラーや不具合があれば直ちに修正し、再度デプロイして確認する。
```

---

## 4. 自分で実行する場合のチェックリスト（コピー用）

```
□ 1. cd でプロジェクトフォルダに移動
□ 2. pip install -r requirements.txt
□ 3. streamlit run src/app.py で起動
□ 4. ブラウザでランキング取得・絞り込み・ポートフォリオ・リストに保存を確認
□ 5. git tag -a v1.1 -m "High-Dividend Hunter Ver.1.1 (機能5件追加)"
□ 6. git push origin main && git push origin v1.1
□ 7. Render ダッシュボードでデプロイ完了を確認
□ 8. 本番URLで同様の動作確認
```

---

## 5. コマンドのみまとめ（一括コピー用）

```bash
cd "c:\Users\Kape7\Desktop\Cursor_projects\High-Dividend Hunter"
pip install -r requirements.txt
streamlit run src/app.py
# 動作確認後 Ctrl+C で停止し、以下を実行
git tag -a v1.1 -m "High-Dividend Hunter Ver.1.1 (機能5件追加)"
git push origin main
git push origin v1.1
```

Render は main へのプッシュで自動デプロイされるため、上記のあとダッシュボードでビルド・デプロイの完了を確認すれば Ver.1.1 が利用可能です。
