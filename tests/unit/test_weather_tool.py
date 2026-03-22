"""
Unit tests for Weather MCP Tool Lambda handler.
"""

import json
import sys
import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'weather_tool'))

# Mock the boto3 client before importing handler
with patch('boto3.client'):
    from handler import (
        lambda_handler,
        validate_input,
        assess_climate_risks,
        fetch_weather_forecast,
        get_historical_disruption_rate,
        calculate_weather_risk,
        list_activated_risks,
        generate_comfort_advisory
    )


class TestInputValidation:
    """Test input validation logic."""
    
    def test_valid_input(self):
        """Test validation with valid inputs."""
        tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()
        next_week = (datetime.now() + timedelta(days=7)).date().isoformat()
        
        is_valid, error = validate_input("LAX", tomorrow, next_week)
        assert is_valid is True
        assert error == ""
    
    def test_missing_destination(self):
        """Test validation with missing destination."""
        tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()
        next_week = (datetime.now() + timedelta(days=7)).date().isoformat()
        
        is_valid, error = validate_input("", tomorrow, next_week)
        assert is_valid is False
        assert "destination" in error
    
    def test_past_start_date(self):
        """Test validation with past start date."""
        yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
        tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()
        
        is_valid, error = validate_input("LAX", yesterday, tomorrow)
        assert is_valid is False
        assert "future" in error
    
    def test_end_before_start(self):
        """Test validation with end date before start date."""
        tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()
        next_week = (datetime.now() + timedelta(days=7)).date().isoformat()
        
        is_valid, error = validate_input("LAX", next_week, tomorrow)
        assert is_valid is False
        assert "after" in error
    
    def test_date_range_too_long(self):
        """Test validation with date range exceeding 30 days."""
        tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()
        far_future = (datetime.now() + timedelta(days=35)).date().isoformat()
        
        is_valid, error = validate_input("LAX", tomorrow, far_future)
        assert is_valid is False
        assert "30 days" in error


class TestClimateRiskAssessment:
    """Test climate risk assessment logic."""
    
    def test_no_risks_clear_weather(self):
        """Test risk assessment with clear weather."""
        forecast = [
            {
                'date': '2024-07-15',
                'temp_high': 25,
                'temp_low': 18,
                'precipitation_prob': 10,
                'conditions': 'Clear',
                'wind_speed': 15,
                'humidity': 60,
                'visibility': 10
            }
        ]
        
        risks = assess_climate_risks(forecast)
        assert risks['storms'] is False
        assert risks['heavy_rain'] is False
        assert risks['extreme_heat'] is False
        assert risks['monsoon'] is False
        assert risks['poor_visibility'] is False
    
    def test_storm_detection(self):
        """Test storm risk detection."""
        forecast = [
            {
                'date': '2024-07-15',
                'temp_high': 25,
                'temp_low': 18,
                'precipitation_prob': 80,
                'conditions': 'Thunderstorm',
                'wind_speed': 40,
                'humidity': 75,
                'visibility': 5
            }
        ]
        
        risks = assess_climate_risks(forecast)
        assert risks['storms'] is True
    
    def test_extreme_heat_detection(self):
        """Test extreme heat detection."""
        forecast = [
            {
                'date': '2024-07-15',
                'temp_high': 38,
                'temp_low': 28,
                'precipitation_prob': 5,
                'conditions': 'Clear',
                'wind_speed': 10,
                'humidity': 40,
                'visibility': 10
            }
        ]
        
        risks = assess_climate_risks(forecast)
        assert risks['extreme_heat'] is True
    
    def test_poor_visibility_detection(self):
        """Test poor visibility detection."""
        forecast = [
            {
                'date': '2024-07-15',
                'temp_high': 20,
                'temp_low': 15,
                'precipitation_prob': 30,
                'conditions': 'Fog',
                'wind_speed': 5,
                'humidity': 90,
                'visibility': 1.5
            }
        ]
        
        risks = assess_climate_risks(forecast)
        assert risks['poor_visibility'] is True
    
    def test_monsoon_detection(self):
        """Test monsoon conditions detection."""
        forecast = [
            {
                'date': '2024-07-15',
                'temp_high': 30,
                'temp_low': 25,
                'precipitation_prob': 85,
                'conditions': 'Rain',
                'wind_speed': 25,
                'humidity': 90,
                'visibility': 3
            }
        ]
        
        risks = assess_climate_risks(forecast)
        assert risks['monsoon'] is True


