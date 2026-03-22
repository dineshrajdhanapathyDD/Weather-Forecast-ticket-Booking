# Implementation Plan: Weather-Wise Flight Booking Agent

## Overview

This implementation plan builds a serverless Weather-Wise Flight Booking Agent on AWS using Python. The system uses Amazon Bedrock (AgentCore with Strands) to orchestrate MCP tools implemented as Lambda functions. The agent analyzes weather forecasts, climate risks, and fare trends to provide actionable booking recommendations through a REST API.

Implementation will proceed incrementally: infrastructure setup, core MCP tools, recommendation algorithms, Bedrock agent configuration, error handling, and comprehensive testing with property-based tests for all 25 correctness properties.

## Tasks

- [x] 1. Set up AWS infrastructure and project structure
  - Create Python project structure with separate directories for each Lambda function
  - Set up AWS CDK or Terraform infrastructure-as-code for Lambda, API Gateway, S3, DynamoDB
  - Configure S3 bucket `weather-wise-historical-data` with folder structure for weather and fare data
  - Configure DynamoDB table `weather-wise-queries` with partition key `query_id` and GSI `destination-timestamp-index`
  - Set up API Gateway with POST /recommend endpoint
  - Configure IAM roles and policies for Lambda functions to access S3 and DynamoDB
  - _Requirements: 1.4, 8.1, 9.1_

- [ ] 2. Implement Weather MCP Tool Lambda function
  - [x] 2.1 Create Weather Tool core structure and external API integration
    - Implement Lambda handler with input validation for destination, start_date, end_date
    - Integrate with external weather API (OpenWeatherMap or WeatherAPI.com) for forecast retrieval
    - Implement S3 data retrieval for historical disruption rates by destination and season
    - Return structured WeatherToolOutput with forecast array and climate_risks object
    - _Requirements: 1.1, 1.2, 1.4_
  
  - [x] 2.2 Implement weather risk calculation algorithm
    - Implement CalculateWeatherRisk algorithm from design (disruption probability + climate risks)
    - Classify risk as High (>40% or severe risk), Medium (15-40%), Low (<15%)
    - Generate risk explanation string with disruption percentage and activated risks
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_
  
  - [x] 2.3 Implement comfort score and advisory generation
    - Implement GenerateComfortAdvisory algorithm analyzing temperature, precipitation, humidity, wind
    - Calculate average temperature, max precipitation probability, average humidity from forecast
    - Generate comfort factors list based on thresholds (cold <10°C, heat >35°C, rain >70%, humidity >80%)
    - Return formatted advisory string with temperature ranges, precipitation likelihood, warnings
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  
  - [ ]* 2.4 Write property tests for Weather Tool
    - **Property 5: Climate Risk Evaluation Completeness** - verify all five climate risk types evaluated
    - **Property 6: Disruption Probability Calculation** - verify output between 0-100
    - **Property 7: Weather Risk Classification** - verify correct classification for all disruption prob and climate risk combinations
    - **Property 8: Comfort Score Calculation Completeness** - verify all four factors (temp, humidity, precip, wind) used
    - **Property 9: Climate Advisory Generation** - verify advisory identifies specific conditions
    - **Property 10: Climate Advisory Completeness** - verify advisory includes temp ranges, precip likelihood, warnings
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.1, 3.2, 3.4**

- [ ] 3. Implement Fare MCP Tool Lambda function
  - [x] 3.1 Create Fare Tool core structure and external API integration
    - Implement Lambda handler with input validation for origin, destination, start_date, end_date
    - Integrate with external fare API (Skyscanner or Amadeus) for current price retrieval
    - Implement S3 data retrieval for 30-day historical fare data by route
    - Calculate trend percentage: ((current - 30d_ago) / 30d_ago) * 100
    - Return structured FareToolOutput with current_price, price_30d_ago, price_trend, trend_percentage, price_history
    - _Requirements: 1.3, 1.4, 4.1_
  
  - [x] 3.2 Implement fare trend classification algorithm
    - Implement ClassifyFareTrend algorithm from design
    - Classify as rising (>10% increase), stable (±10%), dropping (>10% decrease)
    - Generate insight string with trend direction and percentage
    - _Requirements: 4.2, 4.3, 4.4, 4.5, 4.6_
  
  - [ ]* 3.3 Write property tests for Fare Tool
    - **Property 11: Fare Analysis Window** - verify exactly 30 days of price data analyzed
    - **Property 12: Fare Trend Classification** - verify correct classification for all price change percentages
    - **Property 13: Fare Trend Context** - verify output includes trend magnitude context
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6**

- [x] 4. Checkpoint - Ensure MCP tools work independently
  - Test Weather Tool with sample destinations and date ranges
  - Test Fare Tool with sample routes and date ranges
  - Verify S3 data retrieval works correctly
  - Ensure all tests pass, ask the user if questions arise

