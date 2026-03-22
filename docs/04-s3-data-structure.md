# S3 Historical Data Structure

## Bucket: weather-wise-historical-data

### Weather Historical Data

**Path Pattern**: `weather/{destination}/{year}/{month}/disruption_rates.json`

**Example**: `weather/LAX/2024/01/disruption_rates.json`

**File Format**:
```json
{
  "destination": "LAX",
  "year": 2024,
  "month": 1,
  "historical_disruption_rate": 12.5,
  "seasonal_patterns": {
    "storms": {
      "frequency": 0.15,
      "severity": "moderate"
    },
    "heavy_rain": {
      "frequency": 0.25,
      "severity": "low"
    },
    "extreme_heat": {
      "frequency": 0.05,
      "severity": "low"
    },
    "monsoon": {
      "frequency": 0.0,
      "severity": "none"
    },
    "poor_visibility": {
      "frequency": 0.10,
      "severity": "low"
    }
  },
  "average_conditions": {
    "temp_high": 20,
    "temp_low": 10,
    "precipitation_days": 8,
    "humidity": 65
  }
}
```

### Fare Historical Data

**Path Pattern**: `fares/{origin}-{destination}/{year}/{month}/daily_prices.json`

**Example**: `fares/JFK-LAX/2024/01/daily_prices.json`

**File Format**:
```json
{
  "route": "JFK-LAX",
  "year": 2024,
  "month": 1,
  "currency": "USD",
  "daily_prices": [
    {
      "date": "2024-01-01",
      "price": 350.00,
      "availability": "high"
    },
    {
      "date": "2024-01-02",
      "price": 365.00,
      "availability": "medium"
    }
  ],
  "monthly_average": 375.50,
  "monthly_min": 320.00,
  "monthly_max": 450.00
}
```

## Data Update Process

Historical data should be updated daily via scheduled batch jobs:

1. **Weather Data**: Fetch from weather API and aggregate
2. **Fare Data**: Fetch from fare API and store daily snapshots
3. **Upload to S3**: Organize by destination/route, year, and month

## Data Retention

- Lifecycle rule: Delete data older than 365 days
- Keep at least 12 months of historical data for trend analysis
