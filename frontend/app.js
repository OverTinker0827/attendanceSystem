/**
 * Main application logic for student portal
 * Handles registration and attendance marking flows
 */

let capturedEmbeddings = [];
let captureCount = 0;
let isCapturing = false;

// DOM Elements
const welcomeSection = document.getElementById('welcome-section');
const registrationSection = document.getElementById('registration-section');
const cameraSection = document.getElementById('camera-section');
const verificationSection = document.getElementById('verification-section');

const studentInfo = document.getElementById('student-info');
const registerBtn = document.getElementById('register-btn');
const attendanceBtn = document.getElementById('attendance-btn');
const changeIdBtn = document.getElementById('change-id-btn');

const studentIdInput = document.getElementById('student-id-input');
const startRegistrationBtn = document.getElementById('start-registration-btn');
const cancelRegistrationBtn = document.getElementById('cancel-registration-btn');

const webcam = document.getElementById('webcam');
const overlay = document.getElementById('overlay');
const progressBar = document.getElementById('progress-bar');
const progressText = document.getElementById('progress-text');
const captureBtn = document.getElementById('capture-btn');
const cancelCameraBtn = document.getElementById('cancel-camera-btn');

const webcamVerify = document.getElementById('webcam-verify');
const overlayVerify = document.getElementById('overlay-verify');
const verifyBtn = document.getElementById('verify-btn');
const cancelVerifyBtn = document.getElementById('cancel-verify-btn');

/**
 * Initialize application
 */
async function init() {
    console.log('🚀 Initializing Attendance System...');
    
    // Load TensorFlow models
    try {
        showMessage('Loading face recognition models...', false);
        await loadModels();
        console.log('✅ Models loaded successfully');
    } catch (error) {
        console.error('Model loading failed:', error);
        showMessage('Warning: Some features may not work properly', true);
    }
    
    // Check if student ID is stored
    const studentId = getStudentId();
    if (studentId) {
        studentInfo.textContent = `Logged in as: ${studentId}`;
        attendanceBtn.disabled = false;
    } else {
        studentInfo.textContent = 'No student ID found. Please register first.';
        attendanceBtn.disabled = true;
    }
    
    // Set up event listeners
    setupEventListeners();
    
    // Show welcome section
    showSection('welcome');
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
    registerBtn.addEventListener('click', showRegistrationForm);
    attendanceBtn.addEventListener('click', startAttendanceFlow);
    changeIdBtn.addEventListener('click', changeStudentId);
    
    startRegistrationBtn.addEventListener('click', startRegistration);
    cancelRegistrationBtn.addEventListener('click', () => showSection('welcome'));
    
    captureBtn.addEventListener('click', manualCapture);
    cancelCameraBtn.addEventListener('click', cancelCamera);
    
    verifyBtn.addEventListener('click', verifyAttendance);
    cancelVerifyBtn.addEventListener('click', cancelVerification);
}

/**
 * Show specific section and hide others
 */
function showSection(section) {
    welcomeSection.classList.add('hidden');
    registrationSection.classList.add('hidden');
    cameraSection.classList.add('hidden');
    verificationSection.classList.add('hidden');
    
    switch(section) {
        case 'welcome':
            welcomeSection.classList.remove('hidden');
            break;
        case 'registration':
            registrationSection.classList.remove('hidden');
            break;
        case 'camera':
            cameraSection.classList.remove('hidden');
            break;
        case 'verification':
            verificationSection.classList.remove('hidden');
            break;
    }
}

/**
 * Show registration form
 */
function showRegistrationForm() {
    showSection('registration');
    studentIdInput.value = getStudentId() || '';
    studentIdInput.focus();
}

/**
 * Start registration process
 */
async function startRegistration() {
    const studentId = studentIdInput.value.trim();
    
    // Validate student ID
    if (!validateStudentId(studentId)) {
        showMessage('Invalid student ID format. Use: 1RV23CS001 to 1RV23CS420', true);
        return;
    }
    
    // Save student ID
    saveStudentId(studentId);
    studentInfo.textContent = `Logged in as: ${studentId}`;
    
    // Start camera for face capture
    showSection('camera');
    capturedEmbeddings = [];
    captureCount = 0;
    updateProgress();
    
    try {
        await startWebcam(webcam);
        
        // Sync overlay with video
        overlay.width = webcam.videoWidth;
        overlay.height = webcam.videoHeight;
        
        // Start automatic capture
        startAutomaticCapture();
        
    } catch (error) {
        showMessage(error.message, true);
        showSection('registration');
    }
}

