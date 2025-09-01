# TikTok Shop Product & Reviews Scraper

A comprehensive Python scraper that combines multiple tools to discover, scrape, and extract product data and customer reviews from TikTok Shop. This tool uses Firecrawl for URL discovery, Playwright for web scraping with geo-spoofing, and BeautifulSoup for data extraction.

## Project Background

This scraping solution was developed based on practical experience with API integration and web scraping, building upon previous work with Google Play Store APIs for user comment collection and recent exploration of modern scraping tools like Firecrawl API through autonomous agent integration.

The primary objective is to collect customer reviews from Lancôme products on TikTok Shop, with specific focus on Vietnam and Saudi Arabia markets. The solution addresses three core challenges through a modular architecture that tackles each challenge with specialized tools.

## Features

### 🔍 **URL Discovery**
- Uses Firecrawl API to discover TikTok Shop product URLs
- Filters and validates TikTok Shop domains automatically
- Supports multiple TikTok Shop domain variations and regional sites
- Advanced filtering system that removes social media profiles and promotional content

### 🌍 **Multi-Region Support**
- **Geo-spoofing** for US, Vietnam (VN), and Saudi Arabia (SA)
- Automatic region detection from URLs
- Custom user agents, timezones, and geolocation settings
- Regional language support (English, Vietnamese, Arabic)
- URL normalization to handle regional redirects

### 🤖 **Advanced Scraping**
- **Manual captcha handling** - Browser window opens for user intervention
- Anti-detection measures with realistic browser fingerprints
- Multiple retry attempts with different regions
- Automatic URL normalization and region parameter injection
- JavaScript-rendered Single Page Application support

### 📊 **Data Extraction**
- **Product Information**: Name, price, seller, brand, ratings, units sold
- **Customer Reviews**: Username, date, rating, review text, image URLs
- Multi-language support for product specifications
- Comprehensive HTML content preservation
- Multi-language keyword recognition for brands and specifications

### 💾 **Data Output**
- CSV export with all product and review data
- HTML files saved for debugging and verification
- Structured data format for easy analysis
- Source URL tracking for verification

## Technical Architecture

### Three-Stage Approach

**Stage 1: URL Discovery with Firecrawl API**
- Searches for specific product URLs using targeted queries
- Filters results to include only valid TikTok Shop domains
- Removes irrelevant content like social media profiles and promotional materials

**Stage 2: Content Scraping with Playwright**
- Handles JavaScript-rendered Single Page Applications
- Implements geo-location spoofing for regional access
- Provides manual CAPTCHA handling capabilities

**Stage 3: Data Processing with BeautifulSoup**
- Extracts product details and customer reviews
- Supports multi-language content processing
- Generates structured CSV output

### Tool Comparison and Selection

**Firecrawl API (Selected Solution)**
- Successfully returns actual product pages from shop.tiktok.com domains
- Provides targeted URL discovery based on search terms
- Integrates filtering system for TikTok Shop-specific content

**BrightData API (Alternative Tested)**
- Functions more like traditional search engines (Google/Bing)
- Returns general information and social media content
- Limited effectiveness for specific product URL discovery

## Requirements

### Dependencies
```bash
pip install firecrawl-py playwright beautifulsoup4
playwright install
```

