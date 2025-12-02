import requests
import os

# Konfigurasi File
PASS_FILE = 'pass.txt'
WHITELIST_TLD_FILE = 'whitelist-tld.txt'

# URL Sumber
GITHUB_META_URL = 'https://api.github.com/meta'
AWS_IP_RANGES_URL = 'https://ip-ranges.amazonaws.com/ip-ranges.json'

def read_file_to_set(filename):
    """Membaca file ke dalam set untuk menghindari duplikasi, jika file ada."""
    data_set = set()
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    data_set.add(line)
    return data_set

def write_set_to_file(filename, data_set):
    """Menulis set kembali ke file dengan urutan sorted."""
    sorted_data = sorted(list(data_set))
    with open(filename, 'w') as f:
        for item in sorted_data:
            f.write(f"{item}\n")

def fetch_github_data():
    print("Fetching GitHub Meta...")
    try:
        response = requests.get(GITHUB_META_URL)
        response.raise_for_status()
        data = response.json()
        
        ips = set()
        # Mengambil semua IP dari kategori yang relevan
        keys_to_extract = ['hooks', 'web', 'api', 'git', 'pages', 'actions', 'dependabot']
        for key in keys_to_extract:
            if key in data:
                ips.update(data[key])
        
        # GitHub Meta API kadang menyertakan domain di field 'domains' (jika ada)
        domains = set()
        if 'domains' in data:
            # Jika struktur JSON memiliki key domains
            for key, val in data['domains'].items():
                if isinstance(val, list):
                    domains.update(val)
        
        # Fallback manual domain penting jika API tidak menyediakan list domain lengkap
        domains.add("github.com")
        domains.add("githubusercontent.com")
            
        return ips, domains
    except Exception as e:
        print(f"Error fetching GitHub data: {e}")
        return set(), set()

def fetch_aws_data():
    print("Fetching AWS IP Ranges...")
    try:
        response = requests.get(AWS_IP_RANGES_URL)
        response.raise_for_status()
        data = response.json()
        
        ips = set()
        # IPv4
        for item in data.get('prefixes', []):
            ips.add(item['ip_prefix'])
        # IPv6
        for item in data.get('ipv6_prefixes', []):
            ips.add(item['ipv6_prefix'])
            
        # AWS JSON tidak menyediakan list domain, kita tambahkan domain utama saja
        domains = set(["amazonaws.com", "aws.amazon.com"])
        
        return ips, domains
    except Exception as e:
        print(f"Error fetching AWS data: {e}")
        return set(), set()

def main():
    # 1. Baca data existing
    existing_ips = read_file_to_set(PASS_FILE)
    existing_domains = read_file_to_set(WHITELIST_TLD_FILE)
    
    print(f"Loaded {len(existing_ips)} existing IPs and {len(existing_domains)} existing domains.")

    # 2. Fetch Data Baru
    gh_ips, gh_domains = fetch_github_data()
    aws_ips, aws_domains = fetch_aws_data()

    # 3. Gabungkan Data (Merge)
    # Update IPs
    total_ips_before = len(existing_ips)
    existing_ips.update(gh_ips)
    existing_ips.update(aws_ips)
    print(f"IPs updated: {total_ips_before} -> {len(existing_ips)}")

    # Update Domains
    total_domains_before = len(existing_domains)
    existing_domains.update(gh_domains)
    existing_domains.update(aws_domains)
    print(f"Domains updated: {total_domains_before} -> {len(existing_domains)}")

    # 4. Tulis kembali ke file
    write_set_to_file(PASS_FILE, existing_ips)
    write_set_to_file(WHITELIST_TLD_FILE, existing_domains)
    print("Files updated successfully.")

if __name__ == "__main__":
    main()
