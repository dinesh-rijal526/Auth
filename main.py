from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from auth.routes import auth_router
from db.main import init_db

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

app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])
app.include_router(auth_router, prefix='/auth', tags=['auth'])