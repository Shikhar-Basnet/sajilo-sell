from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Sajilo Sell API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://shikharbasnet.com.np",
        "https://www.shikharbasnet.com.np",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Sajilo Sell API is alive"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "sajilo-sell-backend"}