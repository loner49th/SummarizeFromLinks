import openai
from typing import Optional
import logging
import config

logger = logging.getLogger(__name__)


class ContentSummarizer:
    """OpenAI APIを使用してコンテンツを要約するクラス"""

    def __init__(self, api_key: str, model: Optional[str] = None):
        """
        Args:
            api_key: OpenAI APIキー
            model: 使用するモデル名。Noneの場合はconfig.SUMMARIZER_MODELを使用
        """
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model or config.SUMMARIZER_MODEL
    
    def summarize(self, content: str, url: str = "", max_tokens: Optional[int] = None) -> Optional[str]:
        """コンテンツを要約

        Args:
            content: 要約対象のコンテンツ
            url: コンテンツのURL（ログ用）
            max_tokens: 要約の最大トークン数。Noneの場合はconfig.SUMMARIZER_MAX_TOKENSを使用

        Returns:
            要約されたテキスト、エラーの場合はNone
        """
        try:
            logger.info(f"Summarizing content from: {url}")

            # コンテンツが長すぎる場合は切り詰める
            if len(content) > config.CONTENT_MAX_LENGTH:
                content = content[:config.CONTENT_MAX_LENGTH] + "..."
                logger.warning(f"Content truncated to {config.CONTENT_MAX_LENGTH} chars for {url}")

            # プロンプトを作成
            prompt = config.SUMMARIZER_USER_PROMPT_TEMPLATE.format(content=content)

            # OpenAI APIを呼び出し
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": config.SUMMARIZER_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
            )

            summary = response.choices[0].message.content.strip()
            logger.info(f"Successfully summarized content from {url}")
            return summary

        except openai.OpenAIError as e:
            logger.error(f"OpenAI API error for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during summarization for {url}: {e}")
            return None