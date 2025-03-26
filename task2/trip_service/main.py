from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from typing import List, Optional
import jwt
from datetime import datetime
import os

app = FastAPI(title="Trip Service", 
              description="Сервис управления поездками", 
              version="1.0.0")

users_db = {}

users_db[1] = {
    "id": 1,
    "username": "admin",
    "password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
    "first_name": "Admin",
    "last_name": "User",
    "email": "admin@example.com"
}

trips_db = {}

trips_db[1] = {
    "id": 1,
    "route_id": 1,
    "driver_id": 3,
    "user_ids":[1],
    "start_location": "Москва, Красная площадь",
    "end_location": "Санкт-Петербург, Невский проспект",
    "departure_time": "2024-03-27T08:00:00",
    "available_seats": 3,
    "price": 1500.00,
    "description": "Комфортабельный минивэн"
}


SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://127.0.0.1:8001/token")


class Trip(BaseModel):
    id: Optional[int] = None
    driver_id: int
    user_ids: List[int] = []
    start_location: str = Field(..., min_length=1)
    end_location: str = Field(..., min_length=1)
    departure_time: datetime
    available_seats: int = Field(..., gt=0)
    price: float = Field(..., gt=0)
    description: Optional[str] = None

class JoinRequest(BaseModel):
    user_id: int


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
        
    except jwt.PyJWTError:
        raise credentials_exception
    
    return {"username": username}

def check_user_exists(user_id: int):
    return  user_id in users_db


@app.post("/trips/", response_model=Trip, tags=["trips"])
async def create_trip(trip: Trip, current_user: dict = Depends(get_current_user)):

    if not check_user_exists(trip.driver_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )
    
    trip_id = max(trips_db.keys()) + 1 if trips_db else 1
    trip_dict = trip.dict()
    trip_dict["id"] = trip_id
    trip_dict["user_ids"] = [trip.driver_id]
    trips_db[trip_id] = trip_dict

    return trip_dict

@app.get("/trips/", response_model=List[Trip], tags=["trips"])
async def read_trips(current_user: dict = Depends(get_current_user)):
    return list(trips_db.values())

@app.get("/trips/{trip_id}", response_model=Trip, tags=["trips"])
async def read_trip(trip_id: int, current_user: dict = Depends(get_current_user)):

    if trip_id not in trips_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    return trips_db[trip_id]

@app.patch("/trips/{trip_id}/join", response_model=Trip, tags=["trips"])
async def join_trip(trip_id: int, request: JoinRequest, current_user: dict = Depends(get_current_user)):
    
    user_id = request.user_id
    
    if trip_id not in trips_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    if not check_user_exists(user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    trip = trips_db[trip_id]
    if user_id in trip["user_ids"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already joined this trip"
        )
    
    if len(trip["user_ids"]) >= trip["available_seats"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No available seats"
        )
    
    trip["user_ids"].append(user_id)
    return trip

@app.delete("/trips/{trip_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["trips"])
async def delete_trip(trip_id: int, current_user: dict = Depends(get_current_user)):

    if trip_id not in trips_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    del trips_db[trip_id]
    return None
