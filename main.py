import sqlite3
from fastapi import FastAPI, UploadFile, Form, Request, Response, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Union
import uvicorn
import json

from sys import platform

templates = Jinja2Templates(directory='templates')

app = FastAPI(
    title='coupon-backend',
    version='0.1'
)
'''if platform == 'darwin' or platform == 'win32':
    DEBUG = True
    db_name = 'sqlite3.db'
else:
    DEBUG = False
    db_name = 'shop_database.db'
    '''
DEBUG = True
db_name = 'sqlite3.db'

conn = sqlite3.connect(db_name)
cursor = conn.cursor()

@app.get('/')
async def root():
    return {'greetings': 'hello chief!'}


@app.get('/menu')
async def show_menu(request: Request):

    cursor.execute('SELECT * FROM goods WHERE isActive = ?', (1,))
    item_list = cursor.fetchall()

    for item in item_list:
        print(item)



    cursor.execute('SELECT category FROM goods')
    category_list = cursor.fetchall()
    categorys = list(set(category_list))
    category_unique = []
    for cat in categorys:
        category_unique.append(cat[0].replace('(', '').replace(',)', ''))
    category_list = {}
    category_list = category_list.fromkeys(category_unique)


    for category in category_list:
        items = []
        for item in item_list:
            if item[6] == category:
                items.append(item)
        category_list[category] = items

    cursor.execute('SELECT * FROM alert WHERE is_active = 1')
    alerts = cursor.fetchall()
    # print(alerts)

    '''print('=============')

    for cat in category_list:
        print(f'CATEGORY={cat}')
        for item in category_list[cat]:
            print(item)'''
    return templates.TemplateResponse('menu.html', {'request': request,
                                                    'item_list': item_list,
                                                    'new_item_list': category_list,
                                                    'category_list': category_unique,
                                                    'alerts': alerts
                                                    })


# Certificate is saved at: /etc/letsencrypt/live/davidwerent.online/fullchain.pem
# Key is saved at:         /etc/letsencrypt/live/davidwerent.online/privkey.pem
# uvicorn main:app --host 0.0.0.0 --port 443 --ssl-certfile /etc/letsencrypt/live/davidwerent.online/fullchain.pem --ssl-keyfile /etc/letsencrypt/live/davidwerent.online/privkey.pem
def get_item_name(id):
    cursor.execute('SELECT * FROM goods')
    menu = cursor.fetchall()
    for item in menu:
        # print(item)
        if item[0] == id:
            return item[1]


@app.get('/orders')
async def get_all_orders(request: Request, token: Union[str, None] = None):

    if token != 'gudini':
        return {'access': 'denied'}

    cursor.execute('SELECT * FROM orders WHERE isOpen = ?', (1,))
    open_orders = cursor.fetchall()
    open_order_items = {}
    open_orders_items = []
    for order in open_orders:
        temp = order[1].replace('\'', '\"')
        # print(f'temp:\n{temp}')
        req = json.loads(temp)
        req.pop(0)
        order_items = []
        for item in req:
            # print(item)
            item.update({'name': get_item_name(item.get('id'))})
            order_items.append(item)
        open_order_items = {
            'id': order[0],
            'goods': order_items
        }
        open_orders_items.append(open_order_items)
    # print(open_orders_items)

    cursor.execute('SELECT * FROM orders WHERE isOpen = ?', (0,))
    close_orders = cursor.fetchall()
    close_order_items = {}
    close_orders_items = []
    for order in close_orders:
        temp = order[1].replace('\'', '\"')
        # print(f'temp:\n{temp}')
        req = json.loads(temp)
        req.pop(0)
        order_items = []
        for item in req:
            # print(item)
            item.update({'name': get_item_name(item.get('id'))})
            order_items.append(item)
        close_order_items = {
            'id': order[0],
            'goods': order_items
        }
        close_orders_items.append(close_order_items)


    cursor.execute('SELECT * FROM user')
    users = cursor.fetchall()
    print(users)
    user_list = []
    for user in users:
        js_user = {
            'id': user[0],
            'user_id': user[1],
            'phone': user[2],
            'active_order': user[3]
        }
        user_list.append(js_user)

    print(user_list)
    return templates.TemplateResponse('orders.html', {  'request': request,
                                                        'open_orders': open_orders,
                                                        'open_orders_items': open_orders_items,
                                                        'close_orders': close_orders,
                                                        'close_orders_items': close_orders_items,
                                                        'user_list': user_list
                                                        })

class BaseDeleteRequest(BaseModel):
    token: str = None
    id: int = None

class BaseDeleteGoods(BaseModel):
    token: str = None
    id: int = None

@app.post('/delete')
async def delete_order(request: BaseDeleteRequest):
    print(request)
    cursor.execute('UPDATE orders SET isOpen = 0, in_transit = 0 WHERE id = ?', (request.id,))
    cursor.execute('UPDATE user SET active_order = 0 WHERE active_order = ?', (request.id,))
    conn.commit()

    return {'status': 200}


@app.post('/edit_goods')
async def edit_goods(request: Request,
                    name: str = Form(...),
                    desc: str = Form(...),
                    price: int = Form(...),
                     cost : int = Form(...),
                     photo: str = Form(...),
                     category: str = Form(...),
                     id: int = Form(...)):
    cursor.execute('UPDATE goods SET name=?,price=?,cost=?,photo=?,description=?,category=? WHERE id = ?',
                   (name, price, cost, photo, desc, category, id))
    conn.commit()
    return await get_goods(request=request, token='gudini')

@app.post('/delete_goods')
async def delete_goods(request: Request, deleteData: BaseDeleteGoods):
    print(f'need delete item with ID={deleteData.id}')
    cursor.execute('UPDATE goods SET isActive=? WHERE id=?', (0, deleteData.id))
    conn.commit()

    return await get_goods(request=request, token='gudini')



@app.get('/goods')
async def get_goods(request: Request, token: Union[str, None] = None):
    if token != 'gudini':
        return {'access': 'denied'}
    cursor.execute('SELECT * FROM goods WHERE isActive=?', (1,))
    item_list = cursor.fetchall()
    # for item in item_list:
        # print(item)

    cursor.execute('SELECT category FROM goods')
    category_list = cursor.fetchall()
    categorys = list(set(category_list))
    category_unique = []
    for cat in categorys:
        category_unique.append(cat[0].replace('(', '').replace(',)', ''))
    category_list = {}
    category_list = category_list.fromkeys(category_unique)

    for category in category_list:
        items = []
        for item in item_list:
            if item[6] == category:
                items.append(item)
        category_list[category] = items
    '''print('=============')

    for cat in category_list:
        print(f'CATEGORY={cat}')
        for item in category_list[cat]:
            print(item)'''
    return templates.TemplateResponse('goods.html', {'request': request,
                                                    'item_list': item_list,
                                                    'new_item_list': category_list,
                                                    'category_list': category_unique
                                                    })






