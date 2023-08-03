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

    request = str(res)
    user_id = message.from_user.id
    date = datetime.now()
    address = res[0]['address']
    phone = res[0]['phone']
    name = res[0]['name']

    res.pop(0)
    total_sum = 0
    total_cost = 0
    for item in res:
        print(item)
        total_sum += float(item['price']) * float(item['count'])
        total_cost += float(item['cost']) * float(item['count'])
    print(f'total sum = {total_sum}')
    print(f'total cost = {total_cost}')
    new_order = (
        request,
        total_sum,
        total_cost,
        user_id,
        date,
        address,
        phone,
        name
    )
    cursor.execute('INSERT INTO orders(request, totalSum, totalCost, user_id, date, address, phone, name) VALUES (?,?,?,?,?,?,?,?)', new_order)
    conn.commit()
    await message.answer(f'Ваш заказ #{cursor.lastrowid} принят!\nСумма заказа: {total_sum} руб.')


executor.start_polling(dp)
