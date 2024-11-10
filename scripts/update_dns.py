import os
import csv
import logging
from datetime import datetime
import subprocess
from typing import Dict, Tuple

# Configure logging with both file and console output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dns_updates.log'),
        logging.StreamHandler()
    ]
)

def get_command_path(command: str) -> str:
    # Finds the full path of system commands dig and nsupdate
    try:
        result = subprocess.run(['which', command], 
                              capture_output=True, 
                              text=True, 
                              check=True)
        path = result.stdout.strip()
        logging.info(f"Found {command} at: {path}")
        return path
    except subprocess.CalledProcessError:
        error_msg = f"Command '{command}' not found in PATH"
        logging.error(error_msg)
        raise FileNotFoundError(error_msg)

class DNSUpdater:
    def __init__(self, csv_file: str, tsig_key: str, dns_server: str):
        self.csv_file = csv_file
        self.tsig_key = tsig_key
        self.dns_server = dns_server
        self.zone = "ib.bigbank.com"
        logging.info(f"Initialized DNSUpdater with server: {dns_server}, key: {tsig_key}")

    def read_current_records(self) -> Dict[str, str]:
        # Read current DNS records using dig
        try:
            dig_path = get_command_path('dig')
            # Execute dig command for zone transfer
            cmd = f"{dig_path} @{self.dns_server} axfr {self.zone}"
            logging.info(f"Executing dig command: {cmd}")
            
            result = subprocess.run(cmd.split(), 
                                  capture_output=True, 
                                  text=True,
                                  check=True)
            
            if result.stderr:
                logging.warning(f"dig stderr output: {result.stderr}")
             # Parse results into dictionary
            records = {}
            for line in result.stdout.splitlines():
                if "IN A" in line:
                    parts = line.split()
                    fqdn, ip = parts[0], parts[-1]
                    records[fqdn] = ip
                    logging.debug(f"Found existing record: {fqdn} -> {ip}")
            
            logging.info(f"Found {len(records)} existing DNS records")
            return records
        except Exception as e:
            logging.error(f"Error reading current records: {e}")
            return {}

    def read_csv_records(self) -> Dict[str, str]:
        # Read records from the CSV file
        records = {}
        try:
            logging.info(f"Reading CSV file: {self.csv_file}")
            with open(self.csv_file, mode='r') as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    if len(row) >= 2:
                        fqdn, ipv4 = row[0].strip(), row[1].strip()
                        records[fqdn] = ipv4
                        logging.debug(f"Read from CSV: {fqdn} -> {ipv4}")
            
            logging.info(f"Read {len(records)} records from CSV")
            return records
        except Exception as e:
            logging.error(f"Error reading CSV file: {e}")
            return {}

    def update_record(self, fqdn: str, ipv4: str) -> bool:
        # Update a single DNS record using nsupdate
        try:
            # Prepare nsupdate command
            nsupdate_path = get_command_path('nsupdate')
            nsupdate_cmd = f"""
            server {self.dns_server}
            zone {self.zone}
            update delete {fqdn} A
            update add {fqdn} 3600 A {ipv4}
            send
            """
            logging.info(f"Attempting to update record: {fqdn} -> {ipv4}")
            logging.debug(f"Using key file: {self.tsig_key}")
            logging.debug(f"nsupdate command:\n{nsupdate_cmd}")

            # Verify key file exists and is readable
            if not os.path.isfile(self.tsig_key):
                logging.error(f"TSIG key file not found: {self.tsig_key}")
                return False

            # Execute nsupdate command
            process = subprocess.run(
                [nsupdate_path, '-k', self.tsig_key],
                input=nsupdate_cmd,
                text=True,
                capture_output=True,
                check=True
            )

            if process.stderr:
                logging.warning(f"nsupdate stderr for {fqdn}: {process.stderr}")
            
            logging.info(f"Successfully updated record: {fqdn} -> {ipv4}")
            return True

        except subprocess.CalledProcessError as e:
            logging.error(f"nsupdate command failed for {fqdn}: {e.stderr}")
            return False
        except Exception as e:
            logging.error(f"Error updating {fqdn}: {str(e)}")
            return False
    
    # Synchronize DNS records with the CSV file
    def sync_records(self):
        logging.info("Starting DNS record synchronization")
        # Get current and desired states
        current_records = self.read_current_records()
        desired_records = self.read_csv_records()

        # Calculate differences
        to_add = {k: v for k, v in desired_records.items() 
                 if k not in current_records or current_records[k] != v}
        to_delete = {k: v for k, v in current_records.items() 
                    if k not in desired_records}

        logging.info(f"Found {len(to_add)} records to add/update and {len(to_delete)} to delete")

        # Update records
        success_count = 0
        for fqdn, ipv4 in to_add.items():
            if self.update_record(fqdn, ipv4):
                success_count += 1
                logging.info(f"Updated record: {fqdn} -> {ipv4}")
            else:
                logging.error(f"Failed to update record: {fqdn}")

        # Delete records
        for fqdn in to_delete:
            if self.update_record(fqdn, "0.0.0.0"):
                success_count += 1
                logging.info(f"Deleted record: {fqdn}")
            else:
                logging.error(f"Failed to delete record: {fqdn}")

        logging.info(f"Synchronization completed. Successfully processed {success_count} records")

def main():
    logging.info("Starting DNS update process")
    
    # Initialize DNSUpdater with environment variables
    dns_updater = DNSUpdater(
        csv_file=os.getenv('CSV_FILE', 'dns-records.csv'),
        tsig_key=os.getenv('TSIG_KEY', '/etc/bind/rndc.key'),
        dns_server=os.getenv('DNS_SERVER', '172.20.0.2')
    )
    
    try:
        # Run synchronization
        dns_updater.sync_records()
    except Exception as e:
        logging.error(f"Fatal error during DNS update process: {e}")
        raise

if __name__ == '__main__':
    main()