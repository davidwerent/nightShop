from aiogram import Bot, Dispatcher, executor, types
from aiogram.types.web_app_info import WebAppInfo
import json
import sqlite3
from datetime import datetime
from messages import *

bot = Bot('6346069359:AAGLEhImbXUnKIJGI0aG5ahR4lY-Nqqv1Bc')
dp = Dispatcher(bot)

conn = sqlite3.connect('sqlite3.db')
cursor = conn.cursor()


@dp.message_handler(commands=['start'])
async def start(message: types.Message):

    cursor.execute('SELECT * FROM user WHERE user_id=:user_id', {'user_id': message.from_user.id})
    user = cursor.fetchone()
    print(user)
    if user is None:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton(text='Зарегистрироваться', request_contact=True))
        await message.answer(WELCOME_MESSAGE_COURIER_NOREG ,reply_markup=keyboard)
    else:
        await message.answer(WELCOME_MESSAGE_COURIER)

@dp.message_handler(content_types=['contact'])
async def contact(message: types.Message):
    new_user = (message.from_user.id,
                message.contact.phone_number,
                message.chat.id
                )
    print(new_user)
    keyboard = types.ReplyKeyboardRemove()
    try:
        cursor.execute('INSERT INTO user(user_id, phone, link) VALUES (?,?, ?)', new_user)
        conn.commit()
        await message.answer(REG_COMPLETE, reply_markup=keyboard)
    except sqlite3.IntegrityError:
        await message.answer('Я уже зарегистрировал Вас')


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('select'))
async def select_order_to_courier(callback_query: types.CallbackQuery):
    order_id = callback_query.data[6:]
    cursor.execute('UPDATE user SET active_order = ? WHERE user_id =?',
                   (order_id, callback_query.from_user.id))
    cursor.execute('UPDATE orders SET in_transit = ? WHERE id = ?',
                   (1, order_id))
    conn.commit()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    await bot.send_message(callback_query.from_user.id, ORDER_ACCEPT, parse_mode=types.ParseMode.HTML, reply_markup=markup)
    await bot.answer_callback_query(callback_query.id)



@dp.message_handler(commands=['show'])
async def show_order(message: types.Message):
    cursor.execute('SELECT active_order FROM user WHERE user_id= ?', (message.from_user.id,))
    active_order = cursor.fetchone()
    # print(active_order)
    if active_order is not None and active_order[0] != 0:
        await message.answer('У вас уже есть назначенный заказ! Нажми /details')
        return
    cursor.execute('SELECT id, totalSum, address FROM orders WHERE isOpen=:is_open', {'is_open': 1})
    orders = cursor.fetchall()

    if len(orders) == 0:
        await message.answer('Сейчас нет доступных заказов. Попробуйте позже')
        return
    for order in orders:
        keyboard = types.InlineKeyboardMarkup()
        # print(order)
        mes = f"Заказ #{order[0]}\n"
        mes += f"Сумма заказа: {order[1]}\n"
        mes += f"Адрес доставки: {order[2]}\n"
        btn_select = types.InlineKeyboardButton(text='Выбрать', callback_data=f'select{order[0]}')
        keyboard.add(btn_select)
        await message.answer(mes, reply_markup=keyboard)


def get_item_name(id):
    cursor.execute('SELECT * FROM goods')
    menu = cursor.fetchall()
    for item in menu:
        # print(item)
        if item[0] == id:
            return item[1]
    print('\n')


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('cancel'))
async def cancel_order(callback_query: types.CallbackQuery):
    order_id = callback_query.data[6:]
    cursor.execute('UPDATE orders SET in_transit =? WHERE id = ?',
                   (0, order_id))
    cursor.execute('UPDATE user SET active_order =? WHERE user_id =?',
                   (0, callback_query.from_user.id))
    conn.commit()
    await bot.send_message(callback_query.from_user.id, 'Вы отказались от заказа!')
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('btn_complete_yes'))
async def complete_order_confirm(callback_query: types.CallbackQuery):
    order_id = callback_query.data[16:]

    cursor.execute('UPDATE orders SET in_transit = ?, isOpen = ? WHERE id = ?',
                   (0, 0, order_id))
    conn.commit()
    cursor.execute('UPDATE user SET active_order = ? WHERE user_id = ?',
                   (0, callback_query.from_user.id))
    conn.commit()

    await bot.send_message(callback_query.from_user.id, f'Заказ #{order_id} завершен!')
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('btn_complete_no'))
async def complete_order_confirm(callback_query: types.CallbackQuery):

    await bot.answer_callback_query(callback_query.id)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('complete'))
async def complete_order(callback_query: types.CallbackQuery):
    order_id = callback_query.data[8:]
    keyboard = types.InlineKeyboardMarkup()
    btn_yes = types.InlineKeyboardButton(text='Да', callback_data=f'btn_complete_yes{order_id}')
    btn_no = types.InlineKeyboardButton(text='Нет', callback_data='btn_complete_no')
    keyboard.add(btn_yes, btn_no)
    await bot.send_message(callback_query.from_user.id, f'Подтвердите, что заказ #{order_id} доставлен', reply_markup=keyboard)
    await bot.answer_callback_query(callback_query.id)


@dp.message_handler(commands=['details'])
async def show_details(message: types.Message):
    cursor.execute('SELECT active_order FROM user WHERE user_id= ?', (message.from_user.id,))
    active_order = cursor.fetchone()

    # print(active_order)
    if active_order[0] == 0:
        await message.answer('У вас нет назначенного заказа! Список заказов /show')
    else:
        cursor.execute('SELECT * FROM orders WHERE id = ?',(active_order[0],))
        order = cursor.fetchone()
        if order is None:
            await message.answer('У вас нет назначенного заказа! Список заказов /show')
            return
        # print(order)
        mes = f'Детальная информация по заказу #{active_order[0]}\n'
        # print(order[1])
        temp = order[1].replace('\'', '\"')
        request = json.loads(temp)
        mes += f"Адрес: {request[0].get('address')}\n"
        mes += f"Сумма к оплате: {order[2]} руб.\n\"
        mes += f"Контакт покупателя: {request[0].get('phone')}\n\n"
        mes += f"Состав заказа (что надо купить):\n"
        counter = 1
        request.pop(0)
        for item in request:
            mes += f"{counter}. {get_item_name(item.get('id'))}\n"
            # mes += f"ID = {item.get('id')}\n"
            mes += f"Кол-во: \t{item.get('count')}\n"
            mes += f"Рекомендуемая цена за ед: {item.get('cost')} руб\n\n"
            counter += 1
        keyboard = types.InlineKeyboardMarkup()
        btn_cancel = types.InlineKeyboardButton(text='Отказаться', callback_data=f'cancel{active_order[0]}')
        btn_complete = types.InlineKeyboardButton(text='Завершить', callback_data=f'complete{active_order[0]}')
        keyboard.add(btn_cancel, btn_complete)
        await message.answer(mes, reply_markup=keyboard)





executor.start_polling(dp)
