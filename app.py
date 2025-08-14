import requests
import os
from dotenv import load_dotenv

from collections import defaultdict
from flask import Flask, render_template, request, jsonify
from datetime import datetime, timezone

app = Flask(__name__)

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
REVERSE_URL = "http://api.openweathermap.org/geo/1.0/reverse"
ZIP_URL = "https://api.openweathermap.org/geo/1.0/zip"
FORECAST_URL = "http://api.openweathermap.org/data/2.5/forecast"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/weather', methods=['POST'])
def get_weather():
    data = request.get_json()
    city = data.get('location')
    lat = data.get('lat')
    lon = data.get('lon')
    units = data.get('units', 'metric')

    zip_code = data.get('zip')
    country = data.get('country', 'us')

    params = {
        'appid': API_KEY,
        'units': units
    }

    forecast_params = {
        'appid': API_KEY,
        'units': units,
    }

    if lat is not None and lon is not None:
        params['lat'] = lat
        params['lon'] = lon

        forecast_params['lat'] = lat
        forecast_params['lon'] = lon
    elif zip_code:
        params['zip'] = f"{zip_code},{country}"
        forecast_params['zip'] = f"{zip_code},{country}"

    elif city:
        params['q'] = city
        forecast_params['q'] = city
    else:
        return jsonify({'error': 'Please enter location to fetch weather data'}), 400

    try:
        response = requests.get(BASE_URL, params=params)

        if response.status_code != 200:
            weather_error = response.json()
            return jsonify({'error': weather_error.get('message', 'Weather info not found')}), 404
        else:
            weather = response.json()
            # print("\nRESPONSE:", weather)

            # Convert time(s) using timezone offset
            def format_time(unix_time, timezone_offset):
                return datetime.fromtimestamp(unix_time + timezone_offset, tz=timezone.utc).strftime('%I:%M %p')

            def format_local_time(unix_time, timezone_offset):
                return datetime.fromtimestamp(unix_time + timezone_offset, tz=timezone.utc).strftime('%a, %b %d %I:%M %p')

            result = {
                "location": f"{weather['name']}, {weather['sys']['country']}",
                "temp": weather['main']['temp'],
                "temp_min": weather['main']['temp_min'],
                "temp_max": weather['main']['temp_max'],
                "feels_like": weather['main']['feels_like'],
                "description": weather['weather'][0]['description'],
                "wind_speed": weather['wind']['speed'],
                "pressure": weather['main']['pressure'],
                "humidity": weather['main']['humidity'],
                "visibility": weather.get('visibility', 'N/A'),
                "sunrise": format_time(weather['sys']['sunrise'], weather['timezone']),
                "sunset": format_time(weather['sys']['sunset'], weather['timezone']),
                "local_time": format_local_time(weather['dt'], weather['timezone']),
                "weather_icon": weather['weather'][0]['icon']
            }

            forecast_response = requests.get(FORECAST_URL, params=forecast_params)
            # print("\n5 DAY FORECAST:", forecast_response)

            if forecast_response.status_code != 200:
                forecast_error = forecast_response.json()
                print("Forecast error:", forecast_error)
                result["daily"] = []
            else:
                forecast_data = forecast_response.json()
                # print("\nFORECAST DATA:", forecast_data)
                for entry in forecast_data['list']:
                    print(entry['dt_txt'])
                result["daily"] = process_forecast_data(forecast_data)

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

from datetime import datetime, timedelta
from collections import defaultdict

def process_forecast_data(forecast_data):
    grouped = defaultdict(list)

    # Group forecast entries by date
    for entry in forecast_data['list']:
        date_str = datetime.fromtimestamp(entry['dt']).strftime('%Y-%m-%d')
        grouped[date_str].append(entry)

    daily_forecast = []

    today_str = datetime.now().strftime('%Y-%m-%d')

    # Sort dates to process in chronological order
    sorted_dates = sorted(grouped.keys())

    # Start from the next day after today
    for date_str in sorted_dates:
        if date_str <= today_str:
            continue  # Skip today and past dates

        entries = grouped[date_str]

        # Find the entry closest to 15:00:00
        noon_entry = None
        for e in entries:
            dt_txt = e.get('dt_txt', '')
            if '15:00:00' in dt_txt:
                noon_entry = e
                break

        if not noon_entry:
            for e in entries:
                dt_txt = e.get('dt_txt', '')
                if '18:00:00' in dt_txt:
                    noon_entry = e
                    break

        # If still not found, fallback to the first entry of the day
        if not noon_entry:
            noon_entry = entries[0]

        temps = [e['main']['temp'] for e in entries]
        min_temp = round(min(temps))
        max_temp = round(max(temps))
        description = noon_entry['weather'][0]['description']
        icon = noon_entry['weather'][0]['icon']
        wind = round(noon_entry['wind']['speed'], 1)
        pop = int(noon_entry.get('pop', 0) * 100)

        daily_forecast.append({
            "date": date_str,
            "temp_min": min_temp,
            "temp_max": max_temp,
            "description": description,
            "icon": icon,
            "wind_speed": wind,
            "pop": pop
        })

        # Stop after 7 days or 8 days, adjust as needed
        if len(daily_forecast) >= 7:
            break

    return daily_forecast


if __name__ == '__main__':
    app.run(debug=True)
