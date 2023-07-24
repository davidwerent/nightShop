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
    return templates.TemplateResponse('menu.html', {'request': request,
                                                    'item_list': item_list
                                                    })


# Certificate is saved at: /etc/letsencrypt/live/davidwerent.online/fullchain.pem
# Key is saved at:         /etc/letsencrypt/live/davidwerent.online/privkey.pem
# uvicorn main:app --host 0.0.0.0 --port 443 --ssl-certfile /etc/letsencrypt/live/davidwerent.online/fullchain.pem --ssl-keyfile /etc/letsencrypt/live/davidwerent.online/privkey.pem

