from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
import requests

from database import SessionLocal
import models

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.delete("/city")
def delete_city(city_name:str, db: Session = Depends(get_db)):
    city_name = city_name.lower()
    city_data = db.query(models.city).filter(models.city.name==city_name).first()
    if city_data is None:
        raise HTTPException(status_code=404, detail="City not found")

    db.delete(city_data)
    db.commit()
    return {"message":"Deleted Successfully"}
# this is to get a particular city using city_id
# @app.get("/cities/{city_id}")
# def get_city(city_id:str,db:Session=Depends(get_db)):
#     city_data=db.query(models.city).filter(models.city.city_id==city_id).first()
#     if city_data is None:
#         raise HTTPException(status_code=404, detail="City not found")
#     response_data = {
#         "id": city_data.city_id,
#         "name": city_data.name,
#         "long": city_data.long,
#         "lat": city_data.lat,
#         "country": city_data.country
#     }
#     return response_data

# this is for getting all the cities
@app.get("/cities")
def get_city( db: Session = Depends(get_db)):
    import pdb; pdb.set_trace()
    city_data=db.query(models.city).filter()
    if  not city_data :
        raise HTTPException(status_code=404, detail="City not found")
    response_Data=[]
    for data in city_data:
        weather = db.query(models.weather).filter(models.weather.city_id == data.city_id).first()
        weather_info = db.query(models.weather_info).filter(models.weather_info.x   ==data.city_id).first()
        wind_info = db.query(models.wind_info).filter(models.wind_info.city_id == data.city_id).first()

        cur_data = {
            "id": data.city_id,
            "name":data.name,
            "long":data.long,
            "lat":data.lat,
            "country":data.country,
            "weather": {
                "weather_id":weather.weather_id,
                "main":weather.main,
                "description":weather.description
            },
            "weather_info":{
                    "temp":weather_info.temp,
                    "feels_like":weather_info.feels_like,
                    "temp_min":weather_info.temp_min,
                    "temp_max":weather_info.temp_max,
                    "humidity":weather_info.humidity
            },
            "wind_info":{
                "speed":wind_info.speed,
                "gust":wind_info.gust
            }
        }
        response_Data.append(cur_data)
    return response_Data


@app.post("/sync-weather")
def sync_weather(cities: List[str], db: Session = Depends(get_db)):
    API_KEY = "023c9c13319858500d625d1f1b79a09b"
    URL = "http://api.openweathermap.org/data/2.5/weather"
    stored = []

    for city_name in cities:
        params = {"q": city_name, "appid": API_KEY, "units": "metric"}
        res = requests.get(URL, params=params)
        if res.status_code != 200:
            raise HTTPException(status_code=404, detail=f"City {city_name} not found")
        import pdb;pdb.set_trace()
        data = res.json()

        city = models.city(
            name=data["name"].lower(),
            city_id=str(data["id"]),
            long=data["coord"]["lon"],
            lat=data["coord"]["lat"],
            country=data["sys"]["country"],
        )

        weather = models.weather(
            city_id=str(data["id"]),
            weather_id=str(data["id"]),
            description=data["weather"][0]["description"],
            main=data["weather"][0]["main"]
        )
        weather_info =models.weather_info(
            city_id=str(data["id"]),
            temp=data["main"]["temp"],
            feels_like=data["main"]["feels_like"],
            temp_min=data["main"]["temp_min"],
            temp_max=data["main"]["temp_max"],
            humidity=data["main"]["humidity"]
        )
        wind_info=models.wind_info(
            city_id=str(data["id"]),
            speed=data["wind"]["speed"],
            gust=data["wind"]["gust"]
        )
        db.merge(city)
        db.merge(weather)
        db.merge(weather_info)
        db.merge(wind_info)
        db.commit()
        stored.append(city_name)

    return {"success": True, "message": "Data stored", "cities": stored}
