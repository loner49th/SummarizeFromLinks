"""
アプリケーション設定
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
    '.content',
    '.post-content',
    '.entry-content',
    '.article-content'
]

# 削除するHTMLタグ
REMOVE_TAGS = ['script', 'style', 'nav', 'header', 'footer', 'aside']

# 要約設定
SUMMARIZER_MODEL = "gpt-5-mini-2025-08-07"  # 使用するモデル
SUMMARIZER_MAX_TOKENS = 300  # 最大トークン数

# 要約プロンプトテンプレート
SUMMARIZER_SYSTEM_PROMPT = "あなたはサマリーアシスタントは、日本語で文書を的確に要約することに特化したAIです。"

SUMMARIZER_USER_PROMPT_TEMPLATE = """以下のWebページの内容を日本語で簡潔に要約してください。
入力が英語であっても、日本語で丁寧かつ正確に要約を行います。文体はフォーマルで、必要に応じて引用を行います。学術論文、ニュース記事、ビジネスレポートなど、さまざまな文書タイプに対応し、それぞれに適したスタイルで構造的な要約を提供します。

論文の場合の要約の基本構成は以下の通りです：
タイトル、著者情報、目的、方法、結果、結論。
文書の形式がこれと異なる場合は、より適切な構成に調整します。不明確な依頼には追加の情報を求め、正確な要約ができるよう努めます。
常に丁寧で敬意ある日本語表現を使用し、ユーザーとの円滑な対話を重視します。

読みやすくなるように強調すべき点などを強調してください

さらに、要約後には「生成AIを活用して業務効率を高めたい担当者が次に検討すべきこと」を一文で提案します。

内容:
{content}"""

# ファイルパス
DEFAULT_URL_FILE = "urls.txt"
DEFAULT_OUTPUT_FILE = "summaries.txt"
DEFAULT_LOG_FILE = "summarizer.log"

# ログ設定
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_ENCODING = 'utf-8'
