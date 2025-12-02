#!/usr/bin/env python3
import requests
import os
from datetime import datetime
import pytz

# --- KONFIGURASI FOLDER OUTPUT ---
# Mendefinisikan nama folder output
OUTPUT_DIR = 'lists'

# --- KONFIGURASI FILE OUTPUT (MENGGUNAKAN PATH FOLDER) ---
FILE_DROP_IP = os.path.join(OUTPUT_DIR, 'drop.txt')
FILE_PASS_IP = os.path.join(OUTPUT_DIR, 'pass.txt')
FILE_WHITELIST_DOMAIN = os.path.join(OUTPUT_DIR, 'whitelist-domain.txt')
FILE_BLACKLIST_DOMAIN = os.path.join(OUTPUT_DIR, 'blacklist-domain.txt')

# --- KONFIGURASI SUMBER (UPSTREAM) ---
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

def get_current_timestamp():
    wib = pytz.timezone('Asia/Jakarta')
    return datetime.now(wib).strftime('%Y-%m-%d %H:%M WIB')

def ensure_output_dir():
    """Memastikan folder output (lists) tersedia."""
    if not os.path.exists(OUTPUT_DIR):
        try:
            os.makedirs(OUTPUT_DIR)
            print(f"📁 Created directory: {OUTPUT_DIR}")
        except OSError as e:
            print(f"❌ Error creating directory {OUTPUT_DIR}: {e}")

def load_existing_data(filename):
    """Membaca data lama dari file agar tidak hilang (fitur append/merge)."""
    data_set = set()
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Abaikan komentar dan baris kosong
                    if line and not line.startswith(';') and not line.startswith('#'):
                        data_set.add(line)
            print(f"📖 Loaded {len(data_set)} entries from existing {filename}")
        except Exception as e:
            print(f"⚠️ Warning loading {filename}: {e}")
    return data_set

def save_to_file(filename, data_set, header_info=""):
    """Menyimpan data (gabungan lama + baru) ke file."""
    sorted_data = sorted(list(data_set))
    timestamp = get_current_timestamp()
    
    try:
        with open(filename, 'w') as f:
            f.write(f"; {os.path.basename(filename)} - Updated at {timestamp}\n")
            f.write(f"; {header_info}\n")
            f.write("; Total Entries: " + str(len(sorted_data)) + "\n")
            f.write("; ----------------------------------------\n")
            for item in sorted_data:
                f.write(f"{item}\n")
        print(f"✅ Successfully saved {len(sorted_data)} entries to {filename}")
    except Exception as e:
        print(f"❌ Error saving {filename}: {e}")

# --- FUNGSI FETCHING PER LAYANAN ---

def fetch_abuseipdb(existing_set):
    """Fetch blacklist dari AbuseIPDB dan merge ke existing set."""
    api_key = os.environ.get('ABUSEIPDB_KEY')
    if not api_key:
        print("⚠️ AbuseIPDB Key not found! Skipping...")
        return existing_set

    print("running fetch_abuseipdb...")
    params = {
        'key': api_key,
        'plaintext': 'true',
        'limit': '65000',
        'confidenceMinimum': '75'
    }
    try:
        # Note: AbuseIPDB plaintext return list line by line
        response = requests.get(URLS['abuseipdb'], params=params, timeout=30)
        response.raise_for_status()
        
        new_ips = set(line.strip() for line in response.text.splitlines() if line.strip())
        print(f"   Fetched {len(new_ips)} IPs from AbuseIPDB")
        return existing_set.union(new_ips)
    except Exception as e:
        print(f"❌ Error AbuseIPDB: {e}")
        return existing_set

def fetch_google(existing_set):
    print("running fetch_google...")
    new_ips = set()
    for url in URLS['google']:
        try:
            r = requests.get(url, timeout=10)
            data = r.json()
            for prefix in data.get('prefixes', []):
                if 'ipv6Prefix' in prefix: new_ips.add(prefix['ipv6Prefix'])
                if 'ipv4Prefix' in prefix: new_ips.add(prefix['ipv4Prefix'])
        except Exception as e:
            print(f"   Error fetching Google URL {url}: {e}")
    
    print(f"   Fetched {len(new_ips)} IPs from Google")
    return existing_set.union(new_ips)

