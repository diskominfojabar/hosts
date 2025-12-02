import requests
import os

def fetch():
    # Mengambil API Key dari Secrets
    api_key = os.environ.get('ABUSEIPDB_KEY')
    if not api_key:
        print("      [AbuseIPDB] ⚠️ API Key not found. Skipping...")
        return {}

    url = "https://api.abuseipdb.com/api/v2/blacklist"
    params = {
        'key': api_key,
        'plaintext': 'true',     # Format teks polos (satu IP per baris)
        'limit': '65000',        # Limit maksimal fetch
        'confidenceMinimum': '75' # Hanya yang confidence level tinggi
    }
    
    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        
        # Parsing hasil response menjadi Set (untuk otomatis hapus duplikat)
        ips = set(line.strip() for line in response.text.splitlines() if line.strip())
        
        print(f"      [AbuseIPDB] ✅ Fetched {len(ips)} IPs")
        
        # KUNCI UTAMA: Mengembalikan data dengan label 'drop_ip'
        # Label ini akan dibaca manager.py untuk disimpan ke drop.txt
        return {'drop_ip': ips}

    except Exception as e:
        print(f"      [AbuseIPDB] ❌ Error: {e}")
        return {}
