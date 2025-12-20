/**
 * Admin panel logic
 * Handles authentication, attendance viewing, and data export
 */

let adminCredentials = null;

// DOM Elements
const loginSection = document.getElementById('login-section');
const dashboardSection = document.getElementById('dashboard-section');
const loginMessage = document.getElementById('login-message');

const adminUsername = document.getElementById('admin-username');
const adminPassword = document.getElementById('admin-password');
const loginBtn = document.getElementById('login-btn');
const logoutBtn = document.getElementById('logout-btn');

const totalStudentsEl = document.getElementById('total-students');
const todayAttendanceEl = document.getElementById('today-attendance');
const attendanceRateEl = document.getElementById('attendance-rate');

const filterDate = document.getElementById('filter-date');
const filterStudent = document.getElementById('filter-student');
const filterBtn = document.getElementById('filter-btn');
const refreshBtn = document.getElementById('refresh-btn');

const attendanceTbody = document.getElementById('attendance-tbody');
const exportBtn = document.getElementById('export-btn');

const exportStartDate = document.getElementById('export-start-date');
const exportEndDate = document.getElementById('export-end-date');
const exportRangeBtn = document.getElementById('export-range-btn');

/**
 * Initialize admin panel
 */
function init() {
    console.log('🔐 Initializing Admin Panel...');
    
    // Set default date to today
    const today = new Date().toISOString().split('T')[0];
    filterDate.value = today;
    exportStartDate.value = today;
    exportEndDate.value = today;
    
    // Set up event listeners
    setupEventListeners();
    
    // Check if already logged in (credentials in session)
    const savedCredentials = sessionStorage.getItem('admin_credentials');
    if (savedCredentials) {
        adminCredentials = savedCredentials;
        showDashboard();
    }
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
    loginBtn.addEventListener('click', login);
    logoutBtn.addEventListener('click', logout);
    filterBtn.addEventListener('click', loadAttendance);
    refreshBtn.addEventListener('click', refreshDashboard);
    exportBtn.addEventListener('click', exportCurrentView);
    exportRangeBtn.addEventListener('click', exportDateRange);
    
    // Enter key to login
    adminPassword.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') login();
    });
}

/**
 * Login to admin panel
 */
async function login() {
    const username = adminUsername.value.trim();
    const password = adminPassword.value;
    
    if (!username || !password) {
        showLoginMessage('Please enter username and password', true);
        return;
    }
    
    loginBtn.disabled = true;
    loginBtn.textContent = 'Logging in...';
    
    try {
        // Create Basic Auth header
        const credentials = btoa(`${username}:${password}`);
        adminCredentials = `Basic ${credentials}`;
        
        // Test credentials by fetching stats
        const response = await apiCall('/api/admin/stats', 'GET', null, {
            'Authorization': adminCredentials
        });
        
        // Save credentials to session
        sessionStorage.setItem('admin_credentials', adminCredentials);
        
        showDashboard();
        
    } catch (error) {
        showLoginMessage('Invalid credentials', true);
        adminCredentials = null;
    } finally {
        loginBtn.disabled = false;
        loginBtn.textContent = 'Login';
        adminPassword.value = '';
    }
}

/**
 * Logout from admin panel
 */
function logout() {
    adminCredentials = null;
    sessionStorage.removeItem('admin_credentials');
    showLoginSection();
}

/**
 * Show login section
 */
function showLoginSection() {
    loginSection.classList.remove('hidden');
    dashboardSection.classList.add('hidden');
}

/**
 * Show dashboard section
 */
function showDashboard() {
    loginSection.classList.add('hidden');
    dashboardSection.classList.remove('hidden');
    refreshDashboard();
}

/**
 * Show login message
 */
function showLoginMessage(message, isError) {
    loginMessage.textContent = message;
    loginMessage.className = isError ? 'message error' : 'message success';
    loginMessage.classList.remove('hidden');
    
    setTimeout(() => {
        loginMessage.classList.add('hidden');
    }, 3000);
}

