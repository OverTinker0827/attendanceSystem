"""
Generate self-signed SSL certificates for local HTTPS development.
Creates certificates for localhost on ports 8000 and 8001.
"""

from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from datetime import datetime, timedelta, timezone
import ipaddress
import os

def generate_self_signed_cert(
    cert_file="localhost.crt",
    key_file="localhost.key",
    common_name="localhost",
    days_valid=365
):
    """
    Generate a self-signed SSL certificate for localhost.
    
    Args:
        cert_file: Output certificate file path
        key_file: Output private key file path
        common_name: Common name for the certificate (default: localhost)
        days_valid: Number of days the certificate is valid (default: 365)
    """
    
    print(f"🔐 Generating self-signed SSL certificate for {common_name}...")
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # Create certificate subject and issuer (same for self-signed)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Attendance System"),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])
    
    # Build certificate
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=days_valid))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.DNSName("127.0.0.1"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        )
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .sign(private_key, hashes.SHA256())
    )
    
    # Write private key to file
    with open(key_file, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
    print(f"✅ Private key saved to: {key_file}")
    
    # Write certificate to file
    with open(cert_file, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    print(f"✅ Certificate saved to: {cert_file}")
    
    print(f"🎉 Certificate valid for {days_valid} days")
    print(f"⚠️  Note: Browser will show security warning for self-signed certificates")
    print(f"    Click 'Advanced' and 'Proceed to localhost' to continue")


if __name__ == "__main__":
    # Create certs directory if it doesn't exist
    os.makedirs(".", exist_ok=True)
    
    # Generate certificate
    generate_self_signed_cert(
        cert_file="localhost.crt",
        key_file="localhost.key",
        common_name="localhost",
        days_valid=365
    )
    
    print("\n📋 To install the certificate (optional):")
    print("   Windows: Double-click localhost.crt → Install Certificate → Local Machine → Trusted Root")
    print("   Mac: Open Keychain Access → Import localhost.crt → Trust for SSL")
    print("   Linux: Copy to /usr/local/share/ca-certificates/ and run update-ca-certificates")
