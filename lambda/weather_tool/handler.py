"""
Weather MCP Tool Lambda Handler

Fetches weather forecasts and climate risk data for travel destinations.
"""

import json
import os
import boto3
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List
from dateutil import parser


# Initialize AWS clients
s3_client = boto3.client('s3')

# Environment variables
WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY', '')
WEATHER_API_BASE_URL = os.environ.get('WEATHER_API_BASE_URL', 'https://api.openweathermap.org/data/2.5')
S3_BUCKET = os.environ.get('S3_HISTORICAL_DATA_BUCKET', 'weather-wise-historical-data')


def validate_input(destination: str, start_date: str, end_date: str) -> tuple[bool, str]:
    """
    Validate input parameters according to ValidateRequest algorithm from design.
    
    Validates:
    - Required parameters present and non-empty
    - Dates can be in past or future
    - end_date is after start_date
    - Travel window does not exceed 30 days
    - Destination is recognized location (basic validation)
    
    Args:
        destination: Destination city or IATA code
        start_date: Start date in ISO 8601 format
        end_date: End date in ISO 8601 format
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate required parameters
    if not destination or not isinstance(destination, str):
        return False, "Missing required parameter: destination"
    
    if not start_date or not isinstance(start_date, str):
        return False, "Missing required parameter: travel_window with start_date and end_date"
    
    if not end_date or not isinstance(end_date, str):
        return False, "Missing required parameter: travel_window with start_date and end_date"
    
    # Validate date formats and logic
    try:
        start = parser.parse(start_date).date()
        end = parser.parse(end_date).date()
        
        # Validate end_date after start_date
        if end < start:
            return False, "Travel window end_date must be after start_date"
        
        # Validate travel window does not exceed 30 days
        if (end - start).days > 30:
            return False, "Travel window cannot exceed 30 days"
            
    except (ValueError, TypeError) as e:
        return False, f"Invalid date format: {str(e)}"
    
    # Basic destination validation (check if it's a reasonable string)
    destination_clean = destination.strip()
    if len(destination_clean) < 2:
        return False, "Invalid destination: must be IATA code or recognized city name"
    
    # Check if it looks like an IATA code (3 uppercase letters) or a city name
    is_iata = len(destination_clean) == 3 and destination_clean.isupper() and destination_clean.isalpha()
    is_city = len(destination_clean) >= 2 and any(c.isalpha() for c in destination_clean)
    
    if not (is_iata or is_city):
        return False, "Invalid destination: must be IATA code or recognized city name"
    
    return True, ""


def fetch_weather_forecast(destination: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Fetch weather forecast from WeatherAPI.com (supports up to 14 days future forecast).
    
    Args:
        destination: Destination city or IATA code
        start_date: Start date in ISO 8601 format
        end_date: End date in ISO 8601 format
        
    Returns:
        List of daily forecast data
    """
    forecast_data = []
    
    # Parse dates
    start = parser.parse(start_date).date()
    end = parser.parse(end_date).date()
    today = datetime.now().date()
    
    # WeatherAPI.com endpoint
    # Free tier supports: 3 days forecast, 14 days future (with paid plan)
    base_url = "http://api.weatherapi.com/v1"
    
    try:
        # Determine if we need forecast or future API
        days_from_now = (start - today).days
        
        if days_from_now <= 3:
            # Use forecast API for next 3 days
            url = f"{base_url}/forecast.json"
            params = {
                'key': WEATHER_API_KEY,
                'q': destination,
                'days': min((end - start).days + 1, 3),
                'aqi': 'no',
                'alerts': 'yes'
            }
        else:
            # Use future API for 14-300 days ahead (requires paid plan)
            # For free tier, we'll use current + forecast as best estimate
            url = f"{base_url}/forecast.json"
            params = {
                'key': WEATHER_API_KEY,
                'q': destination,
                'days': 3,  # Max for free tier
                'aqi': 'no',
                'alerts': 'yes'
            }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Process forecast data
        if 'forecast' in data and 'forecastday' in data['forecast']:
            for day_data in data['forecast']['forecastday']:
                date_str = day_data['date']
                day_date = parser.parse(date_str).date()
                
                if day_date < start or day_date > end:
                    continue
                
                forecast_data.append({
                    'date': date_str,
                    'temp_high': day_data['day']['maxtemp_c'],
                    'temp_low': day_data['day']['mintemp_c'],
                    'precipitation_prob': day_data['day'].get('daily_chance_of_rain', 0),
                    'conditions': day_data['day']['condition']['text'],
                    'wind_speed': day_data['day']['maxwind_kph'],
                    'humidity': day_data['day']['avghumidity'],
                    'visibility': day_data['day']['avgvis_km']
                })
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather forecast: {str(e)}")
        # Return empty forecast on API failure
        
    return forecast_data


