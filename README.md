# SummarizeFromLinks

URLリストからコンテンツを自動取得し、OpenAI APIを使用して日本語で要約するツールです。ペルソナの興味に基づく記事フィルタリング機能も備えています。

## 機能

- URLリストからの一括コンテンツ取得
- OpenAI gpt-4o-miniを使用した構造化日本語要約
- 埋め込み形式URL（`[URL:embed:cite]`形式）のサポート
- YouTube動画の字幕取得対応
- ペルソナベースの記事フィルタリング（関連度スコアリング）
- 結果の自動保存（Markdownファイル）
- 詳細なログ出力

## 必要要件

- Python 3.13以上
- OpenAI APIキー
- インターネット接続

## インストール

このプロジェクトは [uv](https://github.com/astral-sh/uv) を使用しています。

1. リポジトリをクローン：
```bash
git clone <repository-url>
cd SummarizeFromLinks
```

2. 依存関係のインストール：
```bash
uv sync
```

## セットアップ

1. `.env`ファイルを作成：
```bash
cp .env.example .env
```

2. `.env`ファイルにOpenAI APIキーを設定：
```
OPENAI_API_KEY=your_actual_api_key_here
```

3. `config.py`を作成：
```bash
cp config.example.py config.py
```

4. `config.py`を編集してペルソナの興味・関心をカスタマイズ：
```python
FILTER_PERSONA_INTERESTS = [
    "生成AIを活用したエージェントの開発",
    # 自分の興味・関心を追加
]
```

5. `urls.txt`ファイルを作成し、要約したいURLを1行に1つずつ記載：
```
https://example.com/article1
https://example.com/article2
[https://example.com/article3:embed:cite]
```

## 使い方

### 全件要約（フィルタなし）

```bash
uv run python main.py
```

`urls.txt`のすべてのURLを要約し、`{YYYYMMDD}summaries.md`に保存します。

### ペルソナフィルタリング付き要約

```bash
uv run python filter_main.py
```

`filter_urls.txt`のURLを読み込み、ペルソナの興味との関連度を判定してから、スコア閾値以上の記事のみ要約します。結果は`{YYYYMMDD}filtered.md`に保存されます。

### Windows環境での実行（推奨）

Windows環境では、コンソールの文字エンコーディングの問題を回避するため、以下のいずれかの方法で実行してください：

#### 方法1: 環境変数を設定（推奨）
```cmd
set PYTHONUTF8=1
uv run python main.py
```

#### 方法2: コンソールのコードページを変更
```cmd
chcp 65001
uv run python main.py
```

#### 方法3: PowerShellでの実行
```powershell
$env:PYTHONUTF8=1
uv run python main.py
```

## 出力ファイル

- `{YYYYMMDD}summaries.md` - 全件要約の結果
- `{YYYYMMDD}filtered.md` - フィルタリング済み要約の結果
- `summarizer.log` - 実行ログ

## ファイル構成

```
.
├── main.py              # 全件要約のエントリポイント
├── filter_main.py       # フィルタリング付き要約のエントリポイント
├── url_scraper.py       # URLスクレイピング機能
├── summarizer.py        # OpenAI API要約機能
├── article_filter.py    # ペルソナベースフィルタリング機能
├── config.example.py    # 設定ファイルのサンプル
├── config.py            # 実際の設定ファイル（config.example.pyからコピーして作成）
├── urls.txt             # 全件要約用URLリスト
├── filter_urls.txt      # フィルタリング用URLリスト
├── .env                 # 環境変数（APIキー等）
├── .env.example         # 環境変数のテンプレート
├── summarizer.log       # 実行ログ（生成される）
├── pyproject.toml       # プロジェクト設定
└── README.md            # このファイル
```

## 要約形式

要約には以下の情報が含まれます：

- **記事情報**：タイトル・出典/媒体・公開日・主題
- **要約（全体像）**：記事全体の俯瞰
- **背景・問題意識**：筆者が扱う課題や前提
- **主要論点**：2〜5個の論点を箇条書きで整理
- **結論**：筆者の主張・示唆
- **強調すべき要点**：読みどころ
- **次に検討すべきこと**：生成AI活用の次アクション提案

## トラブルシューティング

### UnicodeEncodeError が発生する

**問題**：
```
UnicodeEncodeError: 'cp932' codec can't encode character '—' in position ...
```

**解決方法**：
上記の「Windows環境での実行」セクションを参照し、`PYTHONUTF8=1`環境変数を設定してください。

### OpenAI APIエラー

**問題**：APIキー関連のエラー

**解決方法**：
1. `.env`ファイルが存在し、正しいAPIキーが設定されているか確認
2. APIキーに課金設定がされているか確認
3. APIの利用制限に達していないか確認

### コンテンツの抽出に失敗する

**問題**：特定のURLでコンテンツが取得できない

**解決方法**：
1. URLが正しいか確認
2. Webサイトがアクセス制限をしていないか確認
3. `summarizer.log`でエラー詳細を確認

## ライセンス

このプロジェクトのライセンスは未定です。

## 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずissueを開いて変更内容を議論してください。
