import openai
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class ContentSummarizer:
    def __init__(self, api_key: str, model: str = "gpt-5-mini-2025-08-07"):
        """
        OpenAI APIを使用したコンテンツ要約クラス
        
        Args:
            api_key: OpenAI APIキー
            model: 使用するモデル名 (デフォルト: gpt-5-mini-2025-08-07)
        """
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
    
    def summarize(self, content: str, url: str = "", max_tokens: int = 300) -> Optional[str]:
        """
        コンテンツを要約する
        
        Args:
            content: 要約対象のコンテンツ
            url: コンテンツのURL（ログ用）
            max_tokens: 要約の最大トークン数
            
        Returns:
            要約されたテキスト、エラーの場合はNone
        """
        try:
            logger.info(f"Summarizing content from: {url}")
            
            # コンテンツが長すぎる場合は切り詰める（おおよそ4000トークン相当）
            if len(content) > 100000:
                content = content[:100000] + "..."
                logger.warning(f"Content truncated for {url}")
            
            prompt = f"""以下のWebページの内容を日本語で簡潔に要約してください。
入力が英語であっても、日本語で丁寧かつ正確に要約を行います。文体はフォーマルで、必要に応じて引用を行います。学術論文、ニュース記事、ビジネスレポートなど、さまざまな文書タイプに対応し、それぞれに適したスタイルで構造的な要約を提供します。

論文の場合の要約の基本構成は以下の通りです：
タイトル、著者情報、目的、方法、結果、結論。
文書の形式がこれと異なる場合は、より適切な構成に調整します。不明確な依頼には追加の情報を求め、正確な要約ができるよう努めます。
常に丁寧で敬意ある日本語表現を使用し、ユーザーとの円滑な対話を重視します。

読みやすくなるように強調すべき点などを強調してください

さらに、要約後には「生成AIを活用して業務効率を高めたい担当者が次に検討すべきこと」を一文で提案します。
            
内容:
{content}"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "あなたはサマリーアシスタントは、日本語で文書を的確に要約することに特化したAIです。"},
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