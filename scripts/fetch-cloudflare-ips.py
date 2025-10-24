#!/usr/bin/env python3
import requests
from datetime import datetime
import pytz

# URLs to fetch Cloudflare IP ranges
CLOUDFLARE_IPV4_URL = "https://www.cloudflare.com/ips-v4/"
CLOUDFLARE_IPV6_URL = "https://www.cloudflare.com/ips-v6/"

def fetch_cloudflare_ips():
    """Fetch IP ranges from Cloudflare URLs."""
    all_ips = []
    
    urls = {
        'IPv4': CLOUDFLARE_IPV4_URL,
        'IPv6': CLOUDFLARE_IPV6_URL
    }
    
    for ip_type, url in urls.items():
        try:
            print(f"Fetching {ip_type} ranges from {url}...")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Cloudflare returns plain text with one IP range per line
            ip_ranges = response.text.strip().split('\n')
            ip_ranges = [ip.strip() for ip in ip_ranges if ip.strip()]
            
            all_ips.extend(ip_ranges)
            print(f"Found {len(ip_ranges)} {ip_type} ranges")
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            continue
    
    return all_ips

def write_to_file(ips, filename='cloudflare-ips.txt'):
    """Write IPs to file with proper formatting."""
    # Get current time in WIB (UTC+7)
    wib = pytz.timezone('Asia/Jakarta')
    current_time = datetime.now(wib).strftime('%Y-%m-%d %H:%M WIB')
    
    with open(filename, 'w') as f:
        f.write("; Cloudflare IPs\n")
        f.write(f"; Based on data crawling @ {current_time}\n")
        f.write("; Source: https://www.cloudflare.com/ips-v4/ and https://www.cloudflare.com/ips-v6/\n")
        f.write("; Please re-check and verify\n")
        f.write("\n")
        
        for ip in ips:
            f.write(f"{ip}\n")
        
        f.write("\n; EOL\n")
    
    print(f"Successfully wrote {len(ips)} IP ranges to {filename}")

if __name__ == "__main__":
    print("Fetching Cloudflare IP ranges...")
    ip_ranges = fetch_cloudflare_ips()
    
    if ip_ranges:
        write_to_file(ip_ranges)
        print(f"Total unique IP ranges: {len(ip_ranges)}")
    else:
        print("No IP ranges fetched. Check your internet connection or URLs.")
        exit(1)
