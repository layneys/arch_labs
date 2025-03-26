from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
import os


app = FastAPI(title="User Service", 
              description="Сервис управления пользователями", 
              version="1.0.0")


SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')

users_db = {}

users_db[1] = {
    "id": 1,
    "username": "admin",
    "password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
    "first_name": "Admin",
    "last_name": "User",
    "email": "admin@example.com"
}

ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(BaseModel):
    id: Optional[int] = None
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(...)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class UserResponse(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    email: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str

def verify_password(plain_password, password):
    return pwd_context.verify(plain_password, password)  


def get_user(username: str):

    for user_id, user in users_db.items():
        if user["username"] == username:
            return user
        
    return None


def authenticate_user(username: str, password: str):

    user = get_user(username)

    if not user:
        return False
    
    if not verify_password(password, user["password"]):
        return False
    
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        if username is None:
            raise credentials_exception
        
        token_data = TokenData(username=username)

    except jwt.PyJWTError:
        raise credentials_exception
    
    user = get_user(token_data.username)

    if user is None:
        raise credentials_exception
    
    return user


@app.post("/token", response_model=Token, tags=["auth"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=UserResponse, tags=["users"])
async def create_user(user: User):

    if get_user(user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    user_id = max(users_db.keys()) + 1 if users_db else 1
    user_dict = user.dict()
    user_dict["id"] = user_id
    users_db[user_id] = user_dict
    return user_dict

@app.get("/users/", response_model=List[UserResponse], tags=["users"])
async def read_users(current_user: dict = Depends(get_current_user)):
    return list(users_db.values())

@app.get("/users/{user_id}", response_model=UserResponse, tags=["users"])
async def read_user(user_id: int, current_user: dict = Depends(get_current_user)):

    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return users_db[user_id]

@app.get("/users/by-username/{username}", response_model=UserResponse, tags=["users"])
async def read_user_by_username(username: str, current_user: dict = Depends(get_current_user)):
    user = get_user(username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@app.get("/users/by-name/{name_mask}", response_model=List[UserResponse], tags=["users"])
async def read_users_by_name(name_mask: str, current_user: dict = Depends(get_current_user)):
    result = []

    for user in users_db.values():
        if (name_mask.lower() in user["first_name"].lower() or 
            name_mask.lower() in user["last_name"].lower()):
            result.append(user)

    return result


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["users"])
async def delete_user(user_id: int, current_user: dict = Depends(get_current_user)):

    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    del users_db[user_id]
    return None