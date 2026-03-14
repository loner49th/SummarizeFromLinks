import os
import sys
import logging
import shutil
from typing import List, Dict
from datetime import datetime
from dotenv import load_dotenv
from url_scraper import URLScraper
from summarizer import ContentSummarizer
from article_filter import ArticleFilter
import config


def setup_console_encoding():
    """コンソール出力のエンコーディングをUTF-8に設定（Windows対策）"""
    if sys.platform == 'win32':
        try:
            # 標準出力をUTF-8に設定
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except AttributeError:
            # Python 3.7未満の場合の対応
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format=config.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(config.DEFAULT_LOG_FILE, encoding=config.LOG_ENCODING)
        ]
    )

def read_urls_from_file(filename: str) -> List[str]:
    """ファイルからURLリストを読み込む

    Args:
        filename: URLリストファイルのパス

    Returns:
        URLのリスト
    """
    logger = logging.getLogger(__name__)
    scraper = URLScraper()
    urls = []

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # 埋め込み形式のURLを解析
                url = scraper.parse_embed_url(line)
                if url:
                    urls.append(url)

        return urls
    except FileNotFoundError:
        logger.error(f"File not found: {filename}")
        return []
    except Exception as e:
        logger.error(f"Error reading file {filename}: {e}")
        return []


def process_url(url: str, scraper: URLScraper, summarizer: ContentSummarizer, article_filter: ArticleFilter) -> Dict[str, str]:
    """単一のURLを処理して要約を生成

    Args:
        url: 処理対象のURL
        scraper: URLScraperインスタンス
        summarizer: ContentSummarizerインスタンス
        article_filter: ArticleFilterインスタンス

    Returns:
        処理結果の辞書（url, summary, status, score, reason, page_title）
    """
    # コンテンツとページタイトルを抽出
    result = scraper.extract_content(url)
    content = result["content"]
    page_title = result["page_title"]

    if not content:
        return {
            'url': url,
            'summary': 'エラー: コンテンツの抽出に失敗',
            'status': 'failed',
            'score': None,
            'reason': None,
            'page_title': page_title,
        }

    # ペルソナとの関連度を判定
    evaluation = article_filter.evaluate(content, url)
    score = evaluation["score"] if evaluation else None
    reason = evaluation.get("reason", "") if evaluation else None

    # 要約を生成
    summary = summarizer.summarize(content, url, page_title=page_title)
    if not summary:
        return {
            'url': url,
            'summary': 'エラー: 要約の生成に失敗',
            'status': 'failed',
            'score': score,
            'reason': reason,
            'page_title': page_title,
        }

    return {
        'url': url,
        'summary': summary,
        'status': 'success',
        'score': score,
        'reason': reason,
        'page_title': page_title,
    }


def save_results(results: List[Dict[str, str]], output_file: str):
    """結果をファイルに保存

    Args:
        results: 処理結果のリスト
        output_file: 出力ファイルパス
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("URL要約結果\n")
        f.write("=" * 50 + "\n\n")

        for result in results:
            f.write(f"URL: {result['url']}\n")
            f.write(f"ステータス: {result['status']}\n")
            score = result.get('score')
            if score is not None:
                stars = "★" * score + "☆" * (5 - score)
                reason = result.get('reason') or ""
                f.write(f"おすすめ度: {stars} ({score}/5)")
                if reason:
                    f.write(f" - {reason}")
                f.write("\n")
            f.write(f"要約: {result['summary']}\n")
            f.write("-" * 50 + "\n\n")

def main():
    """メイン処理"""
    # コンソールのエンコーディングをUTF-8に設定
    setup_console_encoding()
    setup_logging()
    load_dotenv()

    logger = logging.getLogger(__name__)

    # 使用するAIプロバイダーを決定（デフォルト: openai）
    provider = os.getenv('AI_PROVIDER', 'openai').lower()
    if provider == 'claude':
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            logger.error("ANTHROPIC_API_KEY environment variable is not set")
            print("エラー: ANTHROPIC_API_KEYが設定されていません。.envファイルまたは環境変数を確認してください。")
            return
    elif provider == 'gemini':
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            logger.error("GEMINI_API_KEY environment variable is not set")
            print("エラー: GEMINI_API_KEYが設定されていません。.envファイルまたは環境変数を確認してください。")
            return
    else:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("OPENAI_API_KEY environment variable is not set")
            print("エラー: OPENAI_API_KEYが設定されていません。.envファイルまたは環境変数を確認してください。")
            return

    print(f"AIプロバイダー: {provider}")

    # URLリストを読み込み
    urls = read_urls_from_file(config.DEFAULT_URL_FILE)
    if not urls:
        print(f"URLファイル '{config.DEFAULT_URL_FILE}' が見つからないか、有効なURLがありません。")
        return

    print(f"{len(urls)}個のURLを処理します...")

    # スクレイパー・フィルター・要約器を初期化
    scraper = URLScraper()
    article_filter = ArticleFilter(api_key, provider=provider)
    summarizer = ContentSummarizer(api_key, provider=provider)

    # 各URLを処理
    results = []
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] 処理中: {url}")

        result = process_url(url, scraper, summarizer, article_filter)
        results.append(result)

        # 処理結果を表示
        if result['status'] == 'success':
            print(f"  ✓ 要約完了")
            # 要約の最初の100文字だけを表示
            summary_preview = result['summary'][:100] + "..." if len(result['summary']) > 100 else result['summary']
            print(f"  {summary_preview}")
        else:
            print(f"  ✗ {result['summary']}")

    # 結果をファイルに保存（日付付きファイル名を生成）
    date_str = datetime.now().strftime('%Y%m%d')
    output_filename = f"{date_str}summaries.md"
    save_results(results, output_filename)
    print(f"\n処理完了！結果は {output_filename} に保存されました。")

    # コピー先フォルダへコピー（上書き禁止）
    if config.COPY_DEST_DIR:
        dest_path = os.path.join(config.COPY_DEST_DIR, output_filename)
        if os.path.exists(dest_path):
            print(f"コピーをスキップ: {dest_path} は既に存在します。")
        else:
            try:
                shutil.copy(output_filename, dest_path)
                print(f"コピー先フォルダへコピーしました: {dest_path}")
            except Exception as e:
                logger.error(f"コピーに失敗しました: {e}")
                print(f"コピーに失敗しました: {e}")

    # 統計情報を表示
    success_count = sum(1 for r in results if r['status'] == 'success')
    failed_count = len(results) - success_count
    print(f"\n統計:")
    print(f"  成功: {success_count}/{len(urls)} URLs")
    if failed_count > 0:
        print(f"  失敗: {failed_count}/{len(urls)} URLs")

if __name__ == "__main__":
    main()
