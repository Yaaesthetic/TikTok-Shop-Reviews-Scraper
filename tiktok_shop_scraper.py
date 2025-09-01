# run those command
# pip install firecrawl-py playwright beautifulsoup4
# playwright install


import os
import json
import time
import re
import csv
from datetime import datetime
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from typing import Dict, Any, List
from firecrawl import FirecrawlApp
import random

# This the API but for best coding practive it should be in .env or in runtime variable
# if reach limits create account in FIRECRAWL to use free tier
FIRECRAWL_API_KEY = "your api"

# TikTok Shop Domains - Based on research of official TikTok Shop domains
TIKTOK_SHOP_DOMAINS = {
    # Main shop domains
    'shop.tiktok.com': 'main_shop',
    'www.tiktok.com/shop': 'main_shop_path',
    
    # Business and seller domains
    'seller.tiktok.com': 'seller_center',
    'business.tiktokshop.com': 'business_portal',
    
    # Regional variations (common patterns)
    'shop-my.tiktok.com': 'regional_shop_my',
    'shop-sg.tiktok.com': 'regional_shop_sg',
    'shop-th.tiktok.com': 'regional_shop_th',
    'shop-vn.tiktok.com': 'regional_shop_vn',
    'shop-ph.tiktok.com': 'regional_shop_ph',
    'shop-id.tiktok.com': 'regional_shop_id',
    
    # Ads and support related
    'ads.tiktok.com': 'ads_platform',
    'support.tiktok.com': 'support_center'
}

# Shop URL patterns to match
SHOP_URL_PATTERNS = [
    r'.*shop\.tiktok\.com.*',
    r'.*tiktok\.com/shop.*',
    r'.*seller\.tiktok\.com.*',
    r'.*business\.tiktokshop\.com.*',
    r'.*shop-[a-z]{2}\.tiktok\.com.*',  # Regional patterns
    r'.*ads\.tiktok\.com.*help.*shop.*',  # Shop help pages
    r'.*support\.tiktok\.com.*shop.*'     # Shop support pages
]


