# API Specification

## Base URL

```
https://{api-id}.execute-api.{region}.amazonaws.com/prod
```

## Endpoints

### POST /recommend

Generate a booking recommendation based on weather and fare data.

#### Request

**Headers**:
```
Content-Type: application/json
```

**Body**:
```json
{
  "destination": "LAX",
  "origin": "JFK",
  "travel_window": {
    "start_date": "2024-07-15",
    "end_date": "2024-07-22"
  }
}
```

**Parameters**:
- `destination` (string, required): IATA airport code or city name
- `origin` (string, required): IATA airport code
- `travel_window` (object, required):
  - `start_date` (string, required): ISO 8601 date (YYYY-MM-DD)
  - `end_date` (string, required): ISO 8601 date (YYYY-MM-DD)

#### Response

**Success (200)**:
```json
{
  "query_id": "550e8400-e29b-41d4-a716-446655440000",
  "weather_risk": "Low",
  "weather_risk_explanation": "Clear skies expected with minimal disruption risk (8%)",
  "comfort_advisory": "Pleasant temperatures 22-28°C, low humidity, ideal travel conditions",
  "fare_trend_insight": "Prices rising 15% over past 30 days - book soon to lock in rates",
  "booking_recommendation": "Book Now",
  "recommendation_rationale": "Low weather risk and rising fares make this an optimal time to book",
  "alternative_windows": null
}
```

**Success with Alternatives (200)**:
```json
{
  "query_id": "550e8400-e29b-41d4-a716-446655440000",
  "weather_risk": "High",
  "weather_risk_explanation": "Severe storms expected with high disruption risk (65%)",
  "comfort_advisory": "Heavy rain and strong winds expected - uncomfortable travel conditions",
  "fare_trend_insight": "Prices stable over past 30 days",
  "booking_recommendation": "Change Dates",
  "recommendation_rationale": "High weather risk makes travel unsafe - consider alternative dates",
  "alternative_windows": [
    {
      "start_date": "2024-07-08",
      "end_date": "2024-07-15",
      "weather_risk": "Low",
      "fare_trend": "stable",
      "summary": "Clear conditions with stable pricing"
    },
    {
      "start_date": "2024-07-22",
      "end_date": "2024-07-29",
      "weather_risk": "Low",
      "fare_trend": "dropping",
      "summary": "Good weather and decreasing fares"
    }
  ]
}
```

**Error - Invalid Request (400)**:
```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Missing required parameter: destination"
  }
}
```

**Error - Validation Failed (400)**:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Travel window start_date must be in the future"
  }
}
```

**Error - Service Unavailable (500)**:
```json
{
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "Weather data unavailable. Please try again later."
  }
}
```

**Error - Internal Error (500)**:
```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An unexpected error occurred"
  }
}
```

## Rate Limiting

- Rate: 100 requests per second
- Burst: 200 requests

Exceeding these limits will result in HTTP 429 (Too Many Requests).

## CORS

CORS is enabled for all origins. The following headers are supported:
- `Content-Type`
- `Authorization`

## Authentication

Currently, the API does not require authentication. For production use, consider adding:
- API Keys
- AWS IAM authentication
- Cognito user pools
- OAuth 2.0

## Error Codes

| Code | Description |
|------|-------------|
| `INVALID_REQUEST` | Missing required parameters |
| `VALIDATION_ERROR` | Invalid parameter values |
| `SERVICE_UNAVAILABLE` | External service unavailable |
| `DATA_UNAVAILABLE` | Both weather and fare data unavailable |
| `INTERNAL_ERROR` | Unexpected server error |
| `MAX_RETRIES_EXCEEDED` | Failed after retry attempts |

## Example Usage

### cURL

```bash
curl -X POST https://abc123.execute-api.us-east-1.amazonaws.com/prod/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "LAX",
    "origin": "JFK",
    "travel_window": {
      "start_date": "2024-07-15",
      "end_date": "2024-07-22"
    }
  }'
```

### Python

```python
import requests

url = "https://abc123.execute-api.us-east-1.amazonaws.com/prod/recommend"
payload = {
    "destination": "LAX",
    "origin": "JFK",
    "travel_window": {
        "start_date": "2024-07-15",
        "end_date": "2024-07-22"
    }
}

response = requests.post(url, json=payload)
print(response.json())
```

### JavaScript

```javascript
const response = await fetch('https://abc123.execute-api.us-east-1.amazonaws.com/prod/recommend', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    destination: 'LAX',
    origin: 'JFK',
    travel_window: {
      start_date: '2024-07-15',
      end_date: '2024-07-22'
    }
  })
});

const data = await response.json();
console.log(data);
```
