#!/usr/bin/env python3
"""
Script to fetch IP ranges from various sources and maintain whitelist/blacklist files.
IP ranges are automatically sorted alphabetically and duplicates are removed.
"""

import json
import os
import sys
import ipaddress
from typing import List, Set
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

URLS = {
    'google': [
        "https://developers.google.com/static/search/apis/ipranges/googlebot.json",
        "https://developers.google.com/static/search/apis/ipranges/special-crawlers.json",
        "https://developers.google.com/static/search/apis/ipranges/user-triggered-fetchers.json",
        "https://developers.google.com/static/search/apis/ipranges/user-triggered-fetchers-google.json"
    ],
    'cloudflare_v4': "https://www.cloudflare.com/ips-v4/",
    'cloudflare_v6': "https://www.cloudflare.com/ips-v6/",
    'github': "https://api.github.com/meta",
    'aws': "https://ip-ranges.amazonaws.com/ip-ranges.json",
    'abuseipdb': "https://api.abuseipdb.com/api/v2/blacklist"
}

# File mappings (support both naming conventions)
WHITELIST_FILES = ['whitelist.txt', 'pass.txt']
BLACKLIST_FILES = ['blacklist.txt', 'drop.txt']


def fetch_url(url: str, headers: dict = None) -> str:
    """Fetch content from URL with optional headers."""
    try:
        req = Request(url)
        if headers:
            for key, value in headers.items():
                req.add_header(key, value)

        with urlopen(req, timeout=30) as response:
            return response.read().decode('utf-8')
    except (URLError, HTTPError) as e:
        print(f"Error fetching {url}: {e}")
        return None


def extract_google_ips(urls: List[str]) -> Set[str]:
    """Extract IP ranges from Google JSON APIs."""
    ips = set()
    for url in urls:
        print(f"Fetching Google IPs from {url}...")
        content = fetch_url(url)
        if content:
            try:
                data = json.loads(content)
                if 'prefixes' in data:
                    for prefix in data['prefixes']:
                        if 'ipv4Prefix' in prefix:
                            ips.add(prefix['ipv4Prefix'])
                        if 'ipv6Prefix' in prefix:
                            ips.add(prefix['ipv6Prefix'])
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON from {url}: {e}")
    return ips


def extract_cloudflare_ips() -> Set[str]:
    """Extract IP ranges from Cloudflare."""
    ips = set()
    for key in ['cloudflare_v4', 'cloudflare_v6']:
        print(f"Fetching Cloudflare IPs from {URLS[key]}...")
        content = fetch_url(URLS[key])
        if content:
            for line in content.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    ips.add(line)
    return ips


def extract_github_ips() -> Set[str]:
    """Extract IP ranges from GitHub API."""
    print(f"Fetching GitHub IPs from {URLS['github']}...")
    ips = set()
    content = fetch_url(URLS['github'])
    if content:
        try:
            data = json.loads(content)
            # GitHub provides various IP ranges
            keys = ['hooks', 'web', 'api', 'git', 'pages', 'importer', 'actions', 'dependabot']
            for key in keys:
                if key in data:
                    if isinstance(data[key], list):
                        ips.update(data[key])
        except json.JSONDecodeError as e:
            print(f"Error parsing GitHub JSON: {e}")
    return ips


def extract_aws_ips() -> Set[str]:
    """Extract IP ranges from AWS."""
    print(f"Fetching AWS IPs from {URLS['aws']}...")
    ips = set()
    content = fetch_url(URLS['aws'])
    if content:
        try:
            data = json.loads(content)
            if 'prefixes' in data:
                for prefix in data['prefixes']:
                    if 'ip_prefix' in prefix:
                        ips.add(prefix['ip_prefix'])
            if 'ipv6_prefixes' in data:
                for prefix in data['ipv6_prefixes']:
                    if 'ipv6_prefix' in prefix:
                        ips.add(prefix['ipv6_prefix'])
        except json.JSONDecodeError as e:
            print(f"Error parsing AWS JSON: {e}")
    return ips


def extract_abuseipdb_ips(api_key: str = None) -> Set[str]:
    """Extract IP ranges from AbuseIPDB."""
    print(f"Fetching AbuseIPDB blacklist...")
    ips = set()

    if not api_key:
        api_key = os.environ.get('ABUSEIPDB_API_KEY')

    if not api_key:
        print("Warning: ABUSEIPDB_API_KEY not found. Skipping AbuseIPDB.")
        return ips

    headers = {
        'Key': api_key,
        'Accept': 'application/json'
    }

    # Add query parameter for plaintext format
    url = f"{URLS['abuseipdb']}?plaintext"
    content = fetch_url(url, headers)

    if content:
        try:
            # Try JSON format first
            data = json.loads(content)
            if 'data' in data:
                for item in data['data']:
                    if 'ipAddress' in item:
                        ips.add(item['ipAddress'])
        except json.JSONDecodeError:
            # Fallback to plaintext format
            for line in content.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    # Validate if it's a valid IP
                    try:
                        ipaddress.ip_address(line)
                        ips.add(line)
                    except ValueError:
                        continue

    return ips


