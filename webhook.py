from flask import Flask, request, jsonify
import subprocess
import os

class WebhookManager:
    def __init__(self):
        self.app = Flask(__name__)
        self.port = 8080
        self.app_dir = "/home/romaerror5/Desktop/devops/catty-reminders-app"
        self.service_name = "catty-app"
        self.env_file = "/home/romaerror5/Desktop/devops/catty-reminders-app/.env"
        self._register_routes()
    
    def _register_routes(self):
        self.app.route('/', methods=['GET', 'POST'])(self.handle_request)
    
    def handle_request(self):
        if request.method == 'GET':
            return jsonify({"message": "Webhook handler running"}), 200
        
        if request.headers.get('X-GitHub-Event') == 'push':
            payload = request.json
            commit_sha = payload.get('after') if payload else None
            
            if not commit_sha or commit_sha == '0' * 40:
                return jsonify({"message": "No valid SHA"}), 200
            
            self._deploy(commit_sha)
            return jsonify({"message": "Deployment completed"}), 200
        
        return jsonify({"message": "Not a push event"}), 200
    
    def _deploy(self, sha):
        print(">>> Starting deployment...")
        
        subprocess.run(["git", "-C", self.app_dir, "pull"], check=True)
        print(">>> Code updated")
        
        with open(self.env_file, "w") as f:
            f.write(f"DEPLOY_REF={sha}")
        print(f">>> DEPLOY_REF written: {sha}")
        
        subprocess.run(["sudo", "systemctl", "restart", self.service_name], check=True)
        print(">>> Service restarted")
    
    def run(self):
        self.app.run(host='0.0.0.0', port=self.port)

if __name__ == "__main__":
    manager = WebhookManager()
    manager.run()