# -*- coding: utf-8 -*-
import urllib.request, json, sys
sys.stdout.reconfigure(encoding='utf-8')

# Test multiple TikTok download APIs
test_url = 'https://www.tiktok.com/@healthsisther/video/7626670557144026381'
apis = [
    ('tikwm.com', f'https://www.tikwm.com/api/?url={test_url}'),
    ('ssstik.io', f'https://ssstik.io/api?url={test_url}&type=json'),
    ('musicaldown.com', f'https://musicaldown.com/api/download?url={test_url}'),
]

for name, url in apis:
    headers = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
    try:
        req = urllib.request.Request(url, headers=headers)
        r = urllib.request.urlopen(req, timeout=15)
        data = r.read().decode()[:300]
        ct = r.headers.get('content-type', '')
        print(f'{name}: {r.status} (Content-Type: {ct})')
        if 'json' in ct:
            print(f'  JSON: {data[:200]}')
        else:
            print(f'  HTML: {data[:150]}...')
    except Exception as e:
        print(f'{name}: ERROR - {e}')
    print()
