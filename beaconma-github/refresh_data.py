#!/usr/bin/env python3
"""
BEACON Data Refresh Script
Run daily via cron: 0 6 * * * python3 /path/to/refresh_data.py
Pulls latest data from CTHRU, OCPF, and updates the site.
"""
import json, urllib.request, urllib.parse, os, datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

def fetch_json(base_url, params):
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def refresh_cthru():
    """Pull latest CTHRU spending data"""
    base = "https://cthru.data.socrata.com/resource/pegc-naaa.json"
    fy = str(datetime.date.today().year)
    
    # Top vendors
    vendors = fetch_json(base, {
        '$select': 'vendor,sum(amount) as total_spending,count(*) as transactions',
        '$where': f"budget_fiscal_year='{fy}'",
        '$group': 'vendor', '$order': 'total_spending DESC', '$limit': '200'
    })
    with open(os.path.join(DATA_DIR, f'top_vendors_fy{fy}.json'), 'w') as f:
        json.dump(vendors, f, indent=2)
    print(f"[CTHRU] {len(vendors)} vendors for FY{fy}")
    
    # Cabinet spending
    cabinets = fetch_json(base, {
        '$select': 'cabinet_secretariat,sum(amount) as total',
        '$where': f"budget_fiscal_year='{fy}'",
        '$group': 'cabinet_secretariat', '$order': 'total DESC', '$limit': '30'
    })
    with open(os.path.join(DATA_DIR, f'cabinets_fy{fy}.json'), 'w') as f:
        json.dump(cabinets, f, indent=2)
    print(f"[CTHRU] {len(cabinets)} cabinets for FY{fy}")
    
    return len(vendors)

def refresh_ocpf():
    """Pull latest OCPF campaign finance data"""
    base = "https://api.ocpf.us/search/items"
    now = datetime.date.today()
    start = (now - datetime.timedelta(days=365)).strftime('%m/%d/%Y')
    end = now.strftime('%m/%d/%Y')
    
    url = f"{base}?searchTypeCategory=A&startDate={start}&endDate={end}&pagesize=1000&startIndex=0&sortField=amount&sortDirection=DESC&minAmount=1000&withSummary=true"
    req = urllib.request.Request(url, headers={'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
    
    items = data.get('items', [])
    with open(os.path.join(DATA_DIR, 'ocpf_recent.json'), 'w') as f:
        json.dump(items, f, indent=2)
    print(f"[OCPF] {len(items)} contributions in last 365 days (>=$1K)")
    return len(items)

def run():
    ts = datetime.datetime.now().isoformat()
    print(f"\n{'='*60}")
    print(f"BEACON Data Refresh — {ts}")
    print(f"{'='*60}")
    
    try:
        v = refresh_cthru()
    except Exception as e:
        print(f"[CTHRU ERROR] {e}")
        v = 0
    
    try:
        c = refresh_ocpf()
    except Exception as e:
        print(f"[OCPF ERROR] {e}")
        c = 0
    
    log = {'timestamp': ts, 'vendors': v, 'contributions': c}
    with open(os.path.join(DATA_DIR, 'last_refresh.json'), 'w') as f:
        json.dump(log, f, indent=2)
    
    print(f"\nRefresh complete. {v} vendors, {c} contributions.")
    print(f"Next: Run anomaly detection, update BEACON.html")

if __name__ == '__main__':
    run()