class TestWeatherRiskCalculation:
    """Test weather risk calculation algorithm."""
    
    def test_low_risk_no_severe_conditions(self):
        """Test low risk classification with low disruption probability and no severe risks."""
        weather_data = {
            'historical_disruption_rate': 10,
            'climate_risks': {
                'storms': False,
                'heavy_rain': False,
                'extreme_heat': False,
                'monsoon': False,
                'poor_visibility': False
            },
            'forecast': []
        }
        
        risk_level, explanation = calculate_weather_risk(weather_data)
        assert risk_level == "Low"
        assert "Minimal disruption risk" in explanation
        assert "10%" in explanation
    
    def test_medium_risk_moderate_disruption(self):
        """Test medium risk classification with moderate disruption probability."""
        weather_data = {
            'historical_disruption_rate': 25,
            'climate_risks': {
                'storms': False,
                'heavy_rain': False,
                'extreme_heat': False,
                'monsoon': False,
                'poor_visibility': False
            },
            'forecast': []
        }
        
        risk_level, explanation = calculate_weather_risk(weather_data)
        assert risk_level == "Medium"
        assert "Moderate disruption risk" in explanation
        assert "25%" in explanation
    
    def test_high_risk_high_disruption_probability(self):
        """Test high risk classification with high disruption probability."""
        weather_data = {
            'historical_disruption_rate': 50,
            'climate_risks': {
                'storms': False,
                'heavy_rain': False,
                'extreme_heat': False,
                'monsoon': False,
                'poor_visibility': False
            },
            'forecast': []
        }
        
        risk_level, explanation = calculate_weather_risk(weather_data)
        assert risk_level == "High"
        assert "High disruption risk" in explanation
        assert "50%" in explanation
    
    def test_high_risk_severe_climate_risk(self):
        """Test high risk classification with severe climate risk despite low disruption probability."""
        weather_data = {
            'historical_disruption_rate': 10,
            'climate_risks': {
                'storms': True,
                'heavy_rain': False,
                'extreme_heat': False,
                'monsoon': False,
                'poor_visibility': False
            },
            'forecast': []
        }
        
        risk_level, explanation = calculate_weather_risk(weather_data)
        assert risk_level == "High"
        assert "High disruption risk" in explanation
        assert "storms" in explanation
    
    def test_high_risk_multiple_severe_risks(self):
        """Test high risk with multiple severe climate risks."""
        weather_data = {
            'historical_disruption_rate': 15,
            'climate_risks': {
                'storms': True,
                'heavy_rain': True,
                'extreme_heat': False,
                'monsoon': False,
                'poor_visibility': True
            },
            'forecast': []
        }
        
        risk_level, explanation = calculate_weather_risk(weather_data)
        assert risk_level == "High"
        assert "storms" in explanation
        assert "heavy rain" in explanation
        assert "poor visibility" in explanation
    
    def test_boundary_low_medium(self):
        """Test boundary between low and medium risk (15%)."""
        weather_data = {
            'historical_disruption_rate': 15,
            'climate_risks': {
                'storms': False,
                'heavy_rain': False,
                'extreme_heat': False,
                'monsoon': False,
                'poor_visibility': False
            },
            'forecast': []
        }
        
        risk_level, explanation = calculate_weather_risk(weather_data)
        assert risk_level == "Medium"
    
    def test_boundary_medium_high(self):
        """Test boundary between medium and high risk (40%)."""
        weather_data = {
            'historical_disruption_rate': 40,
            'climate_risks': {
                'storms': False,
                'heavy_rain': False,
                'extreme_heat': False,
                'monsoon': False,
                'poor_visibility': False
            },
            'forecast': []
        }
        
        risk_level, explanation = calculate_weather_risk(weather_data)
        assert risk_level == "Medium"
    
    def test_boundary_just_above_40(self):
        """Test just above 40% threshold."""
        weather_data = {
            'historical_disruption_rate': 41,
            'climate_risks': {
                'storms': False,
                'heavy_rain': False,
                'extreme_heat': False,
                'monsoon': False,
                'poor_visibility': False
            },
            'forecast': []
        }
        
        risk_level, explanation = calculate_weather_risk(weather_data)
        assert risk_level == "High"


class TestListActivatedRisks:
    """Test activated risks list generation."""
    
    def test_no_activated_risks(self):
        """Test with no activated risks."""
        climate_risks = {
            'storms': False,
            'heavy_rain': False,
            'extreme_heat': False,
            'monsoon': False,
            'poor_visibility': False
        }
        
        result = list_activated_risks(climate_risks)
        assert result == ""
    
    def test_single_risk(self):
        """Test with single activated risk."""
        climate_risks = {
            'storms': True,
            'heavy_rain': False,
            'extreme_heat': False,
            'monsoon': False,
            'poor_visibility': False
        }
        
        result = list_activated_risks(climate_risks)
        assert result == "storms"
    
    def test_two_risks(self):
        """Test with two activated risks."""
        climate_risks = {
            'storms': True,
            'heavy_rain': True,
            'extreme_heat': False,
            'monsoon': False,
            'poor_visibility': False
        }
        
        result = list_activated_risks(climate_risks)
        assert result == "storms and heavy rain"
    
    def test_multiple_risks(self):
        """Test with multiple activated risks."""
        climate_risks = {
            'storms': True,
            'heavy_rain': True,
            'extreme_heat': True,
            'monsoon': False,
            'poor_visibility': False
        }
        
        result = list_activated_risks(climate_risks)
        assert "storms" in result
        assert "heavy rain" in result
        assert "extreme heat" in result
        assert "and" in result


