import requests

from datetime import datetime, timezone, timedelta
from database import *

import json
import csv
import os

API_KEY = "e269e838e12a130d3319afa425f20a8b"
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

def validate_date(date_string):
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def validate_date_range(start_date, end_date):
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        today = datetime.now().date()
        max_future_date = today + timedelta(days=5)
        
        if start.date() > end.date():
            return False, "Start date must be before or equal to end date"
        
        if start.date() < today:
            return False, "Start date cannot be in the past"
        
        if end.date() > max_future_date:
            return False, "End date cannot be more than 5 days in the future"
        
        return True, "Valid date range"
    except ValueError:
        return False, "Invalid date format"

def validate_location(location_type, location):
    """Validate location exists by making API call"""
    params = {
        'appid': API_KEY,
        'units': 'metric'
    }
    
    if location_type == 'city':
        params['q'] = location
    elif location_type == 'zip':
        # Assume US if no country code provided
        if ',' not in location:
            location = f"{location},US"
        params['zip'] = location
    elif location_type == 'latlon':
        try:
            lat, lon = map(float, location.split(','))
            params['lat'] = lat
            params['lon'] = lon
        except ValueError:
            return False, "Invalid lat/lon format. Use: latitude,longitude"
    
    try:
        response = requests.get(BASE_URL, params=params)
        if response.status_code == 200:
            data = response.json()
            actual_location = f"{data['name']}, {data['sys']['country']}"
            return True, actual_location
        else:
            return False, f"Location not found: {response.json().get('message', 'Unknown error')}"
    except Exception as e:
        return False, f"Error validating location: {str(e)}"

def fetch_weather_data_range(location_type, location, start_date, end_date):
    params = {
        'appid': API_KEY,
        'units': 'metric'
    }
    
    if location_type == 'city':
        params['q'] = location
    elif location_type == 'zip':
        if ',' not in location:
            location = f"{location},US"
        params['zip'] = location
    elif location_type == 'latlon':
        lat, lon = map(float, location.split(','))
        params['lat'] = lat
        params['lon'] = lon
    
    try:
        response = requests.get(FORECAST_URL, params=params)
        if response.status_code != 200:
            return None
        
        forecast_data = response.json()
        
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        daily_data = {}
        for entry in forecast_data['list']:
            entry_date = datetime.fromtimestamp(entry['dt']).date()
            
            if start <= entry_date <= end:
                if entry_date not in daily_data:
                    daily_data[entry_date] = []
                daily_data[entry_date].append(entry)
        
        weather_data_list = []
        current_date = start
        
        while current_date <= end:
            if current_date in daily_data:
                day_entries = daily_data[current_date]
                
                midday_entry = None
                for entry in day_entries:
                    entry_hour = datetime.fromtimestamp(entry['dt']).hour
                    if entry_hour >= 12:  # Take 3PM weather data
                        midday_entry = entry
                        break
                
                if not midday_entry:
                    midday_entry = day_entries[0]  # Fallback to first entry
                
                temps = [e['main']['temp'] for e in day_entries]
                temp_min = min(temps)
                temp_max = max(temps)
                
                timezone_offset = forecast_data['city']['timezone']
                local_time = datetime.fromtimestamp(
                    midday_entry['dt'] + timezone_offset, tz=timezone.utc
                ).strftime('%a, %b %d %I:%M %p')
                
                day_weather = {
                    "date": current_date.strftime('%Y-%m-%d'),
                    "temp": round(midday_entry['main']['temp'], 1),
                    "temp_min": round(temp_min, 1),
                    "temp_max": round(temp_max, 1),
                    "feels_like": round(midday_entry['main']['feels_like'], 1),
                    "description": midday_entry['weather'][0]['description'],
                    "local_time": local_time,
                    "weather_icon": midday_entry['weather'][0]['icon']
                }
                
                weather_data_list.append(day_weather)
            
            current_date += timedelta(days=1)
        
        return weather_data_list
        
    except Exception as e:
        print(f"Error fetching weather data: {str(e)}")
        return None

