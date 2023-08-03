from aiogram import Bot, Dispatcher, executor, types
from aiogram.types.web_app_info import WebAppInfo

bot = Bot('6105878178:AAGUaHuZ6stFOZNAfAtR26XxZo-Wn2qgkp8')
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    markup = types.ReplyKeyboardMarkup()
    markup.add(types.KeyboardButton('Открыть магазин', web_app=WebAppInfo(url='https://davidwerent.online/menu')))
    await message.answer('Привет, покупатель!', reply_markup=markup)


executor.start_polling(dp)