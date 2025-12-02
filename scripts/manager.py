#!/usr/bin/env python3
import os
import pkgutil
import importlib.util
import sys
from datetime import datetime
import pytz

# --- KONFIGURASI PATH ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCES_DIR = os.path.join(BASE_DIR, 'sources')
OUTPUT_DIR = os.path.join(os.path.dirname(BASE_DIR), 'lists')

FILES_MAP = {
    'drop_ip': os.path.join(OUTPUT_DIR, 'drop.txt'),
    'pass_ip': os.path.join(OUTPUT_DIR, 'pass.txt'),
    'whitelist_domain': os.path.join(OUTPUT_DIR, 'whitelist-domain.txt'),
    'blacklist_domain': os.path.join(OUTPUT_DIR, 'blacklist-domain.txt')
}

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def load_existing_data(filepath):
    """Membaca data lama agar tidak hilang (Append Mode)."""
    data = set()
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith(';') and not line.startswith('#'):
                    data.add(line)
    return data

def save_data(filepath, data, source_names):
    """Menyimpan data gabungan ke file."""
    wib = pytz.timezone('Asia/Jakarta')
    timestamp = datetime.now(wib).strftime('%Y-%m-%d %H:%M WIB')
    
    sorted_data = sorted(list(data))
    
    with open(filepath, 'w') as f:
        f.write(f"; Updated at: {timestamp}\n")
        f.write(f"; Sources included: {', '.join(source_names)}\n")
        f.write(f"; Total Entries: {len(sorted_data)}\n")
        f.write("; --------------------------------------------\n")
        for item in sorted_data:
            f.write(f"{item}\n")
    print(f"✅ Saved {len(sorted_data)} entries to {os.path.basename(filepath)}")

def run_plugins():
    # 1. Persiapkan wadah data
    ensure_dir(OUTPUT_DIR)
    
    # Load data lama (Existing)
    aggregated_data = {
        'drop_ip': load_existing_data(FILES_MAP['drop_ip']),
        'pass_ip': load_existing_data(FILES_MAP['pass_ip']),
        'whitelist_domain': load_existing_data(FILES_MAP['whitelist_domain']),
        'blacklist_domain': load_existing_data(FILES_MAP['blacklist_domain'])
    }
    
    active_sources = []

    # 2. Scan folder 'sources' dan jalankan setiap script
    print(f"🔍 Scanning plugins in: {SOURCES_DIR}")
    for filename in os.listdir(SOURCES_DIR):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]
            file_path = os.path.join(SOURCES_DIR, filename)
            
            print(f"   running plugin: {module_name}...")
            
            try:
                # Dynamic Import
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Cek apakah modul punya fungsi fetch()
                if hasattr(module, 'fetch'):
                    # Jalankan fetch()
                    result = module.fetch() 
                    
                    # Merge hasil ke data utama
                    if result:
                        active_sources.append(module_name)
                        for key in aggregated_data.keys():
                            if key in result and result[key]:
                                aggregated_data[key].update(result[key])
                else:
                    print(f"⚠️  Skipping {module_name}: No fetch() function found.")
                    
            except Exception as e:
                print(f"❌ Error in plugin {module_name}: {e}")

    # 3. Simpan hasil akhir
    print("\n💾 Saving aggregated lists...")
    for key, filepath in FILES_MAP.items():
        save_data(filepath, aggregated_data[key], active_sources)

if __name__ == "__main__":
    run_plugins()
