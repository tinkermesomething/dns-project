#!/bin/sh

# Check if rndc.key exists
if [ ! -f /etc/bind/rndc.key ]; then
    echo "Generating a new TSIG key..."
    tsig-keygen -a hmac-sha256 rndc-key > /etc/bind/rndc.key
    chmod 644 /etc/bind/rndc.key
    echo "TSIG key generated successfully"
fi

# Start named in foreground
echo "Starting BIND9..."
exec named -g -c /etc/bind/named.conf