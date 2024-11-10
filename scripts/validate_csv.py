import csv
import sys

def validate_csv(file_path):
        # Validates the CSV file containing DNS records. Returns True if valid, False otherwise.
    try:
         # Open and read the CSV file
        with open(file_path, mode='r') as csv_file:
            csv_reader = csv.reader(csv_file)
            seen_fqdns = set()
             # Process each row in the CSV file
            for row in csv_reader:
                fqdn, ipv4 = row[0], row[1]
                
                # Check for duplicate FQDNs
                if fqdn in seen_fqdns:
                    print(f"Error: Duplicate FQDN found -> {fqdn}")
                    return False
                
                seen_fqdns.add(fqdn)

                # Simple IPv4 validation
                octets = ipv4.split('.')
                if len(octets) != 4 or not all(0 <= int(octet) <= 255 for octet in octets):
                    print(f"Error: Invalid IPv4 address -> {ipv4}")
                    return False
        # If all validations pass
        print("CSV validation passed.")
        return True

    except Exception as e:
        print(f"Error during validation: {e}")
        return False

if __name__ == "__main__":
    if not validate_csv(sys.argv[1]):
        sys.exit(1)  # Exit with error code if validation fails