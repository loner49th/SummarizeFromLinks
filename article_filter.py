import openai
import json
import logging
from typing import Optional, Dict
import config

logger = logging.getLogger(__name__)


class ArticleFilter:
    """記事がペルソナの興味に合致するかをLLMで判定するクラス"""

    def __init__(self, api_key: str, model: Optional[str] = None):
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

            # コンテンツを切り詰め（フィルタリングは冒頭部分で十分）
            truncated = content[:config.FILTER_CONTENT_MAX_LENGTH]
            if len(content) > config.FILTER_CONTENT_MAX_LENGTH:
                truncated += "..."

            # ペルソナの興味リストを文字列化
            interests_text = "\n".join(
                f"- {interest}" for interest in config.FILTER_PERSONA_INTERESTS
            )

            prompt = config.FILTER_USER_PROMPT_TEMPLATE.format(
                interests=interests_text,
                content=truncated,
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": config.FILTER_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )

            raw = response.choices[0].message.content.strip()
            result = json.loads(raw)

            # スコアの妥当性チェック
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
        except openai.OpenAIError as e:
            logger.error(f"OpenAI API error during filtering for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during filtering for {url}: {e}")
            return None
