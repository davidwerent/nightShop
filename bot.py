from aiogram import Bot, Dispatcher, executor, types
from aiogram.types.web_app_info import WebAppInfo
import json
import sqlite3
from datetime import datetime

bot = Bot('6105878178:AAGUaHuZ6stFOZNAfAtR26XxZo-Wn2qgkp8')
dp = Dispatcher(bot)

conn = sqlite3.connect('sqlite3.db')
cursor = conn.cursor()

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    markup = types.ReplyKeyboardMarkup()
    markup.add(types.KeyboardButton('Сделать заказ', web_app=WebAppInfo(url='https://davidwerent.online/menu')))
    await message.answer('Привет, покупатель!', reply_markup=markup)


@dp.message_handler(content_types=['web_app_data'])
async def web_app(message: types.Message):
    res = json.loads(message.web_app_data.data)
    print(res)
    print(res[0])
    print(res[1]["id"])

    request = res
    user_id = message.from_user.id
    date = datetime.now()
    address = res[0]['address']
    phone = res[0]['phone']
    name = res[0]['name']

    res.pop(0)
    total_sum = 0
    for item in res:
        print(item)
        total_sum += item['price'] * item['count']



    await message.answer(res)


executor.start_polling(dp)