/**
 * Start automatic face capture
 */
async function startAutomaticCapture() {
    isCapturing = true;
    
    while (isCapturing && captureCount < CONFIG.NUM_REGISTRATION_IMAGES) {
        try {
            // Show processing message
            progressText.textContent = `Capturing image ${captureCount + 1}...`;
            
            // Detect face and draw box
            const face = await detectFace(webcam);
            const ctx = overlay.getContext('2d');
            ctx.clearRect(0, 0, overlay.width, overlay.height);
            
            if (face) {
                drawFaceBox(overlay, face);
                
                // Generate embedding
                const embedding = await generateEmbedding(webcam);
                capturedEmbeddings.push(embedding);
                captureCount++;
                updateProgress();
                
                // Wait before next capture
                await new Promise(resolve => setTimeout(resolve, CONFIG.CAPTURE_INTERVAL_MS));
            } else {
                progressText.textContent = 'No face detected. Please position your face in frame.';
                await new Promise(resolve => setTimeout(resolve, 500));
            }
            
        } catch (error) {
            console.error('Capture error:', error);
            progressText.textContent = 'Capture failed. Retrying...';
            await new Promise(resolve => setTimeout(resolve, 500));
        }
    }
    
    // All captures done
    if (captureCount === CONFIG.NUM_REGISTRATION_IMAGES) {
        await submitRegistration();
    }
}

/**
 * Update progress bar
 */
function updateProgress() {
    const percentage = (captureCount / CONFIG.NUM_REGISTRATION_IMAGES) * 100;
    progressBar.style.width = `${percentage}%`;
    progressText.textContent = `${captureCount} / ${CONFIG.NUM_REGISTRATION_IMAGES} images captured`;
}

/**
 * Submit registration to backend
 */
async function submitRegistration() {
    isCapturing = false;
    stopWebcam();
    
    progressText.textContent = '📤 Submitting registration...';
    
    try {
        const studentId = getStudentId();
        const response = await apiCall('/api/register', 'POST', {
            student_id: studentId,
            embeddings: capturedEmbeddings
        });
        
        playSuccessSound();
        showDetailedMessage(
            '✅ Registration Successful!',
            `<div class="feedback-success-icon">✓</div>
            <strong>Student ID:</strong> ${studentId}<br>
            <strong>Face Images Captured:</strong> ${CONFIG.NUM_REGISTRATION_IMAGES}<br>
            <strong>Status:</strong> Ready for attendance<br><br>
            <div class="feedback-note">You can now mark your attendance using the "Mark Attendance" button</div>`,
            'success'
        );
        showSection('welcome');
        attendanceBtn.disabled = false;
        
    } catch (error) {
        playErrorSound();
        showDetailedMessage(
            '❌ Registration Failed',
            `<div class="feedback-error-icon">✗</div>
            <strong>Error:</strong> ${error.message}<br><br>
            <strong>Possible causes:</strong><br>
            • Student ID already registered<br>
            • Invalid face embeddings<br>
            • Server connection issue<br><br>
            <strong>Action Required:</strong><br>
            Please try again or contact support if the problem persists.`,
            'error'
        );
        showSection('welcome');
    }
}

/**
 * Cancel camera capture
 */
function cancelCamera() {
    isCapturing = false;
    stopWebcam();
    showSection('welcome');
}

/**
 * Start attendance marking flow
 */
async function startAttendanceFlow() {
    const studentId = getStudentId();
    
    if (!studentId) {
        showMessage(CONFIG.MESSAGES.NO_STUDENT_ID, true);
        return;
    }
    
    showSection('verification');
    
    try {
        await startWebcam(webcamVerify);
        
        // Sync overlay with video
        overlayVerify.width = webcamVerify.videoWidth;
        overlayVerify.height = webcamVerify.videoHeight;
        
        // Start face detection visualization
        visualizeFaceDetection();
        
    } catch (error) {
        showMessage(error.message, true);
        showSection('welcome');
    }
}

/**
 * Visualize face detection (real-time)
 */
async function visualizeFaceDetection() {
    if (!webcamVerify.srcObject) return;
    
    try {
        const face = await detectFace(webcamVerify);
        const ctx = overlayVerify.getContext('2d');
        ctx.clearRect(0, 0, overlayVerify.width, overlayVerify.height);
        
        if (face) {
            drawFaceBox(overlayVerify, face);
        }
    } catch (error) {
        console.error('Detection error:', error);
    }
    
    // Continue visualization
    requestAnimationFrame(visualizeFaceDetection);
}

