import os
import json
import sqlite3
import traceback
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# Optional dependency: requests (used to call Ditto REST API). If not installed,
# endpoints will return an informative error asking to install it.
try:
    import requests
    _HAS_REQUESTS = True
except Exception:
    _HAS_REQUESTS = False

DB_PATH = os.path.join(os.path.dirname(__file__), 'history.db')

app = Flask(__name__)
CORS(app)


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            twin_id TEXT,
            endpoint TEXT,
            payload TEXT,
            response TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()


def save_history(twin_id, endpoint, payload, response_text):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO history (twin_id, endpoint, payload, response, timestamp) VALUES (?,?,?,?,?)',
            (twin_id, endpoint, json.dumps(payload, ensure_ascii=False), response_text, datetime.utcnow().isoformat())
        )
        conn.commit()
        rowid = cur.lastrowid
        conn.close()
        return rowid
    except Exception as e:
        print('Error saving history:', e)
        traceback.print_exc()
        return None


@app.route('/', methods=['GET'])
def root():
    return jsonify({
        'service': 'cloud2edge (history + optional Ditto replication)',
        'endpoints': {
            'save-history': '/save-history (POST)',
            'replicate-ditto': '/replicate-ditto (POST)',
            'health': '/health (GET)'
        }
    })


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'db': DB_PATH, 'requests_installed': _HAS_REQUESTS})


@app.route('/save-history', methods=['POST'])
def api_save_history():
    """Saves a JSON payload to the local history DB.
    Expected JSON: { "twin_id": "optional-id", "endpoint": "source", "payload": {...} }
    """
    try:
        data = request.get_json(force=True)
        if not data or 'payload' not in data:
            return jsonify({'success': False, 'error': 'payload field is required'}), 400

        twin_id = data.get('twin_id')
        endpoint = data.get('endpoint', 'unknown')
        payload = data.get('payload')

        rowid = save_history(twin_id, endpoint, payload, response_text=None)
        return jsonify({'success': True, 'id': rowid})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/replicate-ditto', methods=['POST'])
def api_replicate_ditto():
    """Replicates a payload to Ditto (if configured via env).
    Expected JSON: { "twin_id": "<id>", "payload": {...}, "feature_path": "optional" }

    Environment variables used:
      DITTO_URL    - base URL or full URL template. If contains {twin_id}, it will be formatted.
      DITTO_AUTH   - full Authorization header value (e.g. 'Bearer <token>' or 'Basic ...')

    Examples:
      DITTO_URL="https://ditto.example/api/2/things/{twin_id}/features/myFeature/messages"
      DITTO_AUTH="Bearer abcd..."
    """
    try:
        data = request.get_json(force=True)
        if not data or 'twin_id' not in data or 'payload' not in data:
            return jsonify({'success': False, 'error': 'twin_id and payload required'}), 400

        twin_id = data['twin_id']
        payload = data['payload']

        ditto_url = os.environ.get('DITTO_URL')
        ditto_auth = os.environ.get('DITTO_AUTH')

        if not _HAS_REQUESTS:
            return jsonify({'success': False, 'error': "Missing Python 'requests' package. Install with: pip install requests"}), 500

        if not ditto_url:
            # Ditto not configured — just save history and return.
            rowid = save_history(twin_id, 'replicate-ditto', payload, response_text='ditto_not_configured')
            return jsonify({'success': True, 'notice': 'Ditto not configured, saved to history', 'id': rowid})

        # Build URL
        if '{twin_id}' in ditto_url:
            url = ditto_url.format(twin_id=twin_id)
        else:
            url = ditto_url.rstrip('/') + f'/things/{twin_id}'

        headers = {'Content-Type': 'application/json'}
        if ditto_auth:
            headers['Authorization'] = ditto_auth

        # Send a PUT by default. Caller may pass query params in DITTO_URL if needed.
        try:
            resp = requests.put(url, json=payload, headers=headers, timeout=10)
            resp_text = f'status={resp.status_code}; body={resp.text}'
            save_history(twin_id, 'replicate-ditto', payload, resp_text)
            return jsonify({'success': True, 'status': resp.status_code, 'response': resp.text})
        except requests.RequestException as re:
            save_history(twin_id, 'replicate-ditto', payload, f'error:{str(re)}')
            return jsonify({'success': False, 'error': str(re)}), 500

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/history', methods=['GET'])
def api_history_list():
    """List recent history entries. Optional query param: limit (default 50)"""
    try:
        limit = int(request.args.get('limit', 50))
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('SELECT id, twin_id, endpoint, payload, response, timestamp FROM history ORDER BY id DESC LIMIT ?', (limit,))
        rows = cur.fetchall()
        conn.close()
        entries = []
        for r in rows:
            entries.append({
                'id': r[0],
                'twin_id': r[1],
                'endpoint': r[2],
                'payload': json.loads(r[3]) if r[3] else None,
                'response': r[4],
                'timestamp': r[5]
            })
        return jsonify({'success': True, 'entries': entries})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print('\n' + '=' * 60)
    print('cloud2edge service (history + optional Ditto replication)')
    print('DB path:', DB_PATH)
    print('To enable Ditto replication set env vars: DITTO_URL and DITTO_AUTH')
    print('Example:')
    print("  DITTO_URL='https://ditto.example/api/2/things/{twin_id}/features/featureName/messages'")
    print("  DITTO_AUTH='Bearer <token>'")
    print('Start: python back\\cloud2edge.py')
    print('=' * 60 + '\n')

    init_db()
    app.run(host='0.0.0.0', port=3002, debug=True)
