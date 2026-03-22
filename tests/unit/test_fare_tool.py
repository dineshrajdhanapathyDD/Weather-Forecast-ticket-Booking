"""
Unit tests for Fare MCP Tool Lambda Handler
"""

import json
import sys
import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'fare_tool'))

from handler import (
    lambda_handler,
    validate_input,
    classify_fare_trend,
    fetch_current_fare,
    fetch_historical_fares_from_s3
)


class TestValidateInput:
    """Test input validation"""
    
    def test_valid_input(self):
        """Test validation with valid inputs"""
        is_valid, error = validate_input('JFK', 'LAX', '2024-07-15', '2024-07-22')
        assert is_valid is True
        assert error == ""
    
    def test_missing_origin(self):
        """Test validation with missing origin"""
        is_valid, error = validate_input('', 'LAX', '2024-07-15', '2024-07-22')
        assert is_valid is False
        assert 'origin' in error.lower()
    
    def test_invalid_iata_code(self):
        """Test validation with invalid IATA code"""
        is_valid, error = validate_input('JFKX', 'LAX', '2024-07-15', '2024-07-22')
        assert is_valid is False
        assert 'IATA' in error
    
    def test_lowercase_iata_code(self):
        """Test validation with lowercase IATA code"""
        is_valid, error = validate_input('jfk', 'LAX', '2024-07-15', '2024-07-22')
        assert is_valid is False
        assert 'IATA' in error
    
    def test_invalid_date_format(self):
        """Test validation with invalid date format"""
        is_valid, error = validate_input('JFK', 'LAX', 'invalid-date', '2024-07-22')
        assert is_valid is False
        assert 'date format' in error.lower()
    
    def test_end_before_start(self):
        """Test validation with end_date before start_date"""
        is_valid, error = validate_input('JFK', 'LAX', '2024-07-22', '2024-07-15')
        assert is_valid is False
        assert 'after' in error.lower()


class TestClassifyFareTrend:
    """Test fare trend classification and insight generation"""
    
    def test_rising_trend(self):
        """Test trend classification for rising prices"""
        trend, percentage, insight = classify_fare_trend(560.0, 500.0)
        assert trend == "rising"
        assert percentage == 12.0
        assert "rising" in insight.lower()
        assert "12%" in insight
        assert "book soon" in insight.lower()
    
    def test_dropping_trend(self):
        """Test trend classification for dropping prices"""
        trend, percentage, insight = classify_fare_trend(440.0, 500.0)
        assert trend == "dropping"
        assert percentage == -12.0
        assert "dropping" in insight.lower()
        assert "12%" in insight
        assert "consider waiting" in insight.lower()
    
    def test_stable_trend(self):
        """Test trend classification for stable prices"""
        trend, percentage, insight = classify_fare_trend(505.0, 500.0)
        assert trend == "stable"
        assert percentage == 1.0
        assert "stable" in insight.lower()
        assert "1%" in insight
    
    def test_zero_baseline(self):
        """Test trend classification with zero baseline"""
        trend, percentage, insight = classify_fare_trend(500.0, 0.0)
        assert trend == "stable"
        assert percentage == 0.0
        assert "stable" in insight.lower()
    
    def test_large_increase(self):
        """Test trend classification for large price increase"""
        trend, percentage, insight = classify_fare_trend(600.0, 500.0)
        assert trend == "rising"
        assert percentage == 20.0
        assert "rising" in insight.lower()
        assert "20%" in insight
    
    def test_boundary_rising(self):
        """Test trend at exactly 10% increase boundary"""
        trend, percentage, insight = classify_fare_trend(550.0, 500.0)
        assert trend == "stable"  # Exactly 10% is stable, not rising
        assert percentage == 10.0
        assert "stable" in insight.lower()
    
    def test_boundary_dropping(self):
        """Test trend at exactly -10% decrease boundary"""
        trend, percentage, insight = classify_fare_trend(450.0, 500.0)
        assert trend == "stable"  # Exactly -10% is stable, not dropping
        assert percentage == -10.0
        assert "stable" in insight.lower()
    
    def test_insight_format_rising(self):
        """Test insight string format for rising trend"""
        trend, percentage, insight = classify_fare_trend(575.0, 500.0)
        assert trend == "rising"
        # Verify insight follows the format: "Prices rising X% over past 30 days - book soon"
        assert insight.startswith("Prices rising")
        assert "over past 30 days" in insight
        assert "book soon" in insight
    
    def test_insight_format_dropping(self):
        """Test insight string format for dropping trend"""
        trend, percentage, insight = classify_fare_trend(425.0, 500.0)
        assert trend == "dropping"
        # Verify insight follows the format: "Prices dropping X% - consider waiting"
        assert insight.startswith("Prices dropping")
        assert "consider waiting" in insight
    
    def test_insight_format_stable(self):
        """Test insight string format for stable trend"""
        trend, percentage, insight = classify_fare_trend(505.0, 500.0)
        assert trend == "stable"
        # Verify insight follows the format: "Prices stable (±X%) over past 30 days"
        assert insight.startswith("Prices stable")
        assert "over past 30 days" in insight


