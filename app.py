import os, time, hmac, secrets, requests
from functools import wraps
from flask import Flask, request, session, redirect, url_for, render_template, jsonify, flash

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32)
PANEL_USER = os.environ.get('PANEL_USERNAME', 'admin')
PANEL_PASS = os.environ.get('PANEL_PASSWORD', '')
BOT_API_URL = os.environ.get('BOT_API_URL', '').rstrip('/')
PANEL_API_SECRET = os.environ.get('PANEL_API_SECRET', '')
UPTIME_URLS = [x.strip() for x in os.environ.get('UPTIME_URLS', '').split(',') if x.strip()]

# In-memory short cache to avoid repeatedly hitting targets during one page refresh.
_cache = {}
def check_url(url):
    now = time.time()
    if url in _cache and now - _cache[url][0] < 20:
        return _cache[url][1]
    result = {'url': url, 'status': 'DOWN', 'latency_ms': None, 'http_code': None}
    try:
        start = time.perf_counter()
        r = requests.get(url, timeout=8, allow_redirects=True)
        result['latency_ms'] = round((time.perf_counter() - start) * 1000)
        result['http_code'] = r.status_code
        result['status'] = 'UP' if r.status_code < 500 else 'DOWN'
    except requests.RequestException:
        pass
    _cache[url] = (now, result)
    return result

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return wrapper

def api_call(path, params=None, payload=None):
    if not BOT_API_URL or not PANEL_API_SECRET:
        return {'ok': False, 'error': 'BOT_API_URL or PANEL_API_SECRET is not configured'}, 503
    try:
        r = requests.request('POST' if payload is not None else 'GET', BOT_API_URL + path,
            params=params, json=payload, headers={'X-Panel-Secret': PANEL_API_SECRET}, timeout=12)
        try: data = r.json()
        except ValueError: data = {'ok': False, 'error': 'Bot API returned non-JSON response'}
        return data, r.status_code
    except requests.RequestException as e:
        return {'ok': False, 'error': f'Bot API connection failed: {e.__class__.__name__}'}, 502

@app.get('/health')
def health(): return 'OK', 200

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username','')
        password = request.form.get('password','')
        if PANEL_PASS and hmac.compare_digest(username, PANEL_USER) and hmac.compare_digest(password, PANEL_PASS):
            session.clear(); session['logged_in'] = True
            return redirect(url_for('dashboard'))
        flash('Login failed. Check PANEL_USERNAME and PANEL_PASSWORD. Set a non-empty password in Render.', 'error')
    return render_template('login.html')

@app.get('/logout')
def logout(): session.clear(); return redirect(url_for('login'))

@app.get('/')
@login_required
def dashboard():
    uptime = [check_url(u) for u in UPTIME_URLS]
    return render_template('dashboard.html', uptime=uptime, bot_api_configured=bool(BOT_API_URL and PANEL_API_SECRET), bot_url=BOT_API_URL)

@app.get('/api/groups')
@login_required
def groups():
    try: uid = int(request.args.get('user_id','0'))
    except ValueError: return jsonify({'ok':False,'error':'Invalid user_id'}), 400
    data, code = api_call('/panel-api/groups', {'user_id': uid})
    return jsonify(data), code

@app.get('/api/wallet')
@login_required
def wallet():
    try: chat_id = int(request.args.get('chat_id','0')); user_id = int(request.args.get('user_id','0'))
    except ValueError: return jsonify({'ok':False,'error':'Invalid chat_id/user_id'}), 400
    data, code = api_call('/panel-api/wallet', {'chat_id':chat_id,'user_id':user_id})
    return jsonify(data), code

@app.post('/api/wallet/debit')
@login_required
def debit():
    body = request.get_json(silent=True) or {}
    data, code = api_call('/panel-api/wallet/debit', payload=body)
    return jsonify(data), code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT','10000')))
