print('Testing basic Python...')
try:
    import flask
    print('Flask: OK')
except:
    print('Flask: MISSING - run: pip install flask')

try:
    import requests
    print('Requests: OK')  
except:
    print('Requests: MISSING - run: pip install requests')

print('Done. Now run: python elevenlabs_token_server.py')
