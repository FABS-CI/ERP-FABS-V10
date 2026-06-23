from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from pymongo import MongoClient
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sync MongoDB
client = MongoClient('mongodb://localhost:27017/fabsci_erp')
db = client['fabsci_erp']

class LoginRequest(BaseModel):
    email: str
    password: str

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/auth/login")
def login(credentials: LoginRequest = Body(...)):
    email = credentials.email
    password = credentials.password
    user = db.users.find_one({"email": email})
    
    if not user:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    
    pwd_hash = user.get("password_hash")
    if not pwd_hash:
        raise HTTPException(status_code=401, detail="No password")
    
    # Verify
    try:
        if not bcrypt.checkpw(password.encode('utf-8'), pwd_hash.encode('utf-8')):
            raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create JWT
    user_id = str(user["_id"])
    token = jwt.encode(
        {"user_id": user_id, "email": email, "exp": datetime.now(timezone.utc) + timedelta(days=7)},
        "secret",
        algorithm="HS256"
    )
    
    return {
        "access_token": token,
        "user": {
            "id": user_id,
            "email": email,
            "role": user.get("role", "user")
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
