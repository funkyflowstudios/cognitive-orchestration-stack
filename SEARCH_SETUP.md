# Search Engine Setup Guide

The ARIS research system supports multiple search engines for gathering information. By default, it runs in demonstration mode with curated content.

## Current Setup

### Demonstration Mode (Default)
- **Status**: ✅ Active
- **Content**: Curated, high-quality content for demonstration
- **No setup required**: Works out of the box
- **Perfect for**: Development, testing, and demonstration

### Google Custom Search API (Optional)
- **Status**: Available but requires setup
- **Content**: Real-time search results from Google
- **Setup required**: API credentials needed
- **Perfect for**: Production use with real search results

## Setting Up Google Custom Search API

If you want to use real Google search results instead of demonstration content:

### 1. Get Google API Key
1. Go to [Google Cloud Console](https://console.developers.google.com/)
2. Create a new project or select existing one
3. Enable the "Custom Search API"
4. Create credentials (API Key)
5. Copy the API key

### 2. Create Custom Search Engine
1. Go to [Google Custom Search Engine](https://cse.google.com/cse/)
2. Create a new search engine
3. Set it to search the entire web
4. Copy the Search Engine ID (CSE ID)

### 3. Configure Environment
Add these to your `.env` file:
```env
GOOGLE_API_KEY=your_actual_api_key_here
GOOGLE_CSE_ID=your_actual_cse_id_here
```

### 4. Restart the Application
The system will automatically detect the credentials and use Google search.

## Fallback Behavior

The system is designed to gracefully handle API failures:
- If Google API is not configured → Uses demonstration mode
- If Google API fails → Falls back to demonstration mode
- If both fail → Shows error message

## Cost Considerations

- **Google Custom Search API**: 100 free queries per day
- **Demonstration Mode**: Free, unlimited
- **Recommendation**: Use demonstration mode for development, Google API for production

## Troubleshooting

### "403 Forbidden" Errors
- Check if API key is correct
- Verify Custom Search Engine is set up properly
- Ensure API is enabled in Google Cloud Console

### "No results found"
- Check if CSE ID is correct
- Verify search engine is configured to search the web
- Check if API quota is exceeded

### Still using demonstration mode
- Verify `.env` file has correct credentials
- Restart the application after adding credentials
- Check logs for configuration errors