def create_record():
    print("\n" + "="*50)
    print("CREATE NEW WEATHER RECORDS")
    print("="*50)
    
    base_label = input("Enter base label (e.g., 'NYC Trip'): ").strip()
    if not base_label:
        base_label = "Weather Record"
    
    print("\nLocation Options:")
    print("1. City name")
    print("2. ZIP code")
    print("3. Latitude,Longitude")
    
    while True:
        choice = input("Choose location type (1-3): ").strip()
        if choice == '1':
            location_type = 'city'
            break
        elif choice == '2':
            location_type = 'zip'
            break
        elif choice == '3':
            location_type = 'latlon'
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")
    
    if location_type == 'city':
        location = input("Enter city name (e.g., 'New York' or 'London,UK'): ").strip()
    elif location_type == 'zip':
        location = input("Enter ZIP code (e.g., '10001' or '10001,US'): ").strip()
    else:  # latlon
        location = input("Enter latitude,longitude (e.g., '40.7128,-74.0060'): ").strip()
    
    print("🔍 Validating location...")
    is_valid, result = validate_location(location_type, location)
    if not is_valid:
        print(f"{result}")
        return
    
    print(f"\nDate Range (Today: {datetime.now().strftime('%Y-%m-%d')}, Max: 5 days from today)")
    while True:
        start_date = input("Enter start date (YYYY-MM-DD): ").strip()
        if validate_date(start_date):
            break
        else:
            print("Invalid date format. Use YYYY-MM-DD")
    
    while True:
        end_date = input("Enter end date (YYYY-MM-DD): ").strip()
        if validate_date(end_date):
            is_valid, message = validate_date_range(start_date, end_date)
            if is_valid:
                break
            else:
                print(f"{message}")
        else:
            print("Invalid date format. Use YYYY-MM-DD")
    
    print("Fetching weather forecast data...")
    weather_data_list = fetch_weather_data_range(location_type, location, start_date, end_date)
    if not weather_data_list:
        print("Failed to fetch weather data for the specified date range")
        return
    
    print(f"Creating {len(weather_data_list)} weather records...")
    created_records = []
    
    for i, day_weather in enumerate(weather_data_list, 1):
        if len(weather_data_list) == 1:
            day_label = base_label
        else:
            day_label = f"{base_label} - Day {i}"
        
        record_id = create_weather_record(
            label=day_label,
            location_type=location_type,
            location=location,
            start_date=day_weather['date'],
            end_date=day_weather['date'],
            weather_data=day_weather
        )
        
        created_records.append((record_id, day_weather))
        # print(f"Day {i} record created (ID: {record_id})")
    
    
    print(f"\nRecords Summary:")
    print(f"Base Label: {base_label}")
    print(f"Location: {result}")
    print(f"Date Range: {start_date} to {end_date}")
    print("\nDaily Weather:")
    print("-" * 60)
    for record_id, day_data in created_records:
        print(f"ID {record_id}: {day_data['date']} - {day_data['temp']}°C ({day_data['temp_min']}-{day_data['temp_max']}°C), {day_data['description'].title()}")

def read_records():
    """Display all weather records"""
    print("\n" + "="*80)
    print("ALL WEATHER RECORDS")
    print("="*80)
    
    records = read_all_records()
    
    if not records:
        print("No weather records found.")
        return
    

    print(f"{'ID':<4} {'Label':<25} {'Location':<15} {'Date':<12} {'Temp':<8} {'Description':<15}")
    print("-" * 80)
    
    for record in records:
        print(f"{record['id']:<4} {record['label'][:24]:<25} {record['location'][:14]:<15} {record['start_date']:<12} {record['temp']:.1f}°C {record['description'][:14]:<15}")
    
    print(f"\nTotal records: {len(records)}")

def update_record():
    print("\n" + "="*50)
    print("UPDATE RECORD LABEL")
    print("="*50)
    
    records = read_all_records()
    if not records:
        print("No records available to update.")
        return
    
    print("Current records:")
    for record in records:
        print(f"ID {record['id']}: {record['label']} ({record['start_date']})")
    
    while True:
        try:
            record_id = int(input("\nEnter record ID to update: "))
            record = get_record_by_id(record_id)
            if record:
                break
            else:
                print("Record not found. Please try again.")
        except ValueError:
            print("Please enter a valid number.")
    
    print(f"Current label: '{record['label']}'")
    
    new_label = input("Enter new label: ").strip()
    if not new_label:
        print("Label cannot be empty.")
        return
    
    if update_record_label(record_id, new_label):
        print(f"Record updated successfully!")
        print(f"Old label: '{record['label']}'")
        print(f"New label: '{new_label}'")
    else:
        print("Failed to update record.")

