# Tests

This directory contains unit tests and property-based tests for the Weather-Wise Flight Booking Agent.

## Test Structure

```
tests/
├── unit/                    # Unit tests
│   ├── test_weather_tool.py
│   ├── test_fare_tool.py
│   └── test_recommendation.py
├── property/                # Property-based tests
│   ├── test_weather_properties.py
│   ├── test_fare_properties.py
│   └── test_recommendation_properties.py
└── integration/             # Integration tests
    └── test_api_gateway.py
```

## Running Tests

### All Tests
```bash
pytest tests/
```

### Unit Tests Only
```bash
pytest tests/unit/
```

### Property-Based Tests Only
```bash
pytest tests/property/ -m property
```

### With Coverage
```bash
pytest tests/ --cov=lambda --cov-report=html
```

## Test Framework

- **Unit Tests**: pytest
- **Property-Based Tests**: Hypothesis (Python)
- **Mocking**: moto (AWS services), unittest.mock

## Writing Tests

### Unit Test Example

```python
import pytest
from lambda.weather_tool.handler import lambda_handler

def test_weather_tool_missing_parameters():
    event = {'parameters': {}}
    result = lambda_handler(event, None)
    
    assert result['success'] is False
    assert result['error']['code'] == 'INVALID_INPUT'
```

### Property-Based Test Example

```python
from hypothesis import given, strategies as st
import pytest

@given(
    disruption_prob=st.floats(min_value=0, max_value=100),
    has_severe_risk=st.booleans()
)
def test_weather_risk_classification(disruption_prob, has_severe_risk):
    # Test that weather risk is always one of three valid values
    risk = calculate_weather_risk(disruption_prob, has_severe_risk)
    assert risk in ['Low', 'Medium', 'High']
```

## Test Coverage Goals

- Unit test coverage: > 80%
- Property-based tests: All correctness properties from design.md
- Integration tests: All API endpoints

## Mocking Strategy

### External APIs
- Mock weather API responses
- Mock fare API responses

### AWS Services
- Use moto for S3 and DynamoDB mocking
- Use in-memory stores for local testing

### Lambda Invocations
- Mock Lambda client for recommendation engine tests