class TestComfortAdvisoryGeneration:
    """Test comfort advisory generation algorithm."""
    
    def test_pleasant_weather(self):
        """Test advisory with pleasant weather conditions."""
        forecast = [
            {
                'date': '2024-07-15',
                'temp_high': 24,
                'temp_low': 20,
                'precipitation_prob': 10,
                'conditions': 'Clear',
                'wind_speed': 15,
                'humidity': 60,
                'visibility': 10
            }
        ]
        
        advisory = generate_comfort_advisory(forecast)
        assert "Pleasant temperatures" in advisory
        assert "22°C" in advisory
    
    def test_cold_weather(self):
        """Test advisory with cold temperatures."""
        forecast = [
            {
                'date': '2024-01-15',
                'temp_high': 8,
                'temp_low': 2,
                'precipitation_prob': 20,
                'conditions': 'Cloudy',
                'wind_speed': 20,
                'humidity': 70,
                'visibility': 10
            }
        ]
        
        advisory = generate_comfort_advisory(forecast)
        assert "Cold temperatures" in advisory
        assert "pack warm clothing" in advisory
        assert "5°C" in advisory
    
    def test_extreme_heat(self):
        """Test advisory with extreme heat."""
        forecast = [
            {
                'date': '2024-07-15',
                'temp_high': 40,
                'temp_low': 32,
                'precipitation_prob': 5,
                'conditions': 'Clear',
                'wind_speed': 10,
                'humidity': 40,
                'visibility': 10
            }
        ]
        
        advisory = generate_comfort_advisory(forecast)
        assert "Extreme heat" in advisory
        assert "stay hydrated" in advisory
        assert "36°C" in advisory
    
    def test_high_rain_probability(self):
        """Test advisory with high rain probability."""
        forecast = [
            {
                'date': '2024-07-15',
                'temp_high': 22,
                'temp_low': 18,
                'precipitation_prob': 80,
                'conditions': 'Rain',
                'wind_speed': 15,
                'humidity': 75,
                'visibility': 8
            }
        ]
        
        advisory = generate_comfort_advisory(forecast)
        assert "High chance of rain" in advisory
        assert "bring umbrella" in advisory
    
    def test_possible_rain(self):
        """Test advisory with possible rain."""
        forecast = [
            {
                'date': '2024-07-15',
                'temp_high': 22,
                'temp_low': 18,
                'precipitation_prob': 50,
                'conditions': 'Cloudy',
                'wind_speed': 15,
                'humidity': 70,
                'visibility': 10
            }
        ]
        
        advisory = generate_comfort_advisory(forecast)
        assert "Possible rain showers" in advisory
    
    def test_high_humidity(self):
        """Test advisory with high humidity."""
        forecast = [
            {
                'date': '2024-07-15',
                'temp_high': 28,
                'temp_low': 24,
                'precipitation_prob': 30,
                'conditions': 'Cloudy',
                'wind_speed': 10,
                'humidity': 85,
                'visibility': 10
            }
        ]
        
        advisory = generate_comfort_advisory(forecast)
        assert "High humidity" in advisory
        assert "may feel uncomfortable" in advisory
    
    def test_multiple_comfort_factors(self):
        """Test advisory with multiple comfort factors."""
        forecast = [
            {
                'date': '2024-07-15',
                'temp_high': 40,
                'temp_low': 32,
                'precipitation_prob': 75,
                'conditions': 'Rain',
                'wind_speed': 20,
                'humidity': 85,
                'visibility': 5
            }
        ]
        
        advisory = generate_comfort_advisory(forecast)
        assert "Extreme heat" in advisory
        assert "High chance of rain" in advisory
        assert "High humidity" in advisory
    
    def test_multi_day_average(self):
        """Test advisory calculation across multiple days."""
        forecast = [
            {
                'date': '2024-07-15',
                'temp_high': 20,
                'temp_low': 15,
                'precipitation_prob': 30,
                'conditions': 'Cloudy',
                'wind_speed': 15,
                'humidity': 70,
                'visibility': 10
            },
            {
                'date': '2024-07-16',
                'temp_high': 24,
                'temp_low': 18,
                'precipitation_prob': 20,
                'conditions': 'Clear',
                'wind_speed': 10,
                'humidity': 65,
                'visibility': 10
            },
            {
                'date': '2024-07-17',
                'temp_high': 26,
                'temp_low': 20,
                'precipitation_prob': 10,
                'conditions': 'Clear',
                'wind_speed': 12,
                'humidity': 60,
                'visibility': 10
            }
        ]
        
        advisory = generate_comfort_advisory(forecast)
        # Average temp should be around 21°C
        assert "Pleasant temperatures" in advisory or "Temperatures 21°C" in advisory
    
    def test_empty_forecast(self):
        """Test advisory with empty forecast."""
        forecast = []
        
        advisory = generate_comfort_advisory(forecast)
        assert "No forecast data available" in advisory
    
    def test_boundary_temperature_10(self):
        """Test boundary at 10°C (cold threshold)."""
        forecast = [
            {
                'date': '2024-01-15',
                'temp_high': 12,
                'temp_low': 8,
                'precipitation_prob': 20,
                'conditions': 'Cloudy',
                'wind_speed': 15,
                'humidity': 70,
                'visibility': 10
            }
        ]
        
        advisory = generate_comfort_advisory(forecast)
        # Average is 10°C, should not trigger cold warning
        assert "Cold temperatures" not in advisory
    
    def test_boundary_temperature_18(self):
        """Test boundary at 18°C (pleasant lower bound)."""
        forecast = [
            {
                'date': '2024-07-15',
                'temp_high': 20,
                'temp_low': 16,
                'precipitation_prob': 10,
                'conditions': 'Clear',
                'wind_speed': 10,
                'humidity': 60,
                'visibility': 10
            }
        ]
        
        advisory = generate_comfort_advisory(forecast)
        # Average is 18°C, should trigger pleasant
        assert "Pleasant temperatures" in advisory
    
    def test_boundary_precipitation_40(self):
        """Test boundary at 40% precipitation (possible rain threshold)."""
        forecast = [
            {
                'date': '2024-07-15',
                'temp_high': 22,
                'temp_low': 18,
                'precipitation_prob': 40,
                'conditions': 'Cloudy',
                'wind_speed': 15,
                'humidity': 70,
                'visibility': 10
            }
        ]
        
        advisory = generate_comfort_advisory(forecast)
        # At exactly 40%, should not trigger rain warning
        assert "rain" not in advisory.lower()
    
    def test_boundary_precipitation_70(self):
        """Test boundary at 70% precipitation (high rain threshold)."""
        forecast = [
            {
                'date': '2024-07-15',
                'temp_high': 22,
                'temp_low': 18,
                'precipitation_prob': 70,
                'conditions': 'Rain',
                'wind_speed': 15,
                'humidity': 75,
                'visibility': 8
            }
        ]
        
        advisory = generate_comfort_advisory(forecast)
        # At exactly 70%, should not trigger high rain warning
        assert "High chance of rain" not in advisory


