import requests
import json
from tabulate import tabulate
from urllib.parse import unquote

class PNetLabClient:
    def __init__(self, base_url, user, passwd):
        self.base_url = base_url
        self.user = user
        self.passwd = passwd
        self.cookies = None
        self.xsrf_token = None

    def authenticate(self):
        auth_url = f"{self.base_url}/store/public/auth/login/login"
        headers = {'Content-Type': 'application/json;charset=UTF-8'}
        
        initial_response = requests.get(self.base_url, headers=headers, verify=False)
        xsrf_token = unquote(initial_response.cookies.get("XSRF-TOKEN", ""))
        session_cookie = unquote(initial_response.cookies.get("_session", ""))
        
        headers.update({
            'X-XSRF-TOKEN': xsrf_token,
            'Cookie': f'_session={session_cookie};XSRF-TOKEN={xsrf_token}'
        })
        
        payload = json.dumps({'username': self.user, 'password': self.passwd, 'html': '0', 'captcha': ''})
        auth_response = requests.post(auth_url, headers=headers, data=payload, verify=False)
        
        if auth_response.status_code == 202:
            print("Authentication successful")
            self.cookies = auth_response.cookies
            self.xsrf_token = xsrf_token
        else:
            raise Exception("Authentication failed")

    def retrieve_data(self, endpoint, page_num=1, page_size=25, sort_by="lab_session_id"):
        headers = {'Content-Type': 'application/json;charset=UTF-8'}
        if self.xsrf_token:
            headers['X-XSRF-TOKEN'] = self.xsrf_token
        
        payload = json.dumps({
            "data": {
                "page_number": page_num,
                "page_quantity": page_size,
                "page_total": 0,
                "flag_filter_change": True,
                "flag_filter_logic": "and",
                "data_sort": {sort_by: "desc"},
                "data_filter": {}
            }
        })
        
        response = requests.post(f"{self.base_url}/store/public/admin/{endpoint}/filter", headers=headers, data=payload, cookies=self.cookies, verify=False)
        return response

    def count_items(self, endpoint):
        response = requests.get(f"{self.base_url}/store/public/admin/{endpoint}/count", headers={'Content-Type': 'application/json'}, cookies=self.cookies, verify=False)
        return response

    def join_lab_session(self, session_id):
        payload = json.dumps({"lab_session": str(session_id)})
        response = requests.post(f"{self.base_url}/api/labs/session/factory/join", data=payload, headers={'Content-Type': 'application/json'}, cookies=self.cookies, verify=False)
        return response

    def list_nodes(self):
        response = requests.get(f"{self.base_url}/api/labs/session/topology", headers={'Content-Type': 'application/json'}, cookies=self.cookies, verify=False)
        return response

    def start_node(self, node_id):
        node_payload = json.dumps({"id": str(node_id)})
        response = requests.post(f"{self.base_url}/api/labs/session/nodes/start", headers={'Content-Type': 'application/json'}, data=node_payload, cookies=self.cookies, verify=False)
        return response

    def stop_node(self, node_id):
        node_payload = json.dumps({"id": str(node_id)})
        response = requests.post(f"{self.base_url}/api/labs/session/nodes/stop", headers={'Content-Type': 'application/json'}, data=node_payload, cookies=self.cookies, verify=False)
        return response

    def start_all_nodes(self):
        # Retrieve node statuses
        status_response = self.get_all_nodes_status()
        if status_response:
            status_map = {0: "Powered Off", 2: "Powered On"}
            nodes_to_start = [node_id for node_id, status in status_response["data"].items() if status == 0]
            
            if nodes_to_start:
                for node_id in nodes_to_start:
                    self.start_node(node_id)
            else:
                print("No nodes are Powered Off. No nodes started.")
        else:
            print("Failed to retrieve nodes status. Cannot start nodes.")

    def stop_all_nodes(self):
        # Retrieve node statuses
        status_response = self.get_all_nodes_status()
        if status_response:
            status_map = {0: "Powered Off", 2: "Powered On"}
            nodes_to_stop = [node_id for node_id, status in status_response["data"].items() if status == 2]
            
            if nodes_to_stop:
                for node_id in nodes_to_stop:
                    self.stop_node(node_id)
            else:
                print("No nodes are Powered On. No nodes stopped.")
        else:
            print("Failed to retrieve nodes status. Cannot stop nodes.")

    def get_all_nodes_status(self):
        status_url = f"{self.base_url}/api/labs/session/nodestatus"
        headers = {'Content-Type': 'application/json'}
        
        try:
            response = requests.post(status_url, headers=headers, cookies=self.cookies, verify=False)
            response.raise_for_status()
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Unexpected status code: {response.status_code}")
                print(f"Response message: {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def wipe_all_nodes(self):
        # Retrieve node details and wipe each one
        node_list_response = self.list_nodes()
        
        if node_list_response.status_code == 200:
            nodes_data = node_list_response.json()["data"]["nodes"]
            node_ids = [node["id"] for node in nodes_data.values()]
            
            if node_ids:
                print(f"Found {len(node_ids)} nodes. Starting to wipe all nodes...")
                for node_id in node_ids:
                    wipe_payload = json.dumps({"id": str(node_id)})
                    wipe_response = requests.post(f"{self.base_url}/api/labs/session/nodes/wipe", headers={'Content-Type': 'application/json'}, data=wipe_payload, cookies=self.cookies, verify=False)
                    
                    if wipe_response.status_code == 200:
                        print(f"Node {node_id} wiped successfully")
                    else:
                        print(f"Failed to wipe node {node_id}. Status code: {wipe_response.status_code}, Message: {wipe_response.text}")
            else:
                print("No nodes found to wipe.")
        else:
            print(f"Failed to retrieve nodes. Status code: {node_list_response.status_code}, Message: {node_list_response.text}")

    def sign_out(self):
        response = requests.get(f"{self.base_url}/api/auth/logout", cookies=self.cookies, verify=False)
        if response.status_code == 200:
            print("Signed out successfully")

    def print_node_table(self, nodes, status_response):
        status_map = {0: "Powered Off", 2: "Powered On"}
        
        # Combine node details with their status
        combined_data = []
        for node in nodes:
            node_id = node[1]
            status = status_map.get(status_response["data"].get(str(node_id), "unknown"), "unknown")
            combined_data.append(node + [status])

        # Print the combined node information
        headers = ["Name", "ID", "URL", "Status"]
        print("\n--------------------------- Node Details -------------------------------\n")
        print(tabulate(combined_data, headers))

    def add_node(self, payload):
        """ Add a node based on the provided payload """
        add_node_url = f"{self.base_url}/api/labs/session/nodes/add"
        headers = {'Content-Type': 'application/json'}
        try:
            print(f"Payload: {json.dumps(payload, indent=2)}")  # Log the payload
            response = requests.post(add_node_url, headers=headers, cookies=self.cookies, data=json.dumps(payload), verify=False)
            response.raise_for_status()

            if response.status_code == 201:
                print(f"Node '{payload['name']}' added successfully using template ID: {payload['template']}")
            else:
                print(f"Unexpected status code: {response.status_code}. Response: {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"Failed to add node: {e}")

    def list_available_templates(self):
        template_url = f"{self.base_url}/api/list/templates/"
        try:
            response = requests.get(template_url, cookies=self.cookies, verify=False)
            response.raise_for_status()

            templates = response.json()
            if 'data' in templates:
                if isinstance(templates['data'], dict):
                    filtered_templates = {k: v for k, v in templates['data'].items() if ".missing" not in v}
                elif isinstance(templates['data'], list):
                    filtered_templates = [t for t in templates['data'] if ".missing" not in t.get('name', '')]
                else:
                    print("Unexpected template data structure.")
                    return None
                
                print("Available Templates:")
                for template in filtered_templates:
                    if isinstance(template, dict):
                        print(f"Template: {template.get('name', 'Unknown')}, ID: {template.get('id', 'Unknown')}")
                    else:
                        print(f"Template ID: {template}, Name: {filtered_templates[template]}")
                
                return filtered_templates
            else:
                print("No templates found or unexpected response structure.")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Failed to list templates: {e}")
            return None

    def get_template_payload(self, template_id):
        payload_url = f"{self.base_url}/api/list/templates/{template_id}"
        try:
            response = requests.get(payload_url, cookies=self.cookies, verify=False)
            response.raise_for_status()
            payload = response.json()
            
            # Extract only the key and value pairs
            extracted_payload = {key: value['value'] for key, value in payload['data']['options'].items()}
            
            return extracted_payload
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch template payload: {e}")
            return None