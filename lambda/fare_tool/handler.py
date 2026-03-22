"""
Fare MCP Tool Lambda Handler

Fetches flight fare data and analyzes price trends.
"""

import json
import os
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
import boto3
import requests
from dateutil import parser


# Initialize AWS clients
s3_client = boto3.client('s3')

# Environment variables
FARE_API_KEY = os.environ.get('FARE_API_KEY', '')
FARE_API_ENDPOINT = os.environ.get('FARE_API_ENDPOINT', 'https://api.example.com/fares')
S3_BUCKET = os.environ.get('S3_BUCKET', 'weather-wise-historical-data')


def validate_input(origin: str, destination: str, start_date: str, end_date: str) -> Tuple[bool, str]:
    """
    Validate input parameters according to ValidateRequest algorithm from design.
    
    Validates:
    - Required parameters present and non-empty
    - Origin is valid IATA code (3 uppercase letters)
    - Destination is valid IATA code (3 uppercase letters)
    - Dates can be in past or future
    - end_date is after start_date
    - Travel window does not exceed 30 days
    
    Args:
        origin: Origin airport IATA code
        destination: Destination airport IATA code
        start_date: Start date in ISO 8601 format
        end_date: End date in ISO 8601 format
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate required parameters
    if not origin or not isinstance(origin, str):
        return False, "Missing required parameter: origin"
    
    if not destination or not isinstance(destination, str):
        return False, "Missing required parameter: destination"
    
    if not start_date or not isinstance(start_date, str):
        return False, "Missing required parameter: travel_window with start_date and end_date"
    
    if not end_date or not isinstance(end_date, str):
        return False, "Missing required parameter: travel_window with start_date and end_date"
    
    # Validate IATA codes (3 uppercase letters)
    if len(origin) != 3 or not origin.isupper() or not origin.isalpha():
        return False, f"Invalid origin: must be IATA airport code"
    
    if len(destination) != 3 or not destination.isupper() or not destination.isalpha():
        return False, f"Invalid destination: must be IATA airport code"
    
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
            
    except Exception as e:
        return False, f"Invalid date format: {str(e)}"
    
    return True, ""


def fetch_current_fare(origin: str, destination: str, start_date: str, end_date: str) -> float:
    """
    Generate mock fare data based on route and dates.
    
    Since we don't have a real fare API, this generates realistic mock data
    based on route distance and travel dates.
    
    Args:
        origin: Origin airport IATA code
        destination: Destination airport IATA code
        start_date: Start date in ISO 8601 format
        end_date: End date in ISO 8601 format
        
    Returns:
        Current fare price in USD
    """
    import hashlib
    
    # Generate a deterministic but varied price based on route
    route_hash = hashlib.md5(f"{origin}-{destination}".encode()).hexdigest()
    base_price = int(route_hash[:4], 16) % 400 + 200  # Range: $200-$600
    
    # Add variation based on date (simulate demand fluctuations)
    try:
        start = parser.parse(start_date)
        days_until_travel = (start.date() - datetime.now().date()).days
        
        # Prices tend to be higher closer to travel date
        if days_until_travel < 7:
            price_multiplier = 1.5
        elif days_until_travel < 14:
            price_multiplier = 1.3
        elif days_until_travel < 30:
            price_multiplier = 1.1
        else:
            price_multiplier = 1.0
        
        # Add some randomness based on day of week
        day_variation = (start.weekday() * 13) % 50  # $0-$50 variation
        
        current_price = base_price * price_multiplier + day_variation
        
        return round(current_price, 2)
        
    except Exception:
        # Fallback to base price if date parsing fails
        return float(base_price)


def fetch_historical_fares_from_s3(origin: str, destination: str, current_price: float) -> List[Dict[str, Any]]:
    """
    Generate mock historical fare data for the past 30 days.
    
    Since we don't have real historical data in S3, this generates
    realistic mock data showing price trends.
    
    Args:
        origin: Origin airport IATA code
        destination: Destination airport IATA code
        current_price: Current fare price to base historical data on
        
    Returns:
        List of historical fare records with date and price
    """
    import hashlib
    import random
    
    # Generate deterministic but varied historical prices
    route_seed = int(hashlib.md5(f"{origin}-{destination}".encode()).hexdigest()[:8], 16)
    random.seed(route_seed)
    
    historical_data = []
    today = datetime.now()
    
    # Generate prices for the past 30 days with a trend
    # Randomly choose a trend: rising, stable, or dropping
    trend_type = random.choice(['rising', 'stable', 'dropping'])
    
    for days_ago in range(30, 0, -1):
        date = today - timedelta(days=days_ago)
        
        # Calculate price based on trend
        if trend_type == 'rising':
            # Prices were lower 30 days ago, gradually increasing
            price_factor = 0.75 + (30 - days_ago) * 0.01  # 75% to 105%
        elif trend_type == 'dropping':
            # Prices were higher 30 days ago, gradually decreasing
            price_factor = 1.25 - (30 - days_ago) * 0.01  # 125% to 95%
        else:  # stable
            # Prices fluctuate around current price ±5%
            price_factor = 0.95 + random.random() * 0.1  # 95% to 105%
        
        # Add some daily noise
        daily_noise = random.uniform(-0.03, 0.03)  # ±3%
        historical_price = current_price * price_factor * (1 + daily_noise)
        
        historical_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'price': round(historical_price, 2)
        })
    
    return historical_data


def classify_fare_trend(current_price: float, price_30d_ago: float) -> Tuple[str, float, str]:
    """
    Classify fare trend and generate insight string.
    
    Implements ClassifyFareTrend algorithm from design:
    - Rising: >10% increase
    - Stable: ±10% variation
    - Dropping: >10% decrease
    
    Args:
        current_price: Current fare price
        price_30d_ago: Fare price 30 days ago
        
    Returns:
        Tuple of (trend, trend_percentage, insight)
        trend: "rising", "stable", or "dropping"
        trend_percentage: Percentage change (positive for rising, negative for dropping)
        insight: User-friendly insight string with trend direction and percentage
    """
    if price_30d_ago == 0:
        return "stable", 0.0, "Prices stable over past 30 days"
    
    # Calculate percentage change: ((current - 30d_ago) / 30d_ago) * 100
    change_pct = ((current_price - price_30d_ago) / price_30d_ago) * 100
    
    # Classify trend and generate insight based on percentage thresholds
    if change_pct > 10.0:
        trend = "rising"
        insight = f"Prices rising {round(abs(change_pct))}% over past 30 days - book soon"
    elif change_pct < -10.0:
        trend = "dropping"
        insight = f"Prices dropping {round(abs(change_pct))}% - consider waiting"
    else:
        trend = "stable"
        insight = f"Prices stable (±{round(abs(change_pct))}%) over past 30 days"
    
    return trend, round(change_pct, 2), insight


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for Fare MCP Tool.
    
    Args:
        event: Lambda event containing origin, destination, start_date, end_date
        context: Lambda context
        
    Returns:
        MCPToolResponse with fare data or error
    """
    try:
        # Extract parameters
        parameters = event.get('parameters', {})
        origin = parameters.get('origin', '').upper()
        destination = parameters.get('destination', '').upper()
        start_date = parameters.get('start_date', '')
        end_date = parameters.get('end_date', '')
        
        # Validate inputs
        is_valid, error_message = validate_input(origin, destination, start_date, end_date)
        if not is_valid:
            return {
                'success': False,
                'error': {
                    'code': 'INVALID_INPUT',
                    'message': error_message
                }
            }
        
        # Fetch current fare (mock data)
        try:
            current_price = fetch_current_fare(origin, destination, start_date, end_date)
        except Exception as e:
            return {
                'success': False,
                'error': {
                    'code': 'FARE_GENERATION_ERROR',
                    'message': str(e)
                }
            }
        
        # Generate historical fare data (mock data)
        try:
            price_history = fetch_historical_fares_from_s3(origin, destination, current_price)
        except Exception as e:
            return {
                'success': False,
                'error': {
                    'code': 'HISTORICAL_DATA_ERROR',
                    'message': str(e)
                }
            }
        
        # Get price from 30 days ago
        price_30d_ago = 0.0
        if price_history:
            # Use the oldest record in our 30-day window
            price_30d_ago = float(price_history[0].get('price', 0))
        
        # Calculate trend and generate insight
        price_trend, trend_percentage, fare_insight = classify_fare_trend(current_price, price_30d_ago)
        
        # Return structured FareToolOutput
        return {
            'success': True,
            'data': {
                'current_price': current_price,
                'price_30d_ago': price_30d_ago,
                'price_trend': price_trend,
                'trend_percentage': trend_percentage,
                'fare_insight': fare_insight,
                'price_history': price_history
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
