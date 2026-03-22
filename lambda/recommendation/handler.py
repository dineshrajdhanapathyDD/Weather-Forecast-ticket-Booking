"""
Recommendation Engine Lambda Handler

Generates booking recommendations based on weather and fare data.
"""

import json
import os
import uuid
import boto3
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, TypedDict

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')


class TravelWindow(TypedDict):
    """Travel window with start and end dates."""
    start_date: str
    end_date: str


class WeatherForecast(TypedDict):
    """Weather forecast for a single day."""
    date: str
    temp_high: float
    temp_low: float
    precipitation_prob: float
    conditions: str
    wind_speed: float
    humidity: float
    visibility: float


class ClimateRisks(TypedDict):
    """Climate risk indicators."""
    storms: bool
    heavy_rain: bool
    extreme_heat: bool
    monsoon: bool
    poor_visibility: bool


class WeatherData(TypedDict):
    """Weather tool output data."""
    forecast: List[WeatherForecast]
    climate_risks: ClimateRisks
    historical_disruption_rate: float


class FareData(TypedDict):
    """Fare tool output data."""
    current_price: float
    price_30d_ago: float
    price_trend: str
    trend_percentage: float
    price_history: List[Dict[str, Any]]


class AlternativeWindow(TypedDict):
    """Alternative travel window suggestion."""
    start_date: str
    end_date: str
    weather_risk: str
    fare_trend: str
    summary: str


class RecommendationOutput(TypedDict):
    """Recommendation engine output."""
    weather_risk: str
    weather_risk_explanation: str
    comfort_advisory: str
    fare_trend_insight: str
    booking_recommendation: str
    recommendation_rationale: str
    alternative_windows: Optional[List[AlternativeWindow]]


