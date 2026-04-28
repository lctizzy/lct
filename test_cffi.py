# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

try:
    from curl_cffi import requests as cffi_req
    print('curl_cffi OK')
    
    # Test with impersonation
    url = 'https://www.tiktok.com/@jtrends31/video/7617666013340978453'
    r = cffi_req.get(url, impersonate='chrome120')
    print('Status:', r.status_code)
    print('Length:', len(r.text))
    
    import re
    # Check page content
    text = r.text
    if 'Video unavailable' in text or 'not found' in text.lower():
        print('VIDEO NOT AVAILABLE or removed')
    elif '@jtrends31' in text:
        print('Page loaded, creator found')
        # Try to find download URLs
        patterns = [
            r'"playAddr":\s*\[?\s*{"url":\s*"([^"]+)"',
            r'"downloadAddr":\s*"([^"]+)"',
            r'"video_url":\s*"([^"]+)"',
            r'playAddr.*?"url":\s*"([^"]+)"',
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                found = m.group(1).replace('\\u002F', '/').replace('\\/', '/')
                print('Found URL pattern:', p[:30])
                print('URL:', found[:100])
                break
        else:
            # Look for any video-related JSON
            if '"video"' in text:
                print('Video data found in page but no direct URL match')
            else:
                print('No video data in page')
    else:
        print('Unknown page - first 200 chars:', text[:200])
        
except ImportError:
    print('curl_cffi not installed')
except Exception as e:
    print('Error:', type(e).__name__, str(e)[:300])