/**
 * Verify attendance
 */
async function verifyAttendance() {
    verifyBtn.disabled = true;
    verifyBtn.textContent = '🔄 Verifying...';
    
    // Show processing indicator
    const statusElement = document.getElementById('verification-status');
    statusElement.textContent = '🔄 Analyzing face...';
    
    try {
        // Generate live embedding
        const liveEmbedding = await generateEmbedding(webcamVerify);
        const studentId = getStudentId();
        
        if (!liveEmbedding) {
            showDetailedMessage(
                '⚠️ No Face Detected',
                'Please ensure your face is clearly visible in the frame.\n\n📍 Tips:\n• Face the camera directly\n• Ensure good lighting\n• Remove any obstructions',
                'warning'
            );
            verifyBtn.disabled = false;
            verifyBtn.textContent = 'Verify & Mark Attendance';
            statusElement.textContent = 'Position your face in the frame and click Verify';
            return;
        }
        
        statusElement.textContent = '🔄 Comparing with registered profile...';
        
        // Submit to backend
        const response = await apiCall('/api/verify', 'POST', {
            student_id: studentId,
            live_embedding: liveEmbedding
        });
        
        // Handle response with detailed feedback
        if (response.status === 'ok') {
            const timestamp = new Date().toLocaleTimeString();
            const date = new Date().toLocaleDateString();
            const confidence = response.confidence ? (response.confidence * 100).toFixed(1) : 'N/A';
            const matches = response.matches_found || 'N/A';
            
            playSuccessSound();
            showDetailedMessage(
                '✅ Attendance Marked Successfully!',
                `<div class="feedback-success-icon">✓</div>
                <strong>Student ID:</strong> ${studentId}<br>
                <strong>Date:</strong> ${date}<br>
                <strong>Time:</strong> ${timestamp}<br>
                <strong>Verification Confidence:</strong> ${confidence}%<br>
                <strong>Face Matches:</strong> ${matches}/5<br><br>
                <div class="feedback-note">✓ Your attendance has been recorded</div>`,
                'success'
            );
        } else if (response.status === 'already_marked') {
            const markedTime = response.marked_at ? new Date(response.marked_at).toLocaleTimeString() : 'earlier today';
            const markedDate = response.marked_at ? new Date(response.marked_at).toLocaleDateString() : 'today';
            
            playInfoSound();
            showDetailedMessage(
                'ℹ️ Already Marked',
                `<div class="feedback-info-icon">ℹ️</div>
                You have already marked attendance today.<br><br>
                <strong>Previously marked at:</strong><br>
                📅 ${markedDate}<br>
                🕐 ${markedTime}<br><br>
                <div class="feedback-note">You can only mark attendance once per day</div>`,
                'info'
            );
        } else if (response.status === 'not_registered') {
            playErrorSound();
            showDetailedMessage(
                '❌ Not Registered',
                `<div class="feedback-error-icon">✗</div>
                <strong>Student ID:</strong> ${studentId}<br><br>
                This student ID is not registered in the system.<br><br>
                <strong>Action Required:</strong><br>
                1. Click "Cancel" to go back<br>
                2. Click "Register New Student" button<br>
                3. Complete the face registration process`,
                'error'
            );
        } else if (response.status === 'verification_failed') {
            const confidence = response.best_match ? (response.best_match * 100).toFixed(1) : '0.0';
            const threshold = 80;
            const matches = response.matches_found || 0;
            const requiredMatches = 2;
            
            playErrorSound();
            showDetailedMessage(
                '❌ Face Verification Failed',
                `<div class="feedback-error-icon">✗</div>
                Your face does not match the registered profile.<br><br>
                <div class="verification-details">
                    <div class="detail-row">
                        <span class="detail-label">Best Match Score:</span>
                        <span class="detail-value ${confidence >= threshold ? 'pass' : 'fail'}">${confidence}%</span>
                        <span class="detail-required">(Need: ${threshold}%)</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Face Matches:</span>
                        <span class="detail-value ${matches >= requiredMatches ? 'pass' : 'fail'}">${matches}/5</span>
                        <span class="detail-required">(Need: ${requiredMatches}/5)</span>
                    </div>
                </div><br>
                <strong>💡 Tips to improve verification:</strong><br>
                • Ensure good lighting on your face<br>
                • Position your face in the center of frame<br>
                • Remove glasses if you didn't wear them during registration<br>
                • Face the camera directly<br>
                • Try again in a few seconds<br><br>
                <div class="feedback-note">If problems persist, you may need to re-register</div>`,
                'error'
            );
        } else {
            playErrorSound();
            showDetailedMessage(
                '❌ Verification Failed',
                `<div class="feedback-error-icon">✗</div>
                ${response.message || 'Unknown error occurred.'}<br><br>
                Please try again or contact support if the problem persists.`,
                'error'
            );
        }
        
        stopWebcam();
        showSection('welcome');
        
    } catch (error) {
        playErrorSound();
        showDetailedMessage(
            '❌ Connection Error',
            `<div class="feedback-error-icon">✗</div>
            <strong>Unable to verify attendance</strong><br><br>
            <strong>Error:</strong> ${error.message}<br><br>
            <strong>Possible causes:</strong><br>
            • No internet connection<br>
            • Backend server is not running<br>
            • Network firewall blocking request<br><br>
            Please check your connection and try again.`,
            'error'
        );
        stopWebcam();
        showSection('welcome');
    } finally {
        verifyBtn.disabled = false;
        verifyBtn.textContent = 'Verify & Mark Attendance';
        statusElement.textContent = 'Position your face in the frame and click Verify';
    }
}