class CombinedTikTokShopScraper:
    def __init__(self, firecrawl_key: str = None, headless: bool = False, timeout: int = 60000):
        """
        Initialize the combined scraper
        
        Args:
            firecrawl_key: Firecrawl API key
            headless: Whether to run browser in headless mode
            timeout: Page timeout in milliseconds
        """
        # Initialize Firecrawl for URL discovery
        self.firecrawl = FirecrawlApp(api_key=firecrawl_key or FIRECRAWL_API_KEY)
        
        # Playwright settings
        self.headless = headless
        self.timeout = timeout
        self.output_dir = "scraper_output_final_max"
        self.ensure_output_dir()
        
        # Language customization for CSV extraction
        self.brand_keywords = [
            'Brand', 'Marca', 'Marke', 'Marque',
            'Jenama', 'Merk',
            'Thương hiệu',  # Vietnamese
            'ماركة', 'العلامة التجارية'
        ]
        self.seller_prefixes = [
            'Sold by ', 'Vendido por ', 'Vendu par ',
            'Verkauft von ', 'Dijual oleh ',
            'Được bán bởi ', 'Bán bởi',  # Vietnamese
            'يُباع بواسطة ', 'اسم البائع'
        ]
        self.sold_keywords = ['sold', 'has been sold', 'đã được bán', 'مباع']
        
        # Geo-spoofing configurations
        self.geo_configs = {
            'US': {
                'timezone': 'America/New_York',
                'locale': 'en-US',
                'geolocation': {'latitude': 40.7128, 'longitude': -74.0060},
                'user_agents': [
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
                ],
                'headers': {
                    'Accept-Language': 'en-US,en;q=0.9',
                    'CF-IPCountry': 'US',
                    'X-Forwarded-For': '8.8.8.8',
                }
            },
            'VN': {
                'timezone': 'Asia/Ho_Chi_Minh',
                'locale': 'vi-VN',
                'geolocation': {'latitude': 10.8231, 'longitude': 106.6297},
                'user_agents': [
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ],
                'headers': {
                    'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
                    'CF-IPCountry': 'VN',
                    'X-Forwarded-For': '203.162.4.1',
                }
            },
            'SA': {
                'timezone': 'Asia/Riyadh',
                'locale': 'ar-SA',
                'geolocation': {'latitude': 24.7136, 'longitude': 46.6753},
                'user_agents': [
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ],
                'headers': {
                    'Accept-Language': 'ar-SA,ar;q=0.9,en;q=0.8',
                    'CF-IPCountry': 'SA',
                    'X-Forwarded-For': '213.130.117.1',
                }
            }
        }
        
        # URL region patterns
        self.url_region_patterns = {
            'vn': 'VN', 'sa': 'SA', 'us': 'US', 'uk': 'US',
            'sg': 'VN', 'my': 'VN', 'th': 'VN', 'ph': 'VN', 'id': 'VN',
            'ae': 'SA', 'kw': 'SA', 'qa': 'SA',
        }
        
        print("Combined TikTok Shop Scraper initialized")
        print("   - Firecrawl: TikTok Shop URL discovery")
        print("   - Playwright: Manual scraping with geo-spoofing")
        print("   - BeautifulSoup: HTML processing and CSV generation")
        
    def ensure_output_dir(self):
        """Create output directory if it doesn't exist"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    # ========== FIRECRAWL URL DISCOVERY (FROM CODE 1) ==========
    def _is_tiktok_shop_url(self, url: str) -> bool:
        """Check if URL is a valid TikTok Shop URL"""
        if not url:
            return False
        
        url_lower = url.lower()
        
        # Check against known shop domains
        for domain in TIKTOK_SHOP_DOMAINS.keys():
            if domain in url_lower:
                return True
        
        # Check against URL patterns
        for pattern in SHOP_URL_PATTERNS:
            if re.match(pattern, url_lower):
                return True
        
        return False
    
    def _classify_tiktok_shop_url(self, url: str) -> str:
        """Classify the type of TikTok Shop URL"""
        if not url:
            return 'unknown'
        
        url_lower = url.lower()
        
        # Check specific domain classifications
        for domain, domain_type in TIKTOK_SHOP_DOMAINS.items():
            if domain in url_lower:
                return domain_type
        
        # Pattern-based classification
        if '/product/' in url_lower:
            return 'shop_product'
        elif 'seller' in url_lower:
            return 'seller_portal'
        elif 'business' in url_lower:
            return 'business_portal'
        elif 'shop' in url_lower:
            return 'shop_general'
        else:
            return 'shop_related'

    def discover_tiktok_shop_urls(self, query: str, limit: int = 20, country: str = "vn") -> List[Dict[str, str]]:
        """Use Firecrawl to discover TikTok Shop URLs specifically"""
        print(f"Discovering TikTok Shop URLs for: '{query}'")
        
        all_discovered_urls = []
        
        try:
            print(f"  Searching: {query}")
            
            # The search query and limit are passed directly without enhancement
            search_result = self.firecrawl.search(
                query=query,
                limit=limit,
                country=country
            )
            
            if hasattr(search_result, 'data') and search_result.data:
                for result in search_result.data:
                    url = result.get('url', '')
                    
                    # CRITICAL FILTER: Only accept TikTok Shop URLs
                    if self._is_tiktok_shop_url(url):
                        url_info = {
                            'url': url,
                            'title': result.get('title', ''),
                            'description': result.get('description', ''),
                            'type': self._classify_tiktok_shop_url(url),
                            'query': query
                        }
                        all_discovered_urls.append(url_info)
                    else:
                        print(f"  Filtered out non-shop URL: {url}")
                        
        except Exception as e:
            print(f"  Error searching '{query}': {str(e)}")
        
        # Remove duplicates based on URL
        unique_urls = {}
        for url_info in all_discovered_urls:
            url = url_info['url']
            if url not in unique_urls:
                unique_urls[url] = url_info
        
        # The search API should already honor the limit, but slicing here ensures the final 
        # list length does not exceed the limit after deduplication.
        final_urls = list(unique_urls.values())[:limit]
        
        print(f"Discovered {len(final_urls)} unique TikTok Shop URLs")
        return final_urls

    # ========== PLAYWRIGHT SCRAPING (FROM CODE 2) ==========
    def normalize_url_to_generic_domain(self, url: str) -> tuple[str, str]:
        """Convert any shop-{country}.tiktok.com URL to shop.tiktok.com"""
        original_url = url
        detected_region = None
        
        # Pattern to match shop-{country}.tiktok.com
        pattern = r'shop-([a-z]{2})\.tiktok\.com'
        match = re.search(pattern, url, re.IGNORECASE)
        
        if match:
            country_code = match.group(1).lower()
            detected_region = self.url_region_patterns.get(country_code, 'US')
            
            # Replace shop-{country}.tiktok.com with shop.tiktok.com
            normalized_url = re.sub(pattern, 'shop.tiktok.com', url, flags=re.IGNORECASE)
            
            print(f"URL Conversion:")
            print(f"   Original: {original_url}")
            print(f"   Normalized: {normalized_url}")
            print(f"   Detected Region: {detected_region} (from {country_code})")
            
            return normalized_url, detected_region
        else:
            print(f"URL already in generic format: {url}")
            return url, None
    
    def detect_url_region(self, url: str) -> str:
        """Detect region from URL domain, path, or parameters"""
        url_lower = url.lower()
        
        # Check domain patterns
        for country_code, region in self.url_region_patterns.items():
            if f'shop-{country_code}.' in url_lower:
                print(f"Detected region from domain: {region} (found: shop-{country_code})")
                return region
        
        # Default fallback
        print("No region detected, defaulting to: VN")
        return 'VN'
    
    def modify_url_for_region(self, url: str, region: str) -> str:
        """Add region-specific parameters to the normalized URL"""
        if '?' in url:
            base_url = url.split('?')[0]
            params = []
            if '?' in url:
                existing_params = url.split('?')[1].split('&')
                for param in existing_params:
                    if not param.startswith(('region=', 'locale=', 'local=')):
                        params.append(param)
        else:
            base_url = url
            params = []
        
        # Add region-specific parameters
        if region == 'US':
            params.extend(['region=US', 'local=en'])
        elif region == 'VN':
            params.extend(['region=VN', 'local=vi'])
        elif region == 'SA':
            params.extend(['region=SA', 'local=ar'])
        
        if params:
            modified_url = f"{base_url}?{'&'.join(params)}"
        else:
            modified_url = base_url
            
        return modified_url
    
    def wait_for_captcha_manual(self, page):
        """Wait for user to manually solve captcha or skip URL"""
        print("\n" + "="*60)
        print("CAPTCHA DETECTED!")
        print("Please solve the captcha manually in the browser window.")
        print("Options:")
        print("  - Press ENTER after solving captcha to continue")
        print("  - Type 'skip' or 's' to skip this URL")
        print("  - Type 'quit' or 'q' to quit entire scraping process")
        print("="*60)
        
        user_input = input("Action (ENTER/skip/quit): ").strip().lower()
        
        if user_input in ['skip', 's']:
            print("Skipping this URL...")
            return 'skip'
        elif user_input in ['quit', 'q']:
            print("Quitting scraping process...")
            return 'quit'
        else:
            print("Continuing after captcha solving...")
            # Wait a bit more for page to load after captcha
            time.sleep(5)
            page.wait_for_load_state('domcontentloaded')
            return 'continue'
    
    def check_for_captcha(self, page) -> bool:
        """Check if page contains captcha or verification"""
        captcha_indicators = [
            'verify to continue', 'captcha', 'robot', 'verification', 'refresh'
        ]
        
        try:
            page_text = page.inner_text('body').lower()
            return any(indicator in page_text for indicator in captcha_indicators)
        except:
            return False
    
    def check_for_region_block(self, page) -> bool:
        """Check if page is blocked due to region restrictions"""
        region_block_indicators = [
            'product not available in this country',
            'not available in your country', 
            'not available in your region',
            'product not available in this country or region',
            'this product isn\'t currently available'
        ]
        
        try:
            page_text = page.inner_text('body').lower()
            return any(indicator in page_text for indicator in region_block_indicators)
        except:
            return False
    
    def save_html_content(self, content: str, url: str, attempt: int):
        """Save HTML content to file for debugging"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Create safe filename from URL
        safe_url = re.sub(r'[^a-zA-Z0-9]', '_', url)[:50]
        filename = f"{self.output_dir}/page_content_{safe_url}_attempt_{attempt}_{timestamp}.html"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"HTML content saved to: {filename}")
        return filename
    
    def scrape_url_with_playwright(self, url: str, attempt: int = 1, region: str = 'VN') -> Dict[str, Any]:
        """Scrape single URL using Playwright with manual captcha handling"""
        
        # Normalize URL and detect region
        normalized_url, url_detected_region = self.normalize_url_to_generic_domain(url)
        if url_detected_region:
            region = url_detected_region
        
        geo_config = self.geo_configs.get(region, self.geo_configs['VN'])
        modified_url = self.modify_url_for_region(normalized_url, region)
        
        print(f"Using geo-config for: {region}")
        print(f"Final URL: {modified_url}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox', 
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-web-security',
                    f'--lang={geo_config["locale"]}',
                ]
            )
            
            # Create context with geo-spoofing
            context = browser.new_context(
                user_agent=random.choice(geo_config['user_agents']),
                viewport={'width': 1920, 'height': 1080},
                locale=geo_config['locale'],
                timezone_id=geo_config['timezone'],
                geolocation=geo_config['geolocation'],
                permissions=['geolocation'],
                extra_http_headers=geo_config['headers']
            )
            
            page = context.new_page()
            
            try:
                page.set_default_timeout(self.timeout)
                
                print(f"Navigating to: {modified_url}")
                response = page.goto(modified_url, wait_until='networkidle', timeout=60000)
                
                if not response or not response.ok:
                    return {
                        "error": f"HTTP {response.status if response else 'No response'}", 
                        "region": region,
                        "url": modified_url,
                        "success": False
                    }
                
                print("Waiting for page to load...")
                page.wait_for_load_state('domcontentloaded')
                time.sleep(3)
                
                # Check for region blocking first
                if self.check_for_region_block(page):
                    print(f"Region blocked for {region}")
                    return {
                        "error": "Region blocked", 
                        "region_blocked": True, 
                        "region": region,
                        "url": modified_url,
                        "success": False
                    }
                
                # Check for captcha
                if self.check_for_captcha(page):
                    print("Captcha detected!")
                    if not self.headless:
                        captcha_action = self.wait_for_captcha_manual(page)
                        
                        if captcha_action == 'skip':
                            return {
                                "error": "User skipped URL due to captcha", 
                                "user_skipped": True,
                                "region": region,
                                "url": modified_url,
                                "original_url": url,
                                "success": False
                            }
                        elif captcha_action == 'quit':
                            return {
                                "error": "User quit scraping process", 
                                "user_quit": True,
                                "region": region,
                                "url": modified_url,
                                "original_url": url,
                                "success": False
                            }
                        
                        # Check again after captcha solving
                        if self.check_for_region_block(page):
                            print(f"Still region blocked after captcha for {region}")
                            return {
                                "error": "Region blocked after captcha", 
                                "region_blocked": True, 
                                "region": region,
                                "url": modified_url,
                                "success": False
                            }
                    else:
                        return {
                            "error": "Captcha detected but running in headless mode", 
                            "region": region,
                            "url": modified_url,
                            "success": False
                        }
                
                # Save HTML content
                html_content = page.content()
                html_filename = self.save_html_content(html_content, url, attempt)
                
                return {
                    "url": modified_url,
                    "original_url": url,
                    "region": region,
                    "html_filename": html_filename,
                    "html_content": html_content,
                    "success": True,
                    "scraped_at": datetime.now().isoformat()
                }
                
            except Exception as e:
                print(f"Error during scraping: {str(e)}")
                return {
                    "error": str(e), 
                    "attempt": attempt, 
                    "region": region,
                    "url": modified_url,
                    "original_url": url,
                    "success": False
                }
            finally:
                browser.close()

    # ========== CSV PROCESSING (FROM CODE 3) ==========
    def extract_product_from_html(self, html_content: str, source_url: str = "") -> Dict[str, Any]:
        """Extract product details and reviews from HTML content using BeautifulSoup"""
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract General Product Details
        try:
            product_name = soup.find('h1', class_='title-v0v6fK').get_text(strip=True)
        except AttributeError:
            product_name = 'N/A'

        try:
            price = soup.find('div', class_='price-w1xvrw').find('span').get_text(strip=True)
        except AttributeError:
            price = 'N/A'
            
        try:
            seller_raw_text = soup.find('div', class_='seller-c27aRQ').find('a').get_text(strip=True)
            seller = seller_raw_text
            for prefix in self.seller_prefixes:
                if seller_raw_text.strip().startswith(prefix):
                    seller = seller_raw_text.replace(prefix, '').strip()
                    break
        except AttributeError:
            seller = 'N/A'

        try:
            overall_rating = soup.find('span', class_='infoRatingScore-jSs6kd').get_text(strip=True)
        except AttributeError:
            overall_rating = 'N/A'

        try:
            ratings_text = soup.find('span', class_='infoRatingCount-lKBiTI').get_text(strip=True)
            total_ratings_match = re.search(r'\d+', ratings_text)
            total_ratings = total_ratings_match.group(0) if total_ratings_match else 'N/A'
        except AttributeError:
            total_ratings = 'N/A'
            
        try:
            sold_text = soup.find('div', class_='info__sold-ZdTfzQ').get_text(strip=True)
            sold_count_match = re.search(r'\d+', sold_text)
            sold_count = sold_count_match.group(0) if sold_count_match else 'N/A'
        except AttributeError:
            sold_count = 'N/A'
            
        brand = 'N/A'
        try:
            spec_items = soup.find_all('div', class_='specification-item-xNVbQy')
            for item in spec_items:
                label = item.find('span', class_='name-QGrd5O').get_text(strip=True)
                if label in self.brand_keywords:
                    brand = item.find('span', class_='value-B9KpLv').get_text(strip=True)
                    break
        except AttributeError:
            brand = 'N/A'

        # Extract All Customer Reviews
        review_container = soup.find('div', class_='reviews__bd-xTwQAs')
        reviews = review_container.find_all('div', class_='review-dpC7Ta') if review_container else []
        
        print(f"--- Product Details from {source_url} ---")
        print(f"Name: {product_name}")
        print(f"Price: {price}")
        print(f"Seller: {seller}")
        print(f"Brand: {brand}")
        print(f"Overall Rating: {overall_rating}/5")
        print(f"Total Ratings: {total_ratings}")
        print(f"Units Sold: {sold_count}")
        print(f"Reviews found: {len(reviews)}")
        print("-" * 50)
        
        # Process reviews
        processed_reviews = []
        if not reviews:
            processed_reviews.append({
                'review_username': 'N/A', 
                'review_date': 'N/A', 
                'review_rating': 'N/A', 
                'review_text': 'No reviews found', 
                'review_image_urls': 'N/A'
            })
        else:
            for review in reviews:
                try:
                    username = review.find('div', class_='review-info__nickname-_C8NYg').get_text(strip=True)
                except AttributeError:
                    username = 'N/A'
                try:
                    rating = len(review.find_all('div', class_='rating--on-COWbLl'))
                except AttributeError:
                    rating = 'N/A'
                try:
                    review_text = review.find('div', class_='review-item-S_JAON').get_text(strip=True)
                except AttributeError:
                    review_text = 'N/A'
                try:
                    review_date = review.find('div', class_='reviewSku-4Gh19a').find('div').get_text(strip=True)
                except AttributeError:
                    review_date = 'N/A'
                try:
                    image_tags = review.find('div', class_='review-photo-B_LuTG').find_all('img')
                    image_urls = ', '.join([img['src'] for img in image_tags]) if image_tags else 'No Images'
                except AttributeError:
                    image_urls = 'N/A'

                processed_reviews.append({
                    'review_username': username,
                    'review_date': review_date,
                    'review_rating': rating,
                    'review_text': review_text,
                    'review_image_urls': image_urls
                })
        
        return {
            'product_name': product_name,
            'price': price, 
            'seller': seller,
            'brand': brand,
            'overall_rating': overall_rating,
            'total_ratings': total_ratings,
            'sold_count': sold_count,
            'reviews': processed_reviews,
            'source_url': source_url
        }
    
    def save_to_csv(self, products_data: List[Dict[str, Any]], filename: str = None) -> str:
        """Save all products data to a single CSV file"""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.output_dir}/tiktok_products_reviews_{timestamp}.csv"
        
        fieldnames = [
            'source_url', 'product_name', 'price', 'seller', 'brand', 'overall_rating', 
            'total_ratings', 'sold_count', 'review_username', 'review_date', 
            'review_rating', 'review_text', 'review_image_urls'
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for product_data in products_data:
                for review in product_data['reviews']:
                    writer.writerow({
                        'source_url': product_data['source_url'],
                        'product_name': product_data['product_name'],
                        'price': product_data['price'],
                        'seller': product_data['seller'],
                        'brand': product_data['brand'],
                        'overall_rating': product_data['overall_rating'],
                        'total_ratings': product_data['total_ratings'],
                        'sold_count': product_data['sold_count'],
                        'review_username': review['review_username'],
                        'review_date': review['review_date'],
                        'review_rating': review['review_rating'],
                        'review_text': review['review_text'],
                        'review_image_urls': review['review_image_urls']
                    })
        
        print(f"All products and reviews saved to: {filename}")
        return filename

    # ========== MAIN WORKFLOW ==========
    def run_complete_scraping_workflow(self, query: str, url_limit: int = 10, max_attempts_per_url: int = 3) -> Dict[str, Any]:
        """
        Complete workflow: Discover URLs -> Scrape with Playwright -> Extract to CSV
        
        Args:
            query: Search query for TikTok Shop products
            url_limit: Maximum URLs to discover and scrape
            max_attempts_per_url: Maximum scraping attempts per URL
            
        Returns:
            Complete workflow results
        """
        
        print(f"Starting Complete TikTok Shop Scraping Workflow")
        print(f"Query: {query}")
        print(f"URL Limit: {url_limit}")
        print(f"Max Attempts per URL: {max_attempts_per_url}")
        print("="*80)
        
        # Step 1: Discover TikTok Shop URLs using Firecrawl
        print("\nSTEP 1: DISCOVERING TIKTOK SHOP URLS")
        print("="*50)
        discovered_urls = self.discover_tiktok_shop_urls(query, limit=url_limit)
        
        if not discovered_urls:
            print("No TikTok Shop URLs discovered. Exiting workflow.")
            return {
                'query': query,
                'discovered_urls': [],
                'scraping_results': [],
                'products_data': [],
                'csv_file': None,
                'summary': {'total_discovered': 0, 'successfully_scraped': 0, 'products_extracted': 0}
            }
        
        print(f"Discovered {len(discovered_urls)} URLs to scrape")
        
        # Step 2: Scrape each URL using Playwright with manual captcha handling
        print("\nSTEP 2: SCRAPING URLS WITH PLAYWRIGHT")
        print("="*50)
        
        scraping_results = []
        successful_scrapes = []
        
        regions_to_try = ['VN', 'SA', 'US']  # Prioritize VN and SA as requested
        
        for i, url_info in enumerate(discovered_urls, 1):
            url = url_info['url']
            print(f"\nScraping URL {i}/{len(discovered_urls)}: {url}")
            print(f"   Title: {url_info.get('title', 'N/A')}")
            print(f"   Type: {url_info.get('type', 'N/A')}")
            
            # Try scraping with different regions until successful
            scraped_successfully = False
            
            for attempt in range(1, max_attempts_per_url + 1):
                region = regions_to_try[(attempt - 1) % len(regions_to_try)]
                
                print(f"\n   Attempt {attempt}/{max_attempts_per_url} - Region: {region}")
                
                scrape_result = self.scrape_url_with_playwright(url, attempt, region)
                scrape_result['url_info'] = url_info  # Add original URL info
                
                scraping_results.append(scrape_result)
                
                if scrape_result.get('success', False):
                    print(f"   Successfully scraped on attempt {attempt}")
                    successful_scrapes.append(scrape_result)
                    scraped_successfully = True
                    break
                else:
                    error_msg = scrape_result.get('error', 'Unknown error')
                    print(f"   Attempt {attempt} failed: {error_msg}")
                    
                    if attempt < max_attempts_per_url:
                        wait_time = 3 + random.randint(1, 3)
                        print(f"   Waiting {wait_time} seconds before next attempt...")
                        time.sleep(wait_time)
            
            if not scraped_successfully:
                print(f"   All attempts failed for URL: {url}")
        
        print(f"\nScraping completed: {len(successful_scrapes)}/{len(discovered_urls)} URLs successfully scraped")
        
        # Step 3: Extract product data from successful HTML scrapes
        print("\nSTEP 3: EXTRACTING PRODUCT DATA AND REVIEWS")
        print("="*50)
        
        products_data = []
        
        for scrape_result in successful_scrapes:
            if scrape_result.get('html_content'):
                try:
                    source_url = scrape_result.get('original_url', scrape_result.get('url', ''))
                    product_data = self.extract_product_from_html(
                        scrape_result['html_content'], 
                        source_url
                    )
                    products_data.append(product_data)
                    
                except Exception as e:
                    print(f"Error extracting product data from {source_url}: {str(e)}")
        
        print(f"Extracted product data from {len(products_data)} HTML files")
        
        # Step 4: Save all data to CSV
        print("\nSTEP 4: SAVING TO CSV")
        print("="*30)
        
        csv_file = None
        if products_data:
            csv_file = self.save_to_csv(products_data)
        else:
            print("No product data to save to CSV")
        
        # Step 5: Generate summary
        summary = {
            'total_discovered': len(discovered_urls),
            'successfully_scraped': len(successful_scrapes),
            'products_extracted': len(products_data),
            'csv_generated': csv_file is not None,
            'workflow_completed_at': datetime.now().isoformat()
        }
        
        return {
            'query': query,
            'discovered_urls': discovered_urls,
            'scraping_results': scraping_results,
            'successful_scrapes': successful_scrapes,
            'products_data': products_data,
            'csv_file': csv_file,
            'summary': summary
        }


def main():
    """Main function to run the complete workflow"""
    
    print("COMBINED TIKTOK SHOP SCRAPER")
    print("===============================")
    print("1. Firecrawl discovers TikTok Shop URLs")
    print("2. Playwright scrapes each URL (with manual captcha handling)")
    print("3. BeautifulSoup extracts product data and reviews")
    print("4. All data saved to CSV with source URLs")
    print("="*70)
    
    scraper = CombinedTikTokShopScraper(headless=False, timeout=60000)
    
    query = "Lancôme products TikTok shop Vietnam"
    
    print(f"\nRunning workflow for query: '{query}'")
    print(f"Settings:")
    print(f"   - Headless mode: {scraper.headless}")
    print(f"   - Output directory: {scraper.output_dir}")
    print(f"   - Manual captcha handling: {'Enabled' if not scraper.headless else 'Disabled'}")
    
    # Ask user to confirm before starting
    print(f"\nIMPORTANT:")
    print(f"   - Browser window will open for manual captcha solving")
    print(f"   - You'll need to press ENTER after solving each captcha") 
    print(f"   - The process may take several minutes depending on captchas")
    
    user_input = input(f"\nPress ENTER to start scraping, or 'q' to quit: ").strip().lower()
    if user_input == 'q':
        print("Scraping cancelled by user")
        return
    
    # Run the complete workflow
    try:
        results = scraper.run_complete_scraping_workflow(
            query=query,
            url_limit=100,
            max_attempts_per_url=2
        )
        
        # Print final summary
        print("\n" + "="*70)
        print("FINAL WORKFLOW SUMMARY")
        print("="*70)
        
        summary = results['summary']
        print(f"Query: {results['query']}")
        print(f"URLs Discovered: {summary['total_discovered']}")
        print(f"URLs Successfully Scraped: {summary['successfully_scraped']}")
        print(f"Products Extracted: {summary['products_extracted']}")
        print(f"CSV Generated: {'Yes' if summary['csv_generated'] else 'No'}")
        
        if results['csv_file']:
            print(f"CSV File: {results['csv_file']}")
        
        if results['successful_scrapes']:
            print(f"\nSuccessfully Scraped URLs:")
            for i, scrape in enumerate(results['successful_scrapes'][:5], 1):  # Show first 5
                original_url = scrape.get('original_url', scrape.get('url', 'N/A'))
                region = scrape.get('region', 'N/A')
                print(f"   {i}. {original_url} (Region: {region})")
            
            if len(results['successful_scrapes']) > 5:
                print(f"   ... and {len(results['successful_scrapes']) - 5} more")
        
        print(f"\nWorkflow completed successfully!")
        print(f"Check the '{scraper.output_dir}' directory for all generated files")
        
    except KeyboardInterrupt:
        print(f"\nWorkflow interrupted by user (Ctrl+C)")
    except Exception as e:
        print(f"\nWorkflow failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()