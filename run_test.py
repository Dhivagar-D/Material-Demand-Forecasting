import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import app
print('Imported app, trained=', getattr(app, 'trained', None))
try:
    client = app.app.test_client()
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
    print('Posting payload')
    resp = client.post('/api/predict', json=payload)
    print('Status code:', resp.status_code)
    print('Data:', resp.get_data(as_text=True))
except Exception as e:
    print('Exception during request:', repr(e))
