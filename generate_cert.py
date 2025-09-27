
import datetime
import os
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

def generate_certificates():
    """Generate SSL certificates for both server and client"""
    
    # Generate our key
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    # Create directories if they don't exist
    os.makedirs("server", exist_ok=True)
    os.makedirs("client", exist_ok=True)

    # Write our key to disk for safe keeping
    with open("server/key.pem", "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    # Various details about who we are. For a self-signed certificate the
    # subject and issuer are always the same.
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"California"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"San Francisco"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Dark Comm Terminal"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
    ])

    # Create certificate with multiple Subject Alternative Names
    # This allows the certificate to work with both localhost and .onion addresses
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        # Our certificate will be valid for 365 days
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName(u"localhost"),
            x509.DNSName(u"127.0.0.1"),
            # Add wildcard for .onion addresses (though not standard, helps with testing)
            x509.DNSName(u"*.onion"),
        ]),
        critical=False,
    # Sign our certificate with our private key
    ).sign(key, hashes.SHA256(), default_backend())

    # Write our certificate out to disk for server
    with open("server/cert.pem", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    # Copy the same certificate to client directory for certificate pinning
    with open("client/cert.pem", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print("Generated key.pem and cert.pem in server/ directory.")
    print("Copied cert.pem to client/ directory for certificate pinning.")
    print("Certificate is valid for localhost, 127.0.0.1, and .onion addresses.")

if __name__ == "__main__":
    generate_certificates()
