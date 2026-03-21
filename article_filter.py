import openai
import anthropic
from google import genai
from google.genai import types as genai_types
import json
import re
import logging
from typing import Optional, Dict
import config

logger = logging.getLogger(__name__)


def _extract_json(text: str) -> str:
    """テキストからJSONを抽出する（マークダウンコードブロック対応）"""
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if match:
        return match.group(1)
    return text.strip()


class ArticleFilter:
    """記事がペルソナの興味に合致するかをLLMで判定するクラス"""

    def __init__(self, api_key: str, model: Optional[str] = None, provider: str = "openai"):
        self.provider = provider
        if provider == "claude":
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = model or config.CLAUDE_FILTER_MODEL
        elif provider == "gemini":
            self.client = genai.Client(api_key=api_key)
            self.model = model or config.GEMINI_FILTER_MODEL
        else:
            self.client = openai.OpenAI(api_key=api_key)
            self.model = model or config.FILTER_MODEL

    def evaluate(self, content: str, url: str = "") -> Optional[Dict]:
        """記事内容のペルソナとの関連度を判定する

        Args:
            content: 記事のテキスト内容
            url: 記事のURL（ログ用）

        Returns:
            {"score": int, "reason": str, "title": str} またはエラー時None
        """
        try:
            logger.info(f"Evaluating relevance for: {url}")

            truncated = content[:config.FILTER_CONTENT_MAX_LENGTH]
            if len(content) > config.FILTER_CONTENT_MAX_LENGTH:
                truncated += "..."

            interests_text = "\n".join(
                f"- {interest}" for interest in config.FILTER_PERSONA_INTERESTS
            )

            prompt = config.FILTER_USER_PROMPT_TEMPLATE.format(
                interests=interests_text,
                content=truncated,
            )

            if self.provider == "claude":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=512,
                    system=config.FILTER_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": prompt}],
                )
                raw = _extract_json(response.content[0].text)
            elif self.provider == "gemini":
                response = self.client.models.generate_content(
                    model=self.model,
                    config=genai_types.GenerateContentConfig(
                        system_instruction=config.FILTER_SYSTEM_PROMPT,
                        response_mime_type="application/json",
                    ),
                    contents=prompt,
                )
                raw = response.text.strip()
            else:
                response = self.client.responses.create(
                    model=self.model,
                    instructions=config.FILTER_SYSTEM_PROMPT,
                    input=prompt,
                    text={"format": {"type": "json_object"}},
                )
                raw = response.output_text.strip()

            result = json.loads(raw)

            score = int(result.get("score", 0))
            if not 1 <= score <= 5:
                logger.warning(f"Invalid score {score} for {url}, skipping")
                return None

            result["score"] = score
            logger.info(f"Relevance score for {url}: {score}/5 - {result.get('reason', '')}")
            return result

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse filter response for {url}: {e}")
            return None
        except (anthropic.APIError, openai.OpenAIError) as e:
            logger.error(f"API error during filtering for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during filtering for {url}: {e}")
            return None
