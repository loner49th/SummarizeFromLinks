import requests
from bs4 import BeautifulSoup
from typing import Optional
import logging
import re
import config

logger = logging.getLogger(__name__)


class URLScraper:
    """Webページからコンテンツを抽出するクラス"""

    def __init__(self, timeout: Optional[int] = None):
        """
        Args:
            timeout: タイムアウト時間（秒）。Noneの場合はconfig.SCRAPER_TIMEOUTを使用
        """
        self.timeout = timeout or config.SCRAPER_TIMEOUT
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.SCRAPER_USER_AGENT
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
        """URLからコンテンツを抽出

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
            for tag in soup(config.REMOVE_TAGS):
                tag.decompose()

            # メインコンテンツを抽出
            content = self._extract_main_content(soup)

            # 空白の正規化
            content = ' '.join(content.split())

            # コンテンツの長さをチェック
            if len(content) < config.CONTENT_MIN_LENGTH:
                logger.warning(f"Content too short ({len(content)} chars) for URL: {url}")
                return None

            logger.info(f"Successfully extracted {len(content)} characters from {url}")
            return content

        except requests.RequestException as e:
            logger.error(f"Request error for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            return None

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """BeautifulSoupオブジェクトからメインコンテンツを抽出

        Args:
            soup: BeautifulSoupオブジェクト

        Returns:
            抽出されたテキストコンテンツ
        """
        # セレクターを優先順位順に試行
        for selector in config.CONTENT_SELECTORS:
            elements = soup.select(selector)
            if elements:
                return ' '.join([elem.get_text(strip=True) for elem in elements])

        # メインコンテンツが見つからない場合はbody全体を使用
        body = soup.find('body')
        if body:
            return body.get_text(strip=True)

        # body も見つからない場合はすべてのテキストを返す
        return soup.get_text(strip=True)