# Weather-Wise Flight Booking - Frontend

Modern React-based web interface for the Weather-Wise Flight Booking Agent.

## Features

- 💬 **Chat Mode**: Conversational AI interface powered by Amazon Bedrock
- 🔍 **Search Mode**: Structured form-based flight search
- 🌦️ **Weather Intelligence**: Real-time weather risk analysis
- 💰 **Fare Trends**: Price movement tracking and predictions
- ✅ **Smart Recommendations**: AI-powered booking advice
- 🔁 **Alternative Windows**: Suggested better travel dates

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure API Endpoint

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your API endpoint:

```
REACT_APP_API_ENDPOINT=https://your-api-id.execute-api.us-east-2.amazonaws.com/prod
```

### 3. Run Development Server

```bash
npm start
```

The app will open at [http://localhost:3000](http://localhost:3000)

### 4. Build for Production

```bash
npm run build
```

The production build will be in the `build/` folder.

## Project Structure

```
frontend/
├── public/
│   └── index.html          # HTML template
├── src/
│   ├── components/
│   │   ├── ChatInterface.js       # Chat mode component
│   │   ├── ChatInterface.css
│   │   ├── SearchForm.js          # Search form component
│   │   ├── SearchForm.css
│   │   ├── ResultsDisplay.js      # Results display component
│   │   └── ResultsDisplay.css
│   ├── App.js              # Main app component
│   ├── App.css
│   ├── index.js            # Entry point
│   └── index.css           # Global styles
├── .env.example            # Environment variables template
├── package.json            # Dependencies
└── README.md              # This file
```

## Usage

### Chat Mode

1. Click "💬 Chat Mode"
2. Type your travel query naturally:
   - "I want to fly to Los Angeles from New York in mid-August"
   - "Should I book a flight to Miami from Chicago in early September?"
3. Get conversational AI recommendations with weather and fare insights

### Search Mode

1. Click "🔍 Search Mode"
2. Fill in the form:
   - Origin airport code (e.g., JFK)
   - Destination airport code (e.g., LAX)
   - Departure and return dates
3. Click "Get Weather-Wise Recommendation"
4. View detailed analysis with:
   - Weather risk summary
   - Fare trend insights
   - Booking recommendation
   - Alternative travel windows

## API Integration

The frontend connects to two backend endpoints:

### Chat Endpoint
```
POST /chat
Body: { "message": "your query" }
```

### Recommend Endpoint
```
POST /recommend
Body: {
  "origin": "JFK",
  "destination": "LAX",
  "travel_window": {
    "start_date": "2024-08-15",
    "end_date": "2024-08-22"
  }
}
```

## Deployment

### Deploy to AWS S3 + CloudFront

1. Build the app:
```bash
npm run build
```

2. Create S3 bucket:
```bash
aws s3 mb s3://weather-wise-frontend
```

3. Upload build:
```bash
aws s3 sync build/ s3://weather-wise-frontend --delete
```

4. Configure S3 for static website hosting
5. (Optional) Set up CloudFront distribution for HTTPS

### Deploy to Netlify

1. Build the app:
```bash
npm run build
```

2. Install Netlify CLI:
```bash
npm install -g netlify-cli
```

3. Deploy:
```bash
netlify deploy --prod --dir=build
```

### Deploy to Vercel

1. Install Vercel CLI:
```bash
npm install -g vercel
```

2. Deploy:
```bash
vercel --prod
```

## Environment Variables

- `REACT_APP_API_ENDPOINT`: Your API Gateway endpoint URL

**Note**: API keys are stored securely in the backend Lambda environment variables, not in the frontend.

## Customization

### Colors

Edit the gradient colors in `src/index.css` and component CSS files:

```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### Branding

Update the header in `src/App.js`:

```jsx
<h1>🌦️ Your Brand Name</h1>
```

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Troubleshooting

### CORS Errors

Make sure your API Gateway has CORS enabled:
- Allow Origins: `*` or your frontend domain
- Allow Methods: `POST, OPTIONS`
- Allow Headers: `Content-Type, Authorization`

### API Connection Failed

1. Check `.env` file has correct API endpoint
2. Verify API is deployed and accessible
3. Check browser console for error details

### Build Errors

1. Delete `node_modules` and `package-lock.json`
2. Run `npm install` again
3. Try `npm run build` again

## License

Part of the Weather-Wise Flight Booking Agent project.
