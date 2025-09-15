#!/usr/bin/env python3
"""
🔍 PROXY TESTER
Tests proxies from proxies.txt to see which ones are working
"""

import requests
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

def test_proxy(proxy, timeout=10):
    """Test a single proxy"""
    try:
        # Test URL - simple and fast
        test_url = "http://httpbin.org/ip"
        
        proxies = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
        
        # Make request through proxy
        response = requests.get(test_url, proxies=proxies, timeout=timeout)
        
        if response.status_code == 200:
            data = response.json()
            return proxy, True, data.get('origin', 'Unknown IP')
        else:
            return proxy, False, f"Status: {response.status_code}"
            
    except Exception as e:
        return proxy, False, str(e)[:50]

def load_proxies(filename='proxies.txt'):
    """Load proxies from file"""
    try:
        with open(filename, 'r') as f:
            proxies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        return proxies
    except FileNotFoundError:
        print(f"❌ {filename} not found!")
        return []

def test_all_proxies(proxies, max_workers=20):
    """Test all proxies concurrently"""
    print(f"🔍 Testing {len(proxies)} proxies...")
    print("🕐 This may take a few minutes...")
    print("-" * 50)
    
    working_proxies = []
    failed_proxies = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all proxy tests
        future_to_proxy = {executor.submit(test_proxy, proxy): proxy for proxy in proxies}
        
        # Collect results as they complete
        for i, future in enumerate(as_completed(future_to_proxy), 1):
            proxy, is_working, result = future.result()
            
            if is_working:
                working_proxies.append(proxy)
                print(f"✅ {proxy} - IP: {result}")
            else:
                failed_proxies.append((proxy, result))
                print(f"❌ {proxy} - {result}")
            
            # Progress indicator
            if i % 10 == 0:
                print(f"📊 Progress: {i}/{len(proxies)} tested...")
    
    return working_proxies, failed_proxies

def save_working_proxies(working_proxies, filename='working_proxies.txt'):
    """Save working proxies to a new file"""
    if working_proxies:
        with open(filename, 'w') as f:
            for proxy in working_proxies:
                f.write(f"{proxy}\n")
        print(f"💾 Saved {len(working_proxies)} working proxies to {filename}")

def main():
    print("🔍 PROXY TESTER")
    print("=" * 30)
    
    # Load proxies
    proxies = load_proxies('proxies.txt')
    if not proxies:
        return
    
    print(f"📋 Loaded {len(proxies)} proxies from proxies.txt")
    
    # Test proxies
    start_time = time.time()
    working_proxies, failed_proxies = test_all_proxies(proxies)
    end_time = time.time()
    
    # Results summary
    print("\n" + "=" * 50)
    print("🎉 TESTING COMPLETE!")
    print("=" * 50)
    print(f"⏱️ Test Time: {end_time - start_time:.1f} seconds")
    print(f"✅ Working: {len(working_proxies)}")
    print(f"❌ Failed: {len(failed_proxies)}")
    print(f"📊 Success Rate: {len(working_proxies)/len(proxies)*100:.1f}%")
    
    if working_proxies:
        save_working_proxies(working_proxies)
        print(f"\n🚀 You can now use: python comprehensive_city_scraper.py --proxies working_proxies.txt")
    else:
        print("\n❌ No working proxies found. Try getting proxies from a different source.")
        
    # Show some failed examples
    if failed_proxies:
        print(f"\n❌ First 5 failed proxies:")
        for proxy, error in failed_proxies[:5]:
            print(f"   {proxy}: {error}")

if __name__ == "__main__":
    main() 