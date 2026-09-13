from flask import Flask, request, jsonify
from flask_cors import CORS
import paramiko
import time

app = Flask(__name__)
CORS(app)

ROUTER_USERNAME = "admin"
ROUTER_PASSWORD = "cisco"

def ssh_to_router(router_ip, command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        port = 22
        if ':' in router_ip:
            router_ip, port = router_ip.split(':')
            port = int(port)
        
        client.connect(
            hostname=router_ip,
            port=port,
            username=ROUTER_USERNAME,
            password=ROUTER_PASSWORD,
            look_for_keys=False,
            allow_agent=False,
            timeout=10
        )
        
        shell = client.invoke_shell()
        time.sleep(1)
        
        if shell.recv_ready():
            shell.recv(65535)
        
        shell.send(command + "\n")
        time.sleep(2)
        
        output = ""
        while shell.recv_ready():
            output += shell.recv(65535).decode('utf-8', errors='ignore')
            time.sleep(0.5)
        
        client.close()
        return output
        
    except Exception as e:
        client.close()
        raise Exception(f"SSH connection failed: {str(e)}")

@app.route('/api/execute', methods=['POST'])
def execute():
    data = request.get_json()
    
    if not data or 'router_ip' not in data or 'command' not in data:
        return jsonify({"status": "error", "error": "Missing router_ip or command"}), 400
    
    router_ip = data['router_ip']
    command = data['command']
    
    try:
        output = ssh_to_router(router_ip, command)
        return jsonify({"status": "success", "output": output})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
