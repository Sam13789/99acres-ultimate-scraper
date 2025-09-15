#!/usr/bin/env python3
"""
🌍 COMPREHENSIVE CITY SCRAPER 🌍
Scrapes ALL cities from city_w_id.json across all property types
- Option for test mode (first page only)
- Full mode (all pages until last page)
- Outputs JSON files compatible with optimized_multi_type_cleaner.py
- Stores everything in output/ folder
"""

import requests
import json
import pandas as pd
import time
import os
import re
import random
from datetime import datetime
import argparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import signal
import sys

class ComprehensiveCityScraper:
    def __init__(self, test_mode=False, max_cities=None, specific_cities=None, specific_property_types=None, max_pages=None, proxy_list=None, start_page=None, use_scraperapi=False):
        self.test_mode = test_mode
        self.max_cities = max_cities
        self.specific_cities = specific_cities  # List of city IDs to scrape
        self.specific_property_types = specific_property_types  # List of property types to scrape
        self.max_pages = max_pages  # Max pages per property type
        self.start_page = start_page or 1  # Page to start from (for resuming)
        self.proxy_list = proxy_list or []  # List of proxy servers
        self.current_proxy_index = 0
        self.proxy_lock = threading.Lock()  # Thread-safe proxy rotation
        self.use_scraperapi = use_scraperapi
        self.scraperapi_key = "f9d410254a31e74187f30b70ec66cd28"
        self.session = self._setup_session()
        
        # Interrupt handling variables
        self.interrupted = False
        self.current_city_id = None
        self.current_city_name = None
        self.current_property_type = None
        self.current_properties = []
        self.current_page = 1
        self.setup_interrupt_handler()
        
        # Property type mapping
        self.property_types = {
            1: "Residential Apartment",
            2: "Independent House/Villa", 
            3: "Residential Land",
            4: "Independent/Builder Floor",
            5: "Farm House"
        }
        
        # Load city mapping
        self.load_city_mapping()
        
        # Create output directories
        os.makedirs("output", exist_ok=True)
        os.makedirs("output/json_files", exist_ok=True)
        
        print("🌍 COMPREHENSIVE CITY SCRAPER INITIALIZED")
        print(f"🧪 Test Mode: {'ON (First page only)' if test_mode else 'OFF (All pages)'}")
        if max_cities:
            print(f"🏙️ Max Cities: {max_cities}")
        if specific_cities:
            print(f"🎯 Specific Cities: {len(specific_cities)} selected")
        if specific_property_types:
            types_names = [self.property_types[pt] for pt in specific_property_types if pt in self.property_types]
            print(f"🏠 Property Types: {', '.join(types_names)}")
        if max_pages:
            print(f"📄 Max Pages per Type: {max_pages}")
        if self.start_page > 1:
            print(f"🔄 Starting from Page: {self.start_page} (Resume mode)")
        if self.use_scraperapi:
            print(f"🌐 ScraperAPI: ENABLED (API Service)")
        elif proxy_list:
            print(f"🔄 Proxy Rotation: {len(proxy_list)} proxies loaded")
        print(f"🔄 Retry Logic: ENHANCED (5 retries per page + 2 batch retries)")
        print(f"🚀 Concurrent Scraping: ENABLED (5 pages at once)")
        print(f"💾 Auto-Save: ENABLED (on interruption + completion)")
        print(f"📊 Progress Tracking: ENABLED (saves resume info)")
        print(f"🗂️ Total Cities Available: {len(self.cities)}")
        print("=" * 70)
        
        # Check for previous progress
        self.check_previous_progress()
    
    def setup_interrupt_handler(self):
        """Setup signal handler for graceful interruption"""
        def signal_handler(signum, frame):
            print(f"\n\n🛑 INTERRUPT DETECTED! Saving current data...")
            self.interrupted = True
            self.save_on_interrupt()
            print("💾 Data saved! Raising KeyboardInterrupt to exit gracefully...")
            raise KeyboardInterrupt("User interrupted scraping")
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def save_on_interrupt(self):
        """Save current data when interrupted"""
        try:
            if self.current_properties and len(self.current_properties) > 0:
                print(f"💾 Saving {len(self.current_properties)} properties collected so far...")
                
                # Save intermediate data with current state
                self.save_intermediate_data(
                    self.current_city_id,
                    self.current_city_name,
                    self.current_property_type,
                    self.current_properties,
                    start_page=self.start_page,
                    end_page=self.current_page
                )
                
                # Save progress
                self.save_progress(
                    self.current_city_id,
                    self.current_city_name,
                    self.current_property_type,
                    self.current_page,
                    len(self.current_properties)
                )
                
                print(f"✅ Successfully saved {len(self.current_properties)} properties!")
                print(f"📄 Resume from page {self.current_page + 1} next time")
            else:
                print("⚠️ No properties to save")
                
        except Exception as e:
            print(f"❌ Error saving data on interrupt: {e}")
    
    def count_intermediate_files(self, timestamp):
        """Count properties in intermediate files created during current session"""
        total_count = 0
        json_dir = "output/json_files"
        
        if not os.path.exists(json_dir):
            return 0
            
        try:
            # Look for files with today's timestamp
            today = timestamp[:8]  # YYYYMMDD part
            
            for filename in os.listdir(json_dir):
                if filename.endswith('.json') and today in filename:
                    filepath = os.path.join(json_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                total_count += len(data)
                                print(f"    📄 {filename}: {len(data)} properties")
                    except Exception as e:
                        print(f"    ⚠️ Error reading {filename}: {e}")
                        
        except Exception as e:
            print(f"❌ Error counting intermediate files: {e}")
            
        return total_count
    
    def _setup_session(self):
        """Setup requests session with retry strategy and proxy support"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set proxy if available (only for regular proxy mode, not ScraperAPI)
        if self.proxy_list and not self.use_scraperapi:
            proxy = self._get_next_proxy()
            if proxy:
                session.proxies = {
                    'http': proxy,
                    'https': proxy
                }
                print(f"🔄 Using proxy: {proxy}")
        
        return session
    
    def _get_thread_session(self):
        """Get a thread-safe session for concurrent requests"""
        # Create a new session for each thread to avoid sharing
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set proxy if available (only for regular proxy mode, not ScraperAPI)
        if self.proxy_list and not self.use_scraperapi:
            proxy = self._get_next_proxy()
            if proxy:
                session.proxies = {
                    'http': proxy,
                    'https': proxy
                }
                # Note: Not printing proxy in thread context to avoid output conflicts
        
        return session
    
    def _get_next_proxy(self):
        """Get next proxy from the rotation list (thread-safe)"""
        if not self.proxy_list:
            return None
        
        with self.proxy_lock:
            proxy = self.proxy_list[self.current_proxy_index]
            self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
            return proxy
    
    def _rotate_proxy(self):
        """Rotate to next proxy and refresh session"""
        if self.proxy_list:
            self.session = self._setup_session()
            print(f"    🔄 Rotated to new proxy")
    
    def get_random_headers(self):
        """Generate random headers to avoid blocking"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        accept_languages = [
            'en-US,en;q=0.9',
            'en-US,en;q=0.9,hi;q=0.8',
            'en-IN,en;q=0.9,hi;q=0.8',
            'en-US,en;q=0.8,hi;q=0.7'
        ]
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': random.choice(accept_languages),
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'DNT': '1',
            'sec-gpc': '1',
            'Referer': 'https://www.99acres.com/',
            'Origin': 'https://www.99acres.com'
        }
    
    def load_city_mapping(self):
        """Load city mapping from JSON file"""
        try:
            with open('city_w_id.json', 'r', encoding='utf-8') as f:
                self.cities = json.load(f)
            print(f"✅ Loaded {len(self.cities)} cities from city_w_id.json")
        except FileNotFoundError:
            print("❌ city_w_id.json not found!")
            exit(1)
        except Exception as e:
            print(f"❌ Error loading cities: {e}")
            exit(1)
    
    def _get_city_url_suffix(self, city_id):
        """Get city URL suffix for certain property types"""
        city_suffixes = {
            "1": "delhi-ncr", "2": "delhi-ncr", "3": "delhi-ncr", "4": "delhi-ncr", "5": "delhi-ncr", "6": "delhi-ncr", "7": "noida", "8": "gurgaon", "9": "ghaziabad", "10": "faridabad",
            "12": "mumbai", "13": "mumbai", "14": "mumbai", "15": "mumbai", "16": "mumbai", "17": "mumbai", "19": "pune",
            "20": "bangalore", "21": "bangalore", "22": "bangalore", "23": "bangalore", "217": "bangalore", "252": "bangalore",
            "25": "kolkata", "26": "kolkata", "27": "kolkata", "28": "kolkata", "29": "kolkata", "30": "kolkata",
            "32": "chennai", "33": "chennai", "34": "chennai", "35": "chennai", "36": "chennai",
            "38": "hyderabad", "268": "hyderabad", "269": "hyderabad",
            "45": "ahmedabad", "46": "gandhinagar", "47": "ahmedabad", "48": "ahmedabad", "49": "ahmedabad"
        }
        return city_suffixes.get(str(city_id), "delhi-ncr")
    
    def build_search_url(self, city_id, property_type, page=1):
        """Build search URL for given parameters"""
        if property_type in [1, 2]:
            # Apartments and Houses use residential-apartments path
            base_url = f"https://www.99acres.com/search/property/buy/residential-apartments/?city={city_id}&property_type={property_type}&preference=S&area_unit=1&res_com=R"
        elif property_type in [3, 4, 5]:
            # Land and Builder floors use builder-floor path with location suffix
            city_suffix = self._get_city_url_suffix(city_id)
            base_url = f"https://www.99acres.com/search/property/buy/builder-floor/{city_suffix}?city={city_id}&property_type={property_type}&preference=S&area_unit=1&res_com=R"
        else:
            # Other types use apartments path
            base_url = f"https://www.99acres.com/search/property/buy/residential-apartments/?city={city_id}&property_type={property_type}&preference=S&area_unit=1&res_com=R"
        
        # Add page parameter if not page 1
        if page > 1:
            base_url += f"&page={page}"
            
        return base_url
    
    def extract_properties_from_html(self, html):
        """Extract property data from HTML response"""
        try:
            pattern = r'window\.__initialData__\s*=\s*({.*?});'
            match = re.search(pattern, html, re.DOTALL)
            if match:
                data_str = match.group(1)
                data = json.loads(data_str)
                if ('srp' in data and 'pageData' in data['srp'] and 'properties' in data['srp']['pageData']):
                    properties = data['srp']['pageData']['properties']
                    
                    # Check pagination info - try multiple paths
                    pagination = data.get('srp', {}).get('pageData', {}).get('pagination', {})
                    total_pages = pagination.get('totalPages', None)
                    current_page = pagination.get('currentPage', 1)
                    
                    # Try alternative pagination paths if not found
                    if total_pages is None:
                        # Check if pagination data exists elsewhere
                        alt_pagination = data.get('srp', {}).get('pagination', {})
                        total_pages = alt_pagination.get('totalPages', None)
                        if total_pages is None:
                            total_pages = alt_pagination.get('total_pages', None)
                    
                    # If still no pagination info and we have properties, assume more pages might exist
                    if total_pages is None:
                        # If we have a full page of properties (27 is typical), assume there might be more
                        if len(properties) >= 25:  # Threshold suggesting more pages exist
                            total_pages = 999  # Large number to allow pagination logic to continue
                        else:
                            total_pages = 1  # Likely last page if fewer properties
                    
                    return properties, current_page, total_pages
                    
        except Exception as e:
            print(f"❌ JSON parsing error: {e}")
        
        return [], 1, 1
    
    def fetch_with_retry(self, url, max_retries=3, session=None):
        """Fetch URL with retry logic"""
        # Use provided session or default to self.session
        session_to_use = session if session else self.session
        
        for attempt in range(max_retries):
            try:
                # Reduced output to avoid clutter during concurrent requests
                if attempt > 0:
                    print(f"🔄", end=" ")
                
                # No delays - removed for speed
                
                # Use ScraperAPI if enabled, otherwise use regular proxies
                if self.use_scraperapi:
                    # Use ScraperAPI service
                    scraper_url = f"http://api.scraperapi.com?api_key={self.scraperapi_key}&url={url}"
                    response = session_to_use.get(scraper_url, timeout=60)
                else:
                    # Use regular proxy method
                    headers = self.get_random_headers()
                    response = session_to_use.get(url, headers=headers, timeout=60)
                
                if response.status_code == 200:
                    return response
                elif response.status_code in [403, 429, 417]:
                    print(f"❌ Status {response.status_code} - IP/Proxy blocked")
                    if attempt < max_retries - 1:
                        # Try rotating proxy if available (only for regular proxy mode)
                        if not self.use_scraperapi:
                            self._rotate_proxy()
                        # No delays - removed for speed
                        
            except Exception as e:
                print(f"❌ Error: {str(e)[:50]}...")
                # No delays - removed for speed
        
        return None
    
    def fetch_single_page(self, city_id, property_type, page_num):
        """Fetch a single page - designed for concurrent execution with aggressive retry"""
        url = self.build_search_url(city_id, property_type, page_num)
        
        # Retry logic for pages with 0 properties - more aggressive
        max_retries_per_page = 5  # Increased retries
        page_retry_count = 0
        
        while page_retry_count < max_retries_per_page:
            session = self._get_thread_session()  # Fresh session each retry
            response = self.fetch_with_retry(url, session=session)
            
            if not response:
                page_retry_count += 1
                print(f"🔄 Page {page_num} retry {page_retry_count}/{max_retries_per_page} (fetch failed)")
                if page_retry_count < max_retries_per_page:
                    continue
                else:
                    print(f"❌ Page {page_num} failed after {max_retries_per_page} retries")
                    return page_num, [], 1, 1  # page_num, properties, current_page, total_pages
            
            # Extract properties
            properties, current_page, total_pages = self.extract_properties_from_html(response.text)
            
            # If we got properties, return them
            if properties:
                return page_num, properties, current_page, total_pages
            
            # If 0 properties, always retry unless max retries reached
            page_retry_count += 1
            if page_retry_count < max_retries_per_page:
                print(f"🔄 Page {page_num} retry {page_retry_count}/{max_retries_per_page} (0 properties)")
            else:
                print(f"⚠️ Page {page_num} still 0 properties after {max_retries_per_page} retries")
                return page_num, [], current_page, total_pages
        
        return page_num, [], 1, 1
    
    def scrape_city_property_type(self, city_id, city_name, property_type):
        """Scrape all pages for a city-property type combination using concurrent requests"""
        property_name = self.property_types[property_type]
        print(f"  📄 {property_name}")
        
        # Update instance variables for interrupt handling
        self.current_city_id = city_id
        self.current_city_name = city_name
        self.current_property_type = property_type
        self.current_properties = []
        self.current_page = self.start_page
        
        all_properties = []
        page = self.start_page
        start_page_for_file = self.start_page  # Remember the starting page for filename
        consecutive_empty_batches = 0
        max_consecutive_empty_batches = 2  # Allow up to 2 consecutive empty batches before giving up
        total_pages_estimate = 999  # Will be updated after first batch
        concurrent_pages = 5  # Number of pages to scrape concurrently
        
        if self.start_page > 1:
            print(f"    🔄 Resuming from page {self.start_page}")
            print(f"    ⚠️ Note: Properties from pages 1-{self.start_page-1} are not included in this run")
        
        while True:
            # Check if interrupted
            if self.interrupted:
                print("    🛑 Scraping interrupted, stopping...")
                break
                
            # Calculate the range of pages to scrape concurrently
            pages_to_scrape = []
            for i in range(concurrent_pages):
                current_page = page + i
                
                # Stop if we've reached the max pages limit
                if self.max_pages and current_page > self.max_pages:
                    break
                
                # Stop if we've reached the estimated total pages
                if total_pages_estimate < 999 and current_page > total_pages_estimate:
                    break
                
                pages_to_scrape.append(current_page)
            
            if not pages_to_scrape:
                print(f"    🎯 No more pages to scrape")
                break
            
            print(f"    🚀 Scraping pages {pages_to_scrape[0]}-{pages_to_scrape[-1]} concurrently...")
            
            # Batch retry logic
            batch_retry_count = 0
            max_batch_retries = 2
            batch_successful = False
            
            while batch_retry_count <= max_batch_retries and not batch_successful:
                if batch_retry_count > 0:
                    print(f"    🔄 Retrying batch {batch_retry_count}/{max_batch_retries}...")
                
                # Use ThreadPoolExecutor to scrape pages concurrently
                batch_results = []
                with ThreadPoolExecutor(max_workers=concurrent_pages) as executor:
                    # Submit all page requests
                    future_to_page = {
                        executor.submit(self.fetch_single_page, city_id, property_type, page_num): page_num
                        for page_num in pages_to_scrape
                    }
                    
                    # Collect results as they complete
                    for future in as_completed(future_to_page):
                        page_num = future_to_page[future]
                        try:
                            result = future.result()
                            batch_results.append(result)
                        except Exception as exc:
                            print(f"    ❌ Page {page_num} generated an exception: {exc}")
                            batch_results.append((page_num, [], 1, 1))
                
                # Sort results by page number to maintain order
                batch_results.sort(key=lambda x: x[0])
                
                # Process results
                batch_properties = []
                empty_pages_in_batch = 0
                pages_with_properties = 0
                
                for page_num, properties, current_page, total_pages in batch_results:
                    print(f"    📄 Page {page_num}: ✅ {len(properties)} properties")
                    
                    if properties:
                        batch_properties.extend(properties)
                        pages_with_properties += 1
                        # Update total pages estimate from first successful page
                        if total_pages_estimate == 999 and total_pages < 999:
                            total_pages_estimate = total_pages
                            print(f"    🔢 Total pages estimate updated to: {total_pages}")
                    else:
                        empty_pages_in_batch += 1
                
                # Check if batch was successful (at least one page with properties or we're at high page numbers)
                if pages_with_properties > 0 or page > 100:  # Accept empty batches if we're far along
                    batch_successful = True
                    # Add batch properties to all properties
                    all_properties.extend(batch_properties)
                    # Update current properties and page for interrupt handling
                    self.current_properties = all_properties.copy()
                    self.current_page = page + concurrent_pages - 1
                else:
                    batch_retry_count += 1
                    if batch_retry_count <= max_batch_retries:
                        print(f"    ⚠️ Entire batch empty, retrying...")
                    else:
                        print(f"    ❌ Batch failed after {max_batch_retries} retries")
                        batch_successful = True  # Give up and continue
            
            # Check if entire batch was empty
            if empty_pages_in_batch == len(batch_results):
                consecutive_empty_batches += 1
                print(f"    ⚠️ Empty batch ({consecutive_empty_batches}/{max_consecutive_empty_batches})")
                
                if consecutive_empty_batches >= max_consecutive_empty_batches:
                    print(f"    🎯 {consecutive_empty_batches} consecutive empty batches, likely reached end")
                    break
            else:
                consecutive_empty_batches = 0  # Reset counter when we find properties
            
            # Check break conditions
            should_break = False
            
            # In test mode, only scrape first batch
            if self.test_mode:
                should_break = True
            # If max_pages specified, and we've processed all requested pages
            elif self.max_pages and page + concurrent_pages > self.max_pages:
                print(f"    🎯 Reached max pages limit ({self.max_pages})")
                should_break = True
            # If we have reliable pagination data and processed all pages
            elif total_pages_estimate < 999 and page + concurrent_pages > total_pages_estimate:
                print(f"    🎯 Completed all {total_pages_estimate} pages")
                should_break = True
            
            if should_break:
                break
            
            # Move to next batch
            page += concurrent_pages
            
            print(f"    📊 Batch completed. Total properties so far: {len(all_properties)}")
            
            # Save progress and display info every batch
            self.save_progress(city_id, city_name, property_type, page + concurrent_pages - 1, len(all_properties))
            
            # Show detailed progress every 5 batches
            batch_number = (page - self.start_page) // concurrent_pages
            if batch_number > 0 and batch_number % 5 == 0:
                self.display_progress_info(city_id, city_name, property_type, page + concurrent_pages - 1, len(all_properties))
        
        # Final save for this property type
        if all_properties:
            final_page = page + concurrent_pages - 1 if page > start_page_for_file else start_page_for_file
            self.save_intermediate_data(city_id, city_name, property_type, all_properties, 
                                      start_page_for_file, final_page)
            # Save final progress for this property type
            self.save_progress(city_id, city_name, property_type, final_page, len(all_properties))
            print(f"    📊 Final progress saved - Pages {start_page_for_file}-{final_page}, Total: {len(all_properties):,} properties")
        
        return all_properties
    
    def save_intermediate_data(self, city_id, city_name, property_type, properties, start_page=None, end_page=None):
        """Save intermediate data during scraping to prevent loss"""
        if not properties:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_city_name = "".join(c for c in city_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        
        # Include page range in filename if available
        if start_page and end_page:
            page_range = f"_pages{start_page}-{end_page}"
        elif start_page:
            page_range = f"_from_page{start_page}"
        else:
            page_range = ""
        
        filename = f"output/json_files/city_{city_id}_{safe_city_name}_type{property_type}{page_range}_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(properties, f, indent=2, ensure_ascii=False)
            print(f"    💾 Intermediate save: {filename} ({len(properties)} properties)")
        except Exception as e:
            print(f"    ❌ Failed to save intermediate data: {e}")
    
    def save_progress(self, city_id, city_name, property_type, current_page, total_properties):
        """Save current progress for easy resume"""
        progress_data = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'city_id': city_id,
            'city_name': city_name,
            'property_type': property_type,
            'property_type_name': self.property_types.get(property_type, 'Unknown'),
            'current_page': current_page,
            'total_properties_so_far': total_properties,
            'estimated_completion': f"Page {current_page}" if current_page else "Unknown"
        }
        
        try:
            with open('output/scraping_progress.json', 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"    ⚠️ Failed to save progress: {e}")
    
    def load_progress(self):
        """Load last saved progress"""
        try:
            with open('output/scraping_progress.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
        except Exception as e:
            print(f"⚠️ Failed to load progress: {e}")
            return None
    
    def display_progress_info(self, city_id, city_name, property_type, current_page, total_properties):
        """Display detailed progress information"""
        print(f"\n📊 CURRENT PROGRESS:")
        print(f"    🏙️ City: {city_name} (ID: {city_id})")
        print(f"    🏠 Property Type: {self.property_types.get(property_type, 'Unknown')}")
        print(f"    📄 Current Page: {current_page}")
        print(f"    📈 Properties Collected: {total_properties:,}")
        print(f"    ⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
        print(f"    🔄 To Resume Later: --start-page {current_page + 1}")
        print("-" * 50)
    
    def check_previous_progress(self):
        """Check and display previous progress if available"""
        progress = self.load_progress()
        if progress:
            print(f"\n📈 PREVIOUS SESSION FOUND:")
            print(f"    🏙️ Last City: {progress.get('city_name', 'Unknown')}")
            print(f"    🏠 Property Type: {progress.get('property_type_name', 'Unknown')}")
            print(f"    📄 Last Page: {progress.get('current_page', 'Unknown')}")
            print(f"    📈 Properties: {progress.get('total_properties_so_far', 0):,}")
            print(f"    ⏰ Last Run: {progress.get('timestamp', 'Unknown')}")
            print(f"    🔄 To Resume: python comprehensive_city_scraper.py --start-page {progress.get('current_page', 1) + 1}")
            if self.start_page == 1:
                print(f"    ⚠️ You're starting from page 1 (fresh start)")
            else:
                print(f"    ✅ Current start page: {self.start_page}")
            print("-" * 50)
    
    def scrape_city(self, city_id, city_name):
        """Scrape all property types for a city"""
        print(f"\n🏙️ {city_name} (ID: {city_id})")
        print("-" * 50)
        
        city_data = {}
        
        # Determine which property types to scrape
        property_types_to_scrape = self.specific_property_types if self.specific_property_types else self.property_types.keys()
        
        try:
            for property_type in property_types_to_scrape:
                if property_type in self.property_types:  # Ensure it's a valid property type
                    try:
                        properties = self.scrape_city_property_type(city_id, city_name, property_type)
                        
                        if properties:
                            city_data[property_type] = {
                                'property_type': self.property_types[property_type],
                                'city_name': city_name,
                                'city_id': city_id,
                                'properties': properties,
                                'count': len(properties)
                            }
                            
                            print(f"    📊 Total: {len(properties)} {self.property_types[property_type].lower()}s")
                        else:
                            print(f"    📊 Total: 0 {self.property_types[property_type].lower()}s")
                            
                    except KeyboardInterrupt:
                        print(f"    ⚠️ Property type {self.property_types[property_type]} interrupted")
                        # Don't break, let the outer handler deal with it
                        raise
                    except Exception as e:
                        print(f"    ❌ Error scraping property type {property_type}: {e}")
                        continue
                        
        except KeyboardInterrupt:
            print(f"    ⚠️ City {city_name} scraping interrupted")
            # Re-raise to be caught by outer handler
            raise
        
        return city_data
    
    def save_city_data(self, city_data, city_name, timestamp):
        """Save city data to JSON files by property type"""
        if not city_data:
            return
            
        for property_type, data in city_data.items():
            if data['properties']:
                # Create filename with page info if available
                safe_city_name = "".join(c for c in city_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                
                # Try to get page info from progress if available
                progress = self.load_progress()
                page_range = ""
                if progress and progress.get('property_type') == property_type:
                    start_page = self.start_page
                    end_page = progress.get('current_page', start_page)
                    if start_page and end_page and start_page != end_page:
                        page_range = f"_pages{start_page}-{end_page}"
                    elif start_page:
                        page_range = f"_from_page{start_page}"
                
                filename = f"output/json_files/city_{data['city_id']}_{safe_city_name}_type{property_type}{page_range}_{timestamp}.json"
                
                # Save properties in the format expected by the cleaner
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data['properties'], f, indent=2, ensure_ascii=False)
                
                print(f"    💾 Saved: {filename} ({len(data['properties'])} properties)")
    
    def create_summary_report(self, all_results, timestamp):
        """Create a summary report of all scraped data"""
        summary = {
            'scrape_info': {
                'timestamp': timestamp,
                'test_mode': self.test_mode,
                'max_cities': self.max_cities,
                'total_cities_processed': len(all_results)
            },
            'city_summary': {},
            'property_type_totals': {pt: 0 for pt in self.property_types.values()},
            'grand_total': 0
        }
        
        for city_id, city_data in all_results.items():
            city_name = city_data.get('city_name', 'Unknown')
            city_summary = {
                'city_name': city_name,
                'property_types': {}
            }
            
            city_total = 0
            for property_type, data in city_data.get('data', {}).items():
                count = data['count']
                property_name = data['property_type']
                
                city_summary['property_types'][property_name] = count
                summary['property_type_totals'][property_name] += count
                city_total += count
            
            city_summary['total'] = city_total
            summary['city_summary'][city_id] = city_summary
            summary['grand_total'] += city_total
        
        # Save summary
        summary_file = f"output/scraping_summary_{timestamp}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        return summary, summary_file
    
    def run(self):
        """Run the comprehensive scraper"""
        start_time = time.time()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"🚀 STARTING COMPREHENSIVE SCRAPE")
        print(f"📅 Timestamp: {timestamp}")
        if self.start_page > 1:
            print(f"🔄 RESUMING from page {self.start_page}")
        print("=" * 70)
        
        all_results = {}
        
        # Determine which cities to process
        if self.specific_cities:
            # Filter cities based on specific city IDs
            cities_to_process = [(cid, cname) for cid, cname in self.cities.items() if int(cid) in self.specific_cities]
        else:
            cities_to_process = list(self.cities.items())
        
        # Limit cities if max_cities specified (applies after specific cities filter)
        if self.max_cities:
            cities_to_process = cities_to_process[:self.max_cities]
        
        print(f"🎯 Cities to process: {len(cities_to_process)}")
        if len(cities_to_process) <= 10:  # Show city names if not too many
            city_names = [name for _, name in cities_to_process]
            print(f"📍 Cities: {', '.join(city_names)}")
        print("=" * 70)
        
        processed_cities = 0
        
        try:
            for city_id, city_name in cities_to_process:
                try:
                    processed_cities += 1
                    city_data = self.scrape_city(city_id, city_name)
                    
                    if city_data:
                        all_results[city_id] = {
                            'city_name': city_name,
                            'data': city_data
                        }
                        
                        # Save individual city data
                        self.save_city_data(city_data, city_name, timestamp)
                    
                    print(f"✅ Completed {processed_cities}/{len(cities_to_process)} cities")
                    
                    # No delays - removed for speed
                    
                except Exception as e:
                    print(f"❌ Error processing {city_name}: {e}")
                    continue
                    
        except KeyboardInterrupt:
            print(f"\n⚠️ Interrupted by user. Processed {processed_cities} cities.")
            print(f"💾 Saving collected data before exit...")
            
            # Count properties from intermediate files if no complete city data
            if not all_results:
                print("⚠️ No complete city data to save, but checking intermediate files...")
                intermediate_count = self.count_intermediate_files(timestamp)
                if intermediate_count > 0:
                    print(f"✅ Found {intermediate_count} properties in intermediate files")
                    # Create a dummy summary to show the actual data count
                    all_results['partial'] = {
                        'city_name': 'Partial Data (Interrupted)',
                        'data': {
                            1: {
                                'property_type': 'Residential Apartment',
                                'city_name': 'Various',
                                'city_id': 'partial',
                                'properties': [],
                                'count': intermediate_count
                            }
                        }
                    }
                else:
                    print("⚠️ No intermediate files found either")
            
            # Save whatever data was collected before interruption
            if all_results:
                summary, summary_file = self.create_summary_report(all_results, timestamp)
                print(f"💾 Saved partial results: {summary['grand_total']} properties")
            else:
                print("⚠️ No data found to report")
        
        # Create summary report - check for intermediate files if no main results
        if not all_results:
            print("⚠️ No complete results found, checking for intermediate files...")
            intermediate_count = self.count_intermediate_files(timestamp)
            if intermediate_count > 0:
                print(f"✅ Found {intermediate_count} properties in intermediate files")
                # Create a summary entry for the found data
                all_results['intermediate'] = {
                    'city_name': 'Intermediate Data Found',
                    'data': {
                        1: {
                            'property_type': 'Residential Apartment',
                            'city_name': 'Various',
                            'city_id': 'intermediate',
                            'properties': [],
                            'count': intermediate_count
                        }
                    }
                }
        
        summary, summary_file = self.create_summary_report(all_results, timestamp)
        
        # Print final summary
        elapsed_time = time.time() - start_time
        print("\n" + "=" * 70)
        print("🎉 SCRAPING COMPLETED!")
        print("=" * 70)
        print(f"⏱️ Total Time: {elapsed_time:.1f} seconds")
        print(f"🏙️ Cities Processed: {processed_cities}")
        print(f"📊 Total Properties: {summary['grand_total']}")
        
        # More informative breakdown
        print("\n📋 PROPERTY TYPE BREAKDOWN:")
        for prop_type, count in summary['property_type_totals'].items():
            if count > 0:
                print(f"  {prop_type}: {count} ✅")
            else:
                print(f"  {prop_type}: {count}")
        
        print(f"\n📁 Files saved in: output/")
        print(f"📄 Summary report: {summary_file}")
        
        # Show additional info if intermediate files exist
        if summary['grand_total'] > 0:
            print(f"\n💡 Data successfully collected and saved!")
            print(f"🔧 You can now run: python optimized_multi_type_cleaner.py")
            print(f"   to process the JSON files into clean CSV format!")
        
        return all_results, summary


def main():
    parser = argparse.ArgumentParser(description='Comprehensive 99acres City Scraper')
    parser.add_argument('--test', action='store_true', 
                       help='Test mode: scrape only first page of each property type')
    parser.add_argument('--max-cities', type=int, 
                       help='Maximum number of cities to process (for testing)')
    parser.add_argument('--cities', type=str, 
                       help='Specific city IDs to scrape (comma-separated, e.g., "1,12,20")')
    parser.add_argument('--property-types', type=str, 
                       help='Specific property types to scrape (comma-separated, e.g., "1,2,4")')
    parser.add_argument('--max-pages', type=int, 
                       help='Maximum pages per property type (default: all pages)')
    parser.add_argument('--start-page', type=int, default=1,
                       help='Page number to start from (for resuming scrapes, default: 1)')
    parser.add_argument('--proxies', type=str, 
                       help='Proxy list file (one proxy per line) or comma-separated proxy list')
    parser.add_argument('--scraperapi', action='store_true',
                       help='Use ScraperAPI service for requests')
    
    args = parser.parse_args()
    
    # Parse specific cities
    specific_cities = None
    if args.cities:
        try:
            specific_cities = [int(x.strip()) for x in args.cities.split(',')]
        except ValueError:
            print("❌ Error: Invalid city IDs format. Use comma-separated numbers (e.g., '1,12,20')")
            return
    
    # Parse specific property types
    specific_property_types = None
    if args.property_types:
        try:
            specific_property_types = [int(x.strip()) for x in args.property_types.split(',')]
            # Validate property types
            valid_types = [1, 2, 3, 4, 5]
            invalid_types = [pt for pt in specific_property_types if pt not in valid_types]
            if invalid_types:
                print(f"❌ Error: Invalid property types: {invalid_types}. Valid types are: {valid_types}")
                return
        except ValueError:
            print("❌ Error: Invalid property types format. Use comma-separated numbers (e.g., '1,2,4')")
            return
    
    # Parse proxy list
    proxy_list = None
    if args.proxies:
        try:
            # Check if it's a file or comma-separated list
            if ',' in args.proxies and not os.path.exists(args.proxies):
                # Comma-separated list
                proxy_list = [proxy.strip() for proxy in args.proxies.split(',')]
            elif os.path.exists(args.proxies):
                # File containing proxy list
                with open(args.proxies, 'r') as f:
                    proxy_list = [line.strip() for line in f if line.strip()]
            else:
                print(f"❌ Error: Proxy file '{args.proxies}' not found")
                return
        except Exception as e:
            print(f"❌ Error loading proxies: {e}")
            return
    
    scraper = ComprehensiveCityScraper(
        test_mode=args.test,
        max_cities=args.max_cities,
        specific_cities=specific_cities,
        specific_property_types=specific_property_types,
        max_pages=args.max_pages,
        proxy_list=proxy_list,
        start_page=args.start_page,
        use_scraperapi=args.scraperapi
    )
    
    try:
        results, summary = scraper.run()
        
        if results and summary['grand_total'] > 0:
            print(f"\n✅ Successfully scraped data from {len(results)} cities")
        elif summary['grand_total'] > 0:
            print(f"\n✅ Data was scraped and saved (interrupted session)")
            print(f"📊 Total properties saved: {summary['grand_total']}")
        else:
            print("\n❌ No data was scraped")
            
    except KeyboardInterrupt:
        print("\n⚠️ Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")


if __name__ == "__main__":
    main() 