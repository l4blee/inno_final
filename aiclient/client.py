import json
import logging
from openai import AsyncOpenAI

from .utils import GPTResponse, DallEResponse
from database import Users

logger = logging.getLogger('aiclient')

class OpenAIClient:
    def __init__(self, token: str, gpt_model: str, instruction: str, image_model: str) -> None:
        self._client = AsyncOpenAI(api_key=token)
        self._gpt_model = gpt_model
        self._image_model = image_model
        self._context_base = [{'role': 'system', 'content': instruction}]

        logger.info('Initialized OpenAI client...')

    async def get_gpt_response(self, prompt: str, user: Users) -> GPTResponse:
        context = json.loads(user.context) if user.use_context else []

        context.append({'role': 'user', 'content': prompt})

        res = await self._client.chat.completions.create(
            model=self._gpt_model,
            messages=
            self._context_base + context,
            max_tokens=min(user.tokens_left, 500),
            temperature=0.6
        )

        gpt_response = GPTResponse(
            content=res.choices[0].message.content,
            tokens_total=res.usage.total_tokens,
            tokens_completion=res.usage.completion_tokens
        )
        
        if user.use_context:
            user.context = json.dumps(context)
            user.context_used += gpt_response.tokens_total 

        user.tokens_left -= gpt_response.tokens_completion

        return gpt_response

    async def get_dalle_response(self, prompt: str) -> DallEResponse:
        res = await self._client.images.generate(prompt=prompt, model=self._image_model)
        return DallEResponse(res.data[0].url)
