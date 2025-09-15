# 🏘️ 99acres Ultimate Property Scraper

A comprehensive, interactive property scraper for 99acres.com with granular control over cities, property types, and scraping depth.

## 🚀 Quick Start

1. **Launch Interactive Menu:**
   ```bash
   python run_scraper.py
   ```

2. **Process Results:**
   ```bash
   python optimized_multi_type_cleaner.py
   ```

## 🎯 Features

### **Interactive Launcher (`run_scraper.py`)**
- **🧪 Quick Test:** First page, 5 cities, all types
- **🏙️ Medium Test:** All pages, 10 cities, all types  
- **🌟 Full Scrape:** All cities, all pages, all types
- **🎯 Custom Scrape:** Choose everything yourself

### **Granular Control**
- **🏙️ City Selection:** Choose specific cities or regions (Delhi NCR, Mumbai, Bangalore, etc.)
- **🏠 Property Types:** Select from 5 types (Apartments, Houses, Land, Builder Floors, Farm Houses)
- **📄 Pages Control:** First page only, specific number (1-20), or all pages

### **Organized Output Structure**
```
output/
├── json_files/     # Raw scraped JSON data
├── csv_files/      # Clean optimized CSV files
└── excel_files/    # Excel files for analysis
```

## 🛠️ Advanced Usage

### **Command Line Options**
```bash
# Basic usage
python comprehensive_city_scraper.py --test --max-cities 5

# Specific cities (Delhi NCR, Mumbai, Bangalore)  
python comprehensive_city_scraper.py --cities "1,12,20"

# Specific property types (Apartments and Houses only)
python comprehensive_city_scraper.py --property-types "1,2"

# Limit pages per property type
python comprehensive_city_scraper.py --max-pages 3

# Combined example
python comprehensive_city_scraper.py --cities "1,12" --property-types "1,2,4" --max-pages 5
```

### **Property Types Reference**
1. **Residential Apartments** - Flats/Apartments (excludes projects)
2. **Independent Houses/Villas** - Standalone houses
3. **Residential Land/Plots** - Land for construction
4. **Independent/Builder Floors** - Floor-wise properties
5. **Farm Houses** - Agricultural/recreational properties

## 📊 Output Files

### **CSV Files (output/csv_files/)**
- `city_name_apartments_pages.csv`
- `city_name_houses_villas_pages.csv`
- `city_name_land_plots_pages.csv`
- `city_name_builder_floors_pages.csv`
- `city_name_farm_houses_pages.csv`

### **Excel Files (output/excel_files/)**
- Individual Excel files for each property type
- `city_name_all_types_pages.xlsx` with summary sheet

## 🔧 System Requirements

- **Python 3.7+**
- **Required packages:** `requests`, `pandas`, `openpyxl`
- **Input file:** `city_w_id.json` (city mapping)

## 💡 Tips

- **Start small:** Use Quick Test to verify everything works
- **Regional focus:** Use city selection to focus on specific regions
- **Property-specific:** Select only the property types you need
- **Respectful scraping:** Built-in delays prevent overwhelming the server

## 📁 Project Structure

```
📁 99acres ultimate scraper/
├── 📄 city_w_id.json                    # City mapping data
├── 📄 comprehensive_city_scraper.py     # Main scraper engine
├── 📄 optimized_multi_type_cleaner.py   # Data processor  
├── 📄 run_scraper.py                    # Interactive launcher
├── 📄 check_progress.py                 # Progress checker
├── 📄 test_proxies.py                   # Proxy tester (optional)
├── 📄 get_premium_proxies.py            # Premium proxy fetcher (optional)
├── 📄 README.md                         # This file
├── 📁 facets/                           # Reference data mappings
│   ├── 📄 AMENITIES.csv                 # Amenity ID mappings
│   ├── 📄 FEATURES.csv                  # Feature ID mappings
│   └── 📄 *.csv                         # Other reference mappings
└── 📁 output/                           # All results here
    ├── 📁 json_files/                   # Raw scraped data
    ├── 📁 csv_files/                    # Processed CSV files
    └── 📁 excel_files/                  # Excel reports
```

## 🎯 Workflow

1. **🚀 Scrape:** `python run_scraper.py` → Select options → Scrape data
2. **🔧 Process:** `python optimized_multi_type_cleaner.py` → Convert to CSV/Excel
3. **📊 Analyze:** Open Excel files or use CSV files for analysis

## 🔄 Proxy Support

The scraper supports multiple proxy options:
- **ScraperAPI** (Recommended) - Premium API service
- **Custom proxy files** - Load from text files
- **No proxies** - Direct connection

## 📈 Progress Tracking

- **Auto-save:** Data saved during scraping to prevent loss
- **Resume capability:** Continue from where you left off
- **Progress monitoring:** Check status with `python check_progress.py`

## 🛡️ Features

- **Concurrent scraping:** 5 pages at once for speed
- **Retry logic:** Handles failures gracefully
- **Interrupt handling:** Safe data saving on Ctrl+C
- **Comprehensive data:** 37,000+ properties per major city
- **Clean output:** Optimized fields for each property type

---

**Happy Scraping!** 🏠✨