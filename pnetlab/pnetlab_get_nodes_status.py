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

    # Retrieve node statuses
    status_response = client.get_all_nodes_status()
    if status_response:
        print("\n--------------------------- Node Details -------------------------------\n")
        client.print_node_table(nodes, status_response)
    else:
        print("Failed to retrieve nodes status.")

if __name__ == "__main__":
    main()
