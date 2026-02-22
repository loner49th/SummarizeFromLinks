"""
アプリケーション設定サンプル
このファイルをコピーして config.py として使用してください。
"""

# URLスクレイパー設定
SCRAPER_TIMEOUT = 30  # タイムアウト（秒）
SCRAPER_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# コンテンツ抽出設定
CONTENT_MIN_LENGTH = 100  # コンテンツの最小文字数
CONTENT_MAX_LENGTH = 100000  # 要約に送信する最大文字数

# コンテンツセレクター（優先順位順）
CONTENT_SELECTORS = [
    'article',
    'main',
    '.sd-main',
    '.content',
    '.post-content',
    '.entry-content',
    '.article-content'
]

# 削除するHTMLタグ
REMOVE_TAGS = ['script', 'style', 'nav', 'header', 'footer', 'aside']

# 要約設定
SUMMARIZER_MODEL = "gpt-4o-mini"  # 使用するモデル
SUMMARIZER_MAX_TOKENS = 300  # 最大トークン数

# 要約プロンプトテンプレート
SUMMARIZER_SYSTEM_PROMPT = "あなたはサマリーアシスタントは、日本語で文書を的確に要約することに特化したAIです。"

SUMMARIZER_USER_PROMPT_TEMPLATE = """
あなたは「サマリーアシスタント」です。以下の文章（記事/資料/メモ）を、指定フォーマットで日本語要約してください。
入力が英語でも、出力は必ず日本語で、丁寧かつフォーマルな文体にしてください。
読みやすさのため、重要語句は **太字** で強調してください。
必要に応じて、本文から短い引用（最大25語相当まで）を「」で示して構いません（引用は最小限）。
※タイトルはHTMLから自動取得済みです。提供されたタイトルをそのまま使用し、変更しないでください。

# 要約の出力フォーマット（この見出し構成を厳守）

## 記事情報（要約対象）
- **タイトル**：{page_title}
- **出典/媒体**：
- **公開日/更新日**：
- **主題**：（80文字程度で記述）

---

## 要約（全体像）
（2〜5文で、記事全体が何を主張し何を伝えたいかを俯瞰してまとめる）

---

## 背景・問題意識
（筆者/文書が扱う課題、前提、なぜ今それが重要か）

---

## 主要論点（必要に応じて分割）
### 1) （論点タイトル）
- （要点）
- （要点）
- （必要なら短い引用：「…」）

### 2) （論点タイトル）
- （要点）
- （要点）

（※論点は2〜5個程度。内容に応じて増減可）

---

## 結論（筆者の主張・示唆）
（筆者/文書が最終的に言いたいこと、提案、示唆を簡潔に整理）

---

## 強調すべき要点（読みどころ）
- **（重要ポイント）**
- **（重要ポイント）**
- **（重要ポイント）**

---

## 生成AIを活用して業務効率を高めたい担当者が次に検討すべきこと（1文）
（上の要約内容を踏まえ、業務適用の次アクションを具体的に1文で提案する。句点まで1文厳守）

# 入力テキスト
{content}"""

# ファイルパス
DEFAULT_URL_FILE = "urls.txt"
FILTER_URL_FILE = "filter_urls.txt"
DEFAULT_OUTPUT_FILE = "summaries.md"
DEFAULT_LOG_FILE = "summarizer.log"

# コピー先フォルダ（Noneの場合はコピーしない）
# 例: r"C:\Users\yourname\OneDrive\Documents\summaries"
COPY_DEST_DIR = None

# ログ設定
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_ENCODING = 'utf-8'

# ========================================
# 記事フィルタリング設定
# ========================================

# ペルソナの興味・関心リスト（自分の興味に合わせて編集してください）
FILTER_PERSONA_INTERESTS = [
    "生成AIを活用したエージェントの開発",
    "OpenAI・Anthropic・Google（Gemini）のフロンティアモデルの最新動向・新機能・API変更",
    # 他の興味・関心を追加してください
]

# フィルタリングのスコア閾値（1-5、この値以上を抽出）
FILTER_SCORE_THRESHOLD = 3

# フィルタリング用モデル（軽量モデルでコスト削減）
FILTER_MODEL = "gpt-4o-mini"

# フィルタリング用システムプロンプト
FILTER_SYSTEM_PROMPT = "あなたは記事の関連性を判定するアシスタントです。必ずJSON形式で回答してください。"

# フィルタリング用プロンプトテンプレート
FILTER_USER_PROMPT_TEMPLATE = """以下の記事内容が、指定されたペルソナの興味・関心にどの程度関連するかを判定してください。

# ペルソナの興味・関心
{interests}

# 記事内容（冒頭部分）
{content}

# 回答形式（JSON厳守）
以下のJSON形式で回答してください。JSON以外のテキストは含めないでください。
{{
  "score": <1-5の整数。1=無関係、3=やや関連、5=非常に関連>,
  "reason": "<日本語で関連性の理由を1-2文で>",
  "title": "<記事のタイトル>"
}}"""

# フィルタリング結果の出力ファイル名パターン
FILTER_OUTPUT_PATTERN = "{date}filtered.md"

# フィルタリング時に送信するコンテンツの最大文字数（コスト削減のため短め）
FILTER_CONTENT_MAX_LENGTH = 5000
