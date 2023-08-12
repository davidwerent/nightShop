import sqlite3
from fastapi import FastAPI, UploadFile, Form, Request, Response, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn

templates = Jinja2Templates(directory='templates')

app = FastAPI(
    title='coupon-backend',
    version='0.1'
)

conn = sqlite3.connect('sqlite3.db')
cursor = conn.cursor()

@app.get('/')
async def root():
    return {'greetings': 'hello chief!'}


@app.get('/menu')
async def show_menu(request: Request):

    cursor.execute('SELECT * FROM goods')
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


    print('=============')

    for cat in category_list:
        print(f'CATEGORY={cat}')
        for item in category_list[cat]:
            print(item)
    return templates.TemplateResponse('menu.html', {'request': request,
                                                    'item_list': item_list,
                                                    'new_item_list': category_list,
                                                    'category_list': category_unique
                                                    })


# Certificate is saved at: /etc/letsencrypt/live/davidwerent.online/fullchain.pem
# Key is saved at:         /etc/letsencrypt/live/davidwerent.online/privkey.pem
# uvicorn main:app --host 0.0.0.0 --port 443 --ssl-certfile /etc/letsencrypt/live/davidwerent.online/fullchain.pem --ssl-keyfile /etc/letsencrypt/live/davidwerent.online/privkey.pem

