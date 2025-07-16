import requests
import pandas as pd
import openmeteo_requests
import requests_cache
from retry_requests import retry

from django.shortcuts import render
from .models import WeatherQuery

def get_weather_description(wmo_code):
    descriptions = {
        0: "Ясно",
        1: "Преимущественно ясно",
        2: "Переменная облачность",
        3: "Пасмурно",
        45: "Туман",
        48: "Изморозь",
        51: "Легкая морось",
        53: "Умеренная морось",
        55: "Сильная морось",
        61: "Небольшой дождь",
        63: "Умеренный дождь",
        65: "Сильный дождь",
        71: "Небольшой снегопад",
        73: "Умеренный снегопад",
        75: "Сильный снегопад",
        80: "Небольшие ливни",
        81: "Умеренные ливни",
        82: "Сильные ливни",
        95: "Гроза",
    }
    return descriptions.get(wmo_code, "Неизвестное явление")


def weather_view(request):
    weather_data = None
    error_message = None

    if request.method == 'POST':
        city = request.POST.get('city')

        try:
            geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
            geocoding_params = {'name': city, 'count': 1, 'language': 'ru', 'format': 'json'}
            geo_response = requests.get(geocoding_url, params=geocoding_params)
            geo_response.raise_for_status()
            geo_data = geo_response.json()

            if not geo_data.get('results'):
                raise ValueError(f"Город '{city}' не найден.")

            location = geo_data['results'][0]
            latitude = location['latitude']
            longitude = location['longitude']
            city_name_found = location['name']

            cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
            retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
            openmeteo = openmeteo_requests.Client(session=retry_session)

            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "current": ["temperature_2m", "weather_code"]
            }
            responses = openmeteo.weather_api(url, params=params)
            response = responses[0]

            current = response.Current()
            current_temperature = current.Variables(0).Value()
            current_weather_code = int(current.Variables(1).Value())

            weather_data = {
                'city': city_name_found,
                'temperature': round(current_temperature, 2),
                'description': get_weather_description(current_weather_code)
            }

            WeatherQuery.objects.create(
                city_name=weather_data['city'],
                temperature=weather_data['temperature'],
                description=weather_data['description']
            )

        except ValueError as e:
            error_message = str(e)
        except requests.exceptions.RequestException:
            error_message = "Ошибка сети или API геокодирования недоступен."
        except Exception as e:
            error_message = f"Произошла непредвиденная ошибка: {e}"

    context = {
        'weather': weather_data,
        'error': error_message
    }
    return render(request, 'weather.html', context)


def history_view(request):
    queries = WeatherQuery.objects.all()
    return render(request, 'history.html', {'queries': queries})


