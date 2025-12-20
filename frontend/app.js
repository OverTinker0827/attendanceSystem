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
    
    progressText.textContent = 'Submitting registration...';
    
    try {
        const studentId = getStudentId();
        const response = await apiCall('/api/register', 'POST', {
            student_id: studentId,
            embeddings: capturedEmbeddings
        });
        
        showMessage(CONFIG.MESSAGES.REGISTRATION_SUCCESS, false);
        showSection('welcome');
        attendanceBtn.disabled = false;
        
    } catch (error) {
        showMessage(`Registration failed: ${error.message}`, true);
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
    verifyBtn.textContent = 'Verifying...';
    
    try {
        // Generate live embedding
        const liveEmbedding = await generateEmbedding(webcamVerify);
        const studentId = getStudentId();
        
        if (!liveEmbedding) {
            showMessage(CONFIG.MESSAGES.FACE_NOT_DETECTED, true);
            verifyBtn.disabled = false;
            verifyBtn.textContent = 'Verify & Mark Attendance';
            return;
        }
        
        // Submit to backend
        const response = await apiCall('/api/verify', 'POST', {
            student_id: studentId,
            live_embedding: liveEmbedding
        });
        
        // Handle response with detailed feedback
        if (response.status === 'ok') {
            const timestamp = new Date().toLocaleTimeString();
            const confidence = response.confidence ? (response.confidence * 100).toFixed(1) : 'N/A';
            const matches = response.matches_found || 'N/A';
            
            showDetailedMessage(
                '✓ Attendance Marked Successfully!',
                `Student: ${studentId}\nTime: ${timestamp}\nConfidence: ${confidence}%\nMatches: ${matches}/5`,
                'success'
            );
        } else if (response.status === 'already_marked') {
            const markedTime = response.marked_at ? new Date(response.marked_at).toLocaleTimeString() : 'earlier today';
            showDetailedMessage(
                'Already Marked',
                `You already marked attendance at ${markedTime}`,
                'info'
            );
        } else if (response.status === 'not_registered') {
            showDetailedMessage(
                '✗ Not Registered',
                `Student ID ${studentId} is not registered.\nPlease register first using the Register button.`,
                'error'
            );
        } else if (response.status === 'verification_failed') {
            const confidence = response.best_match ? (response.best_match * 100).toFixed(1) : '0.0';
            const matches = response.matches_found || 0;
            showDetailedMessage(
                '✗ Verification Failed',
                `Face does not match registered profile.\nBest Match: ${confidence}% (Need: 80%)\nMatches: ${matches}/5 (Need: 2/5)\n\nPlease try again with better lighting and face positioning.`,
                'error'
            );
        } else {
            showDetailedMessage(
                '✗ Verification Failed',
                response.message || 'Unknown error occurred. Please try again.',
                'error'
            );
        }
        
        stopWebcam();
        showSection('welcome');
        
    } catch (error) {
        showDetailedMessage(
            '✗ Error',
            `Verification failed: ${error.message}\n\nPlease check your internet connection and try again.`,
            'error'
        );
        stopWebcam();
        showSection('welcome');
    } finally {
        verifyBtn.disabled = false;
        verifyBtn.textContent = 'Verify & Mark Attendance';
    }
}

/**
 * Show detailed message with title and body
 */
function showDetailedMessage(title, body, type = 'success') {
    const messageDiv = document.getElementById('message');
    messageDiv.className = 'message message-' + type;
    messageDiv.innerHTML = `
        <div class="message-title">${title}</div>
        <div class="message-body">${body.replace(/\n/g, '<br>')}</div>
    `;
    messageDiv.classList.remove('hidden');
    
    // Auto-hide after 6 seconds for success/info, keep error visible
    if (type !== 'error') {
        setTimeout(() => {
            messageDiv.classList.add('hidden');
        }, 6000);
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
