#!/usr/bin/env python3
"""
📊 PROGRESS CHECKER
Quick tool to check last scraping progress and get resume command
"""

import json
import os
from datetime import datetime

def check_progress():
    """Check and display current scraping progress"""
    progress_file = 'output/scraping_progress.json'
    
    if not os.path.exists(progress_file):
        print("❌ No progress file found. Start scraping first!")
        return
    
    try:
        with open(progress_file, 'r', encoding='utf-8') as f:
            progress = json.load(f)
        
        print("📊 LAST SCRAPING PROGRESS")
        print("=" * 50)
        print(f"🏙️ City: {progress.get('city_name', 'Unknown')} (ID: {progress.get('city_id', 'N/A')})")
        print(f"🏠 Property Type: {progress.get('property_type_name', 'Unknown')}")
        print(f"📄 Last Completed Page: {progress.get('current_page', 'Unknown')}")
        print(f"📈 Properties Collected: {progress.get('total_properties_so_far', 0):,}")
        print(f"⏰ Last Updated: {progress.get('timestamp', 'Unknown')}")
        print("=" * 50)
        
        next_page = progress.get('current_page', 1) + 1
        print(f"🔄 TO RESUME SCRAPING:")
        print(f"   python comprehensive_city_scraper.py --start-page {next_page}")
        print(f"   OR")
        print(f"   python run_scraper.py (then choose custom scrape)")
        print("=" * 50)
        
        # Check for recent JSON files
        json_dir = 'output/json_files'
        if os.path.exists(json_dir):
            json_files = [f for f in os.listdir(json_dir) if f.endswith('.json') and 'type1' in f]
            if json_files:
                # Get the most recent file
                latest_file = max(json_files, key=lambda x: os.path.getctime(os.path.join(json_dir, x)))
                file_time = datetime.fromtimestamp(os.path.getctime(os.path.join(json_dir, latest_file)))
                
                # Extract page info from filename
                page_info = "No page info"
                if "_pages" in latest_file:
                    page_part = latest_file.split("_pages")[1].split("_")[0]
                    page_info = f"Pages {page_part}"
                elif "_from_page" in latest_file:
                    page_part = latest_file.split("_from_page")[1].split("_")[0]
                    page_info = f"From page {page_part}"
                
                print(f"📁 Latest JSON file: {latest_file}")
                print(f"📄 Page Range: {page_info}")
                print(f"📅 File created: {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print("=" * 50)
                
                # Show last few files with page ranges
                recent_files = sorted(json_files, 
                                    key=lambda x: os.path.getctime(os.path.join(json_dir, x)), 
                                    reverse=True)[:3]
                if len(recent_files) > 1:
                    print("📂 Recent Files:")
                    for i, file in enumerate(recent_files, 1):
                        file_time = datetime.fromtimestamp(os.path.getctime(os.path.join(json_dir, file)))
                        page_info = "No page info"
                        if "_pages" in file:
                            page_part = file.split("_pages")[1].split("_")[0]
                            page_info = f"Pages {page_part}"
                        elif "_from_page" in file:
                            page_part = file.split("_from_page")[1].split("_")[0]
                            page_info = f"From page {page_part}"
                        print(f"  {i}. {page_info} - {file_time.strftime('%H:%M:%S')}")
                    print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error reading progress file: {e}")

if __name__ == "__main__":
    check_progress() 