def fetch_cloudflare(existing_set):
    print("running fetch_cloudflare...")
    new_ips = set()
    try:
        # IPv4
        r4 = requests.get(URLS['cloudflare_v4'], timeout=10)
        new_ips.update(line.strip() for line in r4.text.splitlines() if line.strip())
        # IPv6
        r6 = requests.get(URLS['cloudflare_v6'], timeout=10)
        new_ips.update(line.strip() for line in r6.text.splitlines() if line.strip())
    except Exception as e:
        print(f"   Error fetching Cloudflare: {e}")
        
    print(f"   Fetched {len(new_ips)} IPs from Cloudflare")
    return existing_set.union(new_ips)

def fetch_github(existing_ips, existing_domains):
    print("running fetch_github...")
    new_ips = set()
    new_domains = set()
    try:
        r = requests.get(URLS['github'], timeout=10)
        data = r.json()
        
        # IPs
        keys_ip = ['hooks', 'web', 'api', 'git', 'pages', 'actions', 'dependabot']
        for k in keys_ip:
            if k in data: new_ips.update(data[k])
            
        # Domains (Jika tersedia di API atau hardcoded penting)
        new_domains.add("github.com")
        new_domains.add("githubusercontent.com")
        if 'domains' in data:
            for k, v in data['domains'].items():
                if isinstance(v, list): new_domains.update(v)

    except Exception as e:
        print(f"   Error fetching GitHub: {e}")

    print(f"   Fetched {len(new_ips)} IPs and {len(new_domains)} domains from GitHub")
    return existing_ips.union(new_ips), existing_domains.union(new_domains)

def fetch_aws(existing_set):
    print("running fetch_aws...")
    new_ips = set()
    try:
        r = requests.get(URLS['aws'], timeout=10)
        data = r.json()
        for p in data.get('prefixes', []): new_ips.add(p['ip_prefix'])
        for p in data.get('ipv6_prefixes', []): new_ips.add(p['ipv6_prefix'])
    except Exception as e:
        print(f"   Error fetching AWS: {e}")
        
    print(f"   Fetched {len(new_ips)} IPs from AWS")
    return existing_set.union(new_ips)

def main():
    # 0. Pastikan folder output ada
    ensure_output_dir()

    # 1. Load Data Lama (Existing)
    # Karena path file sekarang sudah include 'lists/', maka ia akan membaca dari folder tsb
    drop_ips = load_existing_data(FILE_DROP_IP)
    pass_ips = load_existing_data(FILE_PASS_IP)
    whitelist_domains = load_existing_data(FILE_WHITELIST_DOMAIN)
    blacklist_domains = load_existing_data(FILE_BLACKLIST_DOMAIN)

    # 2. Fetch Data Baru & Merge
    # A. Blacklist IPs (AbuseIPDB) -> drop.txt
    drop_ips = fetch_abuseipdb(drop_ips)

    # B. Whitelist IPs (Google, CF, GitHub, AWS) -> pass.txt
    pass_ips = fetch_google(pass_ips)
    pass_ips = fetch_cloudflare(pass_ips)
    pass_ips, whitelist_domains = fetch_github(pass_ips, whitelist_domains) # Mengupdate IP dan Domain
    pass_ips = fetch_aws(pass_ips)
    
    # C. Whitelist Domain Tambahan (AWS Domain hardcoded jika perlu)
    whitelist_domains.add("amazonaws.com")
    whitelist_domains.add("aws.amazon.com")

    # D. Blacklist Domain (Placeholder logic, karena tidak ada upstream di request awal)
    # Jika nanti ada sumber, tambahkan fungsi fetch_malware_domains() disini.
    
    # 3. Simpan Kembali ke File (ke folder lists/)
    print("\n--- Saving Files ---")
    save_to_file(FILE_DROP_IP, drop_ips, "Source: AbuseIPDB High Confidence")
    save_to_file(FILE_PASS_IP, pass_ips, "Source: Google, Cloudflare, GitHub, AWS")
    save_to_file(FILE_WHITELIST_DOMAIN, whitelist_domains, "Source: GitHub, AWS Domains")
    save_to_file(FILE_BLACKLIST_DOMAIN, blacklist_domains, "Source: Manual/Custom Blocklist")

if __name__ == "__main__":
    main()