- [ ] 5. Implement Recommendation Engine Lambda function
  - [x] 5.1 Create Recommendation Engine core structure
    - Implement Lambda handler accepting query_id, destination, travel_window, weather_data, fare_data
    - Parse and validate input data structures
    - Return structured RecommendationOutput with all required fields
    - _Requirements: 5.1_
  
  - [x] 5.2 Implement booking recommendation logic algorithm
    - Implement GenerateBookingRecommendation algorithm from design
    - Apply decision rules: High risk → Change Dates; Medium risk + not dropping → Change Dates; Low risk + dropping → Wait; Low risk + rising/stable → Book Now
    - Generate rationale string explaining the recommendation
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [x] 5.3 Implement alternative window search algorithm
    - Implement FindAlternativeWindows algorithm from design
    - Search ±14 days from original start date
    - For each candidate window, invoke Weather and Fare tools
    - Calculate window score (Low=100, Medium=50, High=0 + dropping=30, stable=20, rising=10)
    - Return top 3 alternatives ranked by score
    - _Requirements: 5.6, 6.1, 6.2, 6.3, 6.5_
  
  - [x] 5.4 Implement DynamoDB persistence
    - Create QueryRecord with query_id, timestamp, destination, origin, travel_window, weather_risk, fare_trend, booking_recommendation
    - Set TTL to 90 days from creation (Unix timestamp)
    - Write record to DynamoDB table
    - Log errors but continue if DynamoDB write fails (graceful degradation)
    - _Requirements: 1.5, 9.1, 9.2, 9.3, 9.4, 9.5_
  
  - [ ]* 5.5 Write property tests for Recommendation Engine
    - **Property 14: Booking Recommendation Logic** - verify correct recommendation for all weather risk and fare trend combinations
    - **Property 15: Alternative Window Generation** - verify alternatives suggested when recommending Change Dates
    - **Property 16: Alternative Window Search Range** - verify search within ±14 days
    - **Property 17: Alternative Window Evaluation** - verify both weather risk and fare trend evaluated for alternatives
    - **Property 18: Alternative Window Ranking** - verify at most 3 alternatives ranked by score
    - **Property 19: Alternative Window Completeness** - verify each alternative includes weather risk and fare trend
    - **Property 3: Query Persistence** - verify complete DynamoDB record written with all fields and 90-day TTL
    - **Property 24: DynamoDB Failure Resilience** - verify recommendation returned even if DynamoDB write fails
    - **Validates: Requirements 1.5, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 6.1, 6.2, 6.3, 6.5, 9.1, 9.2, 9.3, 9.4, 9.5**

- [ ] 6. Implement error handling and retry logic
  - [x] 6.1 Implement exponential backoff retry for MCP tool invocations
    - Create InvokeMCPToolWithRetry wrapper function
    - Implement max 2 retries (3 total attempts) with exponential backoff (1s, 2s delays)
    - Return error response after max retries exceeded
    - _Requirements: 10.1_
  
  - [x] 6.2 Implement graceful degradation for partial data failures
    - Implement HandlePartialDataFailure algorithm from design
    - Generate weather-only recommendation when fare data unavailable (with disclaimer)
    - Generate fare-only recommendation when weather data unavailable (with disclaimer)
    - Return error when both data sources unavailable
    - _Requirements: 10.2, 10.3, 10.4, 10.5_
  
  - [x] 6.3 Implement input validation
    - Implement ValidateRequest algorithm from design
    - Validate required parameters: destination, origin, travel_window with start_date and end_date
    - Validate dates are in future and end_date after start_date
    - Validate travel window does not exceed 30 days
    - Validate destination is recognized location and origin is valid IATA code
    - Return HTTP 400 with descriptive error message for validation failures
    - _Requirements: 8.4, 8.5, 10.6, 10.7, 10.8_
  
  - [ ]* 6.4 Write property tests for error handling
    - **Property 4: MCP Tool Failure Handling** - verify error logged and descriptive message returned
    - **Property 23: Input Validation** - verify all validation rules enforced and HTTP 400 returned
    - **Property 25: MCP Tool Retry with Exponential Backoff** - verify 3 total attempts with correct delays
    - **Validates: Requirements 1.6, 8.4, 8.5, 10.1, 10.6, 10.7, 10.8**