def delete_record_menu():
    print("\n" + "="*50)
    print("DELETE WEATHER RECORD")
    print("="*50)
    
    records = read_all_records()
    if not records:
        print("No records available to delete.")
        return
    
    print("Current records:")
    for record in records:
        print(f"ID {record['id']}: {record['label']} - {record['location']} ({record['start_date']})")
    
    while True:
        try:
            record_id = int(input("\nEnter record ID to delete: "))
            record = get_record_by_id(record_id)
            if record:
                break
            else:
                print("Record not found. Please try again.")
        except ValueError:
            print("Please enter a valid number.")
    
    # Confirm deletion
    print(f"\nYou are about to delete:")
    print(f"Label: {record['label']}")
    print(f"Location: {record['location']}")
    print(f"Date: {record['start_date']}")
    print(f"Temperature: {record['temp']}°C")
    
    confirm = input("Are you sure? (yes/no): ").lower()
    if confirm in ['yes', 'y']:
        if delete_record(record_id):
            print("Record deleted successfully!")
        else:
            print("Failed to delete record.")
    else:
        print("Deletion cancelled.")

def export_to_json(records, filename=None):
    if not records:
        print("No records to export.")
        return False
    
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"weather_export_{timestamp}.json"
    
    if not filename.endswith('.json'):
        filename += '.json'
    
    try:
        os.makedirs('exports', exist_ok=True)
        filepath = os.path.join('exports', filename)
        
        export_data = {
            "export_info": {
                "exported_at": datetime.now().isoformat(),
                "total_records": len(records),
                "format": "JSON"
            },
            "weather_records": records
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return True
        
    except Exception as e:
        print(f"JSON export failed: {str(e)}")
        return False

def export_to_csv(records, filename=None):
    if not records:
        print("No records to export.")
        return False
    
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"weather_export_{timestamp}.csv"
    
    if not filename.endswith('.csv'):
        filename += '.csv'
    
    try:
        os.makedirs('exports', exist_ok=True)
        filepath = os.path.join('exports', filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            # Define CSV headers
            fieldnames = [
                'ID', 'Label', 'Location_Type', 'Location', 'Date',
                'Temperature_C', 'Min_Temp_C', 'Max_Temp_C', 'Feels_Like_C',
                'Description', 'Weather_Icon', 'Local_Time', 'Created_At'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for record in records:
                writer.writerow({
                    'ID': record['id'],
                    'Label': record['label'],
                    'Location_Type': record['location_type'],
                    'Location': record['location'],
                    'Date': record['start_date'],
                    'Temperature_C': record['temp'],
                    'Min_Temp_C': record['temp_min'],
                    'Max_Temp_C': record['temp_max'],
                    'Feels_Like_C': record['feels_like'],
                    'Description': record['description'],
                    'Weather_Icon': record['weather_icon'],
                    'Local_Time': record['local_time'],
                    'Created_At': record['created_at']
                })
        
        return True
        
    except Exception as e:
        print(f"CSV export failed: {str(e)}")
        return False

def export_data_menu():
    print("\n" + "="*50)
    print("DATA EXPORT")
    print("="*50)
    
    records = read_all_records()
    if not records:
        print("No records available to export.")
        return
    
    print(f"Found {len(records)} records to export.")
    print("\nExport Options:")
    print("1. JSON - Structured data format")
    print("2. CSV - Spreadsheet compatible")
    print("3. Both formats")
    print("4. Back to main menu")
    
    choice = input("Choose export format (1-4): ").strip()
    
    if choice == '4':
        return
    
    custom_filename = input("Enter filename (press Enter for auto-generation): ").strip()
    if not custom_filename:
        custom_filename = None
    
    success_count = 0
    
    if choice == '1':
        if export_to_json(records, custom_filename):
            success_count += 1
    elif choice == '2':
        if export_to_csv(records, custom_filename):
            success_count += 1
    elif choice == '3':
        if export_to_json(records, custom_filename):
            success_count += 1
        if export_to_csv(records, custom_filename):
            success_count += 1
    else:
        print("Invalid choice.")
        return
    
    if success_count > 0:
        print("\nExport failed.")


def main_menu():
    init_database()
    
    while True:
        print("\n" + "="*50)
        print("WEATHER APP")
        print("="*50)
        print("1. Create - Add weather records for date range")
        print("2. Read - View all saved records")
        print("3. Update - Edit record label")
        print("4. Delete - Remove record")
        print("5. Export - Save data to files")
        print("6. Exit")
        print("="*50)
        
        choice = input("Choose an option (1-6): ").strip()
        
        if choice == '1':
            create_record()
        elif choice == '2':
            read_records()
        elif choice == '3':
            update_record()
        elif choice == '4':
            delete_record_menu()
        elif choice == '5':
            export_data_menu()
        elif choice == '6':
            break
        else:
            print("Invalid choice. Please enter 1-5.")


if __name__ == "__main__":
    main_menu()