### API Key
- **Firecrawl API Key** - Sign up at [Firecrawl](https://firecrawl.dev) for free tier access

## Installation

1. **Clone or download the script**
2. **Install dependencies**:
   ```bash
   pip install firecrawl-py playwright beautifulsoup4
   playwright install
   ```
3. **Get Firecrawl API Key**:
   - Sign up at [Firecrawl](https://firecrawl.dev)
   - Get your free API key
   - Replace `"your api"` in the script with your actual API key

## Configuration

### API Key Setup
```python
FIRECRAWL_API_KEY = "your_actual_api_key_here"
```

### Scraper Settings
```python
scraper = CombinedTikTokShopScraper(
    headless=False,    # Set to True to run without browser window
    timeout=60000      # Page timeout in milliseconds
)
```

### Supported Regions
- **US**: English language, US timezone and geolocation
- **VN**: Vietnamese language, Vietnam timezone and geolocation  
- **SA**: Arabic language, Saudi Arabia timezone and geolocation

## Usage

### Basic Usage
```python
from tiktok_shop_scraper import CombinedTikTokShopScraper

# Initialize scraper
scraper = CombinedTikTokShopScraper(headless=False)

# Run complete workflow
results = scraper.run_complete_scraping_workflow(
    query="Lancôme products TikTok shop Vietnam",
    url_limit=20,
    max_attempts_per_url=2
)
```

### Running the Complete Workflow

1. **Start the scraper**:
   ```bash
   python tiktok_shop_scraper.py
   ```

2. **Handle captchas manually**:
   - Browser window will open when captcha is detected
   - Solve the captcha in the browser
   - Press ENTER in terminal to continue
   - Type 'skip' to skip current URL
   - Type 'quit' to stop scraping

3. **Review results**:
   - Check the `scraper_output_final_max/` directory
   - CSV file contains all product and review data
   - HTML files saved for verification

### Workflow Steps

1. **URL Discovery**: Firecrawl searches for TikTok Shop URLs
2. **URL Filtering**: Only valid TikTok Shop domains are kept
3. **Web Scraping**: Playwright scrapes each URL with geo-spoofing
4. **Data Extraction**: BeautifulSoup extracts product and review data
5. **CSV Generation**: All data saved to structured CSV file

## Technical Implementation Details

### Content Scraping Challenges

**Single Page Application Architecture**
- TikTok Shop uses JavaScript-heavy frontend architecture
- Content loads dynamically after initial page response
- Requires browser automation for proper content access

**Regional Access Patterns**
- Regional URLs (shop-vn.tiktok.com) often redirect to homepage
- Solution: URL normalization to generic format with regional parameters
- Geo-location spoofing implementation for market-specific content

### Anti-Detection Measures
- Realistic browser fingerprinting
- Random user agent rotation
- Appropriate request timing and delays
- Regional timezone and locale configuration

### Multi-Language Data Processing

The extraction system handles content in multiple languages:
- **English**: Standard product specifications and reviews
- **Vietnamese**: Localized content for Vietnam market
- **Arabic**: Right-to-left text support for Saudi Arabia market
- **Spanish**: Additional language support for broader coverage

## File Structure

```
scraper_output_final_max/
├── tiktok_products_reviews_YYYYMMDD_HHMMSS.csv
├── page_content_url1_attempt_1_YYYYMMDD_HHMMSS.html
├── page_content_url2_attempt_1_YYYYMMDD_HHMMSS.html
└── ...
```

### CSV Output Format
| Column | Description |
|--------|-------------|
| `source_url` | Original TikTok Shop product URL |
| `product_name` | Product title |
| `price` | Product price |
| `seller` | Seller name |
| `brand` | Product brand |
| `overall_rating` | Average rating (out of 5) |
| `total_ratings` | Number of ratings |
| `sold_count` | Units sold |
| `review_username` | Reviewer username |
| `review_date` | Review date |
| `review_rating` | Individual review rating |
| `review_text` | Review content |
| `review_image_urls` | Review images (comma-separated) |

## Customization

### Search Queries
```python
# Examples of effective search queries
queries = [
    "Lancôme products TikTok shop Vietnam",
    "skincare TikTok shop Saudi Arabia",
    "electronics TikTok shop"
]
```

### Region Priorities
Modify the `regions_to_try` list to prioritize different regions:
```python
regions_to_try = ['VN', 'SA', 'US']  # Vietnam first, then Saudi Arabia, then US
```

### Adding New Regions
Add new geo-configurations in the `geo_configs` dictionary:
```python
'DE': {
    'timezone': 'Europe/Berlin',
    'locale': 'de-DE',
    'geolocation': {'latitude': 52.5200, 'longitude': 13.4050},
    # ... other settings
}
```

## Troubleshooting

### Common Issues

1. **Captcha Problems**:
   - Ensure `headless=False` for manual captcha solving
   - Wait for page to fully load before solving
   - Some captchas may require multiple attempts

2. **Region Blocking**:
   - Script automatically tries multiple regions
   - VN and SA regions often have better access
   - Some products may not be available in certain regions

3. **API Limits**:
   - Firecrawl free tier has usage limits
   - Create new account or upgrade for higher limits
   - Check API key validity

4. **Scraping Failures**:
   - Increase timeout values for slow connections
   - Check internet connection stability
   - Some URLs may be temporarily unavailable

### Error Messages

- `"Region blocked"`: Product not available in that region
- `"Captcha detected"`: Manual intervention required
- `"HTTP 403/429"`: Rate limiting or access denied
- `"No TikTok Shop URLs discovered"`: Search query needs refinement

## Performance Metrics

- **Speed**: 2-5 URLs per minute (depending on captchas)
- **Success Rate**: ~70-80% (varies by region and time)
- **Data Quality**: High accuracy with manual verification possible
- **Scalability**: Suitable for small to medium datasets (10-100 URLs)

## Future Improvements

### Automation Enhancements
- Integration with automated CAPTCHA solving services
- Advanced proxy rotation for improved access reliability
- Machine learning-based content classification
- Automated quality assessment for extracted data

### Scalability Improvements
- Distributed scraping architecture for large-scale operations
- Database integration for persistent data storage
- Real-time monitoring and alerting systems
- API endpoint development for programmatic access

## Legal and Ethical Considerations

**Important Disclaimers**:

- **Respect robots.txt and terms of service**
- **Use responsibly** - don't overload servers
- **Personal use only** - respect TikTok's commercial interests
- **Data privacy** - handle scraped data appropriately
- **Rate limiting** - built-in delays prevent aggressive scraping

This tool is for educational and research purposes. Users are responsible for complying with all applicable laws and website terms of service.

## Technical Specifications

**Dependencies**
- `firecrawl-py`: URL discovery and search functionality
- `playwright`: Browser automation and JavaScript handling
- `beautifulsoup4`: HTML parsing and data extraction
- Standard Python libraries for data processing

**System Requirements**
- Sufficient memory for browser automation
- Reliable network connectivity
- Display capability for manual CAPTCHA solving
- Storage space for HTML content and CSV output

## Support

For issues, questions, or improvements:
1. Check the troubleshooting section
2. Review the error messages in terminal output
3. Examine saved HTML files for debugging
4. Verify API key and internet connection

***

**Version**: 1.0  
**Last Updated**: September 2025  

This solution represents a practical approach to modern web scraping challenges, combining specialized tools for optimal results while maintaining flexibility for different market requirements and technical constraints.
