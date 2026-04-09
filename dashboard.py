import os
import shutil
import psutil
import json
import zipfile
import re
from datetime import datetime
from flask import Flask, render_template, request, session, redirect, url_for, send_file, jsonify, flash
from mcrcon import MCRcon

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default_fallback_secret_key_123')

# Configuration
MC_DATA_PATH = os.environ.get('MC_DATA_PATH', '/data')
RCON_PASSWORD = os.environ.get('RCON_PASSWORD', '')
RCON_PORT = int(os.environ.get('RCON_PORT', 25575))
DASHBOARD_PASSWORD = os.environ.get('DASHBOARD_PASSWORD', 'admin123')

# Local explicit user credentials
LOCAL_USERNAME = "Djrockzz"
LOCAL_PASSWORD = "rocky@123"

def run_rcon(command):
    try:
        with MCRcon('localhost', RCON_PASSWORD, port=RCON_PORT) as mcr:
            return mcr.command(command)
    except Exception as e:
        return f"Error executing command: {str(e)}"

def format_size(size_in_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} PB"

@app.before_request
def check_auth():
    if request.endpoint not in ['login', 'static'] and not session.get('authenticated'):
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        user = request.form.get('username', '').strip()
        pwd = request.form.get('password', '').strip()
        
        # Check explicit user
        if user == LOCAL_USERNAME and pwd == LOCAL_PASSWORD:
            session['authenticated'] = True
            session['user'] = user
            return redirect(url_for('overview'))
            
        # Check generic password
        elif pwd == DASHBOARD_PASSWORD and not user:
            session['authenticated'] = True
            session['user'] = 'Admin'
            return redirect(url_for('overview'))
            
        else:
            error = "Invalid credentials."
            
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@app.route('/overview')
def overview():
    # Uptime logic roughly via psutil boot time
    uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
    uptime_str = str(uptime).split('.')[0]
    
    # Resources
    cpu_usage = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    mem_used = format_size(mem.used)
    mem_total = format_size(mem.total)
    
    disk = psutil.disk_usage(MC_DATA_PATH if os.path.exists(MC_DATA_PATH) else '/')
    disk_used = format_size(disk.used)
    disk_total = format_size(disk.total)
    
    # Check if Minecraft is running (we assume yes if localhost RCON connects, or we can check via psutil)
    is_online = False
    tps = "N/A"
    players_online = "0/0"
    version = "Unknown"
    
    try:
        with open(os.path.join(MC_DATA_PATH, 'version_history.json'), 'r') as f:
            v_data = json.load(f)
            if v_data and 'currentVersion' in v_data:
                version = v_data['currentVersion']
    except:
        pass
        
    try:
        with MCRcon('localhost', RCON_PASSWORD, port=RCON_PORT) as mcr:
            is_online = True
            tps_res = mcr.command("tps")
            tps = tps_res.split(":")[-1].strip() if "TPS" in tps_res.upper() else tps_res
            
            list_res = mcr.command("list")
            # Format: 'There are X of a max of Y players online:'
            if "max of" in list_res:
                match = re.search(r'(\d+) of a max of (\d+)', list_res)
                if match:
                    players_online = f"{match.group(1)}/{match.group(2)}"
    except:
        pass

    return render_template('overview.html', 
                           uptime=uptime_str, cpu=cpu_usage,
                           mem_used=mem_used, mem_total=mem_total,
                           disk_used=disk_used, disk_total=disk_total,
                           is_online=is_online, tps=tps,
                           players_online=players_online, version=version)

@app.route('/action/<action>', methods=['POST'])
def perform_action(action):
    if action == 'clear_weather':
        run_rcon("weather clear")
    elif action == 'time_day':
        run_rcon("time set day")
    elif action == 'time_night':
        run_rcon("time set night")
    elif action == 'save_all':
        run_rcon("save-all")
    elif action == 'broadcast':
        msg = request.form.get('message', '')
        if msg:
            run_rcon(f'say {msg}')
    return redirect(url_for('overview'))

@app.route('/files', methods=['GET'])
def list_files():
    path = request.args.get('path', MC_DATA_PATH)
    # Security: prevent path traversal out of MC_DATA_PATH
    real_path = os.path.realpath(path)
    real_base = os.path.realpath(MC_DATA_PATH)
    if not real_path.startswith(real_base):
        path = MC_DATA_PATH
    
    items = []
    parent_path = os.path.dirname(real_path) if real_path != real_base else None
    
    if os.path.exists(real_path):
        for item in os.scandir(real_path):
            stat = item.stat()
            items.append({
                'name': item.name,
                'path': item.path,
                'is_dir': item.is_dir(),
                'size_raw': stat.st_size if not item.is_dir() else 0,
                'size': format_size(stat.st_size) if not item.is_dir() else '-',
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })
    
    items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
    return render_template('files.html', items=items, current_path=real_path, parent_path=parent_path, base_path=real_base)

@app.route('/download')
def download_file():
    path = request.args.get('path')
    if os.path.exists(path) and os.path.isfile(path):
        return send_file(path, as_attachment=True)
    return "File not found", 404

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    path = request.form.get('path', MC_DATA_PATH)
    if file and file.filename:
        file.save(os.path.join(path, file.filename))
    return redirect(url_for('list_files', path=path))

@app.route('/delete', methods=['POST'])
def delete_file():
    path = request.form.get('path')
    if os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    return redirect(url_for('list_files', path=os.path.dirname(path)))

