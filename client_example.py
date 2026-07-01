#!/usr/bin/env python3
"""
Example script demonstrating the new SQLite-backed multi-project LLMwiki API.

This shows how to:
1. Register and authenticate
2. Create projects
3. Upload raw documents
4. Ingest documents into wiki
5. Query the wiki
6. Share projects with other users
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:8000"
GEMINI_MODEL = "gemini-flash-lite-latest"

class LLMWikiClient:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.headers = {"Content-Type": "application/json"}
    
    def _request(self, method, endpoint, data=None, files=None):
        """Helper for API requests"""
        url = f"{self.base_url}{endpoint}"
        headers = self.headers.copy()
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        if method == "GET":
            resp = requests.get(url, headers=headers)
        elif method == "POST":
            if files:
                del headers["Content-Type"]  # Let requests handle multipart
                resp = requests.post(url, headers=headers, files=files)
            else:
                resp = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            resp = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            resp = requests.delete(url, headers=headers)
        
        return resp.json() if resp.text else {}
    
    def register(self, username, email, password):
        """Register a new user"""
        print(f"[*] Registering user: {username}")
        result = self._request("POST", "/api/auth/register", {
            "username": username,
            "email": email,
            "password": password
        })
        self.token = result.get("access_token")
        self.user_id = result.get("user", {}).get("id")
        print(f"[✓] Registered and logged in as {username}")
        return result
    
    def login(self, username, password):
        """Login an existing user"""
        print(f"[*] Logging in: {username}")
        result = self._request("POST", "/api/auth/login", {
            "username": username,
            "password": password
        })
        self.token = result.get("access_token")
        self.user_id = result.get("user", {}).get("id")
        print(f"[✓] Logged in as {username}")
        return result
    
    def get_current_user(self):
        """Get current authenticated user"""
        return self._request("GET", "/api/auth/me")
    
    def create_project(self, name, description=""):
        """Create a new wiki project"""
        print(f"[*] Creating project: {name}")
        result = self._request("POST", "/api/projects", {
            "name": name,
            "description": description
        })
        project_id = result.get("id")
        print(f"[✓] Project created with ID: {project_id}")
        return result
    
    def list_projects(self):
        """List all accessible projects"""
        print("[*] Fetching projects...")
        projects = self._request("GET", "/api/projects")
        print(f"[✓] Found {len(projects)} projects:")
        for p in projects:
            role = "Owner" if p.get("is_owner") else f"Member ({p.get('permission_level')})"
            print(f"  - {p['name']} (ID: {p['id']}) [{role}]")
        return projects
    
    def upload_raw_file(self, project_id, file_path):
        """Upload a raw document to a project"""
        print(f"[*] Uploading file: {file_path}")
        with open(file_path, "rb") as f:
            files = {"file": f}
            result = self._request("POST", f"/api/projects/{project_id}/files/raw/upload", files=files)
        print(f"[✓] File uploaded: {result.get('filename')}")
        return result
    
    def list_raw_files(self, project_id):
        """List raw documents in a project"""
        print(f"[*] Fetching raw files for project {project_id}...")
        files = self._request("GET", f"/api/projects/{project_id}/files/raw")
        print(f"[✓] Found {len(files)} raw files:")
        for f in files:
            print(f"  - {f['name']} ({f['size']} bytes)")
        return files
    
    def ingest_file(self, project_id, filename):
        """Ingest a raw file into the wiki"""
        print(f"[*] Ingesting file: {filename}")
        result = self._request("POST", f"/api/projects/{project_id}/ingest", {
            "filename": filename,
            "model": GEMINI_MODEL
        })
        print(f"[✓] Ingested: {result.get('summary')}")
        print(f"    Modified files: {len(result.get('modified_files', []))}")
        return result
    
    def query_wiki(self, project_id, question):
        """Query the wiki in a project"""
        print(f"[*] Querying: {question}")
        result = self._request("POST", f"/api/projects/{project_id}/query", {
            "question": question,
            "model": GEMINI_MODEL
        })
        print(f"[✓] Query complete")
        print(f"    Answer: {result.get('answer')[:200]}...")
        return result
    
    def list_wiki_pages(self, project_id):
        """List wiki pages in a project"""
        print(f"[*] Fetching wiki pages for project {project_id}...")
        pages = self._request("GET", f"/api/projects/{project_id}/files/wiki")
        print(f"[✓] Found {len(pages)} wiki pages:")
        for p in pages:
            print(f"  - {p['name']} ({p['size']} bytes)")
        return pages
    
    def share_project(self, project_id, username, permission="read_write"):
        """Share a project with another user"""
        print(f"[*] Sharing project {project_id} with {username} ({permission})")
        result = self._request("POST", f"/api/projects/{project_id}/share", {
            "username": username,
            "permission_level": permission
        })
        print(f"[✓] Project shared")
        return result
    
    def get_graph(self, project_id):
        """Get graph visualization data"""
        print(f"[*] Fetching graph data for project {project_id}...")
        graph = self._request("GET", f"/api/projects/{project_id}/graph")
        print(f"[✓] Graph has {len(graph.get('nodes', []))} nodes and {len(graph.get('links', []))} links")
        return graph


def demo():
    """Demo script showing typical workflow"""
    client = LLMWikiClient()
    
    # 1. Register/Login
    try:
        client.register("demo_user", "demo@example.com", "demo_password")
    except:
        print("[!] Registration failed, trying login...")
        client.login("demo_user", "demo_password")
    
    # 2. Create a project
    project = client.create_project("Demo Wiki", "Testing the new SQLite system")
    project_id = project["id"]
    
    # 3. List projects
    client.list_projects()
    
    # 4. Check current user
    user = client.get_current_user()
    print(f"[✓] Current user: {user.get('username')}")
    
    # 5. Try to share the project (would need another registered user)
    # client.share_project(project_id, "other_user", "read_write")
    
    # 6. List wiki pages
    client.list_wiki_pages(project_id)
    
    # 7. Get graph
    client.get_graph(project_id)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo()
    else:
        # Interactive usage
        client = LLMWikiClient()
        print("LLMwiki Multi-Project Client")
        print("=" * 40)
        print("Commands: register, login, create-project, list-projects, help")
        
        while True:
            try:
                cmd = input("\n> ").strip().split()
                if not cmd:
                    continue
                
                if cmd[0] == "register":
                    username, email, pwd = cmd[1], cmd[2], cmd[3]
                    client.register(username, email, pwd)
                elif cmd[0] == "login":
                    username, pwd = cmd[1], cmd[2]
                    client.login(username, pwd)
                elif cmd[0] == "create-project":
                    name = " ".join(cmd[1:])
                    client.create_project(name)
                elif cmd[0] == "list-projects":
                    client.list_projects()
                elif cmd[0] == "help":
                    print("Commands: register, login, create-project, list-projects, help, exit")
                elif cmd[0] == "exit":
                    break
                else:
                    print(f"Unknown command: {cmd[0]}")
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
