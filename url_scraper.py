import requests
from bs4 import BeautifulSoup
from typing import Optional
import logging
import re

logger = logging.getLogger(__name__)

class URLScraper:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def parse_embed_url(self, url_line: str) -> Optional[str]:
        """
        埋め込み形式のURLから実際のURLを抽出する
        
        対応形式:
        - [https://example.com:embed:cite]
        - https://example.com
        
        Args:
            url_line: URL行（埋め込み形式または通常形式）
            
        Returns:
            抽出されたURL、無効な場合はNone
        """
        # 埋め込み形式の場合
        if ':embed:cite]' in url_line and url_line.startswith('['):
            # [URL:embed:cite] 形式からURLを抽出
            url = url_line[1:].split(':embed:cite]')[0]
            if url.startswith('http'):
                return url
        
        # 通常のURL形式かチェック
        url_pattern = r'https?://[^\s]+'
        match = re.search(url_pattern, url_line)
        
        if match:
            return match.group(0)
        
        return None
    
    def extract_content(self, url: str) -> Optional[str]:
        """
        URLからコンテンツを抽出する
        
        Args:
            url: 抽出対象のURL
            
        Returns:
            抽出されたテキストコンテンツ、エラーの場合はNone
        """
        try:
            logger.info(f"Fetching content from: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 不要なタグを削除
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                tag.decompose()
            
            # メインコンテンツを抽出
            content_selectors = [
                'article',
                'main', 
                '.content',
                '.post-content',
                '.entry-content',
                '.article-content'
            ]
            
            content = None
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content = ' '.join([elem.get_text(strip=True) for elem in elements])
                    break
            
            # メインコンテンツが見つからない場合はbody全体を使用
            if not content:
                body = soup.find('body')
                if body:
                    content = body.get_text(strip=True)
                else:
                    content = soup.get_text(strip=True)
            
            # 空白の正規化
            content = ' '.join(content.split())
            
            if len(content) < 100:
                logger.warning(f"Content too short for URL: {url}")
                return None
                
            logger.info(f"Successfully extracted {len(content)} characters from {url}")
            return content
            
        except requests.RequestException as e:
            logger.error(f"Request error for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            return None