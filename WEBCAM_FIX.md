# Webcam Access Fix

## Problem
Browser cannot access webcam even with permissions granted.

## Root Cause
**Modern browsers require HTTPS (secure context) to access webcam/microphone for security reasons.** HTTP connections are blocked from accessing camera APIs.

## Solution Applied

### 1. ✅ SSL Certificates Generated
Self-signed certificates have been created in the `certs/` folder:
- `cert.pem` - SSL certificate
- `key.pem` - Private key

### 2. ✅ Backend Updated
Backend now runs with HTTPS on port 8000 using the generated certificates.

### 3. ✅ Frontend Updated
- Frontend now serves over HTTPS on port 8001
- Config updated to use `https://localhost:8000` for API calls

### 4. ✅ Startup Script Updated
The `start.ps1` script now automatically:
- Generates certificates if they don't exist
- Starts backend with HTTPS
- Starts frontend with HTTPS

## How to Use

### Step 1: Start the Application
```powershell
.\start.ps1
```

### Step 2: Accept the Certificate Warning
When you open https://localhost:8001 in your browser:

1. You'll see a **"Your connection is not private"** warning
2. Click **"Advanced"** or **"Show Details"**
3. Click **"Proceed to localhost (unsafe)"**
4. Do this for BOTH:
   - Frontend: https://localhost:8001
   - Backend: https://localhost:8000 (visit this once to accept)

### Step 3: Grant Camera Permission
- Browser will now prompt for camera permission
- Click **"Allow"** when asked

## Browser-Specific Instructions

### Chrome/Edge
1. Go to `chrome://settings/content/camera` or `edge://settings/content/camera`
2. Ensure camera access is allowed for localhost
3. Check that no other app is using the webcam

### Firefox
1. Go to `about:preferences#privacy`
2. Scroll to "Permissions" → "Camera"
3. Ensure localhost has permission
4. Click the "Settings" button next to Camera

### Safari
1. Safari → Preferences → Websites → Camera
2. Allow for localhost

## Still Not Working?

### Check 1: Certificate Accepted?
Visit https://localhost:8000/health in your browser. If you get JSON response, certificate is accepted.

### Check 2: Webcam in Use?
Close other applications that might be using the webcam:
- Zoom, Teams, Skype
- Other browser tabs
- Camera app

### Check 3: Browser Console
1. Press F12 to open Developer Tools
2. Go to "Console" tab
3. Look for specific error messages
4. Common errors:
   - `NotAllowedError`: Permission denied → Grant permission
   - `NotFoundError`: No camera detected → Check hardware
   - `NotReadableError`: Camera in use → Close other apps

### Check 4: Test Webcam
Test if your webcam works at all:
```
https://webcamtests.com
```

## Alternative: Use Chrome Flags (Development Only)

**⚠️ NOT RECOMMENDED FOR PRODUCTION**

If you absolutely need to test with HTTP (not recommended):

1. Open Chrome
2. Go to `chrome://flags/#unsafely-treat-insecure-origin-as-secure`
3. Add: `http://localhost:8001`
4. Relaunch Chrome

## Optional: Install Certificate as Trusted

To avoid the warning every time:

### Windows
1. Double-click `certs\localhost.crt`
2. Click "Install Certificate"
3. Choose "Local Machine"
4. Select "Place all certificates in the following store"
5. Browse → "Trusted Root Certification Authorities"
6. Click OK and install

### Mac
1. Open Keychain Access
2. Drag `certs/localhost.crt` into "System" keychain
3. Double-click the certificate
4. Expand "Trust"
5. Set "When using this certificate" to "Always Trust"

### Linux
```bash
sudo cp certs/localhost.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates
```

## Verification Checklist

- [ ] Application running with HTTPS URLs
- [ ] Certificate warning accepted in browser
- [ ] Visited both https://localhost:8001 AND https://localhost:8000
- [ ] Camera permission granted in browser
- [ ] No other apps using webcam
- [ ] Browser console shows no errors
- [ ] Green camera icon appears (not red/crossed out)

## Technical Details

### Why HTTPS is Required
- **getUserMedia() API**: Browser API to access camera/microphone
- **Security Policy**: Only works in "secure contexts"
- **Secure Contexts**: HTTPS or localhost (with proper setup)
- **Protection**: Prevents malicious websites from accessing camera

### Files Modified
- `backend/main.py` - Added SSL support
- `frontend/config.js` - Changed to HTTPS URL
- `start.ps1` - Auto-generate certs and start with SSL
- `certs/` - Contains SSL certificates

### Port Configuration
- Backend API: https://localhost:8000
- Frontend App: https://localhost:8001
- Both require HTTPS for webcam access