class TestLambdaHandler:
    """Test Lambda handler integration."""
    
    @patch('handler.fetch_weather_forecast')
    @patch('handler.get_historical_disruption_rate')
    def test_successful_request(self, mock_disruption, mock_forecast):
        """Test successful weather data retrieval."""
        tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()
        next_week = (datetime.now() + timedelta(days=7)).date().isoformat()
        
        mock_forecast.return_value = [
            {
                'date': tomorrow,
                'temp_high': 25,
                'temp_low': 18,
                'precipitation_prob': 20,
                'conditions': 'Clear',
                'wind_speed': 15,
                'humidity': 60,
                'visibility': 10
            }
        ]
        mock_disruption.return_value = 8.5
        
        event = {
            'parameters': {
                'destination': 'LAX',
                'start_date': tomorrow,
                'end_date': next_week
            }
        }
        
        result = lambda_handler(event, None)
        
        assert result['success'] is True
        assert 'data' in result
        assert 'forecast' in result['data']
        assert 'climate_risks' in result['data']
        assert 'historical_disruption_rate' in result['data']
        assert result['data']['historical_disruption_rate'] == 8.5
        assert 'weather_risk' in result['data']
        assert 'weather_risk_explanation' in result['data']
        assert 'comfort_advisory' in result['data']
        assert result['data']['weather_risk'] == "Low"  # 8.5% is low risk
        assert "Pleasant temperatures" in result['data']['comfort_advisory']
    
    def test_missing_parameters(self):
        """Test handler with missing parameters."""
        event = {
            'parameters': {
                'destination': 'LAX'
            }
        }
        
        result = lambda_handler(event, None)
        
        assert result['success'] is False
        assert 'error' in result
        assert result['error']['code'] == 'INVALID_INPUT'
    
    def test_invalid_date_format(self):
        """Test handler with invalid date format."""
        event = {
            'parameters': {
                'destination': 'LAX',
                'start_date': 'invalid-date',
                'end_date': '2024-07-22'
            }
        }
        
        result = lambda_handler(event, None)
        
        assert result['success'] is False
        assert 'error' in result
        assert result['error']['code'] == 'INVALID_INPUT'
