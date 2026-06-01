"""
Fetch current weather information using the QWeather API.
For relation analysis of weather and gymnasium reservation.
"""


def get_weather(api_host, private_key, kid, project_id, location):
    """Fetch current weather information from the weather API.

    Args:
        api_host (str): The weather API host.
        private_key (str): The PEM-formatted private key.
        kid (str): The Key ID for the JWT header.
        project_id (str): The subject claim for the JWT.
        location (str): The location query.
        location (str): The location query.

    Returns:
        dict or None: Parsed weather data on success, otherwise None.
    """
    import requests
    from weather_jtw import generate_jwt

    url = f"https://{api_host}/v7/weather/now"

    params = {
        "location": location,
    }
    jwt_token = generate_jwt(private_key, kid, project_id)
    headers = {"Authorization": f"Bearer {jwt_token}"}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("code") == "200":
            weather_info = data.get("now", {})
            return {
                "observation_time": weather_info.get("obsTime"),  # 观察时间
                "temperature": weather_info.get("temp"),
                "feels_like": weather_info.get("feelsLike"),  # 体感温度
                "condition": weather_info.get("text"),  # 天气状况描述
                "humidity": weather_info.get("humidity"),
                "wind_speed": weather_info.get("windSpeed"),
                "wind_scale": weather_info.get("windScale"),  # 风力等级
                "precipitation": weather_info.get("precip"),  # 降水量
                "visibility": weather_info.get("vis"),
            }
        else:
            print(f"Failed to get weather data: {data.get('message')}")
            return None
    except requests.RequestException as e:
        print(f"Error while fetching weather data: {e}")
        return None


def get_air_quality(api_host, private_key, kid, project_id, location):
    """Fetch current air quality information from the weather API.

    Args:
        api_host (str): The weather API host.
        private_key (str): The PEM-formatted private key.
        kid (str): The Key ID for the JWT header.
        project_id (str): The subject claim for the JWT.
        location (str): The location query.
    """
    import requests
    from weather_jtw import generate_jwt

    longitude, latitude = location.split(",")
    url = f"https://{api_host}/airquality/v1/current/{latitude}/{longitude}"

    jwt_token = generate_jwt(private_key, kid, project_id)
    # print(f"Generated JWT for Air Quality API: {jwt_token}")
    headers = {"Authorization": f"Bearer {jwt_token}"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        # print(f"Air Quality API Response: {data}")
        if "indexes" in data and len(data["indexes"]) > 0:
            air_info = data["indexes"][0]
            return {
                "name": air_info.get("name"),  # 空气质量等级名称
                "aqi": air_info.get("aqi"),  # 空气质量指数
                "level": air_info.get("level"),  # 空气质量等级
                "category": air_info.get("category"),  # 空气质量类别
            }
        else:
            print(f"Failed to get air quality data: {data.get('message')}")
            return None
    except requests.RequestException as e:
        print(f"Error while fetching air quality data: {e}")
        return None


if __name__ == "__main__":
    import json
    import os
    from dotenv import load_dotenv

    load_dotenv(override=True)
    weather_config = json.loads(os.getenv("WEATHER_CONFIG", "{}"))
    # print(f"Loaded weather configuration: {weather_config}")
    my_location = weather_config.get("location")
    my_api_host = weather_config.get("API_HOST")
    my_private_key = weather_config.get("PRIVATE_KEY")
    my_kid = weather_config.get("JWT_KID")
    my_project_id = weather_config.get("PROJECT_ID")

    weather_data = get_weather(
        my_api_host, my_private_key, my_kid, my_project_id, my_location
    )
    air_quality_data = get_air_quality(
        my_api_host,
        my_private_key,
        my_kid,
        my_project_id,
        my_location,
    )

    if weather_data:
        print(f"Observation Time: {weather_data['observation_time']}")
        print(f"Current Weather at {my_location}:")
        print(f"Temperature: {weather_data['temperature']}°C")
        print(f"Feels Like: {weather_data['feels_like']}°C")
        print(f"Condition: {weather_data['condition']}")
        print(f"Humidity: {weather_data['humidity']}%")
        print(f"Wind Speed: {weather_data['wind_speed']} km/h")
        print(f"Wind Scale: {weather_data['wind_scale']}")
        print(f"Precipitation: {weather_data['precipitation']} mm")
        print(f"Visibility: {weather_data['visibility']} km")
    if air_quality_data:
        print(f"Air Quality at {my_location}:")
        print(f"Name: {air_quality_data['name']}")
        print(f"Category: {air_quality_data['category']}")
        print(f"AQI: {air_quality_data['aqi']}")
        print(f"Level: {air_quality_data['level']}")