def assess_climate_risks(forecast: List[Dict[str, Any]]) -> Dict[str, bool]:
    """
    Assess climate risks based on forecast data.
    
    Args:
        forecast: List of daily forecast data
        
    Returns:
        Dictionary of climate risk flags
    """
    risks = {
        'storms': False,
        'heavy_rain': False,
        'extreme_heat': False,
        'monsoon': False,
        'poor_visibility': False
    }
    
    if not forecast:
        return risks
    
    for day in forecast:
        # Check for storms
        if day['conditions'] in ['Thunderstorm', 'Squall', 'Tornado']:
            risks['storms'] = True
        
        # Check for heavy rain
        if day['conditions'] == 'Rain' and day['precipitation_prob'] > 70:
            risks['heavy_rain'] = True
        
        # Check for extreme heat (>35°C)
        if day['temp_high'] > 35:
            risks['extreme_heat'] = True
        
        # Check for monsoon conditions (heavy rain + high humidity)
        if day['precipitation_prob'] > 80 and day['humidity'] > 85:
            risks['monsoon'] = True
        
        # Check for poor visibility (<2km)
        if day['visibility'] < 2:
            risks['poor_visibility'] = True
    
    return risks


def get_historical_disruption_rate(destination: str, start_date: str) -> float:
    """
    Retrieve historical disruption rate from S3.
    
    Args:
        destination: Destination city or IATA code
        start_date: Start date to determine season
        
    Returns:
        Historical disruption rate (0-100)
    """
    try:
        # Parse date to determine season
        date = parser.parse(start_date)
        month = date.month
        
        # Determine season
        if month in [12, 1, 2]:
            season = 'winter'
        elif month in [3, 4, 5]:
            season = 'spring'
        elif month in [6, 7, 8]:
            season = 'summer'
        else:
            season = 'fall'
        
        # Construct S3 key
        s3_key = f"weather/{destination}/{date.year}/{month:02d}/disruption_rates.json"
        
        # Fetch from S3
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=s3_key)
        data = json.loads(response['Body'].read().decode('utf-8'))
        
        return data.get('disruption_rate', 0)
        
    except Exception as e:
        print(f"Error fetching historical disruption rate: {str(e)}")
        # Return default value if S3 fetch fails
        return 10.0  # Default 10% disruption rate


def list_activated_risks(climate_risks: Dict[str, bool]) -> str:
    """
    Generate a human-readable list of activated climate risks.
    
    Args:
        climate_risks: Dictionary of climate risk flags
        
    Returns:
        Comma-separated string of activated risks
    """
    risk_names = {
        'storms': 'storms',
        'heavy_rain': 'heavy rain',
        'extreme_heat': 'extreme heat',
        'monsoon': 'monsoon conditions',
        'poor_visibility': 'poor visibility'
    }
    
    activated = [
        risk_names[key] 
        for key, value in climate_risks.items() 
        if value and key in risk_names
    ]
    
    if not activated:
        return ""
    elif len(activated) == 1:
        return activated[0]
    elif len(activated) == 2:
        return f"{activated[0]} and {activated[1]}"
    else:
        return ", ".join(activated[:-1]) + f", and {activated[-1]}"


