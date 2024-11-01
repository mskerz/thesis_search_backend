from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from route.auth import router as auth_router
from route.role import role_router
from route.advisor import advisor_router
from route.thesis import thesis_router
from route.search import search_router
import os
from dotenv import load_dotenv
load_dotenv()
app = FastAPI()


# app.get('/x')
# async def index():
#     return {"message":"welcome to server"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# สร้างลิสต์ของ routers
routes_import = [
    auth_router,
    role_router,
    advisor_router,
    thesis_router,
    search_router
]

@app.get('/')
def root():
    return {"message":"Welcome to server"} 

for router in routes_import:
    app.include_router(router, prefix="/api")

## uvicorn main:app --reload 

if __name__ == "__main__":
    try:
        uvicorn.run("main:app",host="0.0.0.0", port=8000, reload=True)
    except KeyboardInterrupt:
        print("KeyboardInterrupt detected. Stopping the server gracefully.")
        