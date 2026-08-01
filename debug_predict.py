import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import app as m
print('imported app')

# Use the real function names from app.py
try:
    print('calling load_data()')
    m.load_data()
except Exception as e:
    print('load_data() error:', repr(e))

try:
    print('calling preprocess()')
    m.preprocess()
except Exception as e:
    print('preprocess() error:', repr(e))

print('trained:', getattr(m, 'trained', None))
client = m.app.test_client()
payload = {
    'Category': 'Groceries',
    'Region': 'North',
    'Inventory Level': 200,
    'Price': 12.0,
    'Discount': 0,
    'Weather Condition': 'Sunny',
    'Holiday/Promotion': 0,
    'Competitor Pricing': 10.0,
    'Seasonality': 'Spring'
}
print('payload', payload)
resp = client.post('/api/predict', json=payload)
print('status', resp.status_code)
print('data', resp.get_data(as_text=True))
