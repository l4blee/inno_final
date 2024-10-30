import aiogram.utils
import aiogram.utils.media_group
from dotenv import load_dotenv; load_dotenv()

import asyncio
import re
import os
import logging
from traceback import print_exc

import aiogram

import database as db
import aiclient


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s - %(name)s - %(message)s', datefmt='%H:%M:%S')

logger = logging.getLogger()
dp = aiogram.Dispatcher()
bot = aiogram.Bot(os.getenv('TELEGRAM_API_TOKEN'))
database = db.DBClient(os.getenv('DATABASE_URL'))
ai = aiclient.OpenAIClient(
    os.getenv('OPENAI_API_KEY'), 
    os.getenv('OPENAI_GPT_MODEL'),
    os.getenv('OPENAI_GPT_INSTRUCTION'),
    os.getenv('OPENAI_IMAGE_MODEL')
)
IMAGE_REGEX = re.compile(r'\[IMAGE]{(.+)}')


@dp.update.outer_middleware()
async def check_registration(handler, event: aiogram.types.Update, data: aiogram.types.Message):
    await bot.send_chat_action(event.message.chat.id, 'typing')
    try:
        with database.get_session() as session:
            if database.get_user(event.message.from_user.id, session):
                    return await handler(event, data)
            
            database.add_user(event.message.from_user.id, session)
            session.commit()

        return await handler(event, data)
    except Exception:
        logger.error('Caught exception with the following stacktrace:')
        print_exc()
        await event.message.reply('Произошла ошибка, попробуйте позже!')


@dp.message(aiogram.filters.Command('switch_context'))
async def switch_context(msg: aiogram.types.Message):
    with database.get_session() as session:
        user = database.get_user(msg.from_user.id, session)
        user.use_context = not user.use_context

        await msg.reply(
            f'Использование контекста *{["отключено", "включено"][int(user.use_context)]}*!',
            parse_mode='Markdown'    
        )
        session.commit()


@dp.message(aiogram.filters.Command('delete_context'))
async def delete_context(msg: aiogram.types.Message):
    with database.get_session() as session:
        user = database.get_user(msg.from_user.id, session)
        user.context = '[]'

        session.commit()

    await msg.reply('Конекст успешно удален!')


@dp.message()
async def index(msg: aiogram.types.Message):
    with database.get_session() as session:
        user = database.get_user(msg.from_user.id, session)

        if user.tokens_left <= 0:
            await msg.reply('У Вас закончились токены!')
            return
        
        if user.context_capacity <= user.context_used:
            await msg.reply('Достигнут максимальный размер контекста!')
            return

        gpt_response = await ai.get_gpt_response(msg.text, user)
        res_text = gpt_response.content[:IMAGE_REGEX.search(gpt_response.content).start()]
        media_group = aiogram.utils.media_group.MediaGroupBuilder(caption=res_text)
        for img in IMAGE_REGEX.findall(gpt_response.content):
            dalle_response = await ai.get_dalle_response(img)
            media_group.add_photo(dalle_response.img_url)

        session.commit()

    await msg.reply_media_group(media_group.build())


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())