# Weather-Wise API Examples

This directory contains example code demonstrating how to use the Weather-Wise Flight Booking APIs.

## Available Examples

### `api_comparison.py`

Demonstrates the difference between the two API endpoints:
- `/recommend` - Structured JSON API
- `/chat` - Conversational AI API

**Usage**:
```bash
# Update API_BASE_URL in the script first
python api_comparison.py

# Or run specific tests:
python api_comparison.py --structured      # Test structured API only
python api_comparison.py --conversational  # Test conversational API only
python api_comparison.py --compare         # Show comparison
python api_comparison.py --various         # Test various query formats
```

## Quick Examples

### Structured API (`/recommend`)

**Python**:
```python
import requests

response = requests.post(
    'https://your-api-gateway/prod/recommend',
    json={
        "destination": "LAX",
        "origin": "JFK",
        "travel_window": {
            "start_date": "2024-07-15",
            "end_date": "2024-07-22"
        }
    }
)

result = response.json()
print(result['data']['booking_recommendation'])
```

**JavaScript**:
```javascript
const response = await fetch('https://your-api-gateway/prod/recommend', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    destination: 'LAX',
    origin: 'JFK',
    travel_window: {
      start_date: '2024-07-15',
      end_date: '2024-07-22'
    }
  })
});

const result = await response.json();
console.log(result.data.booking_recommendation);
```

**cURL**:
```bash
curl -X POST https://your-api-gateway/prod/recommend \
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

### Conversational API (`/chat`)

**Python**:
```python
import requests

response = requests.post(
    'https://your-api-gateway/prod/chat',
    json={
        "message": "I want to fly to Los Angeles from New York in mid-July"
    }
)

result = response.json()
print(result['response'])
```

**JavaScript**:
```javascript
const response = await fetch('https://your-api-gateway/prod/chat', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    message: 'I want to fly to Los Angeles from New York in mid-July'
  })
});

const result = await response.json();
console.log(result.response);
```

**cURL**:
```bash
curl -X POST https://your-api-gateway/prod/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to fly to Los Angeles from New York in mid-July"
  }'
```

## Response Examples

### Structured API Response

```json
{
  "success": true,
  "data": {
    "query_id": "550e8400-e29b-41d4-a716-446655440000",
    "weather_risk": "Low",
    "weather_risk_explanation": "Clear skies expected with minimal disruption risk (8%)",
    "comfort_advisory": "Pleasant temperatures 22-28°C, low humidity, ideal travel conditions",
    "fare_trend_insight": "Prices rising 15% over past 30 days - book soon to lock in rates",
    "booking_recommendation": "Book Now",
    "recommendation_rationale": "Low weather risk and rising fares make this an optimal time to book",
    "alternative_windows": null
  }
}
```

### Conversational API Response

```json
{
  "statusCode": 200,
  "body": {
    "response": "🌦️ Weather Risk Summary: Low\nClear skies expected with minimal disruption risk (8%)\n\n🌡️ Comfort & Climate Advisory:\nPleasant temperatures 22-28°C, low humidity, ideal travel conditions\n\n💰 Fare Trend Insight:\nPrices rising 15% over past 30 days - book soon to lock in rates\n\n✅ Final Booking Recommendation: Book Now\nLow weather risk and rising fares make this an optimal time to book"
  }
}
```

## Integration Examples

### React Component

```jsx
import { useState } from 'react';

function FlightBookingAssistant() {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState('chat'); // 'chat' or 'structured'

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (mode === 'chat') {
        // Conversational API
        const res = await fetch('https://your-api-gateway/prod/chat', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ message: query })
        });
        const data = await res.json();
        setResponse(data.response);
      } else {
        // Structured API (requires parsing query first)
        const res = await fetch('https://your-api-gateway/prod/recommend', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(JSON.parse(query)) // Assumes JSON input
        });
        const data = await res.json();
        setResponse(JSON.stringify(data.data, null, 2));
      }
    } catch (error) {
      setResponse(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="booking-assistant">
      <div className="mode-selector">
        <button onClick={() => setMode('chat')} 
                className={mode === 'chat' ? 'active' : ''}>
          Conversational
        </button>
        <button onClick={() => setMode('structured')} 
                className={mode === 'structured' ? 'active' : ''}>
          Structured
        </button>
      </div>

      <form onSubmit={handleSubmit}>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={mode === 'chat' 
            ? "Ask about flight booking..." 
            : "Enter JSON request..."}
          rows={mode === 'chat' ? 3 : 10}
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Processing...' : 'Get Recommendation'}
        </button>
      </form>

      {response && (
        <div className="response" style={{ whiteSpace: 'pre-wrap' }}>
          {response}
        </div>
      )}
    </div>
  );
}
```

### Python CLI Tool

```python
#!/usr/bin/env python3
import requests
import sys
import json

API_BASE = "https://your-api-gateway/prod"

def get_recommendation(message: str, use_chat: bool = True):
    """Get booking recommendation"""
    if use_chat:
        # Conversational API
        response = requests.post(
            f"{API_BASE}/chat",
            json={"message": message}
        )
        result = response.json()
        return result.get('response', 'No response')
    else:
        # Structured API (requires proper JSON)
        data = json.loads(message)
        response = requests.post(
            f"{API_BASE}/recommend",
            json=data
        )
        result = response.json()
        return json.dumps(result.get('data', {}), indent=2)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cli_tool.py <message>")
        print("       python cli_tool.py --structured <json>")
        sys.exit(1)
    
    use_chat = sys.argv[1] != "--structured"
    message = " ".join(sys.argv[2:] if not use_chat else sys.argv[1:])
    
    print(get_recommendation(message, use_chat))
```

## Error Handling

### Handling API Errors

```python
import requests

def safe_api_call(endpoint, payload):
    """Make API call with error handling"""
    try:
        response = requests.post(
            endpoint,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400:
            error = response.json()
            print(f"Invalid request: {error.get('error', {}).get('message')}")
        elif response.status_code == 500:
            print("Server error. Please try again later.")
        else:
            print(f"Unexpected error: {response.status_code}")
            
    except requests.Timeout:
        print("Request timed out. Please try again.")
    except requests.ConnectionError:
        print("Connection error. Check your internet connection.")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    return None
```

## Best Practices

1. **Choose the Right Endpoint**:
   - Use `/recommend` for programmatic access with structured data
   - Use `/chat` for user-facing conversational interfaces

2. **Handle Timeouts**:
   - Set appropriate timeout values (30s recommended)
   - Implement retry logic for transient failures

3. **Cache Responses**:
   - Cache common queries to reduce costs
   - Use query_id for deduplication

4. **Monitor Usage**:
   - Track API calls and costs
   - Set up CloudWatch alarms for errors

5. **Validate Input**:
   - Validate dates are in the future
   - Ensure airport codes are valid
   - Check travel window doesn't exceed 30 days

## Getting Your API Endpoint

After deploying with CDK:

```bash
# Get API endpoint
aws cloudformation describe-stacks \
  --stack-name WeatherWiseStack \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text

# Get chat endpoint specifically
aws cloudformation describe-stacks \
  --stack-name WeatherWiseStack \
  --query 'Stacks[0].Outputs[?OutputKey==`ChatEndpoint`].OutputValue' \
  --output text
```

## Support

For more examples and documentation:
- Main README: `../README.md`
- Agent Documentation: `../agent/README.md`
- Integration Guide: `../docs/bedrock-agent-integration.md`
- Deployment Guide: `../docs/deployment-guide.md`
