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

    return templates.TemplateResponse('menu.html', {'request': request})

if __name__ == 'main':
    uvicorn.run(
               app,
               host="0.0.0.0",
               port=443,
               ssl_keyfile="/etc/letsencrypt/live/davidwerent.online/fullchain.pem",
               ssl_certfile="/etc/letsencrypt/live/davidwerent.online/privkey.pem"
               )