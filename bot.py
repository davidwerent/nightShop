from aiogram import Bot, Dispatcher, executor, types
from aiogram.types.web_app_info import WebAppInfo
import json
import sqlite3
from datetime import datetime
from messages import *

bot = Bot('6105878178:AAGUaHuZ6stFOZNAfAtR26XxZo-Wn2qgkp8')
dp = Dispatcher(bot)

conn = sqlite3.connect('sqlite3.db')
cursor = conn.cursor()


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('Сделать заказ', web_app=WebAppInfo(url='https://davidwerent.online/menu')))

    cursor.execute('SELECT * FROM orders WHERE user_id=:user_id and isOpen=:is_open', {'user_id': message.from_user.id,
                                                                                       'is_open': 1})
    orders = cursor.fetchall()
    if len(orders) == 0:
        await message.answer(WELCOME_MESSAGE, reply_markup=markup)
        return
    else:
        await message.answer(WELCOME_MESSAGE, reply_markup=types.ReplyKeyboardRemove())


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('cancel'))
async def process_callback_button_send_cert(callback_query: types.CallbackQuery):
    cursor.execute('SELECT id FROM orders WHERE user_id = ? and isOpen = ?', (callback_query.from_user.id, 1))
    order_id = cursor.fetchone()
    print(f'callback data {callback_query.data}:\norder_id = {order_id[0]}')
    cursor.execute('UPDATE orders SET isOpen = ? WHERE user_id = ?', (0, callback_query.from_user.id))
    cursor.execute('UPDATE user SET active_order = ? WHERE active_order = ?', (0, order_id[0]))
    conn.commit()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('Сделать заказ', web_app=WebAppInfo(url='https://davidwerent.online/menu')))

    await bot.send_message(callback_query.from_user.id, 'Заказ отменен!', parse_mode=types.ParseMode.HTML, reply_markup=markup)
    await bot.answer_callback_query(callback_query.id)

def get_courier_by_order_id(order_id):
    cursor.execute('SELECT link FROM user WHERE active_order = ?', (order_id,))
    result = cursor.fetchone()
    print(result)
    if result is not None:
        return result[0]
    else:
        return None

@dp.message_handler(commands=['my'])
async def get_order_list(message: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    btn_cancel = types.InlineKeyboardButton(text='Отменить заказ', callback_data='cancel')


    cursor.execute('SELECT * FROM orders WHERE user_id=:user_id and isOpen=:is_open', {'user_id': message.from_user.id,
                                                                                    'is_open': 1})
    orders = cursor.fetchall()

    cursor.execute('SELECT in_transit FROM orders WHERE user_id = ? and isOpen= ?',
                   (message.from_user.id, 1))
    status = cursor.fetchone()
    if status is None:
        await message.answer('У вас нет активного заказа!')
        return
    if status[0] == 1:
        status_text = 'курьер назначен'
    else:
        status_text = 'ожидание курьера'
    # print(orders)
    if len(orders) == 0:
        await message.answer('У вас нет активного заказа!')
        return
    if len(orders) == 1:
        order = orders[0]
        print(order)
        mes = f'Заказ #{order[0]}\n'
        mes += f'Статус заказа: {status_text}\n'
        mes += f'Стоимость заказа: {order[2]} руб\n'
        address = order[1].replace('\'', '\"')
        js = json.loads(address)
        mes += f'Адрес доставки: {js[0].get("address")}'
        btn_chat_courier = types.InlineKeyboardButton(text='Написать курьеру',
                                                      url=f'tg://user?id={get_courier_by_order_id(order[0])}')
        keyboard.add(btn_cancel, btn_chat_courier)
        await message.answer(mes, reply_markup=keyboard)
        return
    for order in orders:
        print(order)
        order_id = order[0]
        mes = f'Заказ #{order_id}\n'
        mes += f'Статус заказа: {status_text}\n'
        mes += f'Стоимость заказа: {order[2]} руб\n'
        address = order[1].replace('\'', '\"')
        js = json.loads(address)
        mes += f'Адрес доставки: {js[0].get("address")}'
        await message.answer(mes, reply_markup=keyboard)

    # await message.answer('some flow', reply_markup=keyboard)


@dp.message_handler(commands=['new'])
async def new_order(message: types.Message):
    cursor.execute('SELECT * FROM orders WHERE user_id=:user_id and isOpen=:is_open', {'user_id': message.from_user.id,
                                                                                       'is_open': 1})
    orders = cursor.fetchall()


    if len(orders) != 0:
        await message.answer('У вас уже есть активный заказ. \nОтмените его или дождитесь получения заказа')
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('Сделать заказ', web_app=WebAppInfo(url='https://davidwerent.online/menu')))

    await message.answer('На клавиатуре есть кнопка "Сделать заказ"', reply_markup=markup)


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
        name,
        True  # status of order  True default
    )
    cursor.execute(
        'INSERT INTO orders(request, totalSum, totalCost, user_id, date, address, phone, name, isOpen) VALUES (?,?,?,?,?,?,?,?,?)',
        new_order)
    conn.commit()
    await bot.send_message('5732368072', 'В магазине разместили новый заказ! Проверьте бота с заказом')
    await message.answer(f'Ваш заказ #{cursor.lastrowid} принят!\nСумма заказа: {total_sum} руб.',
                         reply_markup=types.ReplyKeyboardRemove())
    # await message.answer(message.web_app_data.data)


executor.start_polling(dp)
