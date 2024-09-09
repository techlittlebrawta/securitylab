# pnetlab_wipe_all_nodes.py
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
        
        # Stop all nodes that are powered on
        nodes_to_stop = [node_id for node_id, status in status_response["data"].items() if status == 2]
        
        if nodes_to_stop:
            for node_id in nodes_to_stop:
                response = client.stop_node(node_id)
                if response.status_code == 200:
                    print(f"Node {node_id} stopped successfully")
                else:
                    print(f"Failed to stop node {node_id}. Status code: {response.status_code}, Message: {response.text}")
        else:
            print("No nodes are Powered On. No nodes stopped.")

        # Wipe all nodes after stopping them
        print("\nProceeding to wipe all nodes...")
        client.wipe_all_nodes()

        # Re-fetch the updated node status after wipe
        updated_status_response = client.get_all_nodes_status()
        if updated_status_response:
            # Update the combined data with the latest statuses
            combined_data = []
            for node in nodes:
                node_id = node[1]
                status = status_map.get(updated_status_response["data"].get(str(node_id), 0), "unknown")
                combined_data.append(node + [status])
            
            # Print the combined node information
            headers = ["Name", "ID", "URL", "Status"]
            print("\n--------------------------- Node Details -------------------------------\n")
            print(tabulate(combined_data, headers))
        else:
            print("Failed to retrieve updated nodes status. No table displayed.")
    else:
        print("Failed to retrieve nodes status. No table displayed.")

if __name__ == "__main__":
    main()
