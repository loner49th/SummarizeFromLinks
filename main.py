import os
import logging
from typing import List
from dotenv import load_dotenv
from url_scraper import URLScraper
from summarizer import ContentSummarizer

def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('summarizer.log', encoding='utf-8')
        ]
    )

def read_urls_from_file(filename: str) -> List[str]:
    """ファイルからURLリストを読み込む"""
    try:
        from url_scraper import URLScraper
        scraper = URLScraper()
        urls = []
        
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
        logging.error(f"File not found: {filename}")
        return []

def main():
    """メイン処理"""
    setup_logging()
    load_dotenv()
    
    logger = logging.getLogger(__name__)
    
    # 環境変数からAPIキーを取得
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable is not set")
        print("エラー: OPENAI_API_KEYが設定されていません。.envファイルまたは環境変数を確認してください。")
        return
    
    # URLファイルの指定
    url_file = "urls.txt"  # デフォルトファイルを使用
    
    # URLリストを読み込み
    urls = read_urls_from_file(url_file)
    if not urls:
        print(f"URLファイル '{url_file}' が見つからないか、有効なURLがありません。")
        return
    
    print(f"{len(urls)}個のURLを処理します...")
    
    # スクレイパーと要約器を初期化
    scraper = URLScraper()
    summarizer = ContentSummarizer(api_key)
    
    # 結果を保存するリスト
    results = []
    
    # 各URLを処理
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] 処理中: {url}")
        
        # コンテンツを抽出
        content = scraper.extract_content(url)
        if not content:
            print("  エラー: コンテンツの抽出に失敗しました")
            results.append({
                'url': url,
                'summary': 'エラー: コンテンツの抽出に失敗',
                'status': 'failed'
            })
            continue
        
        # 要約を生成
        summary = summarizer.summarize(content, url)
        if not summary:
            print("  エラー: 要約の生成に失敗しました")
            results.append({
                'url': url,
                'summary': 'エラー: 要約の生成に失敗',
                'status': 'failed'
            })
            continue
        
        print(f"  要約: {summary}")
        results.append({
            'url': url,
            'summary': summary,
            'status': 'success'
        })
    
    # 結果をファイルに保存
    output_file = "summaries.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("URL要約結果\n")
        f.write("=" * 50 + "\n\n")
        
        for result in results:
            f.write(f"URL: {result['url']}\n")
            f.write(f"ステータス: {result['status']}\n")
            f.write(f"要約: {result['summary']}\n")
            f.write("-" * 50 + "\n\n")
    
    print(f"\n処理完了！結果は {output_file} に保存されました。")
    
    # 統計情報を表示
    success_count = sum(1 for r in results if r['status'] == 'success')
    print(f"成功: {success_count}/{len(urls)} URLs")

if __name__ == "__main__":
    main()
