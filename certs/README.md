# Attendance System - Certificate Generation

This directory contains SSL certificates for HTTPS communication between the frontend and backend.

## Generate Certificates

Run the certificate generation script:

```bash
python generate_certs.py
```

This will create:
- `localhost.crt` - SSL certificate
- `localhost.key` - Private key

## Files

- `generate_certs.py` - Certificate generation script
- `localhost.crt` - SSL certificate (generated)
- `localhost.key` - Private key (generated)

## Usage

The certificates are automatically used by:
- Backend (FastAPI/Uvicorn) on port 8000
- Frontend (http-server) on port 8001

## Security Note

These are **self-signed certificates** for local development only.

- Browser will show security warnings
- Click "Advanced" → "Proceed to localhost"
- For production, use proper SSL certificates (e.g., Let's Encrypt)

## Installing the Certificate (Optional)

To avoid browser warnings, you can install the certificate as trusted:

### Windows
1. Double-click `localhost.crt`
2. Click "Install Certificate"
3. Select "Local Machine"
4. Place in "Trusted Root Certification Authorities"

### macOS
1. Open "Keychain Access"
2. File → Import Items → Select `localhost.crt`
3. Double-click the certificate
4. Expand "Trust" section
5. Set "When using this certificate" to "Always Trust"

### Linux
```bash
sudo cp localhost.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates
```

## Validity

Certificates are valid for **365 days** from generation date.

After expiry, regenerate using `python generate_certs.py`.