@app.route('/edit', methods=['GET', 'POST'])
def edit_file():
    path = request.args.get('path')
    if not path or not os.path.exists(path):
        return "File not found", 404
        
    if request.method == 'POST':
        content = request.form.get('content', '')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        flash("File saved successfully!")
        return redirect(url_for('edit_file', path=path))
        
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    return render_template('edit.html', content=content, path=path)

@app.route('/players')
def players():
    ops = []
    whitelist = []
    banned = []
    cache = []
    
    def load_json(name):
        fpath = os.path.join(MC_DATA_PATH, name)
        if os.path.exists(fpath):
            try:
                with open(fpath, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []

    ops = load_json('ops.json')
    whitelist = load_json('whitelist.json')
    banned = load_json('banned-players.json')
    cache = load_json('usercache.json')
    
    ops_uuids = [o.get('uuid') for o in ops]
    whitelist_uuids = [w.get('uuid') for w in whitelist]
    banned_uuids = [b.get('uuid') for b in banned]
    
    # We use usercache as the primary list of known players
    player_list = []
    for p in cache:
        uuid = p.get('uuid')
        player_list.append({
            'name': p.get('name'),
            'uuid': uuid,
            'is_op': uuid in ops_uuids,
            'is_whitelisted': uuid in whitelist_uuids,
            'is_banned': uuid in banned_uuids,
            'expiresOn': str(p.get('expiresOn', ''))
        })
        
    return render_template('players.html', players=player_list)

@app.route('/rcon', methods=['POST'])
def rcon_action():
    cmd = request.form.get('command')
    redirect_url = request.form.get('redirect', url_for('overview'))
    if cmd:
        run_rcon(cmd)
    return redirect(redirect_url)

@app.route('/console')
def console():
    return render_template('console.html')

@app.route('/console/logs')
def get_logs():
    log_path = os.path.join(MC_DATA_PATH, 'logs', 'latest.log')
    try:
        with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()[-100:]
            return jsonify({'lines': lines})
    except:
        return jsonify({'lines': ['Server is offline or log file missing.']})

@app.route('/console/command', methods=['POST'])
def console_command():
    cmd = request.json.get('command', '') if request.is_json else request.form.get('command', '')
    if cmd:
        result = run_rcon(cmd)
        return jsonify({'result': result})
    return jsonify({'result': ''})

@app.route('/worlds')
def worlds():
    world_dirs = ['world', 'world_nether', 'world_the_end', 'world/DIM-1', 'world/DIM1']
    worlds_data = []
    for d in world_dirs:
        w_path = os.path.join(MC_DATA_PATH, d)
        if os.path.exists(w_path) and os.path.isdir(w_path):
            total_size = 0
            for dirpath, _, filenames in os.walk(w_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if not os.path.islink(fp):
                        total_size += os.path.getsize(fp)
            worlds_data.append({
                'name': d,
                'path': w_path,
                'size': format_size(total_size),
                'modified': datetime.fromtimestamp(os.stat(w_path).st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })
    return render_template('worlds.html', worlds=worlds_data)

@app.route('/worlds/download')
def download_world():
    world_path = request.args.get('path')
    if world_path and os.path.exists(world_path):
        name = os.path.basename(world_path.strip('/'))
        zip_path = f'/tmp/{name}_backup.zip'
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(world_path):
                for file in files:
                    fp = os.path.join(root, file)
                    zf.write(fp, os.path.relpath(fp, world_path))
        return send_file(zip_path, as_attachment=True, download_name=f'{name}_backup.zip')
    return "World not found", 404

@app.route('/options', methods=['GET', 'POST'])
def options():
    props_file = os.path.join(MC_DATA_PATH, 'server.properties')
    if request.method == 'POST':
        # Simple string replacement for properties
        try:
            with open(props_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            with open(props_file, 'w', encoding='utf-8') as f:
                for line in lines:
                    if '=' in line and not line.startswith('#'):
                        key = line.split('=')[0].strip()
                        if key in request.form:
                            f.write(f"{key}={request.form[key]}\n")
                            continue
                    f.write(line)
            # Apply changes by running a save or reload
            run_rcon("reload")
            flash("Settings saved.")
        except Exception as e:
            flash(f"Error saving: {str(e)}")
            
        return redirect(url_for('options'))

    props = {}
    if os.path.exists(props_file):
        with open(props_file, 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    k, v = line.strip().split('=', 1)
                    props[k] = v

    return render_template('options.html', props=props)

@app.route('/backups')
def backups():
    backups_dir = os.path.join(MC_DATA_PATH, 'backups')
    os.makedirs(backups_dir, exist_ok=True)
    items = []
    
    for item in os.scandir(backups_dir):
        if item.is_file() and item.name.endswith('.zip'):
            stat = item.stat()
            items.append({
                'name': item.name,
                'path': item.path,
                'size': format_size(stat.st_size),
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })
    items.sort(key=lambda x: x['modified'], reverse=True)
    return render_template('backups.html', backups=items)

@app.route('/backups/create', methods=['POST'])
def create_backup():
    backups_dir = os.path.join(MC_DATA_PATH, 'backups')
    world_dir = os.path.join(MC_DATA_PATH, 'world')
    os.makedirs(backups_dir, exist_ok=True)
    
    if os.path.exists(world_dir):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_name = f'backup_{timestamp}.zip'
        zip_path = os.path.join(backups_dir, zip_name)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(world_dir):
                for file in files:
                    filepath = os.path.join(root, file)
                    zf.write(filepath, os.path.relpath(filepath, MC_DATA_PATH))
    return redirect(url_for('backups'))

@app.route('/network')
def network():
    return render_template('network.html', rcon_port=RCON_PORT)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"[DASHBOARD] Starting Flask on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
