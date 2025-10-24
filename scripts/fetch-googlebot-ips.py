#!/usr/bin/env python3
import requests
import json
from datetime import datetime
import pytz

# URLs to fetch Googlebot IP ranges
URLS = [
    "https://developers.google.com/static/search/apis/ipranges/googlebot.json",
    "https://developers.google.com/static/search/apis/ipranges/special-crawlers.json",
    "https://developers.google.com/static/search/apis/ipranges/user-triggered-fetchers.json",
    "https://developers.google.com/static/search/apis/ipranges/user-triggered-fetchers-google.json"
]

def fetch_ip_ranges():
    """Fetch IP ranges from all URLs and combine them."""
    all_ips = []
    
    for url in URLS:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract IPv6 and IPv4 prefixes
            for prefix in data.get('prefixes', []):
                if 'ipv6Prefix' in prefix:
                    all_ips.append(prefix['ipv6Prefix'])
                elif 'ipv4Prefix' in prefix:
                    all_ips.append(prefix['ipv4Prefix'])
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            continue
    
    # Remove duplicates and sort
    all_ips = sorted(list(set(all_ips)))
    return all_ips

def write_to_file(ips, filename='googlebot.txt'):
    """Write IPs to file with proper formatting."""
    # Get current time in WIB (UTC+7)
    wib = pytz.timezone('Asia/Jakarta')
    current_time = datetime.now(wib).strftime('%Y-%m-%d %H:%M WIB')
    
    with open(filename, 'w') as f:
        f.write("; Google bot IPs allowed by LHR\n")
        f.write(f"; Based on data crawling @ {current_time}\n")
        f.write("; Source: https://developers.google.com/static/search/apis/ipranges/googlebot.json https://developers.google.com/static/search/apis/ipranges/special-crawlers.json https://developers.google.com/static/search/apis/ipranges/user-triggered-fetchers.json and https://developers.google.com/static/search/apis/ipranges/user-triggered-fetchers-google.json\n")
        f.write("; Please re-check and verify\n")
        
        for ip in ips:
            f.write(f"{ip}\n")
        
        f.write("; EOL\n")
    
    print(f"Successfully wrote {len(ips)} IP ranges to {filename}")

if __name__ == "__main__":
    print("Fetching Googlebot IP ranges...")
    ip_ranges = fetch_ip_ranges()
    
    if ip_ranges:
        write_to_file(ip_ranges)
        print(f"Total unique IP ranges: {len(ip_ranges)}")
    else:
        print("No IP ranges fetched. Check your internet connection or URLs.")
        exit(1)
