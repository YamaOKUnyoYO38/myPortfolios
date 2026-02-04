# バックアップ: initial-release

**保存日**: 機能追加前の初回デプロイ時点  
**内容**: 配当利回りランキング取得・テーブル表示・CSVダウンロード

## 復元手順

プロジェクトルートで、このフォルダの内容を上書きコピーしてください。

```bash
# 例: Windows (PowerShell)
Copy-Item -Path backup\initial-release\src\* -Destination src\ -Recurse -Force
Copy-Item -Path backup\initial-release\requirements.txt -Destination . -Force
Copy-Item -Path backup\initial-release\Dockerfile -Destination . -Force
```

```bash
# 例: Mac / Linux
cp -r backup/initial-release/src/* src/
cp backup/initial-release/requirements.txt .
cp backup/initial-release/Dockerfile .
```