- [x] 7. Configure Amazon Bedrock Agent with Strands orchestration
  - [x] 7.1 Create Bedrock Agent configuration
    - Define agent with AgentCore and Strands orchestration
    - Configure agent to invoke Weather Tool, Fare Tool, and Recommendation Engine in sequence
    - Set up agent instructions for workflow: validate input → get weather → get fares → generate recommendation
    - Configure agent to handle conversation context and multi-turn interactions
    - _Requirements: 1.1, 1.2, 1.3_
  
  - [x] 7.2 Implement response formatting
    - Implement FormatResponse template from design
    - Include emoji indicators: 🌦️ Weather Risk, 🌡️ Comfort Advisory, 💰 Fare Trend, ✅ Recommendation, 🔁 Alternatives
    - Include all required sections with proper formatting
    - Conditionally include Alternative Travel Windows section only when alternatives exist
    - Ensure response does not explain AWS services or MCP protocol
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_
  
  - [x] 7.3 Configure API Gateway integration
    - Wire API Gateway POST /recommend endpoint to Bedrock Agent
    - Configure request/response transformations for JSON format
    - Set up HTTP status codes: 200 for success, 400 for validation errors, 500 for service errors
    - Ensure API response includes all required fields: weather_risk, comfort_advisory, fare_trend, booking_recommendation, alternative_windows
    - _Requirements: 8.1, 8.2, 8.3, 8.6_
  
  - [ ]* 7.4 Write property tests for agent orchestration
    - **Property 1: MCP Tool Invocation Completeness** - verify all required tools invoked with correct parameters
    - **Property 2: Historical Data Access** - verify S3 accessed for historical weather and fare data
    - **Property 20: Response Structure Completeness** - verify all required sections with emoji indicators present
    - **Property 21: Response Content Restrictions** - verify no AWS/MCP explanations in response
    - **Property 22: API Response Format** - verify valid JSON with all required fields
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 8.2, 8.3, 8.6**

- [x] 8. Checkpoint - End-to-end integration testing
  - Test complete flow from API Gateway through Bedrock Agent to all Lambda functions
  - Verify weather risk calculation with various disruption probabilities and climate risks
  - Verify fare trend classification with various price changes
  - Verify booking recommendation logic for all weather/fare combinations
  - Verify alternative window search and ranking
  - Verify DynamoDB records created with correct TTL
  - Verify error handling and retry logic
  - Verify graceful degradation for partial failures
  - Ensure all tests pass, ask the user if questions arise

- [ ] 9. Set up property-based testing framework
  - [x] 9.1 Configure fast-check for Python (using Hypothesis instead)
    - Install Hypothesis library for property-based testing in Python
    - Configure test runner (pytest) with Hypothesis integration
    - Set minimum 100 iterations per property test
    - Set up test tagging: Feature: weather-wise-flight-booking, Property {N}: {property_text}
    - _Requirements: All requirements (testing framework)_
  
  - [x] 9.2 Organize property tests by component
    - Create test files for Weather Tool (Properties 5-10)
    - Create test files for Fare Tool (Properties 11-13)
    - Create test files for Recommendation Engine (Properties 3, 14-19, 24)
    - Create test files for Agent Orchestration (Properties 1, 2, 4, 20-23, 25)
    - _Requirements: All requirements (test organization)_

- [ ]* 10. Write remaining property-based tests
  - Run all 25 property tests with minimum 100 iterations each
  - Verify all properties pass consistently
  - Document any edge cases discovered during property testing
  - Fix any bugs revealed by property tests
  - _Requirements: All requirements (comprehensive validation)_

- [ ]* 11. Write unit tests for edge cases and specific scenarios
  - Test empty weather data, extreme temperatures, 100% precipitation probability
  - Test malformed API responses and network timeouts
  - Test "no alternatives found" scenario (Requirement 6.4)
  - Test partial failure scenarios: weather-only, fare-only, complete failure
  - Test boundary conditions: exactly 10% price change, exactly 15% and 40% disruption probability
  - Test travel window edge cases: 1-day window, 30-day window, dates at year boundary
  - _Requirements: All requirements (edge case coverage)_

- [ ] 12. Final integration and deployment preparation
  - [x] 12.1 Create deployment scripts and documentation
    - Write deployment scripts for infrastructure (CDK/Terraform)
    - Document environment variables and configuration for each Lambda function
    - Document external API keys and credentials setup
    - Create README with setup instructions and architecture overview
    - _Requirements: All requirements (deployment)_
  
  - [x] 12.2 Set up monitoring and logging
    - Configure CloudWatch Logs for all Lambda functions
    - Set up CloudWatch Metrics for API Gateway request counts and latencies
    - Configure alarms for error rates and Lambda timeouts
    - Enable X-Ray tracing for distributed tracing across components
    - _Requirements: 1.6, 10.1 (observability)_
  
  - [x] 12.3 Prepare sample historical data for S3
    - Create sample historical weather disruption data for common destinations
    - Create sample historical fare data for common routes
    - Upload sample data to S3 with correct folder structure
    - Document data format and update process
    - _Requirements: 1.4 (historical data)_

- [x] 13. Final checkpoint - Complete system validation
  - Run full test suite (unit tests + property tests + integration tests)
  - Verify all 25 correctness properties pass
  - Test with real external APIs (weather and fare)
  - Verify end-to-end flow with multiple test scenarios
  - Verify monitoring and logging working correctly
  - Ensure all tests pass, ask the user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties across all inputs
- Unit tests validate specific examples, edge cases, and error conditions
- Implementation uses Python for all Lambda functions
- Hypothesis library used for property-based testing (Python equivalent of fast-check)
- All algorithms from design document implemented as specified
- Checkpoints ensure incremental validation at key milestones
