### Automation DNS Records Management ###

You are working in a team that is, amongst other things, responsible for the DNS records in a dedicated DNZ zone called ‘ib.bigbank.com’.
Since even small mistakes in DNS records can have significant consequences, the team has decided to automate the management ( creation, update, and deletion) of DNS records.
You’ve been tasked to come up with a proposal on how to automate the management of these DNS records. The only input to the automation will receive is a a simple CSV file with the following structure:
FQDN,IPv4
e.g.
machine1.mgmt.ib.bigbank.com, 172.16.1.50
machine1.ipmi.ib.bigbank.com, 172.16.20.50
machine1.ib.bigbank.com, 10.33.0.50
netapp1.svm.ib.bigbank.com, 192.168.47.11

The automation will be part of a pipeline that can be run at any time and will always take the latest version of above-mentioned CSV file as input.

As much as possible, the solution shall be idempotent (updating only records that have changed), and safe to use in a zone that contains existing records.

Please prepare a working PoC of the automation step (on your private laptop is ok) that can be demo’ed to the team.

Furthermore, submit a diagram that explains the solution along with the code beforehand.

### Folder structure ###

/ (Root repository)
│
├── .github/
│   └── workflows/
│       └── dns-update.yml          # GitHub Actions workflow file
│
├── scripts/
│   ├── validate_csv.py            # Python script to validate CSV
│   ├── update_dns.py              # Python script to update DNS records
│   └── requirements.txt           # Updated Python dependencies
│
├── data/
│   └── dns-records.csv            # CSV file containing DNS records
│
├── docker/
│   ├── docker-compose.yml         # Docker compose file to build bind9 DNS server and github runner
│   ├── config/                    # BIND9 configuration directory
│   │   ├── named.conf             # Main BIND9 configuration
│   │   ├── rndc.key               # TSIG key file
|   |   ├── endpoint.sh            # Script to create the TSIG key file inside the bind9 DNS server if it's not present 
│   │   └── zones/
│   │       └── ib.bigbank.com.zone  # DNS zone file
│   │
│   ├── cache/                     # BIND9 cache directory (mounted in container)
│   ├── records/                   # BIND9 records directory (mounted in container)
|   └── .env/                      # local-only environment file containing token and project variables
│
└── README.md                      # Project documentation             


