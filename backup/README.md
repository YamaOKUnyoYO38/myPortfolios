# バックアップ用フォルダ

このフォルダには、機能追加前の **High-Dividend Hunter** の状態を保存しています。

## 含まれるフォルダ

| フォルダ | 内容 |
|----------|------|
| **initial-release/** | 初回デプロイ時点のアプリ（配当利回りランキング取得・テーブル表示・CSVダウンロード） |
| **restore-instructions/** | 復元するときのプロンプト（手順）をまとめたテキストファイル |

## 復元方法

`restore-instructions/復元するときのプロンプト.txt` に、コピー＆ペーストで使える復元用コマンドを記載しています。

`initial-release/` の内容をプロジェクトルートに上書きコピーすると、この時点の状態に戻せます。

- `backup/initial-release/src/` → `src/`
- `backup/initial-release/requirements.txt` → `requirements.txt`
- `backup/initial-release/Dockerfile` → `Dockerfile`

新しいバックアップを追加する場合は、日付やバージョン名のフォルダ（例: `20250204-baseline/`）を作成し、同様の構成で保存してください。