/**
 * Refresh dashboard data
 */
async function refreshDashboard() {
    await loadStatistics();
    await loadConfiguration();
    await loadAttendance();
}

/**
 * Load statistics
 */
async function loadStatistics() {
    try {
        const stats = await apiCall('/api/admin/stats', 'GET', null, {
            'Authorization': adminCredentials
        });
        
        totalStudentsEl.textContent = stats.total_registered_students;
        todayAttendanceEl.textContent = stats.today_attendance;
        
        const rate = stats.total_registered_students > 0
            ? (stats.today_attendance / stats.total_registered_students * 100).toFixed(1)
            : 0;
        attendanceRateEl.textContent = `${rate}%`;
        
    } catch (error) {
        console.error('Failed to load statistics:', error);
        if (error.message.includes('401')) {
            logout();
        }
    }
}

/**
 * Load configuration
 */
async function loadConfiguration() {
    try {
        const stats = await apiCall('/api/admin/stats', 'GET', null, {
            'Authorization': adminCredentials
        });
        
        if (stats.config) {
            document.getElementById('config-threshold').textContent = 
                stats.config.similarity_threshold.toFixed(2);
            document.getElementById('config-matches').textContent = 
                `${stats.config.min_matches_required} out of ${stats.config.num_embeddings}`;
            document.getElementById('config-pattern').textContent = 
                stats.config.student_id_pattern;
        }
    } catch (error) {
        console.error('Failed to load configuration:', error);
    }
}

/**
 * Load attendance records
 */
async function loadAttendance() {
    const date = filterDate.value;
    const studentId = filterStudent.value.trim();
    
    try {
        let endpoint = `/api/admin/attendance?date=${date}`;
        if (studentId) {
            endpoint += `&student_id=${studentId}`;
        }
        
        const data = await apiCall(endpoint, 'GET', null, {
            'Authorization': adminCredentials
        });
        
        displayAttendanceTable(data);
        
    } catch (error) {
        console.error('Failed to load attendance:', error);
        attendanceTbody.innerHTML = '<tr><td colspan="3" class="text-center">Error loading data</td></tr>';
    }
}

/**
 * Display attendance table
 */
function displayAttendanceTable(data) {
    if (data.attendance.length === 0) {
        attendanceTbody.innerHTML = '<tr><td colspan="3" class="text-center">No attendance records found</td></tr>';
        return;
    }
    
    attendanceTbody.innerHTML = data.attendance.map(record => `
        <tr>
            <td>${record.student_id}</td>
            <td>
                <span class="status-badge ${record.present ? 'present' : 'absent'}">
                    ${record.present ? '✓ Present' : '✗ Absent'}
                </span>
            </td>
            <td>${record.marked_at ? formatDateTime(record.marked_at) : 'N/A'}</td>
        </tr>
    `).join('');
}

/**
 * Format datetime string
 */
function formatDateTime(dateTimeStr) {
    const date = new Date(dateTimeStr);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Export current view as CSV
 */
async function exportCurrentView() {
    const date = filterDate.value;
    await exportDateRange(date, date);
}

/**
 * Export date range as CSV
 */
async function exportDateRange(startDate = null, endDate = null) {
    const start = startDate || exportStartDate.value;
    const end = endDate || exportEndDate.value;
    
    if (!start || !end) {
        alert('Please select start and end dates');
        return;
    }
    
    try {
        const url = `${CONFIG.BACKEND_URL}/api/admin/export?start_date=${start}&end_date=${end}`;
        
        // Create a temporary link to download the file
        const response = await fetch(url, {
            headers: {
                'Authorization': adminCredentials
            }
        });
        
        if (!response.ok) {
            throw new Error('Export failed');
        }
        
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `attendance_${start}_${end}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(downloadUrl);
        document.body.removeChild(a);
        
    } catch (error) {
        console.error('Export failed:', error);
        alert('Failed to export data');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', init);