/**
 * Show detailed message with title and body
 */
function showDetailedMessage(title, body, type = 'success') {
    const messageDiv = document.getElementById('message');
    
    // Fade out if already visible
    if (!messageDiv.classList.contains('hidden')) {
        messageDiv.style.opacity = '0';
        setTimeout(() => {
            updateMessageContent();
        }, 200);
    } else {
        updateMessageContent();
    }
    
    function updateMessageContent() {
        messageDiv.className = 'message message-' + type;
        messageDiv.innerHTML = `
            <button class="message-close" onclick="document.getElementById('message').classList.add('hidden');">×</button>
            <div class="message-title">${title}</div>
            <div class="message-body">${body}</div>
        `;
        messageDiv.classList.remove('hidden');
        messageDiv.style.display = 'block';
        
        // Trigger animation
        setTimeout(() => {
            messageDiv.style.opacity = '1';
        }, 10);
        
        // Scroll to message
        messageDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
        // Auto-hide after duration based on type
        const duration = type === 'success' ? 8000 : type === 'info' ? 7000 : 0; // Keep errors visible
        if (duration > 0) {
            setTimeout(() => {
                messageDiv.style.opacity = '0';
                setTimeout(() => {
                    messageDiv.classList.add('hidden');
                }, 300);
            }, duration);
        }
    }
}

/**
 * Play success sound (simple beep)
 */
function playSuccessSound() {
    if ('AudioContext' in window || 'webkitAudioContext' in window) {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            gainNode.gain.value = 0.1;
            
            oscillator.start();
            oscillator.stop(audioContext.currentTime + 0.1);
        } catch (e) {
            console.log('Audio not available');
        }
    }
}

/**
 * Play error sound
 */
function playErrorSound() {
    if ('AudioContext' in window || 'webkitAudioContext' in window) {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 300;
            oscillator.type = 'sine';
            gainNode.gain.value = 0.1;
            
            oscillator.start();
            oscillator.stop(audioContext.currentTime + 0.2);
        } catch (e) {
            console.log('Audio not available');
        }
    }
}

/**
 * Play info sound
 */
function playInfoSound() {
    if ('AudioContext' in window || 'webkitAudioContext' in window) {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 600;
            oscillator.type = 'sine';
            gainNode.gain.value = 0.1;
            
            oscillator.start();
            oscillator.stop(audioContext.currentTime + 0.15);
        } catch (e) {
            console.log('Audio not available');
        }
    }
}

/**
 * Cancel verification
 */
function cancelVerification() {
    stopWebcam();
    showSection('welcome');
}

/**
 * Change student ID
 */
function changeStudentId() {
    deleteCookie(CONFIG.COOKIE_NAME);
    studentInfo.textContent = 'No student ID found. Please register first.';
    attendanceBtn.disabled = true;
    showRegistrationForm();
}

/**
 * Manual capture (backup if automatic fails)
 */
async function manualCapture() {
    if (captureCount >= CONFIG.NUM_REGISTRATION_IMAGES) return;
    
    try {
        const embedding = await generateEmbedding(webcam);
        capturedEmbeddings.push(embedding);
        captureCount++;
        updateProgress();
        
        if (captureCount === CONFIG.NUM_REGISTRATION_IMAGES) {
            await submitRegistration();
        }
    } catch (error) {
        showMessage('Capture failed: ' + error.message, true);
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', init);
