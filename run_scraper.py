#!/usr/bin/env python3
"""
🚀 ENHANCED SCRAPER LAUNCHER
Interactive launcher for comprehensive city scraper with granular control
"""

import subprocess
import sys
import json

def load_cities():
    """Load city mapping from JSON file"""
    try:
        with open('city_w_id.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ city_w_id.json not found!")
        return {}

def print_main_menu():
    print("\n🌍 COMPREHENSIVE CITY SCRAPER")
    print("=" * 50)
    print("1. 🧪 QUICK TEST - First page, 5 cities, all types")
    print("2. 🏙️ MEDIUM TEST - All pages, 10 cities, all types") 
    print("3. 🌟 FULL SCRAPE - All cities, all pages, all types")
    print("4. 🎯 CUSTOM SCRAPE - Choose everything")
    print("5. 📊 CHECK PROGRESS - See last scraping progress")
    print("6. 🔍 TEST PROXIES - Check which proxies work")
    print("7. ❌ Exit")
    print("=" * 50)

def print_cities_menu(cities, selected_cities=None):
    """Print cities selection menu"""
    print("\n🏙️ CITY SELECTION")
    print("=" * 40)
    print("0. ✅ ALL CITIES (Default)")
    
    # Group cities by major regions
    major_cities = {
        "Delhi NCR": [(cid, name) for cid, name in cities.items() if any(x in name.lower() for x in ['delhi', 'ncr', 'noida', 'gurgaon', 'ghaziabad', 'faridabad'])],
        "Mumbai Region": [(cid, name) for cid, name in cities.items() if 'mumbai' in name.lower()],
        "Bangalore": [(cid, name) for cid, name in cities.items() if 'bangalore' in name.lower()],
        "Chennai": [(cid, name) for cid, name in cities.items() if 'chennai' in name.lower()],
        "Kolkata": [(cid, name) for cid, name in cities.items() if 'kolkata' in name.lower()],
        "Hyderabad": [(cid, name) for cid, name in cities.items() if 'hyderabad' in name.lower()],
        "Pune": [(cid, name) for cid, name in cities.items() if 'pune' in name.lower()],
        "Ahmedabad": [(cid, name) for cid, name in cities.items() if 'ahmedabad' in name.lower()]
    }
    
    option = 1
    city_options = {}
    
    for region, region_cities in major_cities.items():
        if region_cities:
            print(f"\n📍 {region}:")
            for cid, name in region_cities[:5]:  # Show first 5 cities per region
                status = "✅" if selected_cities and int(cid) in selected_cities else "  "
                print(f"{status}{option:2d}. {name} (ID: {cid})")
                city_options[option] = int(cid)
                option += 1
    
    print(f"\n💡 Enter numbers separated by commas (e.g., 1,5,8)")
    print(f"💡 Or enter 0 for ALL cities")
    print(f"💡 Total cities available: {len(cities)}")
    
    return city_options

def print_property_types_menu(selected_types=None):
    """Print property types selection menu"""
    print("\n🏠 PROPERTY TYPE SELECTION")
    print("=" * 40)
    print("0. ✅ ALL TYPES (Default)")
    
    property_types = {
        1: "Residential Apartments",
        2: "Independent Houses/Villas", 
        3: "Residential Land/Plots",
        4: "Independent/Builder Floors",
        5: "Farm Houses"
    }
    
    for pt_id, pt_name in property_types.items():
        status = "✅" if selected_types and pt_id in selected_types else "  "
        print(f"{status}{pt_id}. {pt_name}")
    
    print(f"\n💡 Enter numbers separated by commas (e.g., 1,2,4)")
    print(f"💡 Or enter 0 for ALL types")
    
    return property_types

def get_cities_selection(cities):
    """Get city selection from user"""
    while True:
        city_options = print_cities_menu(cities)
        
        try:
            choice = input("\nEnter city selection: ").strip()
            
            if choice == "0" or choice == "":
                return None  # All cities
            
            selected_numbers = [int(x.strip()) for x in choice.split(',')]
            selected_cities = []
            
            for num in selected_numbers:
                if num in city_options:
                    selected_cities.append(city_options[num])
                else:
                    print(f"❌ Invalid option: {num}")
                    raise ValueError()
            
            if selected_cities:
                # Show confirmation
                city_names = [cities[str(cid)] for cid in selected_cities if str(cid) in cities]
                print(f"\n✅ Selected cities: {', '.join(city_names)}")
                return selected_cities
            
        except ValueError:
            print("❌ Invalid input. Please try again.")

def get_property_types_selection():
    """Get property types selection from user"""
    while True:
        property_types = print_property_types_menu()
        
        try:
            choice = input("\nEnter property type selection: ").strip()
            
            if choice == "0" or choice == "":
                return None  # All types
            
            selected_types = [int(x.strip()) for x in choice.split(',')]
            
            # Validate types
            valid_types = list(property_types.keys())
            invalid_types = [pt for pt in selected_types if pt not in valid_types]
            
            if invalid_types:
                print(f"❌ Invalid property types: {invalid_types}")
                continue
            
            if selected_types:
                # Show confirmation
                type_names = [property_types[pt] for pt in selected_types]
                print(f"\n✅ Selected types: {', '.join(type_names)}")
                return selected_types
            
        except ValueError:
            print("❌ Invalid input. Please try again.")

def get_pages_selection():
    """Get pages per property type selection"""
    print("\n📄 PAGES PER PROPERTY TYPE")
    print("=" * 40)
    print("1. 📄 FIRST PAGE ONLY (Test mode)")
    print("2. 📄 SPECIFIC NUMBER (1-20 pages)")
    print("3. 📄 ALL PAGES (Complete scrape)")
    print("4. 📄 RESUME FROM PAGE (Start from specific page)")
    
    while True:
        try:
            choice = input("\nEnter pages option (1-4): ").strip()
            
            if choice == "1":
                return {"mode": "test"}
            elif choice == "2":
                pages = int(input("Enter number of pages (1-20): ").strip())
                if 1 <= pages <= 20:
                    return {"mode": "max_pages", "value": pages}
                else:
                    print("❌ Please enter a number between 1 and 20")
            elif choice == "3":
                return {"mode": "all"}  # All pages
            elif choice == "4":
                start_page = int(input("Enter starting page number (e.g., 59): ").strip())
                if start_page > 0:
                    return {"mode": "resume", "start_page": start_page}
                else:
                    print("❌ Please enter a valid page number (> 0)")
            else:
                print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")
                
        except ValueError:
            print("❌ Invalid input. Please enter a number.")

def run_command(cmd):
    """Run a command and show output"""
    print(f"\n🚀 Running: {' '.join(cmd)}")
    print("-" * 70)
    
    try:
        subprocess.run(cmd, check=True)
        print("\n✅ Command completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Command failed with exit code {e.returncode}")
    except KeyboardInterrupt:
        print("\n⚠️ Command interrupted by user")

def check_proxy_file():
    """Check if proxy file exists and ask user if they want to use it"""
    import os
    
    proxy_files = ['working_proxies.txt', 'proxies.txt']
    available_files = [f for f in proxy_files if os.path.exists(f)]
    
    print(f"\n🔄 PROXY OPTIONS")
    print("=" * 40)
    
    option_num = 1
    proxy_options = {}
    
    # Add ScraperAPI option
    print(f"{option_num}. 🌐 Use ScraperAPI (Recommended)")
    proxy_options[option_num] = "scraperapi"
    option_num += 1
    
    # Add available proxy files
    for file in available_files:
        try:
            with open(file, 'r') as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            print(f"{option_num}. {file} ({len(lines)} proxies)")
            proxy_options[option_num] = file
            option_num += 1
        except:
            print(f"{option_num}. {file} (error reading file)")
            proxy_options[option_num] = file
            option_num += 1
    
    print(f"{option_num}. Don't use proxies")
    proxy_options[option_num] = None
    
    while True:
        try:
            choice = input(f"\nSelect proxy option (1-{option_num}): ").strip()
            choice_num = int(choice)
            
            if choice_num in proxy_options:
                selected_option = proxy_options[choice_num]
                if selected_option == "scraperapi":
                    print("✅ Will use ScraperAPI service")
                    return "scraperapi"
                elif selected_option is None:
                    print("✅ Will run without proxies")
                    return None
                else:
                    print(f"✅ Will use proxies from: {selected_option}")
                    return selected_option
            else:
                print(f"❌ Invalid choice. Please select 1-{option_num}.")
                
        except ValueError:
            print("❌ Invalid input. Please enter a number.")

def main():
    # Load cities data
    cities = load_cities()
    if not cities:
        print("❌ Cannot load cities data. Exiting.")
        return
    
    while True:
        print_main_menu()
        
        try:
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == "1":
                # Quick test
                proxy_file = check_proxy_file()
                cmd = [sys.executable, "comprehensive_city_scraper.py", "--test", "--max-cities", "5"]
                if proxy_file == "scraperapi":
                    cmd.extend(["--scraperapi"])
                elif proxy_file:
                    cmd.extend(["--proxies", proxy_file])
                run_command(cmd)
                
            elif choice == "2":
                # Medium test
                proxy_file = check_proxy_file()
                cmd = [sys.executable, "comprehensive_city_scraper.py", "--max-cities", "10"]
                if proxy_file == "scraperapi":
                    cmd.extend(["--scraperapi"])
                elif proxy_file:
                    cmd.extend(["--proxies", proxy_file])
                run_command(cmd)
                
            elif choice == "3":
                # Full scrape
                print("⚠️ WARNING: This will scrape ALL cities and may take several hours!")
                confirm = input("Are you sure? (yes/no): ").strip().lower()
                if confirm in ['yes', 'y']:
                    proxy_file = check_proxy_file()
                    cmd = [sys.executable, "comprehensive_city_scraper.py"]
                    if proxy_file == "scraperapi":
                        cmd.extend(["--scraperapi"])
                    elif proxy_file:
                        cmd.extend(["--proxies", proxy_file])
                    run_command(cmd)
                else:
                    print("❌ Cancelled")
                    
            elif choice == "4":
                # Custom scrape
                print("\n🎯 CUSTOM SCRAPE CONFIGURATION")
                print("=" * 50)
                
                # Get city selection
                selected_cities = get_cities_selection(cities)
                
                # Get property types selection
                selected_property_types = get_property_types_selection()
                
                # Get pages selection
                pages_choice = get_pages_selection()
                
                # Get proxy selection
                proxy_file = check_proxy_file()
                
                # Build command
                cmd = [sys.executable, "comprehensive_city_scraper.py"]
                
                if selected_cities:
                    cities_str = ','.join(map(str, selected_cities))
                    cmd.extend(["--cities", cities_str])
                
                if selected_property_types:
                    types_str = ','.join(map(str, selected_property_types))
                    cmd.extend(["--property-types", types_str])
                
                # Handle pages configuration
                if pages_choice["mode"] == "test":
                    cmd.append("--test")
                elif pages_choice["mode"] == "max_pages":
                    cmd.extend(["--max-pages", str(pages_choice["value"])])
                elif pages_choice["mode"] == "resume":
                    cmd.extend(["--start-page", str(pages_choice["start_page"])])
                
                if proxy_file == "scraperapi":
                    cmd.extend(["--scraperapi"])
                elif proxy_file:
                    cmd.extend(["--proxies", proxy_file])
                
                # Show final configuration
                print("\n🔧 FINAL CONFIGURATION:")
                print("=" * 30)
                print(f"Cities: {'All' if not selected_cities else f'{len(selected_cities)} selected'}")
                print(f"Property Types: {'All' if not selected_property_types else f'{len(selected_property_types)} selected'}")
                if pages_choice["mode"] == "test":
                    print(f"Pages: First page only")
                elif pages_choice["mode"] == "max_pages":
                    print(f"Pages: Max {pages_choice['value']} per type")
                elif pages_choice["mode"] == "resume":
                    print(f"Pages: Resume from page {pages_choice['start_page']}")
                else:
                    print(f"Pages: All pages")
                if proxy_file == "scraperapi":
                    print("Proxies: Yes (ScraperAPI)")
                elif proxy_file:
                    print(f"Proxies: Yes ({proxy_file})")
                else:
                    print("Proxies: No")
                
                confirm = input("\n🚀 Start scraping with this configuration? (y/n): ").strip().lower()
                if confirm in ['y', 'yes']:
                    run_command(cmd)
                else:
                    print("❌ Cancelled")
                    
            elif choice == "5":
                # Check progress
                print("\n📊 CHECKING LAST PROGRESS")
                print("=" * 50)
                cmd = [sys.executable, "check_progress.py"]
                run_command(cmd)
                
            elif choice == "6":
                # Test proxies
                print("\n🔍 TESTING PROXIES")
                print("=" * 50)
                print("This will test all proxies in proxies.txt to see which ones work.")
                confirm = input("Are you sure you want to test proxies? (yes/no): ").strip().lower()
                if confirm in ['yes', 'y']:
                    cmd = [sys.executable, "test_proxies.py"]
                    run_command(cmd)
                else:
                    print("❌ Cancelled")
                    
            elif choice == "7":
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please select 1-7.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        
        input("\nPress Enter to continue...")
        print("\n" * 2)

if __name__ == "__main__":
    main() 