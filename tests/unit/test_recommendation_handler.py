"""
Unit tests for Recommendation Engine Lambda handler.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda/recommendation'))

from handler import (
    lambda_handler, 
    validate_input, 
    generate_booking_recommendation,
    calculate_window_score,
    find_alternative_windows,
    persist_to_dynamodb
)


class TestValidateInput:
    """Test input validation."""
    
    def test_valid_input_minimal(self):
        """Test validation with minimal valid input."""
        event = {
            'destination': 'LAX',
            'travel_window': {
                'start_date': '2024-07-15',
                'end_date': '2024-07-22'
            }
        }
        is_valid, error = validate_input(event)
        assert is_valid is True
        assert error is None
    
    def test_valid_input_complete(self):
        """Test validation with complete input including weather and fare data."""
        event = {
            'query_id': 'test-123',
            'destination': 'LAX',
            'travel_window': {
                'start_date': '2024-07-15',
                'end_date': '2024-07-22'
            },
            'weather_data': {
                'forecast': [
                    {
                        'date': '2024-07-15',
                        'temp_high': 28.0,
                        'temp_low': 22.0,
                        'precipitation_prob': 10.0,
                        'conditions': 'Clear',
                        'wind_speed': 15.0,
                        'humidity': 60.0,
                        'visibility': 10.0
                    }
                ],
                'climate_risks': {
                    'storms': False,
                    'heavy_rain': False,
                    'extreme_heat': False,
                    'monsoon': False,
                    'poor_visibility': False
                },
                'historical_disruption_rate': 8.0
            },
            'fare_data': {
                'current_price': 450.0,
                'price_30d_ago': 400.0,
                'price_trend': 'rising',
                'trend_percentage': 12.5,
                'price_history': []
            }
        }
        is_valid, error = validate_input(event)
        assert is_valid is True
        assert error is None
    
    def test_missing_destination(self):
        """Test validation fails when destination is missing."""
        event = {
            'travel_window': {
                'start_date': '2024-07-15',
                'end_date': '2024-07-22'
            }
        }
        is_valid, error = validate_input(event)
        assert is_valid is False
        assert 'destination' in error
    
    def test_missing_travel_window(self):
        """Test validation fails when travel_window is missing."""
        event = {
            'destination': 'LAX'
        }
        is_valid, error = validate_input(event)
        assert is_valid is False
        assert 'travel_window' in error
    
    def test_missing_start_date(self):
        """Test validation fails when start_date is missing."""
        event = {
            'destination': 'LAX',
            'travel_window': {
                'end_date': '2024-07-22'
            }
        }
        is_valid, error = validate_input(event)
        assert is_valid is False
        assert 'start_date' in error
    
    def test_missing_end_date(self):
        """Test validation fails when end_date is missing."""
        event = {
            'destination': 'LAX',
            'travel_window': {
                'start_date': '2024-07-15'
            }
        }
        is_valid, error = validate_input(event)
        assert is_valid is False
        assert 'end_date' in error
    
    def test_invalid_travel_window_type(self):
        """Test validation fails when travel_window is not an object."""
        event = {
            'destination': 'LAX',
            'travel_window': 'invalid'
        }
        is_valid, error = validate_input(event)
        assert is_valid is False
        assert 'object' in error
    
    def test_invalid_weather_data_type(self):
        """Test validation fails when weather_data is not an object."""
        event = {
            'destination': 'LAX',
            'travel_window': {
                'start_date': '2024-07-15',
                'end_date': '2024-07-22'
            },
            'weather_data': 'invalid'
        }
        is_valid, error = validate_input(event)
        assert is_valid is False
        assert 'weather_data' in error
    
    def test_invalid_forecast_type(self):
        """Test validation fails when forecast is not an array."""
        event = {
            'destination': 'LAX',
            'travel_window': {
                'start_date': '2024-07-15',
                'end_date': '2024-07-22'
            },
            'weather_data': {
                'forecast': 'invalid'
            }
        }
        is_valid, error = validate_input(event)
        assert is_valid is False
        assert 'forecast' in error and 'array' in error
    
    def test_invalid_disruption_rate_range(self):
        """Test validation fails when disruption rate is out of range."""
        event = {
            'destination': 'LAX',
            'travel_window': {
                'start_date': '2024-07-15',
                'end_date': '2024-07-22'
            },
            'weather_data': {
                'historical_disruption_rate': 150.0
            }
        }
        is_valid, error = validate_input(event)
        assert is_valid is False
        assert 'between 0 and 100' in error
    
    def test_invalid_fare_trend_value(self):
        """Test validation fails when fare trend is invalid."""
        event = {
            'destination': 'LAX',
            'travel_window': {
                'start_date': '2024-07-15',
                'end_date': '2024-07-22'
            },
            'fare_data': {
                'price_trend': 'invalid'
            }
        }
        is_valid, error = validate_input(event)
        assert is_valid is False
        assert 'rising, stable, dropping' in error


class TestLambdaHandler:
    """Test Lambda handler function."""
    
    def test_handler_success_minimal(self):
        """Test handler with minimal valid input."""
        event = {
            'destination': 'LAX',
            'travel_window': {
                'start_date': '2024-07-15',
                'end_date': '2024-07-22'
            }
        }
        result = lambda_handler(event, None)
        
        assert result['success'] is True
        assert 'data' in result
        
        data = result['data']
        assert 'query_id' in data
        assert 'weather_risk' in data
        assert 'weather_risk_explanation' in data
        assert 'comfort_advisory' in data
        assert 'fare_trend_insight' in data
        assert 'booking_recommendation' in data
        assert 'recommendation_rationale' in data
        assert 'alternative_windows' in data
    
    def test_handler_success_with_query_id(self):
        """Test handler preserves provided query_id."""
        event = {
            'query_id': 'custom-query-123',
            'destination': 'LAX',
            'travel_window': {
                'start_date': '2024-07-15',
                'end_date': '2024-07-22'
            }
        }
        result = lambda_handler(event, None)
        
        assert result['success'] is True
        assert result['data']['query_id'] == 'custom-query-123'
    
    def test_handler_generates_query_id(self):
        """Test handler generates query_id when not provided."""
        event = {
            'destination': 'LAX',
            'travel_window': {
                'start_date': '2024-07-15',
                'end_date': '2024-07-22'
            }
        }
        result = lambda_handler(event, None)
        
        assert result['success'] is True
        assert 'query_id' in result['data']
        assert len(result['data']['query_id']) > 0
    
    def test_handler_with_complete_data(self):
        """Test handler with complete weather and fare data."""
        event = {
            'destination': 'LAX',
            'travel_window': {
                'start_date': '2024-07-15',
                'end_date': '2024-07-22'
            },
            'weather_data': {
                'forecast': [
                    {
                        'date': '2024-07-15',
                        'temp_high': 28.0,
                        'temp_low': 22.0,
                        'precipitation_prob': 10.0,
                        'conditions': 'Clear',
                        'wind_speed': 15.0,
                        'humidity': 60.0,
                        'visibility': 10.0
                    }
                ],
                'climate_risks': {
                    'storms': False,
                    'heavy_rain': False,
                    'extreme_heat': False,
                    'monsoon': False,
                    'poor_visibility': False
                },
                'historical_disruption_rate': 8.0
            },
            'fare_data': {
                'current_price': 450.0,
                'price_30d_ago': 400.0,
                'price_trend': 'rising',
                'trend_percentage': 12.5,
                'price_history': []
            }
        }
        result = lambda_handler(event, None)
        
        assert result['success'] is True
        assert 'data' in result
    
    def test_handler_error_missing_destination(self):
        """Test handler returns error for missing destination."""
        event = {
            'travel_window': {
                'start_date': '2024-07-15',
                'end_date': '2024-07-22'
            }
        }
        result = lambda_handler(event, None)
        
        assert result['success'] is False
        assert 'error' in result
        assert result['error']['code'] == 'INVALID_INPUT'
        assert 'destination' in result['error']['message']
    
    def test_handler_error_missing_travel_window(self):
        """Test handler returns error for missing travel_window."""
        event = {
            'destination': 'LAX'
        }
        result = lambda_handler(event, None)
        
        assert result['success'] is False
        assert 'error' in result
        assert result['error']['code'] == 'INVALID_INPUT'
        assert 'travel_window' in result['error']['message']
    
    def test_handler_error_invalid_weather_data(self):
        """Test handler returns error for invalid weather data."""
        event = {
            'destination': 'LAX',
            'travel_window': {
                'start_date': '2024-07-15',
                'end_date': '2024-07-22'
            },
            'weather_data': {
                'historical_disruption_rate': 150.0
            }
        }
        result = lambda_handler(event, None)
        
        assert result['success'] is False
        assert 'error' in result
        assert result['error']['code'] == 'INVALID_INPUT'
    
    def test_handler_returns_all_required_fields(self):
        """Test handler returns all required fields in RecommendationOutput."""
        event = {
            'destination': 'LAX',
            'travel_window': {
                'start_date': '2024-07-15',
                'end_date': '2024-07-22'
            }
        }
        result = lambda_handler(event, None)
        
        assert result['success'] is True
        data = result['data']
        
        # Check all required fields are present
        required_fields = [
            'query_id',
            'weather_risk',
            'weather_risk_explanation',
            'comfort_advisory',
            'fare_trend_insight',
            'booking_recommendation',
            'recommendation_rationale',
            'alternative_windows'
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"


class TestBookingRecommendationLogic:
    """Test booking recommendation logic algorithm."""
    
    def test_high_weather_risk_always_change_dates(self):
        """Test that high weather risk always recommends Change Dates regardless of fare trend."""
        # High risk + rising fares
        rec, rationale = generate_booking_recommendation("High", "rising")
        assert rec == "Change Dates"
        assert "High weather risk" in rationale
        
        # High risk + stable fares
        rec, rationale = generate_booking_recommendation("High", "stable")
        assert rec == "Change Dates"
        assert "High weather risk" in rationale
        
        # High risk + dropping fares
        rec, rationale = generate_booking_recommendation("High", "dropping")
        assert rec == "Change Dates"
        assert "High weather risk" in rationale
    
    def test_medium_risk_non_dropping_fares_change_dates(self):
        """Test that medium risk with non-dropping fares recommends Change Dates."""
        # Medium risk + rising fares
        rec, rationale = generate_booking_recommendation("Medium", "rising")
        assert rec == "Change Dates"
        assert "Moderate weather risk" in rationale
        assert "rising" in rationale
        
        # Medium risk + stable fares
        rec, rationale = generate_booking_recommendation("Medium", "stable")
        assert rec == "Change Dates"
        assert "Moderate weather risk" in rationale
        assert "stable" in rationale
    
    def test_medium_risk_dropping_fares_wait(self):
        """Test that medium risk with dropping fares recommends Wait."""
        rec, rationale = generate_booking_recommendation("Medium", "dropping")
        assert rec == "Wait"
        assert "Moderate weather risk" in rationale
        assert "dropping" in rationale
    
    def test_low_risk_dropping_fares_wait(self):
        """Test that low risk with dropping fares recommends Wait."""
        rec, rationale = generate_booking_recommendation("Low", "dropping")
        assert rec == "Wait"
        assert "Low weather risk" in rationale
        assert "dropping" in rationale
    
    def test_low_risk_rising_fares_book_now(self):
        """Test that low risk with rising fares recommends Book Now."""
        rec, rationale = generate_booking_recommendation("Low", "rising")
        assert rec == "Book Now"
        assert "Low weather risk" in rationale
        assert "rising" in rationale
    
    def test_low_risk_stable_fares_book_now(self):
        """Test that low risk with stable fares recommends Book Now."""
        rec, rationale = generate_booking_recommendation("Low", "stable")
        assert rec == "Book Now"
        assert "Low weather risk" in rationale
        assert "stable" in rationale
    
    def test_recommendation_always_returns_valid_value(self):
        """Test that recommendation is always one of the three valid values."""
        valid_recommendations = ["Book Now", "Wait", "Change Dates"]
        
        weather_risks = ["Low", "Medium", "High"]
        fare_trends = ["rising", "stable", "dropping"]
        
        for weather_risk in weather_risks:
            for fare_trend in fare_trends:
                rec, rationale = generate_booking_recommendation(weather_risk, fare_trend)
                assert rec in valid_recommendations
                assert len(rationale) > 0
    
    def test_handler_uses_recommendation_logic_with_weather_data(self):
        """Test that handler uses recommendation logic when weather data is provided."""
        event = {
            'destination': 'LAX',
            'travel_window': {
                'start_date': '2024-07-15',
                'end_date': '2024-07-22'
            },
            'weather_data': {
                'weather_risk': 'High',
                'weather_risk_explanation': 'Severe storms expected',
                'comfort_advisory': 'Uncomfortable conditions'
            },
            'fare_data': {
                'price_trend': 'dropping',
                'fare_trend_insight': 'Prices dropping 15%'
            }
        }
        result = lambda_handler(event, None)
        
        assert result['success'] is True
        data = result['data']
        # High risk should always recommend Change Dates
        assert data['booking_recommendation'] == "Change Dates"
        assert "High weather risk" in data['recommendation_rationale']
    
    def test_handler_uses_recommendation_logic_low_risk_rising_fares(self):
        """Test handler recommends Book Now for low risk and rising fares."""
        event = {
            'destination': 'LAX',
            'travel_window': {
                'start_date': '2024-07-15',
                'end_date': '2024-07-22'
            },
            'weather_data': {
                'weather_risk': 'Low',
                'weather_risk_explanation': 'Clear skies',
                'comfort_advisory': 'Pleasant conditions'
            },
            'fare_data': {
                'price_trend': 'rising',
                'fare_trend_insight': 'Prices rising 12%'
            }
        }
        result = lambda_handler(event, None)
        
        assert result['success'] is True
        data = result['data']
        assert data['booking_recommendation'] == "Book Now"
        assert "Low weather risk" in data['recommendation_rationale']
        assert "rising" in data['recommendation_rationale']
    
    def test_handler_uses_recommendation_logic_low_risk_dropping_fares(self):
        """Test handler recommends Wait for low risk and dropping fares."""
        event = {
            'destination': 'LAX',
            'travel_window': {
                'start_date': '2024-07-15',
                'end_date': '2024-07-22'
            },
            'weather_data': {
                'weather_risk': 'Low',
                'weather_risk_explanation': 'Clear skies',
                'comfort_advisory': 'Pleasant conditions'
            },
            'fare_data': {
                'price_trend': 'dropping',
                'fare_trend_insight': 'Prices dropping 15%'
            }
        }
        result = lambda_handler(event, None)
        
        assert result['success'] is True
        data = result['data']
        assert data['booking_recommendation'] == "Wait"
        assert "Low weather risk" in data['recommendation_rationale']
        assert "dropping" in data['recommendation_rationale']
    
    def test_handler_uses_recommendation_logic_medium_risk_stable_fares(self):
        """Test handler recommends Change Dates for medium risk and stable fares."""
        event = {
            'destination': 'LAX',
            'travel_window': {
                'start_date': '2024-07-15',
                'end_date': '2024-07-22'
            },
            'weather_data': {
                'weather_risk': 'Medium',
                'weather_risk_explanation': 'Possible rain',
                'comfort_advisory': 'Moderate conditions'
            },
            'fare_data': {
                'price_trend': 'stable',
                'fare_trend_insight': 'Prices stable'
            }
        }
        result = lambda_handler(event, None)
        
        assert result['success'] is True
        data = result['data']
        assert data['booking_recommendation'] == "Change Dates"
        assert "Moderate weather risk" in data['recommendation_rationale']


class TestCalculateWindowScore:
    """Test window score calculation algorithm."""
    
    def test_low_risk_dropping_fares_highest_score(self):
        """Test that low risk + dropping fares gets highest score (130)."""
        score = calculate_window_score("Low", "dropping")
        assert score == 130  # 100 + 30
    
    def test_low_risk_stable_fares(self):
        """Test that low risk + stable fares gets 120 points."""
        score = calculate_window_score("Low", "stable")
        assert score == 120  # 100 + 20
    
    def test_low_risk_rising_fares(self):
        """Test that low risk + rising fares gets 110 points."""
        score = calculate_window_score("Low", "rising")
        assert score == 110  # 100 + 10
    
    def test_medium_risk_dropping_fares(self):
        """Test that medium risk + dropping fares gets 80 points."""
        score = calculate_window_score("Medium", "dropping")
        assert score == 80  # 50 + 30
    
    def test_medium_risk_stable_fares(self):
        """Test that medium risk + stable fares gets 70 points."""
        score = calculate_window_score("Medium", "stable")
        assert score == 70  # 50 + 20
    
    def test_medium_risk_rising_fares(self):
        """Test that medium risk + rising fares gets 60 points."""
        score = calculate_window_score("Medium", "rising")
        assert score == 60  # 50 + 10
    
    def test_high_risk_dropping_fares(self):
        """Test that high risk + dropping fares gets 30 points."""
        score = calculate_window_score("High", "dropping")
        assert score == 30  # 0 + 30
    
    def test_high_risk_stable_fares(self):
        """Test that high risk + stable fares gets 20 points."""
        score = calculate_window_score("High", "stable")
        assert score == 20  # 0 + 20
    
    def test_high_risk_rising_fares_lowest_score(self):
        """Test that high risk + rising fares gets lowest score (10)."""
        score = calculate_window_score("High", "rising")
        assert score == 10  # 0 + 10


class TestFindAlternativeWindows:
    """Test alternative window search algorithm."""
    
    @patch('handler.invoke_weather_tool')
    @patch('handler.invoke_fare_tool')
    def test_find_alternatives_returns_top_3(self, mock_fare, mock_weather):
        """Test that find_alternative_windows returns at most 3 alternatives."""
        # Mock weather and fare tool responses
        mock_weather.return_value = {
            'weather_risk': 'Low',
            'weather_risk_explanation': 'Clear skies',
            'comfort_advisory': 'Pleasant'
        }
        mock_fare.return_value = {
            'price_trend': 'dropping',
            'fare_trend_insight': 'Prices dropping'
        }
        
        alternatives = find_alternative_windows(
            '2024-07-15',
            '2024-07-22',
            'LAX',
            'JFK'
        )
        
        # Should return at most 3 alternatives
        assert len(alternatives) <= 3
        
        # Each alternative should have required fields
        for alt in alternatives:
            assert 'start_date' in alt
            assert 'end_date' in alt
            assert 'weather_risk' in alt
            assert 'fare_trend' in alt
            assert 'summary' in alt
            assert 'score' not in alt  # Score should be removed from output
    
    @patch('handler.invoke_weather_tool')
    @patch('handler.invoke_fare_tool')
    def test_find_alternatives_skips_original_window(self, mock_fare, mock_weather):
        """Test that original window is not included in alternatives."""
        mock_weather.return_value = {
            'weather_risk': 'Low',
            'weather_risk_explanation': 'Clear skies',
            'comfort_advisory': 'Pleasant'
        }
        mock_fare.return_value = {
            'price_trend': 'stable',
            'fare_trend_insight': 'Prices stable'
        }
        
        original_start = '2024-07-15'
        original_end = '2024-07-22'
        
        alternatives = find_alternative_windows(
            original_start,
            original_end,
            'LAX',
            'JFK'
        )
        
        # Original window should not be in alternatives
        for alt in alternatives:
            assert not (alt['start_date'] == original_start and alt['end_date'] == original_end)
    
    @patch('handler.invoke_weather_tool')
    @patch('handler.invoke_fare_tool')
    def test_find_alternatives_sorted_by_score(self, mock_fare, mock_weather):
        """Test that alternatives are sorted by score (best first)."""
        # Return different scores for different dates
        def weather_side_effect(dest, start, end):
            # Make earlier dates have lower risk
            if start < '2024-07-10':
                return {'weather_risk': 'Low', 'weather_risk_explanation': 'Clear', 'comfort_advisory': 'Good'}
            else:
                return {'weather_risk': 'High', 'weather_risk_explanation': 'Storms', 'comfort_advisory': 'Poor'}
        
        def fare_side_effect(origin, dest, start, end):
            return {'price_trend': 'stable', 'fare_trend_insight': 'Stable'}
        
        mock_weather.side_effect = weather_side_effect
        mock_fare.side_effect = fare_side_effect
        
        alternatives = find_alternative_windows(
            '2024-07-15',
            '2024-07-22',
            'LAX',
            'JFK'
        )
        
        # Verify alternatives are sorted by score (Low risk should come first)
        if len(alternatives) >= 2:
            # Calculate scores for verification
            scores = [calculate_window_score(alt['weather_risk'], alt['fare_trend']) for alt in alternatives]
            # Scores should be in descending order
            assert scores == sorted(scores, reverse=True)
    
    @patch('handler.invoke_weather_tool')
    @patch('handler.invoke_fare_tool')
    def test_find_alternatives_handles_tool_failures(self, mock_fare, mock_weather):
        """Test that find_alternative_windows handles tool invocation failures gracefully."""
        # Make some calls fail
        mock_weather.side_effect = [
            None,  # First call fails
            {'weather_risk': 'Low', 'weather_risk_explanation': 'Clear', 'comfort_advisory': 'Good'},
            None,  # Third call fails
        ] + [{'weather_risk': 'Low', 'weather_risk_explanation': 'Clear', 'comfort_advisory': 'Good'}] * 30
        
        mock_fare.return_value = {
            'price_trend': 'stable',
            'fare_trend_insight': 'Stable'
        }
        
        alternatives = find_alternative_windows(
            '2024-07-15',
            '2024-07-22',
            'LAX',
            'JFK'
        )
        
        # Should still return alternatives (just fewer)
        assert isinstance(alternatives, list)
    
    @patch('handler.invoke_weather_tool')
    @patch('handler.invoke_fare_tool')
    def test_find_alternatives_preserves_window_duration(self, mock_fare, mock_weather):
        """Test that alternative windows have the same duration as original."""
        mock_weather.return_value = {
            'weather_risk': 'Low',
            'weather_risk_explanation': 'Clear',
            'comfort_advisory': 'Good'
        }
        mock_fare.return_value = {
            'price_trend': 'stable',
            'fare_trend_insight': 'Stable'
        }
        
        original_start = datetime.strptime('2024-07-15', '%Y-%m-%d')
        original_end = datetime.strptime('2024-07-22', '%Y-%m-%d')
        original_duration = (original_end - original_start).days
        
        alternatives = find_alternative_windows(
            '2024-07-15',
            '2024-07-22',
            'LAX',
            'JFK'
        )
        
        # Each alternative should have same duration
        for alt in alternatives:
            alt_start = datetime.strptime(alt['start_date'], '%Y-%m-%d')
            alt_end = datetime.strptime(alt['end_date'], '%Y-%m-%d')
            alt_duration = (alt_end - alt_start).days
            assert alt_duration == original_duration


class TestPersistToDynamoDB:
    """Test DynamoDB persistence."""
    
    @patch.dict(os.environ, {'DYNAMODB_TABLE': 'test-table'})
    @patch('handler.dynamodb')
    def test_persist_success(self, mock_dynamodb):
        """Test successful DynamoDB persistence."""
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        result = persist_to_dynamodb(
            query_id='test-123',
            destination='LAX',
            origin='JFK',
            travel_window_start='2024-07-15',
            travel_window_end='2024-07-22',
            weather_risk='Low',
            fare_trend='rising',
            booking_recommendation='Book Now'
        )
        
        assert result is True
        mock_table.put_item.assert_called_once()
        
        # Verify the item structure
        call_args = mock_table.put_item.call_args
        item = call_args[1]['Item']
        
        assert item['query_id'] == 'test-123'
        assert item['destination'] == 'LAX'
        assert item['origin'] == 'JFK'
        assert item['travel_window_start'] == '2024-07-15'
        assert item['travel_window_end'] == '2024-07-22'
        assert item['weather_risk'] == 'Low'
        assert item['fare_trend'] == 'rising'
        assert item['booking_recommendation'] == 'Book Now'
        assert 'timestamp' in item
        assert 'ttl' in item
        
        # Verify TTL is approximately 90 days from now
        now = datetime.now()
        ttl_date = datetime.fromtimestamp(item['ttl'])
        days_diff = (ttl_date - now).days
        assert 89 <= days_diff <= 91  # Allow 1 day tolerance
    
    @patch.dict(os.environ, {'DYNAMODB_TABLE': 'test-table'})
    @patch('handler.dynamodb')
    def test_persist_handles_dynamodb_error(self, mock_dynamodb):
        """Test that persist_to_dynamodb handles DynamoDB errors gracefully."""
        mock_table = MagicMock()
        mock_table.put_item.side_effect = Exception("DynamoDB error")
        mock_dynamodb.Table.return_value = mock_table
        
        result = persist_to_dynamodb(
            query_id='test-123',
            destination='LAX',
            origin='JFK',
            travel_window_start='2024-07-15',
            travel_window_end='2024-07-22',
            weather_risk='Low',
            fare_trend='rising',
            booking_recommendation='Book Now'
        )
        
        # Should return False but not raise exception
        assert result is False
    
    @patch.dict(os.environ, {})
    def test_persist_handles_missing_env_var(self):
        """Test that persist_to_dynamodb handles missing environment variable."""
        result = persist_to_dynamodb(
            query_id='test-123',
            destination='LAX',
            origin='JFK',
            travel_window_start='2024-07-15',
            travel_window_end='2024-07-22',
            weather_risk='Low',
            fare_trend='rising',
            booking_recommendation='Book Now'
        )
        
        # Should return False but not raise exception
        assert result is False


class TestLambdaHandlerWithAlternatives:
    """Test Lambda handler with alternative window search."""
    
    @patch('handler.persist_to_dynamodb')
    @patch('handler.find_alternative_windows')
    def test_handler_finds_alternatives_for_change_dates(self, mock_find_alt, mock_persist):
        """Test that handler finds alternatives when recommendation is Change Dates."""
        mock_persist.return_value = True
        mock_find_alt.return_value = [
            {
                'start_date': '2024-07-20',
                'end_date': '2024-07-27',
                'weather_risk': 'Low',
                'fare_trend': 'stable',
                'summary': 'Weather: Low, Fares: stable'
            }
        ]
        
        event = {
            'destination': 'LAX',
            'origin': 'JFK',
            'travel_window': {
                'start_date': '2024-07-15',
                'end_date': '2024-07-22'
            },
            'weather_data': {
                'weather_risk': 'High',
                'weather_risk_explanation': 'Severe storms',
                'comfort_advisory': 'Dangerous conditions'
            },
            'fare_data': {
                'price_trend': 'stable',
                'fare_trend_insight': 'Prices stable'
            }
        }
        
        result = lambda_handler(event, None)
        
        assert result['success'] is True
        data = result['data']
        
        # Should recommend Change Dates
        assert data['booking_recommendation'] == 'Change Dates'
        
        # Should have alternatives
        assert data['alternative_windows'] is not None
        assert len(data['alternative_windows']) > 0
        
        # Verify find_alternative_windows was called
        mock_find_alt.assert_called_once()
    
    @patch('handler.persist_to_dynamodb')
    @patch('handler.find_alternative_windows')
    def test_handler_no_alternatives_for_book_now(self, mock_find_alt, mock_persist):
        """Test that handler does not search alternatives for Book Now recommendation."""
        mock_persist.return_value = True
        
        event = {
            'destination': 'LAX',
            'origin': 'JFK',
            'travel_window': {
                'start_date': '2024-07-15',
                'end_date': '2024-07-22'
            },
            'weather_data': {
                'weather_risk': 'Low',
                'weather_risk_explanation': 'Clear skies',
                'comfort_advisory': 'Pleasant'
            },
            'fare_data': {
                'price_trend': 'rising',
                'fare_trend_insight': 'Prices rising'
            }
        }
        
        result = lambda_handler(event, None)
        
        assert result['success'] is True
        data = result['data']
        
        # Should recommend Book Now
        assert data['booking_recommendation'] == 'Book Now'
        
        # Should not have alternatives
        assert data['alternative_windows'] is None
        
        # Verify find_alternative_windows was NOT called
        mock_find_alt.assert_not_called()
    
    @patch('handler.persist_to_dynamodb')
    @patch('handler.find_alternative_windows')
    def test_handler_persists_to_dynamodb(self, mock_find_alt, mock_persist):
        """Test that handler persists query to DynamoDB."""
        mock_persist.return_value = True
        mock_find_alt.return_value = []
        
        event = {
            'query_id': 'test-query-123',
            'destination': 'LAX',
            'origin': 'JFK',
            'travel_window': {
                'start_date': '2024-07-15',
                'end_date': '2024-07-22'
            },
            'weather_data': {
                'weather_risk': 'Low',
                'weather_risk_explanation': 'Clear',
                'comfort_advisory': 'Good'
            },
            'fare_data': {
                'price_trend': 'stable',
                'fare_trend_insight': 'Stable'
            }
        }
        
        result = lambda_handler(event, None)
        
        assert result['success'] is True
        
        # Verify persist_to_dynamodb was called with correct parameters
        mock_persist.assert_called_once()
        call_args = mock_persist.call_args[1]
        
        assert call_args['query_id'] == 'test-query-123'
        assert call_args['destination'] == 'LAX'
        assert call_args['origin'] == 'JFK'
        assert call_args['travel_window_start'] == '2024-07-15'
        assert call_args['travel_window_end'] == '2024-07-22'
        assert call_args['weather_risk'] == 'Low'
        assert call_args['fare_trend'] == 'stable'
        assert call_args['booking_recommendation'] == 'Book Now'
    
    @patch('handler.persist_to_dynamodb')
    @patch('handler.find_alternative_windows')
    def test_handler_continues_on_dynamodb_failure(self, mock_find_alt, mock_persist):
        """Test that handler continues and returns recommendation even if DynamoDB fails."""
        mock_persist.return_value = False  # Simulate DynamoDB failure
        mock_find_alt.return_value = []
        
        event = {
            'destination': 'LAX',
            'origin': 'JFK',
            'travel_window': {
                'start_date': '2024-07-15',
                'end_date': '2024-07-22'
            },
            'weather_data': {
                'weather_risk': 'Low',
                'weather_risk_explanation': 'Clear',
                'comfort_advisory': 'Good'
            },
            'fare_data': {
                'price_trend': 'stable',
                'fare_trend_insight': 'Stable'
            }
        }
        
        result = lambda_handler(event, None)
        
        # Should still succeed despite DynamoDB failure
        assert result['success'] is True
        assert 'data' in result
        assert result['data']['booking_recommendation'] == 'Book Now'
