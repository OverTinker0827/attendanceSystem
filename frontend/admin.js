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
/**
 * Load statistics
 */
async function loadStatistics() {
    try {
        // Get all students
        const students = await apiCall('/api/admin/students', 'GET', null, {
            'Authorization': adminCredentials
        });
        
        // Get all attendance records
        const attendanceRecords = await apiCall('/api/admin/attendance', 'GET', null, {
            'Authorization': adminCredentials
        });
        
        // Total registered students
        const totalStudents = students.length;
        totalStudentsEl.textContent = totalStudents;
        
        // Calculate today's attendance (unique students who marked attendance today)
        const today = new Date().toISOString().split('T')[0];
        const studentsMarkedToday = new Set();
        
        attendanceRecords.forEach(record => {
            if (record.last_marked_at) {
                const markedDate = record.last_marked_at.split('T')[0];
                if (markedDate === today) {
                    studentsMarkedToday.add(record.student_id);
                }
            }
        });
        
        const todayCount = studentsMarkedToday.size;
        
        // ✅ Display as "x/total students" format
        todayAttendanceEl.textContent = `${todayCount}/${totalStudents}`;
        
        // ✅ Calculate average attendance percentage across all students and subjects
        if (attendanceRecords.length > 0) {
            const totalPercentage = attendanceRecords.reduce((sum, record) => {
                return sum + (record.attendance_percentage || 0);
            }, 0);
            const avgRate = (totalPercentage / attendanceRecords.length).toFixed(1);
            attendanceRateEl.textContent = `${avgRate}%`;
        } else {
            attendanceRateEl.textContent = '0.0%';
        }
        
        console.log(`📊 Statistics: ${todayCount} out of ${totalStudents} students marked attendance today`);
        
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
/**
 * Load attendance records
 */
async function loadAttendance() {
    const date = filterDate.value;
    const studentId = filterStudent.value.trim();
    
    try {
        // ✅ Updated endpoint - remove date parameter since backend returns all records
        let endpoint = `/api/admin/attendance`;
        
        const data = await apiCall(endpoint, 'GET', null, {
            'Authorization': adminCredentials
        });
        
        // ✅ Backend returns array directly, not wrapped in object
        console.log('Attendance data received:', data);
        console.log('Is array?', Array.isArray(data));
        
        // Filter on client side if needed
        let filteredData = data;
        if (studentId) {
            filteredData = data.filter(record => 
                record.student_id.toLowerCase().includes(studentId.toLowerCase())
            );
        }
        
        displayAttendanceTable(filteredData);
        
    } catch (error) {
        console.error('Failed to load attendance:', error);
        attendanceTbody.innerHTML = '<tr><td colspan="6" class="text-center">Error loading data</td></tr>';
    }
}

/**
 * Display attendance table
 */
function displayAttendanceTable(data) {
    // ✅ Add defensive checks
    if (!Array.isArray(data)) {
        console.error('Expected array but got:', typeof data, data);
        attendanceTbody.innerHTML = '<tr><td colspan="6" class="text-center">Invalid data format</td></tr>';
        return;
    }
    
    if (data.length === 0) {
        attendanceTbody.innerHTML = '<tr><td colspan="6" class="text-center">No attendance records found</td></tr>';
        return;
    }
    
    // ✅ Updated to match backend response structure
    attendanceTbody.innerHTML = data.map(record => `
        <tr>
            <td>${record.student_id || 'N/A'}</td>
            <td>${record.subject || 'N/A'}</td>
            <td>${record.attendance_percentage?.toFixed(2) || '0.00'}%</td>
            <td>${record.total_classes || 0}</td>
            <td>${record.attended_classes || 0}</td>
            <td>${record.last_marked_at ? formatDateTime(record.last_marked_at) : 'Never'}</td>
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
/**
 * Export current view as CSV
 */
async function exportCurrentView() {
    try {
        const data = await apiCall('/api/admin/attendance', 'GET', null, {
            'Authorization': adminCredentials
        });
        
        if (!Array.isArray(data) || data.length === 0) {
            alert('No data to export');
            return;
        }
        
        // Convert to CSV
        const headers = ['Student ID', 'Subject', 'Attendance %', 'Total Classes', 'Attended', 'Last Marked'];
        const csvRows = [
            headers.join(','),
            ...data.map(record => [
                record.student_id,
                record.subject,
                record.attendance_percentage?.toFixed(2) || '0.00',
                record.total_classes || 0,
                record.attended_classes || 0,
                record.last_marked_at || 'Never'
            ].join(','))
        ];
        
        const csvContent = csvRows.join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `attendance_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
    } catch (error) {
        console.error('Export failed:', error);
        alert('Failed to export data');
    }
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
