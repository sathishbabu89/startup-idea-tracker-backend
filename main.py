from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import UserDB, User
from database import SessionLocal, engine, Base
import bcrypt
import os
from dotenv import load_dotenv
from pydantic import BaseModel

# ----------------------------------------
# 1. Setup
# ----------------------------------------
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

Base.metadata.create_all(bind=engine)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------------------------------
# 2. FastAPI App + CORS
# ----------------------------------------
app = FastAPI()

origins = [
    "http://localhost:3000",
    "https://startupidea-hotocloud.web.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------
# 3. JWT Helpers
# ----------------------------------------
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return email
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ----------------------------------------
# 4. Request Models
# ----------------------------------------
class LoginRequest(BaseModel):
    email: str
    password: str

# ----------------------------------------
# 5. Routes
# ----------------------------------------
@app.get("/")
def root():
    return {"message": "FastAPI backend is running 🚀"}

@app.post("/register")
def register_user(user: User, db: Session = Depends(get_db)):
    existing_user = db.query(UserDB).filter(UserDB.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists!")

    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    new_user = UserDB(
        username=user.username,
        email=user.email,
        password=hashed_password.decode('utf-8')
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": f"User {new_user.username} registered successfully!"}

# ✅ UPDATED LOGIN ENDPOINT (accepts JSON)
@app.post("/login")
def login_user(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.email == request.email).first()
    if not user or not bcrypt.checkpw(request.password.encode('utf-8'), user.password.encode('utf-8')):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return {"access_token": token, "token_type": "bearer"}

@app.get("/users")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(UserDB).all()
    return users

@app.get("/me")
def read_me(token: str, db: Session = Depends(get_db)):
    email = verify_token(token)
    user = db.query(UserDB).filter(UserDB.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": user.username, "email": user.email}
