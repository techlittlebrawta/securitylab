#!/usr/bin/python3
import sys
import requests
from veracode_api_signing.plugin_requests import RequestsAuthPluginVeracodeHMAC
from datetime import datetime
import os
import json
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)

# Veracode API base URL for listing applications
API_BASE = "https://api.veracode.com/appsec/v1/applications"

# Headers for API requests
HEADERS = {"User-Agent": "Python HMAC Example"}

# Maximum number of retries for API requests
MAX_RETRIES = 5

# Delay between retries in seconds
DELAY = 5

# Function to make API request
def make_api_request(url):
    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = requests.get(url, auth=RequestsAuthPluginVeracodeHMAC(), headers=HEADERS)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            if response.status_code == 429:  # Rate limit error
                logging.warning(f"Rate limit reached. Retrying in {DELAY} seconds...")
                time.sleep(DELAY)
                retries += 1
            else:
                logging.error(f"Error occurred while making API request to {url}: {e}")
                raise
    logging.error(f"Failed to make API request to {url} after {MAX_RETRIES} retries.")
    return None

# Function to get all applications
def get_all_applications():
    url = API_BASE
    applications = []
    while url:
        response = make_api_request(url)
        if not response or "_embedded" not in response:
            logging.error("No Veracode applications found.")
            return []
        applications.extend(response["_embedded"]["applications"])
        # Check for next page
        url = response["_links"].get("next", {}).get("href")
    return applications

# Function to get findings
def get_findings(application_guid):
    url = f"https://api.veracode.com/appsec/v2/applications/{application_guid}/findings?size=500"
    findings = []
    while url:
        response = make_api_request(url)
        if not response or "_embedded" not in response:
            logging.error(f"No findings found for application with GUID: {application_guid}")
            return None
        findings.extend(response["_embedded"]["findings"])
        # Check for next page
        url = response["_links"].get("next", {}).get("href")
    return findings

# Function to sanitize filename
def sanitize_filename(filename):
    filename = filename.replace('_', ' ')  # replace underscores with spaces
    return "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_')).rstrip()

# Function to save findings as JSON
def save_findings_as_json(application_name, findings):
    try:
        dirpath = "/opt/splunk/etc/apps/TA-veracode/data/"
        sanitized_app_name = sanitize_filename(application_name)
        filename = f"{sanitized_app_name}.json"
        filepath = os.path.join(dirpath, filename)
        with open(filepath, "w") as f:
            json.dump(findings if findings else {}, f, indent=4)
        logging.info(f"Veracode findings for {application_name} saved to: {filepath}")
    except FileNotFoundError as e:
        logging.error(f"Directory not found: {e}")
    except IOError as e:
        logging.error(f"IOError occurred while saving findings: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

# Main function
def main():
    applications = get_all_applications()
    if not applications:
        sys.exit(1)
    for application in applications:
        application_guid = application["guid"]
        application_name = application["profile"]["name"]
        findings = get_findings(application_guid)
        save_findings_as_json(application_name, findings)

# Entry point
if __name__ == "__main__":
    main()
