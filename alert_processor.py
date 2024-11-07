import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from queue import Queue
import threading
import time
import dateutil.parser
import logging
import os
import re
import traceback

# Set up basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Queue to hold incoming alerts
alert_queue = Queue()
alert_queue_RAW = Queue()
processed_identifiers = set()

# File paths
API_INPUT_FILE = "api.xml"
API_FEED_FILE = "api_recent.xml"
API_CAP_OUTPUT_FILE = "recent.xml"
API_FEED_FILE_RAW = "api_feed.xml"
API_UPDATE_FILE_RAW = "api_update.xml"

# List to keep non-expired alerts
active_alerts = []
active_alerts_RAW = []

def filter_non_expired_alerts():
    """Filters non-expired alerts and updates the active alert lists."""
    current_time = datetime.now(timezone.utc)
    global active_alerts, active_alerts_RAW

    new_active_alerts = []
    new_active_alerts_RAW = []

    # Define the XML files to process
    xml_files = [API_FEED_FILE_RAW, API_UPDATE_FILE_RAW]
    namespace = {"atom": "http://www.w3.org/2005/Atom"}
    
    # Filter active alerts to keep only non-expired ones
    for alert, RAWDATA in zip(active_alerts, active_alerts_RAW):
        uriExists = False
        uri = ""
        
        # Extract resources and check for specific mime type
        resources = re.findall(r"<resource>\s*(.*?)\s*</resource>", RAWDATA, re.MULTILINE | re.IGNORECASE | re.DOTALL)
        for resource in resources:
            mimeType = re.search(r"<mimeType>\s*(.*?)\s*</mimeType>", resource, re.MULTILINE | re.IGNORECASE | re.DOTALL)
            if mimeType and mimeType.group(1) == "audio/x-ipaws-audio-mp3":
                uri_match = re.search(r"<uri>\s*(.*?)\s*</uri>", resource, re.MULTILINE | re.IGNORECASE | re.DOTALL)
                if uri_match:
                    uri = uri_match.group(1)
                    uriExists = True     

        uidExists = False
        eas_uid = ""
        # Extract EAS-UID
        parameters = re.findall(r"<parameter>\s*(.*?)\s*</parameter>", RAWDATA, re.MULTILINE | re.IGNORECASE | re.DOTALL)
        for param in parameters:
            valuename = re.search(r"<valuename>\s*(.*?)\s*</valuename>", param, re.MULTILINE | re.IGNORECASE | re.DOTALL)
            if(valuename and valuename.group(1) == "EAS-UID"):
                uid_match = re.search(r"<value>\s*(.*?)\s*</value>", param, re.MULTILINE | re.IGNORECASE | re.DOTALL)
                if uid_match:
                    eas_uid = uid_match.group(1)
                    uidExists = True

        expires_text = re.search(r"<expires>\s*(.*?)\s*</expires>", RAWDATA, re.MULTILINE | re.IGNORECASE | re.DOTALL)
        if expires_text:
            expires = dateutil.parser.parse(expires_text.group(1))
            if expires > current_time:
                new_active_alerts.append(alert)
                new_active_alerts_RAW.append(RAWDATA)
            else:
                # If the alert is expired and URI exists, delete the corresponding file in ./media/
                if uriExists:
                    file_path = f"./media/{uri.split('/')[-1]}"
                    if os.path.exists(file_path):
                        os.remove(file_path)
                
                if uidExists:
                    # If the alert is expired and EAS-UID exists, delete the corresponding file in ./Web/alerts
                    file_path = f"./Web/alerts/{eas_uid}"
                    if os.path.exists(file_path):
                        os.remove(file_path)
    
                    # Process each XML file to remove expired <entry> based on UID match
                    for xml_file in xml_files:
                        tree = ET.parse(xml_file)
                        root = tree.getroot()

                        for entry in root.findall("atom:entry", namespaces=namespace):
                            entry_id = entry.find("atom:id", namespaces=namespace)
                            if entry_id is not None and eas_uid in entry_id.text:
                                root.remove(entry)
                                break
                        
                        # Write the updated XML back to the file without ns0 prefix
                        ET.register_namespace('', "http://www.w3.org/2005/Atom")  # Prevent 'ns0' in output
                        tree.write(xml_file, encoding="utf-8", xml_declaration=False)

    active_alerts, active_alerts_RAW = new_active_alerts, new_active_alerts_RAW

def read_alerts_from_api():
    """Reads alerts from the API input file and adds new alerts to the queue."""
    try:
        time.sleep(1)  # Sleep to avoid frequent reads
        with open(API_INPUT_FILE, 'r') as file:
            RAWDATA = file.read()

        AlertList = re.findall(r'<alert xmlns="[^"]*" xmlns:ds="[^"]*">(.*?)</alert>', RAWDATA, re.MULTILINE | re.IGNORECASE | re.DOTALL)

        for alert in AlertList:
            identifier = re.search(r"<identifier>\s*(.*?)\s*</identifier>", alert, re.MULTILINE | re.IGNORECASE | re.DOTALL).group(1)

            if identifier in processed_identifiers:
                logging.info(f"Alert with identifier {identifier} has already been processed. Skipping.")
                continue

            expires_text = re.search(r"<expires>\s*(.*?)\s*</expires>", alert, re.MULTILINE | re.IGNORECASE | re.DOTALL).group(1)
            expires = dateutil.parser.parse(expires_text)
            if expires > datetime.now(timezone.utc):
                logging.info(f"Adding alert to active list: {identifier}")
                active_alerts.append(alert)
                active_alerts_RAW.append(RAWDATA)
                processed_identifiers.add(identifier)
            else:
                logging.info(f"Alert with identifier {identifier} has expired. Skipping.")
    except Exception as e:
        logging.error(f"An error occurred while reading alerts from {API_INPUT_FILE}: {e}")
        traceback.print_exc()

def process_alert_queue():
    """Processes the alert queue and writes non-expired alerts to the output file."""
    filter_non_expired_alerts()  # Remove expired alerts from active lists

    one_alert = False
    # Build the XML file content
    xml_file = '<ns1:alerts xmlns:ns1="http://localhost-ipaws.services/feed">'
    for alert in active_alerts_RAW:
        if len(active_alerts_RAW) == 1:
            xml_file = f"{alert}"
            one_alert = True
        else:
            xml_file += f"{alert}"
            one_alert = False

    xml_declaration = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    logging.info(f"Writing {len(active_alerts_RAW)} alerts to {API_FEED_FILE}.")
    
    with open(API_FEED_FILE, "w", encoding="UTF-8") as f:
        if one_alert:
            f.write(xml_declaration + xml_file)
        else:
            f.write(xml_declaration + xml_file + '</ns1:alerts>')

    os.system(f"cp {API_FEED_FILE} CAP/{API_CAP_OUTPUT_FILE}")

def background_processor():
    """Main loop for background processing of alerts."""
    while True:
        read_alerts_from_api()
        process_alert_queue()
        time.sleep(1)  # Update interval

def start_background_thread():
    """Starts the background thread for alert processing."""
    thread = threading.Thread(target=background_processor, daemon=True)
    thread.start()

if __name__ == "__main__":
    start_background_thread()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Shutting down alert processor.")
