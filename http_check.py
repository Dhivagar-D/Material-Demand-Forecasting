import urllib.request
import json

urls = ['http://127.0.0.1:10000/', 'http://127.0.0.1:10000/api/options', 'http://127.0.0.1:10000/api/health']
for u in urls:
    try:
        with urllib.request.urlopen(u, timeout=5) as r:
            print(u, r.status)
            data = r.read().decode('utf-8')
            print(data[:400])
    except Exception as e:
        print('ERROR', u, repr(e))
