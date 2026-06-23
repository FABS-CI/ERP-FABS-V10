#!/bin/bash

# TLS Certificate Generation Script
# Generates self-signed certificates for development
# For production, use Let's Encrypt / AWS ACM

set -e

CERT_DIR="${1:-.}"
CERT_NAME="${2:-localhost}"
DAYS="${3:-365}"

echo "🔐 Generating TLS Certificates"
echo "  Directory: $CERT_DIR"
echo "  Name: $CERT_NAME"
echo "  Valid for: $DAYS days"
echo ""

# Create directory if needed
mkdir -p "$CERT_DIR"

CERT_FILE="$CERT_DIR/$CERT_NAME.pem"
KEY_FILE="$CERT_DIR/$CERT_NAME-key.pem"
CA_CERT_FILE="$CERT_DIR/ca.pem"
CA_KEY_FILE="$CERT_DIR/ca-key.pem"

# Function to generate CA certificate
generate_ca() {
    echo "📋 Generating CA Certificate..."
    openssl genrsa -out "$CA_KEY_FILE" 4096 2>/dev/null
    
    openssl req -new -x509 -days $DAYS -key "$CA_KEY_FILE" -out "$CA_CERT_FILE" \
        -subj "/C=CI/ST=Abidjan/L=Abidjan/O=FABS-CI/CN=FABS-CA" 2>/dev/null
    
    echo "✅ CA Certificate: $CA_CERT_FILE"
    echo "✅ CA Key: $CA_KEY_FILE"
}

# Function to generate server certificate
generate_cert() {
    echo "📋 Generating Server Certificate..."
    
    # Generate private key
    openssl genrsa -out "$KEY_FILE" 4096 2>/dev/null
    
    # Create CSR
    openssl req -new -key "$KEY_FILE" -out /tmp/$CERT_NAME.csr \
        -subj "/C=CI/ST=Abidjan/L=Abidjan/O=FABS-CI/CN=$CERT_NAME" 2>/dev/null
    
    # Create certificate
    openssl x509 -req -days $DAYS -in /tmp/$CERT_NAME.csr \
        -CA "$CA_CERT_FILE" -CAkey "$CA_KEY_FILE" -CAcreateserial \
        -out "$CERT_FILE" \
        -extfile <(printf "subjectAltName=DNS:$CERT_NAME,DNS:localhost,IP:127.0.0.1") \
        2>/dev/null
    
    # Cleanup CSR
    rm -f /tmp/$CERT_NAME.csr
    
    echo "✅ Server Cert: $CERT_FILE"
    echo "✅ Server Key: $KEY_FILE"
}

# Check if OpenSSL is installed
if ! command -v openssl &> /dev/null; then
    echo "❌ openssl not found. Install with: apt-get install openssl"
    exit 1
fi

# Generate CA if not exists
if [ ! -f "$CA_CERT_FILE" ] || [ ! -f "$CA_KEY_FILE" ]; then
    generate_ca
else
    echo "⏭️  CA certificate exists, skipping..."
fi

# Generate server certificate
if [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
    echo "⏭️  Certificate already exists."
    read -p "Regenerate? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

generate_cert

# Display certificate info
echo ""
echo "📊 Certificate Information:"
openssl x509 -in "$CERT_FILE" -text -noout 2>/dev/null | grep -E "Subject:|Issuer:|Not Before|Not After|Public-Key"

echo ""
echo "✅ Certificates ready for development!"
echo ""
echo "📝 Update .env:"
echo "  TLS_ENABLED=true"
echo "  TLS_PORT=8443"
echo "  TLS_CERT_PATH=$CERT_FILE"
echo "  TLS_KEY_PATH=$KEY_FILE"
echo "  TLS_MTLS_ENABLED=false"
echo "  TLS_MTLS_CA_PATH=$CA_CERT_FILE"
