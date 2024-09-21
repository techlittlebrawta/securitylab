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
            node_name = input("Enter the name for the new node: ")

            # Fetch the default payload for the selected template
            payload = client.get_template_payload(selected_template_id)
            if payload:
                payload['name'] = node_name  # Update the node name in the payload

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
