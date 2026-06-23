from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from passlib.context import CryptContext
import os
from datetime import datetime, timedelta
import jwt

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB
MONGO_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/fabs_ci')
client = MongoClient(MONGO_URI)
db = client['fabs_ci']

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "dev-secret-key-2026"

@app.get("/api/health")
async def health():
    return {"status": "ok"}

@app.post("/api/auth/login")
async def login(email: str, password: str):
    user = db.users.find_one({"email": email})
    
    if not user:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    
    if not pwd_context.verify(password, user['password']):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    
    token = jwt.encode(
        {"user_id": str(user["_id"]), "exp": datetime.utcnow() + timedelta(days=7)},
        SECRET_KEY,
        algorithm="HS256"
    )
    
    return {
        "access_token": token,
        "user": {"id": str(user["_id"]), "email": user["email"], "role": user["role"]}
    }