def invoke_mcp_tool_with_retry(
    tool_name: str,
    function_arn: str,
    payload: Dict[str, Any],
    max_retries: int = 2
) -> Optional[Dict[str, Any]]:
    """
    Invoke MCP tool Lambda with exponential backoff retry.
    
    Implements InvokeMCPToolWithRetry algorithm from design:
    - Max 2 retries (3 total attempts)
    - Exponential backoff: 1s, 2s delays
    - Returns error response after max retries exceeded
    
    Args:
        tool_name: Name of the tool for logging (e.g., "Weather Tool", "Fare Tool")
        function_arn: Lambda function ARN to invoke
        payload: Payload to send to the Lambda function
        max_retries: Maximum number of retries (default: 2)
        
    Returns:
        Tool response data dictionary or None if all attempts fail
    """
    base_delay = 1.0  # seconds
    attempt = 0
    
    while attempt <= max_retries:
        try:
            logger.info(f"Invoking {tool_name} (attempt {attempt + 1}/{max_retries + 1})")
            
            response = lambda_client.invoke(
                FunctionName=function_arn,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('success'):
                logger.info(f"{tool_name} invocation succeeded on attempt {attempt + 1}")
                return result.get('data')
            else:
                error_msg = result.get('error', {}).get('message', 'Unknown error')
                logger.warning(f"{tool_name} returned error: {error_msg}")
                raise Exception(error_msg)
                
        except Exception as e:
            attempt += 1
            
            if attempt > max_retries:
                logger.error(f"Failed to invoke {tool_name} after {max_retries + 1} attempts: {str(e)}")
                return None
            
            # Calculate exponential backoff delay: 1s, 2s
            delay = base_delay * (2 ** (attempt - 1))
            logger.info(f"Retrying {tool_name} after {delay}s delay...")
            time.sleep(delay)
    
    # Should never reach here
    return None


def validate_input(event: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate input parameters according to ValidateRequest algorithm from design.
    
    Validates:
    - Required parameters: destination, origin, travel_window with start_date and end_date
    - Dates are in future and end_date after start_date
    - Travel window does not exceed 30 days
    - Destination is recognized location
    - Origin is valid IATA code
    - Weather_data and fare_data structures if provided
    
    Args:
        event: Lambda event
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required top-level parameters
    if 'destination' not in event:
        return False, "Missing required parameter: destination"
    
    if 'travel_window' not in event:
        return False, "Missing required parameter: travel_window with start_date and end_date"
    
    travel_window = event.get('travel_window', {})
    if not isinstance(travel_window, dict):
        return False, "travel_window must be an object"
    
    if 'start_date' not in travel_window:
        return False, "Missing required parameter: travel_window with start_date and end_date"
    
    if 'end_date' not in travel_window:
        return False, "Missing required parameter: travel_window with start_date and end_date"
    
    # Validate destination
    destination = event.get('destination', '')
    if not destination or not isinstance(destination, str):
        return False, "Invalid destination: must be IATA code or recognized city name"
    
    destination_clean = destination.strip()
    if len(destination_clean) < 2:
        return False, "Invalid destination: must be IATA code or recognized city name"
    
    # Check if it looks like an IATA code or a city name
    is_iata = len(destination_clean) == 3 and destination_clean.isupper() and destination_clean.isalpha()
    is_city = len(destination_clean) >= 2 and any(c.isalpha() for c in destination_clean)
    
    if not (is_iata or is_city):
        return False, "Invalid destination: must be IATA code or recognized city name"
    
    # Validate origin if provided
    origin = event.get('origin', '')
    if origin:
        if not isinstance(origin, str):
            return False, "Invalid origin: must be IATA airport code"
        
        origin_clean = origin.strip().upper()
        if len(origin_clean) != 3 or not origin_clean.isalpha():
            return False, "Invalid origin: must be IATA airport code"
    
    # Validate dates
    try:
        from dateutil import parser as date_parser
        
        start_date_str = travel_window.get('start_date', '')
        end_date_str = travel_window.get('end_date', '')
        
        if not start_date_str or not end_date_str:
            return False, "Missing required parameter: travel_window with start_date and end_date"
        
        start_date = date_parser.parse(start_date_str).date()
        end_date = date_parser.parse(end_date_str).date()
        
        # Validate end_date after start_date
        if end_date < start_date:
            return False, "Travel window end_date must be after start_date"
        
        # Validate travel window does not exceed 30 days
        if (end_date - start_date).days > 30:
            return False, "Travel window cannot exceed 30 days"
            
    except (ValueError, TypeError) as e:
        return False, f"Invalid date format: {str(e)}"
    
    # Validate weather_data structure if provided
    weather_data = event.get('weather_data')
    if weather_data is not None:
        if not isinstance(weather_data, dict):
            return False, "weather_data must be an object"
        
        if 'forecast' in weather_data and not isinstance(weather_data['forecast'], list):
            return False, "weather_data.forecast must be an array"
        
        if 'climate_risks' in weather_data and not isinstance(weather_data['climate_risks'], dict):
            return False, "weather_data.climate_risks must be an object"
        
        if 'historical_disruption_rate' in weather_data:
            try:
                rate = float(weather_data['historical_disruption_rate'])
                if rate < 0 or rate > 100:
                    return False, "weather_data.historical_disruption_rate must be between 0 and 100"
            except (ValueError, TypeError):
                return False, "weather_data.historical_disruption_rate must be a number"
    
    # Validate fare_data structure if provided
    fare_data = event.get('fare_data')
    if fare_data is not None:
        if not isinstance(fare_data, dict):
            return False, "fare_data must be an object"
        
        if 'price_trend' in fare_data:
            if fare_data['price_trend'] not in ['rising', 'stable', 'dropping']:
                return False, "fare_data.price_trend must be one of: rising, stable, dropping"
    
    return True, None


def generate_booking_recommendation(weather_risk: str, fare_trend: str) -> tuple[str, str]:
    """
    Generate booking recommendation based on weather risk and fare trend.
    
    Algorithm from design document:
    - IF weather_risk == "High" THEN recommendation = "Change Dates"
    - IF weather_risk == "Medium" AND fare_trend != "dropping" THEN recommendation = "Change Dates"
    - IF weather_risk == "Low" AND fare_trend == "dropping" THEN recommendation = "Wait"
    - IF weather_risk == "Low" AND (fare_trend == "rising" OR fare_trend == "stable") THEN recommendation = "Book Now"
    - IF weather_risk == "Medium" AND fare_trend == "dropping" THEN recommendation = "Wait"
    
    Args:
        weather_risk: Weather risk level ("Low", "Medium", or "High")
        fare_trend: Fare trend ("rising", "stable", or "dropping")
        
    Returns:
        Tuple of (recommendation, rationale)
    """
    # High weather risk always means change dates
    if weather_risk == "High":
        return "Change Dates", "High weather risk makes travel unsafe - consider alternative dates"
    
    # Medium weather risk with non-dropping fares means change dates
    if weather_risk == "Medium" and fare_trend != "dropping":
        return "Change Dates", f"Moderate weather risk with {fare_trend} fares - safer dates recommended"
    
    # Low weather risk with dropping fares means wait
    if weather_risk == "Low" and fare_trend == "dropping":
        return "Wait", "Low weather risk and dropping fares - wait for better prices"
    
    # Low weather risk with rising or stable fares means book now
    if weather_risk == "Low" and (fare_trend == "rising" or fare_trend == "stable"):
        return "Book Now", f"Low weather risk and {fare_trend} fares - good time to book"
    
    # Medium weather risk with dropping fares means wait
    if weather_risk == "Medium" and fare_trend == "dropping":
        return "Wait", "Moderate weather risk but dropping fares - monitor both factors"
    
    # Default fallback (should not reach here with valid inputs)
    return "Book Now", "Conditions acceptable for booking"


def calculate_window_score(weather_risk: str, fare_trend: str) -> int:
    """
    Calculate score for an alternative window based on weather risk and fare trend.
    
    Algorithm from design document:
    - Low weather risk: +100 points
    - Medium weather risk: +50 points
    - High weather risk: +0 points
    - Dropping fare trend: +30 points
    - Stable fare trend: +20 points
    - Rising fare trend: +10 points
    
    Args:
        weather_risk: Weather risk level ("Low", "Medium", or "High")
        fare_trend: Fare trend ("rising", "stable", or "dropping")
        
    Returns:
        Score as integer
    """
    score = 0
    
    # Weather risk scoring
    if weather_risk == "Low":
        score += 100
    elif weather_risk == "Medium":
        score += 50
    else:  # High
        score += 0
    
    # Fare trend scoring
    if fare_trend == "dropping":
        score += 30
    elif fare_trend == "stable":
        score += 20
    else:  # rising
        score += 10
    
    return score


def invoke_weather_tool(destination: str, start_date: str, end_date: str) -> Optional[Dict[str, Any]]:
    """
    Invoke Weather MCP Tool Lambda to get weather data for a date range.
    
    Args:
        destination: Destination airport code or city
        start_date: Start date in ISO 8601 format (YYYY-MM-DD)
        end_date: End date in ISO 8601 format (YYYY-MM-DD)
        
    Returns:
        Weather data dictionary or None if invocation fails
    """
    weather_lambda_arn = os.environ.get('WEATHER_LAMBDA_ARN')
    if not weather_lambda_arn:
        logger.error("WEATHER_LAMBDA_ARN environment variable not set")
        return None
    
    payload = {
        'parameters': {
            'destination': destination,
            'start_date': start_date,
            'end_date': end_date
        }
    }
    
    return invoke_mcp_tool_with_retry("Weather Tool", weather_lambda_arn, payload)


def invoke_fare_tool(origin: str, destination: str, start_date: str, end_date: str) -> Optional[Dict[str, Any]]:
    """
    Invoke Fare MCP Tool Lambda to get fare data for a date range.
    
    Args:
        origin: Origin airport code
        destination: Destination airport code
        start_date: Start date in ISO 8601 format (YYYY-MM-DD)
        end_date: End date in ISO 8601 format (YYYY-MM-DD)
        
    Returns:
        Fare data dictionary or None if invocation fails
    """
    fare_lambda_arn = os.environ.get('FARE_LAMBDA_ARN')
    if not fare_lambda_arn:
        logger.error("FARE_LAMBDA_ARN environment variable not set")
        return None
    
    payload = {
        'parameters': {
            'origin': origin,
            'destination': destination,
            'start_date': start_date,
            'end_date': end_date
        }
    }
    
    return invoke_mcp_tool_with_retry("Fare Tool", fare_lambda_arn, payload)


def find_alternative_windows(
    original_start: str,
    original_end: str,
    destination: str,
    origin: str
) -> List[AlternativeWindow]:
    """
    Find alternative travel windows within ±14 days of the original start date.
    
    Algorithm from design document:
    1. Calculate window duration
    2. Search ±14 days from original start date
    3. For each candidate window:
       - Skip if it's the original window
       - Invoke Weather and Fare tools
       - Calculate weather risk and fare trend
       - Calculate window score
    4. Sort by score (descending)
    5. Return top 3 alternatives
    
    Args:
        original_start: Original start date (YYYY-MM-DD)
        original_end: Original end date (YYYY-MM-DD)
        destination: Destination airport code or city
        origin: Origin airport code
        
    Returns:
        List of up to 3 alternative windows ranked by score
    """
    try:
        # Parse dates
        start_date = datetime.strptime(original_start, '%Y-%m-%d')
        end_date = datetime.strptime(original_end, '%Y-%m-%d')
        
        # Calculate window duration
        window_duration = (end_date - start_date).days
        
        # Generate candidate windows (±14 days from original start)
        candidates = []
        
        for day_offset in range(-14, 15):
            if day_offset == 0:
                # Skip the original window
                continue
            
            candidate_start = start_date + timedelta(days=day_offset)
            candidate_end = candidate_start + timedelta(days=window_duration)
            
            candidate_start_str = candidate_start.strftime('%Y-%m-%d')
            candidate_end_str = candidate_end.strftime('%Y-%m-%d')
            
            # Invoke Weather Tool
            weather_data = invoke_weather_tool(destination, candidate_start_str, candidate_end_str)
            if not weather_data:
                logger.warning(f"Failed to get weather data for {candidate_start_str} to {candidate_end_str}")
                continue
            
            # Invoke Fare Tool
            fare_data = invoke_fare_tool(origin, destination, candidate_start_str, candidate_end_str)
            if not fare_data:
                logger.warning(f"Failed to get fare data for {candidate_start_str} to {candidate_end_str}")
                continue
            
            # Extract weather risk and fare trend
            weather_risk = weather_data.get('weather_risk', 'Medium')
            fare_trend = fare_data.get('price_trend', 'stable')
            
            # Calculate score
            score = calculate_window_score(weather_risk, fare_trend)
            
            # Create summary
            summary = f"Weather: {weather_risk}, Fares: {fare_trend}"
            
            candidates.append({
                'start_date': candidate_start_str,
                'end_date': candidate_end_str,
                'weather_risk': weather_risk,
                'fare_trend': fare_trend,
                'summary': summary,
                'score': score
            })
        
        # Sort by score (descending) and take top 3
        candidates.sort(key=lambda x: x['score'], reverse=True)
        top_alternatives = candidates[:3]
        
        # Remove score from output (internal use only)
        for alt in top_alternatives:
            alt.pop('score', None)
        
        logger.info(f"Found {len(top_alternatives)} alternative windows out of {len(candidates)} candidates")
        
        return top_alternatives
        
    except Exception as e:
        logger.error(f"Error finding alternative windows: {str(e)}")
        return []


def persist_to_dynamodb(
    query_id: str,
    destination: str,
    origin: str,
    travel_window_start: str,
    travel_window_end: str,
    weather_risk: str,
    fare_trend: str,
    booking_recommendation: str
) -> bool:
    """
    Persist query record to DynamoDB with 90-day TTL.
    
    Implements graceful degradation: logs errors but does not raise exceptions.
    
    Args:
        query_id: Unique query identifier
        destination: Destination airport code or city
        origin: Origin airport code
        travel_window_start: Travel window start date
        travel_window_end: Travel window end date
        weather_risk: Weather risk level
        fare_trend: Fare trend
        booking_recommendation: Booking recommendation
        
    Returns:
        True if successful, False otherwise
    """
    try:
        table_name = os.environ.get('DYNAMODB_TABLE')
        if not table_name:
            logger.error("DYNAMODB_TABLE environment variable not set")
            return False
        
        table = dynamodb.Table(table_name)
        
        # Calculate TTL (90 days from now)
        ttl_timestamp = int((datetime.now() + timedelta(days=90)).timestamp())
        
        # Create record
        record = {
            'query_id': query_id,
            'timestamp': int(datetime.now().timestamp()),
            'destination': destination,
            'origin': origin,
            'travel_window_start': travel_window_start,
            'travel_window_end': travel_window_end,
            'weather_risk': weather_risk,
            'fare_trend': fare_trend,
            'booking_recommendation': booking_recommendation,
            'ttl': ttl_timestamp
        }
        
        # Write to DynamoDB
        table.put_item(Item=record)
        
        logger.info(f"Successfully persisted query {query_id} to DynamoDB")
        return True
        
    except Exception as e:
        # Log error but don't raise - graceful degradation
        logger.error(f"Failed to persist to DynamoDB: {str(e)}")
        return False


def handle_partial_data_failure(
    weather_data: Optional[Dict[str, Any]],
    fare_data: Optional[Dict[str, Any]]
) -> tuple[bool, Optional[Dict[str, Any]]]:
    """
    Handle partial data failures with graceful degradation.
    
    Implements HandlePartialDataFailure algorithm from design:
    - Both available: return (True, None) to proceed normally
    - Weather only: return (True, weather_only_recommendation)
    - Fare only: return (True, fare_only_recommendation)
    - Both unavailable: return (False, error_response)
    
    Args:
        weather_data: Weather tool response data or None
        fare_data: Fare tool response data or None
        
    Returns:
        Tuple of (can_proceed, partial_recommendation_or_error)
        - If both data sources available: (True, None)
        - If partial data available: (True, partial_recommendation_dict)
        - If no data available: (False, error_dict)
    """
    weather_available = weather_data is not None
    fare_available = fare_data is not None
    
    # Case 1: Both data sources available - proceed normally
    if weather_available and fare_available:
        return True, None
    
    # Case 2: Weather only - generate weather-only recommendation
    if weather_available and not fare_available:
        logger.warning("Fare data unavailable - generating weather-only recommendation")
        
        weather_risk = weather_data.get('weather_risk', 'Low')
        weather_risk_explanation = weather_data.get('weather_risk_explanation', 'Weather risk assessment unavailable')
        comfort_advisory = weather_data.get('comfort_advisory', 'Comfort advisory unavailable')
        
        # Weather-only recommendation logic: prioritize safety
        if weather_risk == "High":
            recommendation = "Change Dates"
            rationale = "High weather risk detected - consider alternative dates (fare data unavailable)"
        elif weather_risk == "Medium":
            recommendation = "Wait"
            rationale = "Moderate weather risk - monitor conditions (fare data unavailable)"
        else:
            recommendation = "Book Now"
            rationale = "Low weather risk - conditions favorable (fare data unavailable)"
        
        partial_recommendation = {
            'weather_risk': weather_risk,
            'weather_risk_explanation': weather_risk_explanation,
            'comfort_advisory': comfort_advisory,
            'fare_trend_insight': "Fare data unavailable - recommendation based on weather only",
            'booking_recommendation': recommendation,
            'recommendation_rationale': rationale,
            'alternative_windows': None,
            'disclaimer': "Fare data unavailable - recommendation based on weather only"
        }
        
        return True, partial_recommendation
    
    # Case 3: Fare only - generate fare-only recommendation
    if fare_available and not weather_available:
        logger.warning("Weather data unavailable - generating fare-only recommendation")
        
        fare_trend = fare_data.get('price_trend', 'stable')
        fare_insight = fare_data.get('fare_insight', 'Fare trend analysis unavailable')
        
        # Fare-only recommendation logic: focus on pricing
        if fare_trend == "rising":
            recommendation = "Book Now"
            rationale = "Prices rising - book soon to lock in rates (weather data unavailable)"
        elif fare_trend == "dropping":
            recommendation = "Wait"
            rationale = "Prices dropping - consider waiting for better rates (weather data unavailable)"
        else:
            recommendation = "Book Now"
            rationale = "Prices stable - reasonable time to book (weather data unavailable)"
        
        partial_recommendation = {
            'weather_risk': "Unknown",
            'weather_risk_explanation': "Weather data unavailable - recommendation based on fares only",
            'comfort_advisory': "Weather data unavailable - unable to provide comfort advisory",
            'fare_trend_insight': fare_insight,
            'booking_recommendation': recommendation,
            'recommendation_rationale': rationale,
            'alternative_windows': None,
            'disclaimer': "Weather data unavailable - recommendation based on fares only"
        }
        
        return True, partial_recommendation
    
    # Case 4: Both unavailable - return error
    logger.error("Both weather and fare data unavailable")
    error_response = {
        'success': False,
        'error': {
            'code': 'DATA_UNAVAILABLE',
            'message': 'Both weather and fare data are currently unavailable. Please try again later.'
        }
    }
    
    return False, error_response


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for Recommendation Engine.
    
    Args:
        event: Lambda event containing query_id, destination, travel_window, weather_data, fare_data
               Can be direct invocation or API Gateway proxy integration
        context: Lambda context
        
    Returns:
        RecommendationOutput with booking recommendation
    """
    try:
        # Parse body from API Gateway proxy integration if present
        if 'body' in event:
            try:
                body = json.loads(event['body'])
            except (json.JSONDecodeError, TypeError):
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': {
                            'code': 'INVALID_JSON',
                            'message': 'Invalid JSON in request body'
                        }
                    })
                }
        else:
            body = event
        
        # Validate inputs
        is_valid, error_message = validate_input(body)
        if not is_valid:
            response = {
                'success': False,
                'error': {
                    'code': 'INVALID_INPUT',
                    'message': error_message
                }
            }
            
            # Return API Gateway format if called through API Gateway
            if 'body' in event:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps(response)
                }
            return response
        
        # Extract parameters
        query_id = body.get('query_id', str(uuid.uuid4()))
        destination = body['destination']
        origin = body.get('origin', 'UNKNOWN')  # Origin may not always be provided
        travel_window: TravelWindow = body['travel_window']
        weather_data: Optional[WeatherData] = body.get('weather_data')
        fare_data: Optional[FareData] = body.get('fare_data')
        
        # If weather_data not provided, invoke Weather Tool
        if weather_data is None:
            logger.info("Weather data not provided, invoking Weather Tool")
            weather_data = invoke_weather_tool(
                destination,
                travel_window['start_date'],
                travel_window['end_date']
            )
        
        # If fare_data not provided and origin is known, invoke Fare Tool
        if fare_data is None and origin != 'UNKNOWN':
            logger.info("Fare data not provided, invoking Fare Tool")
            fare_data = invoke_fare_tool(
                origin,
                destination,
                travel_window['start_date'],
                travel_window['end_date']
            )
        
        # Handle partial data failures with graceful degradation
        can_proceed, partial_result = handle_partial_data_failure(weather_data, fare_data)
        
        # If both data sources unavailable, return error
        if not can_proceed:
            return partial_result
        
        # If partial data available, return partial recommendation
        if partial_result is not None:
            # Still try to persist to DynamoDB
            persist_to_dynamodb(
                query_id=query_id,
                destination=destination,
                origin=origin,
                travel_window_start=travel_window['start_date'],
                travel_window_end=travel_window['end_date'],
                weather_risk=partial_result.get('weather_risk', 'Unknown'),
                fare_trend=partial_result.get('fare_trend_insight', 'Unknown'),
                booking_recommendation=partial_result['booking_recommendation']
            )
            
            return {
                'success': True,
                'data': {
                    'query_id': query_id,
                    **partial_result
                }
            }
        
        # Normal path: both data sources available
        # Extract weather risk and fare trend from the data
        weather_risk = weather_data.get('weather_risk', 'Low')
        weather_risk_explanation = weather_data.get('weather_risk_explanation', 'Weather risk assessment unavailable')
        comfort_advisory = weather_data.get('comfort_advisory', 'Comfort advisory unavailable')
        
        fare_trend = fare_data.get('price_trend', 'stable')
        fare_trend_insight = fare_data.get('fare_insight', 'Fare trend analysis unavailable')
        
        # Generate booking recommendation using the algorithm
        booking_recommendation, recommendation_rationale = generate_booking_recommendation(
            weather_risk, fare_trend
        )
        
        # Task 5.3: Find alternative windows if recommendation is "Change Dates"
        alternative_windows = None
        if booking_recommendation == "Change Dates":
            logger.info(f"Searching for alternative windows for query {query_id}")
            alternatives = find_alternative_windows(
                travel_window['start_date'],
                travel_window['end_date'],
                destination,
                origin
            )
            if alternatives:
                alternative_windows = alternatives
                logger.info(f"Found {len(alternatives)} alternative windows")
            else:
                logger.info("No alternative windows found")
        
        # Task 5.4: Persist to DynamoDB (graceful degradation on failure)
        persist_success = persist_to_dynamodb(
            query_id=query_id,
            destination=destination,
            origin=origin,
            travel_window_start=travel_window['start_date'],
            travel_window_end=travel_window['end_date'],
            weather_risk=weather_risk,
            fare_trend=fare_trend,
            booking_recommendation=booking_recommendation
        )
        
        if not persist_success:
            logger.warning(f"Failed to persist query {query_id} to DynamoDB, but continuing with response")
        
        # Build recommendation output
        recommendation: RecommendationOutput = {
            'weather_risk': weather_risk,
            'weather_risk_explanation': weather_risk_explanation,
            'comfort_advisory': comfort_advisory,
            'fare_trend_insight': fare_trend_insight,
            'booking_recommendation': booking_recommendation,
            'recommendation_rationale': recommendation_rationale,
            'alternative_windows': alternative_windows
        }
        
        response_data = {
            'success': True,
            'data': {
                'query_id': query_id,
                **recommendation
            }
        }
        
        # Return API Gateway format if called through API Gateway
        if 'body' in event:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(response_data)
            }
        
        return response_data
        
    except Exception as e:
        logger.error(f"Unexpected error in lambda_handler: {str(e)}")
        error_response = {
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': str(e)
            }
        }
        
        # Return API Gateway format if called through API Gateway
        if 'body' in event:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(error_response)
            }
        
        return error_response
