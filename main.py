import requests
from datetime import datetime

API_KEY = "e269e838e12a130d3319afa425f20a8b"
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "http://api.openweathermap.org/data/2.5/forecast"

def kelvin_to_celsius(kelvin):
    return round(kelvin - 273.15, 2)

def get_weather(city):
    params = {
        'q': city,
        'appid': API_KEY
    }
    response = requests.get(BASE_URL, params=params)
    
    if response.status_code == 200:
        data = response.json()
        
        location = f"{data['name']}, {data['sys']['country']}"
        temp = kelvin_to_celsius(data['main']['temp'])
        feels_like = kelvin_to_celsius(data['main']['feels_like'])
        temp_min = kelvin_to_celsius(data['main']['temp_min'])
        temp_max = kelvin_to_celsius(data['main']['temp_max'])
        pressure = data['main']['pressure']
        humidity = data['main']['humidity']
        visibility = data.get('visibility', 'N/A')
        wind_speed = data['wind']['speed']
        description = data['weather'][0]['description']
        icon = data['weather'][0]['icon']
        clouds = data['clouds']['all']
        
        sunrise = datetime.fromtimestamp(data['sys']['sunrise']).strftime('%H:%M:%S')
        sunset = datetime.fromtimestamp(data['sys']['sunset']).strftime('%H:%M:%S')
        
        print(f"\nWeather in {location}")
        print("-" * 40)
        print(f"Temperature     : {temp}°C (feels like {feels_like}°C)")
        print(f"Min Temp        : {temp_min}°C")
        print(f"Max Temp        : {temp_max}°C")
        print(f"Wind Speed     : {wind_speed} m/s")
        print(f"Pressure        : {pressure} hPa")
        print(f"Humidity        : {humidity}%")
        print(f"Visibility      : {visibility} meters")
        print(f"Description     : {description}")
        print(f"Sunrise         : {sunrise}")
        print(f"Sunset          : {sunset}")
        print(f"Cloud Cover     : {clouds}%")
        print(f"Icon Code       : {icon}")
        print("-" * 40)
    else:
        print("⚠️ Not found. Could not fetch weather data. Check the city name. To make search more precise put the city's name, comma, 2-letter country code")

def get_5daysweather(city):
    params = {
        'q':city,
        'appid': API_KEY
    }

    response = requests.get(FORECAST_URL, params=params)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n5-Day Forecast for {data['city']['name']}, {data['city']['country']}")
        print("-" * 40)

        # print(data)
        printed_dates = set()
        for entry in data['list']:
            dt_txt = entry['dt_txt']
            date = dt_txt.split()[0]
            time = dt_txt.split()[1]
            if time == "12:00:00" and date not in printed_dates:
                printed_dates.add(date)
                temp = kelvin_to_celsius(entry['main']['temp'])
                desc = entry['weather'][0]['description']
                icon = entry['weather'][0]['icon']
                readable_date = datetime.strptime(date, "%Y-%m-%d").strftime("%A, %b %d")
                print(f"{readable_date}")
                print(f"Temp     : {temp}°C")
                print(f"Weather  : {desc}")
                print(f"Icon     : {icon}")
                print("-" * 30)
    else:
        print("⚠️  Could not fetch forecast. Try again.")

def get_hourly_forecast(city):
    params = {
        'q': city,
        'appid': API_KEY
    }
    response = requests.get(FORECAST_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        print(f"\nHourly Forecast for {data['city']['name']}, {data['city']['country']}")
        print("-" * 50)
        for entry in data['list'][:8]:  # every 3 hours data available, so next 24 hours
            time = datetime.strptime(entry['dt_txt'], "%Y-%m-%d %H:%M:%S").strftime("%I %p")
            temp = kelvin_to_celsius(entry['main']['temp'])
            desc = entry['weather'][0]['description']
            wind = entry['wind']['speed']
            print(f"{time} | {temp}°C | {desc.capitalize():<20} | {wind} m/s")
        print("-" * 50)
    else:
        print("⚠️ Could not fetch hourly forecast.")


def get_current_location():
    try:
        res = requests.get("http://ip-api.com/json")
        data = res.json()
        if data['status'] == "success":
            return data['city']
        else:
            return None
    except:
        return None


# MAIN
city_name = input("Enter a city name: ")
# city_name = get_current_location()
if city_name:
    print(f"📍 Detected location: {city_name}")
else:
    print("⚠️ Could not detect location. Defaulting to New York.")
    city_name = "New York."
# get_weather(city_name)
# get_5daysweather(city_name)
# get_weather(city_name)
get_hourly_forecast(city_name)
