#!/usr/bin/env python3
"""
Fetch premium proxies from ProxyScrape using authenticated API
"""
import requests
import time

def get_authenticated_ips():
    """Check which IPs are authenticated"""
    print("🔍 Checking authenticated IPs...")
    
    url = "https://api.proxyscrape.com/v2/account/datacenter_shared/whitelist?auth=nhuyjukilompnbvfrtyuui&type=get"
    
    try:
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            print("✅ Authenticated IPs:")
            print(response.text)
            return True
        else:
            print(f"❌ API Error: Status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking IPs: {e}")
        return False

def get_premium_proxies():
    """Get premium datacenter proxy list"""
    print("🔄 Fetching premium proxies from ProxyScrape...")
    
    url = "https://api.proxyscrape.com/v2/account/datacenter_shared/proxy-list?auth=nhuyjukilompnbvfrtyuui&type=getproxies&country[]=all&protocol=http&format=normal&status=all"
    
    try:
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            proxy_text = response.text.strip()
            
            if not proxy_text or proxy_text.startswith('Error'):
                print(f"❌ API returned error: {proxy_text}")
                return []
            
            proxies = [line.strip() for line in proxy_text.split('\n') if line.strip()]
            
            print(f"✅ Retrieved {len(proxies)} premium proxies")
            
            # Save to file
            with open('premium_proxies.txt', 'w') as f:
                for proxy in proxies:
                    f.write(f"{proxy}\n")
            
            print(f"💾 Saved {len(proxies)} proxies to premium_proxies.txt")
            
            # Show first few proxies
            print(f"\n📋 First 5 premium proxies:")
            for i, proxy in enumerate(proxies[:5], 1):
                print(f"  {i}. {proxy}")
            
            return proxies
            
        else:
            print(f"❌ API Error: Status {response.status_code}")
            print(f"Response: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Error fetching proxies: {e}")
        return []

def test_premium_proxies(proxies, sample_size=3):
    """Test a few premium proxies"""
    print(f"\n🧪 Testing {sample_size} premium proxies...")
    
    working_count = 0
    for i, proxy in enumerate(proxies[:sample_size], 1):
        try:
            print(f"Testing {i}/{sample_size}: {proxy}")
            
            proxies_dict = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            
            # Test with httpbin first
            response = requests.get(
                'http://httpbin.org/ip', 
                proxies=proxies_dict, 
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {proxy} - WORKING! IP: {data.get('origin', 'Unknown')}")
                working_count += 1
                
                # Test with 99acres to be sure
                print(f"   Testing 99acres...")
                test_response = requests.get(
                    'https://www.99acres.com', 
                    proxies=proxies_dict, 
                    timeout=15,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                )
                
                if test_response.status_code == 200:
                    print(f"   ✅ 99acres also works!")
                else:
                    print(f"   ⚠️ 99acres status: {test_response.status_code}")
                    
            else:
                print(f"❌ {proxy} - Status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {proxy} - Error: {str(e)[:50]}")
        
        time.sleep(2)  # Small delay between tests
    
    print(f"\n📊 Test Results: {working_count}/{sample_size} premium proxies working")
    return working_count > 0

if __name__ == "__main__":
    print("🔑 ProxyScrape Premium Proxy Setup")
    print("=" * 50)
    
    # Check authenticated IPs first
    if get_authenticated_ips():
        print("\n" + "=" * 50)
        
        # Get premium proxies
        proxies = get_premium_proxies()
        
        if proxies:
            # Test a few
            if test_premium_proxies(proxies):
                print(f"\n🎉 SUCCESS! Your premium proxies are working!")
                print(f"💡 Run your scraper with:")
                print(f"   python comprehensive_city_scraper.py --proxies premium_proxies.txt --test --cities 1")
                print(f"   python run_scraper.py  # (will auto-detect premium_proxies.txt)")
            else:
                print(f"\n⚠️ Proxies retrieved but having connection issues")
                print(f"💡 Try running anyway - they might work better with 99acres:")
                print(f"   python comprehensive_city_scraper.py --proxies premium_proxies.txt --test --cities 1")
        else:
            print("❌ No premium proxies retrieved. Check your auth token or account status.")
    else:
        print("❌ Authentication failed. Check your auth token.") 