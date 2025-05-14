from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from typing import List, Optional
import jwt
from datetime import datetime
import os
from pymongo import MongoClient, IndexModel, ASCENDING
from bson import ObjectId



DB_HOST = os.getenv("MONGO_HOST")
client = MongoClient(host=[DB_HOST])
db = client['trip_service']
collection = db['trips']

collection.create_indexes([
    IndexModel([("driver_id", ASCENDING)]),
    IndexModel([("start_location", ASCENDING)]),
    IndexModel([("end_location", ASCENDING)]),
    IndexModel([("departure_time", ASCENDING)])
])


app = FastAPI(
    title="Trip Service",
    description="Сервис управления поездками",
    version="1.0.0"
)


class TripBase(BaseModel):
    route_id: int
    driver_id: int = Field(..., gt=0)
    user_ids: List[int] = []
    start_location: str = Field(..., min_length=1)
    end_location: str = Field(..., min_length=1)
    departure_time: datetime
    available_seats: int = Field(..., gt=0)
    price: float = Field(..., gt=0)
    description: Optional[str] = None


class TripResponse(TripBase):
    id: str


class JoinRequest(BaseModel):
    user_id: int


SECRET_KEY = os.getenv('SECRET_KEY', "your-secret-key")
ALGORITHM = os.getenv('ALGORITHM', "HS256")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://user-service:8001/token")


def get_current_user(token: str = Depends(oauth2_scheme)):
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
        return username
    except jwt.PyJWTError:
        raise credentials_exception


@app.post("/trips/", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
def create_trip(trip: TripBase, current_user: str = Depends(get_current_user)):
    trip_dict = trip.dict()
    result = collection.insert_one(trip_dict)
    trip_dict["id"] = str(result.inserted_id)
    return trip_dict


@app.get("/trips/", response_model=List[TripResponse])
def get_all_trips(current_user: str = Depends(get_current_user)):
    trips = []
    for trip in collection.find():
        trip["id"] = str(trip["_id"])
        trips.append(trip)
    return trips


@app.get("/trips/{trip_id}", response_model=TripResponse)
def get_trip(trip_id: str, current_user: str = Depends(get_current_user)):
    if not ObjectId.is_valid(trip_id):
        raise HTTPException(status_code=400, detail="Invalid trip ID")
    
    trip = collection.find_one({"_id": ObjectId(trip_id)})
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    trip["id"] = str(trip["_id"])
    return trip


@app.patch("/trips/{trip_id}/join", response_model=TripResponse)
def join_trip(trip_id: str, request: JoinRequest, current_user: str = Depends(get_current_user)):
    if not ObjectId.is_valid(trip_id):
        raise HTTPException(status_code=400, detail="Invalid trip ID")
    
    trip = collection.find_one({"_id": ObjectId(trip_id)})
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if request.user_id in trip["user_ids"]:
        raise HTTPException(status_code=400, detail="User already joined")
    
    if len(trip["user_ids"]) >= trip["available_seats"]:
        raise HTTPException(status_code=400, detail="No available seats")
    
    collection.update_one(
        {"_id": ObjectId(trip_id)},
        {"$push": {"user_ids": request.user_id}}
    )
    
    updated_trip = collection.find_one({"_id": ObjectId(trip_id)})
    updated_trip["id"] = str(updated_trip["_id"])
    return updated_trip


@app.delete("/trips/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trip(trip_id: str, current_user: str = Depends(get_current_user)):
    if not ObjectId.is_valid(trip_id):
        raise HTTPException(status_code=400, detail="Invalid trip ID")
    
    result = collection.delete_one({"_id": ObjectId(trip_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Trip not found")
    return None
