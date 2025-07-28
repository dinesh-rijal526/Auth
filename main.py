from fastapi import FastAPI
from contextlib import asynccontextmanager
from auth.routes import auth_router
from db.main import init_db
from middleware import register_middleware

@asynccontextmanager
async def life_span(app:FastAPI):
    print('Server is starting...')
    await init_db()
    yield
    print('Server has been stoped...')

app = FastAPI(
    title='Auth ',
    description='It is a FastAPI auth API'
)

register_middleware(app)
app.include_router(auth_router, prefix='/auth', tags=['auth'])