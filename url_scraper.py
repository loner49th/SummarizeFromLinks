import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict
import logging
import re
import config
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

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

    def _extract_youtube_video_id(self, url: str) -> Optional[str]:
        """
        YouTubeのURLから動画IDを抽出する

        Args:
            url: YouTube URL

        Returns:
            動画ID、抽出できない場合はNone
        """
        # youtube.com/watch?v=VIDEO_ID 形式
        match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
        if match:
            return match.group(1)

        # youtube.com/embed/VIDEO_ID 形式
        match = re.search(r'youtube\.com/embed/([a-zA-Z0-9_-]{11})', url)
        if match:
            return match.group(1)

        return None

    def _get_youtube_transcript(self, video_id: str) -> Optional[str]:
        """
        YouTube動画の字幕を取得する

        Args:
            video_id: YouTube動画ID

        Returns:
            字幕テキスト、取得できない場合はNone
        """
        try:
            # YouTubeTranscriptApiのインスタンスを作成
            ytt_api = YouTubeTranscriptApi()

            # 日本語字幕を優先的に取得、なければ英語
            try:
                fetched_transcript = ytt_api.fetch(video_id, languages=['ja', 'en'])
                logger.info(f"Found transcript for video {video_id} in {fetched_transcript.language}")
            except Exception as e:
                logger.warning(f"Failed to fetch transcript with language preference: {e}")
                # 言語指定なしで再試行
                fetched_transcript = ytt_api.fetch(video_id)
                logger.info(f"Found default transcript for video {video_id}")

            # 字幕をテキストに変換
            text = ' '.join([snippet.text for snippet in fetched_transcript])

            logger.info(f"Successfully extracted YouTube transcript for video {video_id} ({len(text)} chars)")
            return text

        except TranscriptsDisabled:
            logger.warning(f"Transcripts are disabled for video {video_id}")
            return None
        except NoTranscriptFound:
            logger.warning(f"No transcript found for video {video_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting YouTube transcript for {video_id}: {e}")
            return None
    
    def _extract_page_title_from_soup(self, soup: BeautifulSoup) -> Optional[str]:
        """BeautifulSoupオブジェクトからページタイトルを抽出

        Args:
            soup: BeautifulSoupオブジェクト

        Returns:
            ページタイトル。og:titleを優先し、なければtitleタグを使用
        """
        # og:titleを優先
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content'].strip()

        # titleタグにフォールバック
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            return title_tag.string.strip()

        return None

    def _fetch_page_title(self, url: str) -> Optional[str]:
        """URLからページタイトルのみを取得（YouTube字幕パス用）

        Args:
            url: タイトルを取得するURL

        Returns:
            ページタイトル、取得失敗時はNone
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            return self._extract_page_title_from_soup(soup)
        except Exception as e:
            logger.warning(f"Failed to fetch page title for {url}: {e}")
            return None

    def extract_content(self, url: str) -> Dict[str, Optional[str]]:
        """URLからコンテンツとページタイトルを抽出

        Args:
            url: 抽出対象のURL

        Returns:
            {"content": テキストコンテンツ, "page_title": ページタイトル}
            取得失敗時は各値がNone
        """
        try:
            logger.info(f"Fetching content from: {url}")

            # YouTubeのURLの場合は字幕を取得
            video_id = self._extract_youtube_video_id(url)
            if video_id:
                logger.info(f"Detected YouTube URL, extracting transcript for video {video_id}")
                transcript = self._get_youtube_transcript(video_id)
                if transcript:
                    # 字幕取得成功時もページタイトルを取得
                    page_title = self._fetch_page_title(url)
                    return {"content": transcript, "page_title": page_title}
                else:
                    logger.warning(f"Failed to get transcript for YouTube video {video_id}, falling back to HTML scraping")

            # 通常のWebページのスクレイピング
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # ページタイトルを抽出（タグ削除前に実施）
            page_title = self._extract_page_title_from_soup(soup)

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
                return {"content": None, "page_title": page_title}

            logger.info(f"Successfully extracted {len(content)} characters from {url}")
            return {"content": content, "page_title": page_title}

        except requests.RequestException as e:
            logger.error(f"Request error for {url}: {e}")
            return {"content": None, "page_title": None}
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            return {"content": None, "page_title": None}

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