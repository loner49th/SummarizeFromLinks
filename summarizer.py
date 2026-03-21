import openai
import anthropic
from google import genai
from google.genai import types as genai_types
from typing import Optional
import logging
import config

logger = logging.getLogger(__name__)


class ContentSummarizer:
    """OpenAI、Claude、または Gemini API を使用してコンテンツを要約するクラス"""

    def __init__(self, api_key: str, model: Optional[str] = None, provider: str = "openai"):
        """
        Args:
            api_key: APIキー
            model: 使用するモデル名。Noneの場合はconfigのデフォルトを使用
            provider: "openai"、"claude"、または "gemini"
        """
        self.provider = provider
        if provider == "claude":
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = model or config.CLAUDE_SUMMARIZER_MODEL
        elif provider == "gemini":
            self.client = genai.Client(api_key=api_key)
            self.model = model or config.GEMINI_SUMMARIZER_MODEL
        else:
            self.client = openai.OpenAI(api_key=api_key)
            self.model = model or config.SUMMARIZER_MODEL

    def summarize(self, content: str, url: str = "", page_title: Optional[str] = None, max_tokens: Optional[int] = None) -> Optional[str]:
        """コンテンツを要約

        Args:
            content: 要約対象のコンテンツ
            url: コンテンツのURL（ログ用）
            page_title: HTMLから取得したページタイトル。Noneの場合はLLMが推測
            max_tokens: 要約の最大トークン数。Noneの場合はconfigのデフォルトを使用

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
            prompt = config.SUMMARIZER_USER_PROMPT_TEMPLATE.format(
                content=content,
                page_title=page_title if page_title else "",
            )

            if self.provider == "claude":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens or config.SUMMARIZER_MAX_TOKENS * 10,
                    system=config.SUMMARIZER_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": prompt}],
                )
                summary = response.content[0].text.strip()
            elif self.provider == "gemini":
                response = self.client.models.generate_content(
                    model=self.model,
                    config=genai_types.GenerateContentConfig(
                        system_instruction=config.SUMMARIZER_SYSTEM_PROMPT,
                    ),
                    contents=prompt,
                )
                summary = response.text.strip()
            else:
                response = self.client.responses.create(
                    model=self.model,
                    instructions=config.SUMMARIZER_SYSTEM_PROMPT,
                    input=prompt,
                )
                summary = response.output_text.strip()

            logger.info(f"Successfully summarized content from {url}")
            return summary

        except (anthropic.APIError, openai.OpenAIError) as e:
            logger.error(f"API error for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during summarization for {url}: {e}")
            return None