def generate_comfort_advisory(forecast: List[Dict[str, Any]]) -> str:
    """
    Generate comfort advisory based on weather conditions.
    
    Algorithm from design:
    - Calculate average temperature, max precipitation probability, average humidity
    - Generate comfort factors based on thresholds:
      - Cold: avg_temp < 10°C
      - Pleasant: 18°C <= avg_temp <= 26°C
      - Heat: avg_temp > 35°C
      - Rain: max_precip_prob > 70% (high), > 40% (possible)
      - Humidity: avg_humidity > 80%
    
    Args:
        forecast: List of daily forecast data
        
    Returns:
        Formatted advisory string with comfort factors
    """
    if not forecast:
        return "No forecast data available"
    
    # Calculate average temperature (mean of highs and lows)
    temps = []
    for day in forecast:
        avg_day_temp = (day['temp_high'] + day['temp_low']) / 2
        temps.append(avg_day_temp)
    avg_temp = sum(temps) / len(temps)
    
    # Calculate max precipitation probability
    max_precip_prob = max(day['precipitation_prob'] for day in forecast)
    
    # Calculate average humidity
    avg_humidity = sum(day['humidity'] for day in forecast) / len(forecast)
    
    # Generate comfort factors
    comfort_factors = []
    
    # Temperature assessment
    if avg_temp < 10:
        comfort_factors.append(f"Cold temperatures ({avg_temp:.0f}°C) - pack warm clothing")
    elif avg_temp > 35:
        comfort_factors.append(f"Extreme heat ({avg_temp:.0f}°C) - stay hydrated")
    elif 18 <= avg_temp <= 26:
        comfort_factors.append(f"Pleasant temperatures ({avg_temp:.0f}°C)")
    else:
        comfort_factors.append(f"Temperatures {avg_temp:.0f}°C")
    
    # Precipitation assessment
    if max_precip_prob > 70:
        comfort_factors.append("High chance of rain - bring umbrella")
    elif max_precip_prob > 40:
        comfort_factors.append("Possible rain showers")
    
    # Humidity assessment
    if avg_humidity > 80:
        comfort_factors.append("High humidity - may feel uncomfortable")
    
    # Join factors into advisory string
    advisory = ", ".join(comfort_factors)
    
    return advisory


def calculate_weather_risk(weather_data: Dict[str, Any]) -> tuple[str, str]:
    """
    Calculate weather risk level based on disruption probability and climate risks.
    
    Algorithm from design:
    - High: disruption_prob > 40 OR severe_risk_detected
    - Medium: disruption_prob >= 15 AND disruption_prob <= 40
    - Low: disruption_prob < 15 AND no severe risks
    
    Args:
        weather_data: Dictionary containing historical_disruption_rate and climate_risks
        
    Returns:
        Tuple of (risk_level, explanation)
    """
    disruption_prob = weather_data.get('historical_disruption_rate', 0)
    climate_risks = weather_data.get('climate_risks', {})
    
    # Check if any severe risk is detected
    severe_risk_detected = any([
        climate_risks.get('storms', False),
        climate_risks.get('heavy_rain', False),
        climate_risks.get('extreme_heat', False),
        climate_risks.get('monsoon', False),
        climate_risks.get('poor_visibility', False)
    ])
    
    # Classify risk level
    if disruption_prob > 40 or severe_risk_detected:
        risk_level = "High"
        activated_risks = list_activated_risks(climate_risks)
        if activated_risks:
            explanation = f"High disruption risk ({disruption_prob:.0f}%) with {activated_risks}"
        else:
            explanation = f"High disruption risk ({disruption_prob:.0f}%)"
    elif 15 <= disruption_prob <= 40:
        risk_level = "Medium"
        explanation = f"Moderate disruption risk ({disruption_prob:.0f}%)"
    else:
        risk_level = "Low"
        explanation = f"Minimal disruption risk ({disruption_prob:.0f}%)"
    
    return risk_level, explanation


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for Weather MCP Tool.
    
    Args:
        event: Lambda event containing destination, start_date, end_date
        context: Lambda context
        
    Returns:
        MCPToolResponse with weather data or error
    """
    try:
        # Extract parameters
        parameters = event.get('parameters', {})
        destination = parameters.get('destination')
        start_date = parameters.get('start_date')
        end_date = parameters.get('end_date')
        
        # Validate inputs
        is_valid, error_msg = validate_input(destination, start_date, end_date)
        if not is_valid:
            return {
                'success': False,
                'error': {
                    'code': 'INVALID_INPUT',
                    'message': error_msg
                }
            }
        
        # Fetch weather forecast from external API
        forecast = fetch_weather_forecast(destination, start_date, end_date)
        
        # Assess climate risks
        climate_risks = assess_climate_risks(forecast)
        
        # Get historical disruption rate from S3
        historical_disruption_rate = get_historical_disruption_rate(destination, start_date)
        
        # Calculate weather risk
        weather_data = {
            'forecast': forecast,
            'climate_risks': climate_risks,
            'historical_disruption_rate': historical_disruption_rate
        }
        risk_level, risk_explanation = calculate_weather_risk(weather_data)
        
        # Generate comfort advisory
        comfort_advisory = generate_comfort_advisory(forecast)
        
        # Return structured response
        return {
            'success': True,
            'data': {
                'forecast': forecast,
                'climate_risks': climate_risks,
                'historical_disruption_rate': historical_disruption_rate,
                'weather_risk': risk_level,
                'weather_risk_explanation': risk_explanation,
                'comfort_advisory': comfort_advisory
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': str(e)
            }
        }
