# pnetlab_start_all_nodes.py
import requests
import json
from tabulate import tabulate
from pnetlab_main_script import PNetLabClient

def main():
    base_url = "http://192.168.1.252"
    user = 'LabNodeManager'
    passwd = 'pnet'

    client = PNetLabClient(base_url, user, passwd)
    client.authenticate()

    # List nodes
    nodes_response = client.list_nodes().json()
    nodes = [[node["name"], node["id"], node["url"]] for node in nodes_response["data"]["nodes"].values()]

    # Get all nodes status
    status_response = client.get_all_nodes_status()
    if status_response:
        # Map status codes to descriptions
        status_map = {0: "Powered Off", 2: "Powered On"}

        # Combine node details with their status
        combined_data = []
        nodes_to_start = [node_id for node_id, status in status_response["data"].items() if status == 0]

        if nodes_to_start:
            for node_id in nodes_to_start:
                response = client.start_node(node_id)
                if response.status_code == 200:
                    print(f"Node {node_id} started successfully")
                else:
                    print(f"Failed to start node {node_id}. Status code: {response.status_code}, Message: {response.text}")
        else:
            print("No nodes are Powered Off. No nodes started.")

        # Update the combined data with the latest statuses
        for node in nodes:
            node_id = node[1]
            status = status_map.get(status_response["data"].get(str(node_id), 0), "unknown")
            combined_data.append(node + [status])

        # Print the combined node information
        headers = ["Name", "ID", "URL", "Status"]
        print("\n--------------------------- Node Details -------------------------------\n")
        print(tabulate(combined_data, headers))
    else:
        print("Failed to retrieve nodes status. No table displayed.")

if __name__ == "__main__":
    main()
