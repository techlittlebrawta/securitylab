import logging
from pnetlab_main_script import PNetLabClient

# Define a dictionary to map template prefixes or full names to custom configurations
template_configurations = {
    'vsrx': {'ram': 8192, 'ethernet': 8},
    'windows': {'ram': 16384, 'ethernet': 4},
    'cisco': {'ram': 4096, 'ethernet': 2},
    'linux': {'ram': 2048, 'ethernet': 1},
    # Add more template mappings as needed
}

def get_template_configuration(template_id):
    """Get the configuration for a template based on its prefix."""
    # Iterate over the template configurations dictionary
    for prefix, config in template_configurations.items():
        # If the template ID starts with the prefix, return the corresponding config
        if template_id.startswith(prefix):
            return config
    # Return None if no matching configuration is found
    return None

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

                # Get the custom configuration based on template ID prefix
                config = get_template_configuration(selected_template_id)
                
                if config:
                    # Apply the custom configuration for the selected template
                    payload['ram'] = config['ram']  # Set custom RAM
                    payload['ethernet'] = config['ethernet']  # Set custom Ethernet

                    logging.info(f"Applying custom specs for template '{selected_template_id}': RAM={config['ram']}MB, Ethernet={config['ethernet']} interfaces")
                else:
                    logging.info(f"No custom specs found for template '{selected_template_id}'. Using default specs.")

                # Add the node with the updated payload
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
