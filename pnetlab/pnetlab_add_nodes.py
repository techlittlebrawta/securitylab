import logging
from pnetlab_main_script import PNetLabClient

def main():
    base_url = "http://192.168.1.252"
    user = 'LabNodeManager'
    passwd = 'pnet'

    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    try:
        # Instantiate the client
        client = PNetLabClient(base_url, user, passwd)
        client.authenticate()

        # List available templates
        templates = client.list_available_templates()

        # If templates are available, add nodes
        if templates:
            # Allow user to select a template
            selected_template_id = input("Enter the Template ID to use: ")
            base_node_name = input("Enter the base name for the new node: ")

            # Ask for the number of nodes (default to 1 if none provided)
            try:
                node_count = int(input("Enter the number of nodes to add (default is 1): ") or "1")
            except ValueError:
                node_count = 1  # Fallback to default if user input is invalid

            # Fetch the default payload for the selected template
            payload = client.get_template_payload(selected_template_id)
            if payload:
                # Loop to add multiple nodes
                for i in range(1, node_count + 1):
                    # Format the node name with two digits, using `-01`, `-02`, etc.
                    node_name = f"{base_node_name}-{i:02d}"
                    payload['name'] = node_name  # Update the node name for each instance

                    print(f"Adding node '{node_name}' using template ID: {selected_template_id}")
                    client.add_node(payload)

            else:
                print("Failed to fetch the default payload for the selected template.")
        else:
            print("No templates available to add nodes.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
