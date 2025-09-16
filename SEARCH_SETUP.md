# Search Engine Setup Guide

The ARIS research system features a comprehensive multi-API search system with advanced filtering and quality scoring. By default, it runs in demonstration mode with curated content.

## Current Setup

### Demonstration Mode (Default)
- **Status**: ✅ Active
- **Content**: Curated, high-quality content for demonstration
- **No setup required**: Works out of the box
- **Perfect for**: Development, testing, and demonstration

### Bing Web Search API (Recommended)
- **Status**: Available and easy to set up
- **Content**: Real-time search results from Bing
- **Setup required**: Just an API key (no complex cloud setup)
- **Perfect for**: Production use with real search results
- **Free tier**: 1,000 searches per month

### DuckDuckGo Instant Answer API (Free)
- **Status**: Available automatically
- **Content**: Basic search results from DuckDuckGo
- **Setup required**: None (completely free)
- **Perfect for**: Basic search functionality
- **Limitations**: Limited to factual queries

### Google Custom Search API (Advanced)
- **Status**: Available but requires setup
- **Content**: Real-time search results from Google
- **Setup required**: Google Cloud project + API credentials
- **Perfect for**: High-volume production use

## Setting Up Bing Web Search API (Recommended)

Bing is much easier to set up than Google Cloud:

### 1. Get Bing API Key
1. Go to [Azure Cognitive Services](https://azure.microsoft.com/en-us/services/cognitive-services/bing-web-search-api/)
2. Sign up for a free Azure account
3. Create a Bing Search resource
4. Get your API key from the resource dashboard
5. Free tier: 1,000 searches per month

### 2. Configure Environment
Add this to your `.env` file:
```env
BING_API_KEY=your_actual_bing_api_key_here
```

### 3. Restart the Application
The system will automatically detect the Bing API key and use real search results.

## Setting Up Google Custom Search API (Advanced)

If you prefer Google's official API:

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

## Advanced Features

### Quality Scoring System
The search system includes an advanced quality scoring algorithm that evaluates:
- **Title Relevance** (40%): How well the title matches the query
- **Content Relevance** (30%): How well the body matches the query
- **Content Length** (10%): Longer content gets higher scores
- **Domain Authority** (10%): Trusted domains get bonus points
- **HTTPS Security** (5%): Secure connections get bonus points
- **Freshness** (5%): Recent content gets bonus points

### Advanced Filtering
The system automatically filters out:
- Non-English content and domains
- Low-quality results (short titles, poor relevance)
- Irrelevant content (login pages, social media)
- Duplicate results
- Results with too many non-ASCII characters

### Multi-API Fallback Chain
1. **Bing Web Search API** (if configured)
2. **DuckDuckGo Instant Answer API** (always available)
3. **Google Custom Search API** (if configured)
4. **Demonstration Mode** (final fallback)

## Fallback Behavior

The system is designed to gracefully handle API failures:
- If Bing API is not configured → Tries DuckDuckGo
- If DuckDuckGo fails → Tries Google Custom Search API
- If Google API is not configured → Uses demonstration mode
- If all APIs fail → Uses demonstration mode

## Cost Considerations

- **Bing Web Search API**: 1,000 free searches per month, then $5 per 1,000 searches
- **DuckDuckGo Instant Answer API**: Completely free, unlimited
- **Google Custom Search API**: 100 free queries per day
- **Demonstration Mode**: Free, unlimited
- **Recommendation**: Use Bing API for production (easiest setup), demonstration mode for development

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