def read_existing_ips(file_path: str) -> Set[str]:
    """Read existing IPs from file."""
    ips = set()
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    ips.add(line)
    return ips


def sort_ips(ips: Set[str]) -> List[str]:
    """Sort IPs alphabetically with proper IP sorting."""
    ipv4_list = []
    ipv6_list = []
    other_list = []

    for ip in ips:
        try:
            network = ipaddress.ip_network(ip, strict=False)
            if network.version == 4:
                ipv4_list.append(ip)
            else:
                ipv6_list.append(ip)
        except ValueError:
            other_list.append(ip)

    # Sort each category
    ipv4_sorted = sorted(ipv4_list, key=lambda x: ipaddress.ip_network(x, strict=False))
    ipv6_sorted = sorted(ipv6_list, key=lambda x: ipaddress.ip_network(x, strict=False))
    other_sorted = sorted(other_list)

    return ipv4_sorted + ipv6_sorted + other_sorted


def write_ips_to_file(file_path: str, ips: Set[str], header_comment: str = None):
    """Write IPs to file in sorted order."""
    sorted_ips = sort_ips(ips)

    with open(file_path, 'w') as f:
        if header_comment:
            f.write(f"# {header_comment}\n")
            f.write(f"# Total entries: {len(sorted_ips)}\n")
            f.write(f"# Last updated: {os.popen('date').read().strip()}\n\n")

        for ip in sorted_ips:
            f.write(f"{ip}\n")

    print(f"Written {len(sorted_ips)} entries to {file_path}")


def get_file_path(file_list: List[str]) -> str:
    """Get the first existing file path or create the first one."""
    for file_path in file_list:
        if os.path.exists(file_path):
            return file_path
    return file_list[0]  # Return first option if none exist


def main():
    """Main function to fetch and update IP lists."""
    print("Starting IP ranges fetch and update process...\n")

    # Fetch whitelist IPs
    print("=" * 50)
    print("FETCHING WHITELIST IPs")
    print("=" * 50)

    whitelist_ips = set()

    # Google
    whitelist_ips.update(extract_google_ips(URLS['google']))

    # Cloudflare
    whitelist_ips.update(extract_cloudflare_ips())

    # GitHub
    whitelist_ips.update(extract_github_ips())

    # AWS
    whitelist_ips.update(extract_aws_ips())

    print(f"\nTotal new whitelist IPs fetched: {len(whitelist_ips)}")

    # Fetch blacklist IPs
    print("\n" + "=" * 50)
    print("FETCHING BLACKLIST IPs")
    print("=" * 50)

    blacklist_ips = extract_abuseipdb_ips()
    print(f"\nTotal new blacklist IPs fetched: {len(blacklist_ips)}")

    # Merge with existing files
    print("\n" + "=" * 50)
    print("MERGING WITH EXISTING FILES")
    print("=" * 50)

    # Whitelist
    whitelist_file = get_file_path(WHITELIST_FILES)
    existing_whitelist = read_existing_ips(whitelist_file)
    print(f"Existing whitelist entries: {len(existing_whitelist)}")

    merged_whitelist = existing_whitelist.union(whitelist_ips)
    new_whitelist_count = len(merged_whitelist) - len(existing_whitelist)
    print(f"New whitelist entries to add: {new_whitelist_count}")

    # Blacklist
    blacklist_file = get_file_path(BLACKLIST_FILES)
    existing_blacklist = read_existing_ips(blacklist_file)
    print(f"Existing blacklist entries: {len(existing_blacklist)}")

    merged_blacklist = existing_blacklist.union(blacklist_ips)
    new_blacklist_count = len(merged_blacklist) - len(existing_blacklist)
    print(f"New blacklist entries to add: {new_blacklist_count}")

    # Write to files
    print("\n" + "=" * 50)
    print("WRITING TO FILES")
    print("=" * 50)

    write_ips_to_file(
        whitelist_file,
        merged_whitelist,
        "Whitelist - Google, Cloudflare, GitHub, AWS IP Ranges"
    )

    write_ips_to_file(
        blacklist_file,
        merged_blacklist,
        "Blacklist - AbuseIPDB"
    )

    print("\n" + "=" * 50)
    print("PROCESS COMPLETED SUCCESSFULLY")
    print("=" * 50)
    print(f"Total whitelist entries: {len(merged_whitelist)}")
    print(f"Total blacklist entries: {len(merged_blacklist)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