@patch('handler.s3_client')
@patch('handler.requests.get')
class TestLambdaHandler:
    """Test Lambda handler integration"""
    
    def test_successful_fare_retrieval(self, mock_requests, mock_s3):
        """Test successful fare data retrieval"""
        # Mock external API response
        mock_response = MagicMock()
        mock_response.json.return_value = {'price': 550.0}
        mock_response.raise_for_status = MagicMock()
        mock_requests.return_value = mock_response
        
        # Mock S3 response
        today = datetime.now()
        # Use 29 days ago to ensure it's within the 30-day window
        twenty_nine_days_ago = today - timedelta(days=29)
        historical_data = [
            {'date': twenty_nine_days_ago.isoformat(), 'price': 500.0},
            {'date': (twenty_nine_days_ago + timedelta(days=14)).isoformat(), 'price': 525.0}
        ]
        
        mock_s3_response = {
            'Body': MagicMock(read=lambda: json.dumps(historical_data).encode('utf-8'))
        }
        # Return data on first call, NoSuchKey on second
        mock_s3.get_object.side_effect = [
            mock_s3_response,
            Exception('NoSuchKey')
        ]
        
        # Create event
        event = {
            'parameters': {
                'origin': 'JFK',
                'destination': 'LAX',
                'start_date': '2024-07-15',
                'end_date': '2024-07-22'
            }
        }
        
        # Call handler
        result = lambda_handler(event, None)
        
        # Verify response
        assert result['success'] is True
        assert 'data' in result
        assert result['data']['current_price'] == 550.0
        # After sorting, the first item (oldest) should be 500.0
        assert result['data']['price_30d_ago'] == 500.0
        assert result['data']['price_trend'] == 'stable'  # 10% exactly is stable
        assert result['data']['trend_percentage'] == 10.0
        assert 'fare_insight' in result['data']
        assert 'stable' in result['data']['fare_insight'].lower()
    
    def test_missing_parameters(self, mock_requests, mock_s3):
        """Test handler with missing parameters"""
        event = {
            'parameters': {
                'origin': 'JFK'
                # Missing destination, start_date, end_date
            }
        }
        
        result = lambda_handler(event, None)
        
        assert result['success'] is False
        assert result['error']['code'] == 'INVALID_INPUT'
    
    def test_invalid_iata_code(self, mock_requests, mock_s3):
        """Test handler with invalid IATA code"""
        event = {
            'parameters': {
                'origin': 'INVALID',
                'destination': 'LAX',
                'start_date': '2024-07-15',
                'end_date': '2024-07-22'
            }
        }
        
        result = lambda_handler(event, None)
        
        assert result['success'] is False
        assert result['error']['code'] == 'INVALID_INPUT'
    
    def test_api_failure(self, mock_requests, mock_s3):
        """Test handler when external API fails"""
        # Mock API failure
        mock_requests.side_effect = Exception("API connection failed")
        
        event = {
            'parameters': {
                'origin': 'JFK',
                'destination': 'LAX',
                'start_date': '2024-07-15',
                'end_date': '2024-07-22'
            }
        }
        
        result = lambda_handler(event, None)
        
        assert result['success'] is False
        assert result['error']['code'] == 'FARE_API_ERROR'
    
    def test_s3_failure(self, mock_requests, mock_s3):
        """Test handler when S3 retrieval fails"""
        # Mock successful API call
        mock_response = MagicMock()
        mock_response.json.return_value = {'price': 550.0}
        mock_response.raise_for_status = MagicMock()
        mock_requests.return_value = mock_response
        
        # Mock S3 failure with access denied
        mock_s3.get_object.side_effect = Exception("Access Denied")
        
        event = {
            'parameters': {
                'origin': 'JFK',
                'destination': 'LAX',
                'start_date': '2024-07-15',
                'end_date': '2024-07-22'
            }
        }
        
        result = lambda_handler(event, None)
        
        assert result['success'] is False
        assert result['error']['code'] == 'S3_RETRIEVAL_ERROR'


class TestFetchCurrentFare:
    """Test external API integration"""
    
    @patch('handler.requests.get')
    def test_successful_api_call(self, mock_requests):
        """Test successful fare API call"""
        mock_response = MagicMock()
        mock_response.json.return_value = {'price': 550.0}
        mock_response.raise_for_status = MagicMock()
        mock_requests.return_value = mock_response
        
        price = fetch_current_fare('JFK', 'LAX', '2024-07-15', '2024-07-22')
        
        assert price == 550.0
        mock_requests.assert_called_once()
    
    @patch('handler.requests.get')
    def test_api_timeout(self, mock_requests):
        """Test API timeout handling"""
        mock_requests.side_effect = Exception("Timeout")
        
        with pytest.raises(Exception) as exc_info:
            fetch_current_fare('JFK', 'LAX', '2024-07-15', '2024-07-22')
        
        assert "Failed to fetch current fare" in str(exc_info.value)


class TestFetchHistoricalFares:
    """Test S3 historical data retrieval"""
    
    @patch('handler.s3_client')
    def test_successful_s3_retrieval(self, mock_s3):
        """Test successful S3 data retrieval"""
        today = datetime.now()
        # Use 29 days ago to ensure it's within the 30-day window
        twenty_nine_days_ago = today - timedelta(days=29)
        historical_data = [
            {'date': twenty_nine_days_ago.isoformat(), 'price': 500.0},
            {'date': (twenty_nine_days_ago + timedelta(days=14)).isoformat(), 'price': 525.0}
        ]
        
        # Mock S3 to return data only on first call, NoSuchKey on second
        mock_s3_response = {
            'Body': MagicMock(read=lambda: json.dumps(historical_data).encode('utf-8'))
        }
        mock_s3.get_object.side_effect = [
            mock_s3_response,
            Exception('NoSuchKey')
        ]
        
        result = fetch_historical_fares_from_s3('JFK', 'LAX')
        
        assert len(result) == 2
        # After sorting by date, the first item should be the oldest (500.0)
        assert result[0]['price'] == 500.0
        assert result[1]['price'] == 525.0
    
    @patch('handler.s3_client')
    def test_s3_no_data(self, mock_s3):
        """Test S3 retrieval when no data exists"""
        mock_s3.get_object.side_effect = mock_s3.exceptions.NoSuchKey({}, 'NoSuchKey')
        
        result = fetch_historical_fares_from_s3('JFK', 'LAX')
        
        assert result == []
