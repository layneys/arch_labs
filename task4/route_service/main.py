from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field
import jwt
from fastapi.security import OAuth2PasswordBearer
import os

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://127.0.0.1:8001/token")

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')

routes_db = {}

app = FastAPI(title="Route Service", 
              description="Сервис управления маршрутами", 
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

route_db = {}

routes_db[1] = {
    "id": 1,
    "user_id": 1,
    "start_point": "Москва",
    "end_point": "Санкт-Петербург",
    "waypoints": ["Когалым"],
    "distance":1337.321123,
    "description": "Анекдот",
    "created_at": "2024-03-27T08:00:00",
    "updated_at": "2024-03-27T08:00:00",
}


class RouteCreate(BaseModel):
    user_id: int
    start_point: str = Field(..., min_length=1)
    end_point: str = Field(..., min_length=1)
    waypoints: List[str] = []
    distance: float = Field(..., gt=0)
    description: Optional[str] = None

class Route(RouteCreate):
    id: int
    created_at: datetime
    updated_at: datetime



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
    
    return {"username": username, "id": id}

def check_user_exists(user_id: int):
    return  user_id in users_db


@app.post("/routes/", response_model=Route, status_code=status.HTTP_201_CREATED,  tags=["routes"])
async def create_route(route: RouteCreate, current_user: dict = Depends(get_current_user)):

    route_id = max(routes_db.keys()) + 1 if routes_db else 1
    now = datetime.now()
    
    new_route = Route(
        id=route_id,
        created_at=now,
        updated_at=now,
        **route.dict()
    )
    
    routes_db[route_id] = new_route.dict()
    return new_route


@app.get("/routes/", response_model=List[Route],  tags=["routes"])
async def get_routes(current_user: dict = Depends(get_current_user)):
    return list(routes_db.values())


@app.get("/routes/user/{user_id}", response_model=List[Route],  tags=["routes"])
async def get_user_routes(
    user_id: int,
    current_user: dict = Depends(get_current_user),
):
    

    user_routes = [
        route for route in routes_db.values()
        if route["user_id"] == user_id
    ]
    
    return user_routes


@app.get("/routes/{route_id}", response_model=Route,  tags=["routes"])
async def get_route(route_id: int, current_user: dict = Depends(get_current_user)):
    if route_id not in routes_db:
        raise HTTPException(status_code=404, detail="Route not found")
    return routes_db[route_id]


@app.patch("/routes/{route_id}", response_model=Route,  tags=["routes"])
async def update_route(
    route_id: int, 
    route: RouteCreate,
    current_user: dict = Depends(get_current_user),
):
    if route_id not in routes_db:
        raise HTTPException(status_code=404, detail="Route not found")

    
    updated_route = Route(
        id=route_id,
        created_at=routes_db[route_id]["created_at"],
        updated_at=datetime.now(),
        **route.dict()
    )
    
    routes_db[route_id] = updated_route.dict()
    return updated_route

@app.delete("/routes/{route_id}", status_code=status.HTTP_204_NO_CONTENT,  tags=["routes"])
async def delete_route(route_id: int, current_user: dict = Depends(get_current_user)):
    if route_id not in routes_db:
        raise HTTPException(status_code=404, detail="Route not found")
    
    del routes_db[route_id]

    