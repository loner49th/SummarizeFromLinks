import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv
from url_scraper import URLScraper
from summarizer import ContentSummarizer
from article_filter import ArticleFilter
from main import setup_console_encoding, read_urls_from_file
import config


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


def save_filtered_results(results, output_file: str):
    """フィルタリング結果をMarkdownファイルに保存

    Args:
        results: フィルタリング済みの結果リスト
        output_file: 出力ファイルパス
    """
    total_urls = results["total"]
    filtered = results["filtered"]

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# ペルソナ向け記事抽出結果\n\n")
        f.write(f"抽出日: {datetime.now().strftime('%Y-%m-%d')}\n\n")
        f.write(f"対象URL数: {total_urls} / フィルタ通過: {len(filtered)}")
        f.write(f" (閾値: {config.FILTER_SCORE_THRESHOLD}/5以上)\n\n")

        # ペルソナの興味リストを表示
        f.write("## 対象ペルソナの興味・関心\n\n")
        for interest in config.FILTER_PERSONA_INTERESTS:
            f.write(f"- {interest}\n")
        f.write("\n---\n\n")

        for i, item in enumerate(filtered, 1):
            title = item.get("title", "タイトル不明")
            url = item["url"]
            score = item["score"]
            reason = item.get("reason", "")
            summary = item.get("summary", "")

            # 星表示を生成
            stars = "★" * score + "☆" * (5 - score)

            f.write(f"## {i}. [{title}]({url})\n\n")
            f.write(f"**関連度**: {stars} ({score}/5)\n\n")
            f.write(f"**関連理由**: {reason}\n\n")

            if summary:
                f.write(f"### 要約\n\n{summary}\n\n")

            f.write("---\n\n")


def main():
    """メイン処理: URL読み込み → フィルタリング → 要約 → 出力"""
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
    urls = read_urls_from_file(config.FILTER_URL_FILE)
    if not urls:
        print(f"URLファイル '{config.FILTER_URL_FILE}' が見つからないか、有効なURLがありません。")
        return

    print(f"{len(urls)}個のURLを処理します...")
    print(f"フィルタ閾値: {config.FILTER_SCORE_THRESHOLD}/5以上\n")

    scraper = URLScraper()
    article_filter = ArticleFilter(api_key, provider=provider)
    summarizer = ContentSummarizer(api_key, provider=provider)

    filtered_articles = []

    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] スクレイピング中: {url}")

        # Step 1: コンテンツとページタイトルを取得
        scraped = scraper.extract_content(url)
        content = scraped["content"]
        page_title = scraped["page_title"]

        if not content:
            print(f"  ✗ コンテンツ取得失敗、スキップ")
            continue

        # Step 2: 関連性を判定
        print(f"  → 関連性を判定中...")
        evaluation = article_filter.evaluate(content, url)
        if not evaluation:
            print(f"  ✗ 関連性判定失敗、スキップ")
            continue

        score = evaluation["score"]
        reason = evaluation.get("reason", "")
        # タイトルはHTMLから取得した値を優先し、取得できなかった場合はLLM推定値を使用
        title = page_title or evaluation.get("title", "タイトル不明")

        if score < config.FILTER_SCORE_THRESHOLD:
            print(f"  → スコア {score}/5 (関連度不足) - {title}")
            continue

        print(f"  ✓ スコア {score}/5 - {title}")
        print(f"    理由: {reason}")

        # Step 3: 関連記事のみ要約
        print(f"  → 要約を生成中...")
        summary = summarizer.summarize(content, url, page_title=page_title)
        if not summary:
            print(f"  ✗ 要約生成失敗")
            summary = ""

        filtered_articles.append({
            "url": url,
            "title": title,
            "score": score,
            "reason": reason,
            "summary": summary,
        })

    # 結果を保存
    results = {
        "total": len(urls),
        "filtered": filtered_articles,
    }

    date_str = datetime.now().strftime('%Y%m%d')
    output_file = config.FILTER_OUTPUT_PATTERN.format(date=date_str)
    save_filtered_results(results, output_file)

    print(f"\n{'=' * 50}")
    print(f"処理完了！")
    print(f"  対象URL数: {len(urls)}")
    print(f"  フィルタ通過: {len(filtered_articles)}")
    print(f"  結果ファイル: {output_file}")


if __name__ == "__main__":
    main()
