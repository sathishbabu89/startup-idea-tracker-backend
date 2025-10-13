from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from models import UserDB, User
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from typing import List
import bcrypt
from database import Base, engine
Base.metadata.create_all(bind=engine)

# Create DB tables
UserDB.metadata.create_all(bind=engine)

# Dependency - create and close session per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

# CORS setup
origins = [
    "http://localhost:3000",                    # local React dev
    "https://startupidea-hotocloud.web.app"    # Firebase hosted React app
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Temporary local in-memory database
fake_db = {}

@app.get("/")
def root():
    return {"message": "FastAPI backend is running 🚀"}

@app.post("/register")
def register_user(user: User, db: Session = Depends(get_db)):
    existing_user = db.query(UserDB).filter(UserDB.email == user.email).first()
    if existing_user:
        return {"message": "User already exists!"}

    # Hash the password
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())

    # Save user with hashed password
    new_user = UserDB(
        username=user.username,
        email=user.email,
        password=hashed_password.decode('utf-8')
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": f"User {new_user.username} registered successfully!"}

@app.post("/login")
def login_user(user: User, db: Session = Depends(get_db)):
    existing_user = db.query(UserDB).filter(UserDB.email == user.email).first()
    if not existing_user:
        return {"message": "Invalid email or password"}

    # Verify hashed password
    if bcrypt.checkpw(user.password.encode('utf-8'), existing_user.password.encode('utf-8')):
        return {"message": f"Login successful! Welcome {existing_user.username}"}
    else:
        return {"message": "Invalid email or password"}

@app.get("/users")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(UserDB).all()

    return users
