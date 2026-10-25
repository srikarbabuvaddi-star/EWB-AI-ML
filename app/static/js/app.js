/**
 * Students Database Management Application
 * Academic Administration Dashboard Client Script
 * Internship Assignment — EWB Edu Tech Pvt. Ltd.
 */

const API_BASE = window.location.origin;

// State management
let state = {
    students: [],
    totalCount: 0,
    limit: 10,
    offset: 0,
    search: '',
    course: '',
    activeStudentId: null,
    deleteCandidate: null
};

// DOM Elements
const studentsTableBody = document.getElementById('studentsTableBody');
const emptyState = document.getElementById('emptyState');
const loadingIndicator = document.getElementById('loadingIndicator');
const searchInput = document.getElementById('searchInput');
const courseFilter = document.getElementById('courseFilter');
const pageSizeSelect = document.getElementById('pageSizeSelect');
const paginationInfo = document.getElementById('paginationInfo');
const prevPageBtn = document.getElementById('prevPageBtn');
const nextPageBtn = document.getElementById('nextPageBtn');
const refreshBtn = document.getElementById('refreshBtn');
const resetFiltersBtn = document.getElementById('resetFiltersBtn');

// Modals
const studentModal = document.getElementById('studentModal');
const studentForm = document.getElementById('studentForm');
const modalTitle = document.getElementById('modalTitle');
const saveStudentBtn = document.getElementById('saveStudentBtn');
const deleteModal = document.getElementById('deleteModal');
const detailsModal = document.getElementById('detailsModal');
const detailsContent = document.getElementById('detailsContent');

// KPI Counters
const totalStudentsCount = document.getElementById('totalStudentsCount');
const activeCoursesCount = document.getElementById('activeCoursesCount');
const currentYearCount = document.getElementById('currentYearCount');
const healthStatusBadge = document.getElementById('healthStatusBadge');

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    loadStudents();
    setupEventListeners();
});

function setupEventListeners() {
    // Search with debounce
    let debounceTimer;
    searchInput.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            state.search = e.target.value.trim();
            state.offset = 0;
            loadStudents();
        }, 300);
    });

    // Course filter
    courseFilter.addEventListener('change', (e) => {
        state.course = e.target.value;
        state.offset = 0;
        loadStudents();
    });

    // Page size
    pageSizeSelect.addEventListener('change', (e) => {
        state.limit = parseInt(e.target.value, 10);
        state.offset = 0;
        loadStudents();
    });

    // Pagination buttons
    prevPageBtn.addEventListener('click', () => {
        if (state.offset > 0) {
            state.offset = Math.max(0, state.offset - state.limit);
            loadStudents();
        }
    });

    nextPageBtn.addEventListener('click', () => {
        if (state.offset + state.limit < state.totalCount) {
            state.offset += state.limit;
            loadStudents();
        }
    });

    // Refresh & reset
    refreshBtn.addEventListener('click', () => {
        loadStudents();
        checkHealth();
    });

    resetFiltersBtn.addEventListener('click', () => {
        searchInput.value = '';
        courseFilter.value = '';
        state.search = '';
        state.course = '';
        state.offset = 0;
        loadStudents();
    });

    // Form submission
    studentForm.addEventListener('submit', handleFormSubmit);

    // Delete confirmation
    document.getElementById('confirmDeleteBtn').addEventListener('click', executeDelete);
}

// Health check
async function checkHealth() {
    try {
        const res = await fetch(`${API_BASE}/health`);
        if (res.ok) {
            const data = await res.json();
            if (data.status === 'healthy') {
                healthStatusBadge.innerHTML = `<span class="status-dot"></span> System Online • SQLite Connected`;
                healthStatusBadge.style.backgroundColor = 'var(--success-bg)';
                healthStatusBadge.style.color = 'var(--success-text)';
            }
        } else {
            throw new Error('Health check non-200');
        }
    } catch (err) {
        healthStatusBadge.innerHTML = `<span class="status-dot" style="background-color:#ef4444;"></span> System Degraded`;
        healthStatusBadge.style.backgroundColor = 'var(--danger-bg)';
        healthStatusBadge.style.color = 'var(--danger-text)';
    }
}

// Load students from real FastAPI backend
async function loadStudents() {
    showLoading(true);

    try {
        const params = new URLSearchParams();
        params.append('limit', state.limit);
        params.append('offset', state.offset);
        if (state.search) params.append('search', state.search);
        if (state.course) params.append('course', state.course);

        const res = await fetch(`${API_BASE}/students?${params.toString()}`);
        if (!res.ok) {
            throw new Error(`Failed to fetch students (HTTP ${res.status})`);
        }

        const data = await res.json();
        const totalHeader = res.headers.get('X-Total-Count');
        state.totalCount = totalHeader ? parseInt(totalHeader, 10) : data.length;
        state.students = data;

        renderStudentsTable();
        updatePaginationControls();
        updateKPICounters();
    } catch (err) {
        console.error(err);
        showToast(err.message || 'Error connecting to students API', 'error');
        showLoading(false);
    }
}

// Render table
function renderStudentsTable() {
    showLoading(false);
    studentsTableBody.innerHTML = '';

    if (state.students.length === 0) {
        emptyState.style.display = 'block';
        return;
    }

    emptyState.style.display = 'none';

    state.students.forEach((student) => {
        const tr = document.createElement('tr');

        // Initials avatar
        const initials = student.name
            .split(' ')
            .map(part => part[0])
            .join('')
            .substring(0, 2)
            .toUpperCase();

        const courseDisplay = student.course
            ? `<span class="course-badge">${escapeHtml(student.course)}</span>`
            : '<span style="color: var(--text-muted); font-style: italic;">Unassigned</span>';

        const phoneDisplay = student.phone
            ? escapeHtml(student.phone)
            : '<span style="color: var(--text-muted); font-style: italic;">—</span>';

        const dobDisplay = student.date_of_birth || '—';
        const enrollmentDisplay = student.enrollment_date || '—';

        tr.innerHTML = `
            <td style="font-weight: 600; color: var(--text-secondary);">#${student.id}</td>
            <td>
                <div class="student-name-cell">
                    <div class="avatar-badge">${initials}</div>
                    <div class="student-name">${escapeHtml(student.name)}</div>
                </div>
            </td>
            <td>${escapeHtml(student.email)}</td>
            <td>${courseDisplay}</td>
            <td>${dobDisplay}</td>
            <td>${phoneDisplay}</td>
            <td>${enrollmentDisplay}</td>
            <td>
                <div class="table-actions">
                    <button class="btn btn-secondary btn-icon" title="View Details" onclick="viewStudentDetails(${student.id})">
                        <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                        </svg>
                    </button>
                    <button class="btn btn-secondary btn-icon" title="Edit Student" onclick="openEditModal(${student.id})">
                        <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                        </svg>
                    </button>
                    <button class="btn btn-outline-danger btn-icon" title="Delete Student" onclick="promptDelete(${student.id}, '${escapeHtml(student.name)}')">
                        <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                        </svg>
                    </button>
                </div>
            </td>
        `;

        studentsTableBody.appendChild(tr);
    });
}

function updatePaginationControls() {
    const start = state.totalCount === 0 ? 0 : state.offset + 1;
    const end = Math.min(state.offset + state.limit, state.totalCount);
    paginationInfo.textContent = `Showing ${start}–${end} of ${state.totalCount} students`;

    prevPageBtn.disabled = state.offset === 0;
    nextPageBtn.disabled = state.offset + state.limit >= state.totalCount;
}

function updateKPICounters() {
    totalStudentsCount.textContent = state.totalCount;

    // Distinct courses from loaded items
    const courses = new Set(state.students.map(s => s.course).filter(Boolean));
    activeCoursesCount.textContent = courses.size;

    // Current year enrollments
    const currentYear = new Date().getFullYear().toString();
    const currentYearStudents = state.students.filter(s => s.enrollment_date && s.enrollment_date.startsWith(currentYear));
    currentYearCount.textContent = currentYearStudents.length;
}

// Modal handling
function openAddModal() {
    state.activeStudentId = null;
    modalTitle.textContent = 'Add New Student';
    saveStudentBtn.textContent = 'Save Student';
    studentForm.reset();

    // Default enrollment date to today
    document.getElementById('enrollmentDateInput').value = new Date().toISOString().split('T')[0];

    // Restrict DOB to past
    document.getElementById('dobInput').max = new Date().toISOString().split('T')[0];

    studentModal.classList.add('active');
}

async function openEditModal(studentId) {
    state.activeStudentId = studentId;
    modalTitle.textContent = `Edit Student #${studentId}`;
    saveStudentBtn.textContent = 'Update Student';
    studentForm.reset();

    try {
        const res = await fetch(`${API_BASE}/students/${studentId}`);
        if (!res.ok) throw new Error('Failed to retrieve student record');

        const student = await res.json();
        document.getElementById('nameInput').value = student.name || '';
        document.getElementById('emailInput').value = student.email || '';
        document.getElementById('dobInput').value = student.date_of_birth || '';
        document.getElementById('courseInput').value = student.course || '';
        document.getElementById('phoneInput').value = student.phone || '';
        document.getElementById('enrollmentDateInput').value = student.enrollment_date || '';
        document.getElementById('addressInput').value = student.address || '';

        studentModal.classList.add('active');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function closeStudentModal() {
    studentModal.classList.remove('active');
    state.activeStudentId = null;
}

async function handleFormSubmit(e) {
    e.preventDefault();

    const name = document.getElementById('nameInput').value.trim();
    const email = document.getElementById('emailInput').value.trim();
    const date_of_birth = document.getElementById('dobInput').value;
    const course = document.getElementById('courseInput').value.trim() || null;
    const phone = document.getElementById('phoneInput').value.trim() || null;
    const enrollment_date = document.getElementById('enrollmentDateInput').value || null;
    const address = document.getElementById('addressInput').value.trim() || null;

    if (!name) {
        showToast('Student name is required.', 'error');
        return;
    }
    if (!email) {
        showToast('Valid student email is required.', 'error');
        return;
    }
    if (!date_of_birth) {
        showToast('Date of birth is required.', 'error');
        return;
    }

    const payload = {
        name,
        email,
        date_of_birth,
        course,
        phone,
        enrollment_date,
        address
    };

    saveStudentBtn.disabled = true;
    saveStudentBtn.textContent = 'Saving...';

    try {
        let res;
        if (state.activeStudentId) {
            // PUT update
            res = await fetch(`${API_BASE}/students/${state.activeStudentId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        } else {
            // POST create
            res = await fetch(`${API_BASE}/students`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        }

        const data = await res.json();

        if (res.status === 201 || res.status === 200) {
            showToast(state.activeStudentId ? 'Student updated successfully!' : 'Student created successfully!', 'success');
            closeStudentModal();
            loadStudents();
        } else if (res.status === 409) {
            showToast(data.detail || 'Email already exists.', 'error');
        } else if (res.status === 422) {
            const errDetail = Array.isArray(data.detail) ? data.detail.map(d => d.msg).join('; ') : data.detail;
            showToast(`Validation error: ${errDetail}`, 'error');
        } else {
            showToast(data.detail || 'An unexpected error occurred.', 'error');
        }
    } catch (err) {
        showToast(err.message || 'Network error occurred.', 'error');
    } finally {
        saveStudentBtn.disabled = false;
        saveStudentBtn.textContent = state.activeStudentId ? 'Update Student' : 'Save Student';
    }
}

// View details modal
async function viewStudentDetails(studentId) {
    try {
        const res = await fetch(`${API_BASE}/students/${studentId}`);
        if (!res.ok) throw new Error('Student not found.');

        const student = await res.json();
        detailsContent.innerHTML = `
            <div class="details-list">
                <div class="details-label">Student ID:</div>
                <div class="details-value">#${student.id}</div>

                <div class="details-label">Full Name:</div>
                <div class="details-value" style="font-weight: 600;">${escapeHtml(student.name)}</div>

                <div class="details-label">Email Address:</div>
                <div class="details-value">${escapeHtml(student.email)}</div>

                <div class="details-label">Date of Birth:</div>
                <div class="details-value">${student.date_of_birth}</div>

                <div class="details-label">Program / Course:</div>
                <div class="details-value">${student.course ? escapeHtml(student.course) : '<span style="color:var(--text-muted);">None</span>'}</div>

                <div class="details-label">Phone:</div>
                <div class="details-value">${student.phone ? escapeHtml(student.phone) : '<span style="color:var(--text-muted);">None</span>'}</div>

                <div class="details-label">Enrollment Date:</div>
                <div class="details-value">${student.enrollment_date || '<span style="color:var(--text-muted);">None</span>'}</div>

                <div class="details-label">Address:</div>
                <div class="details-value">${student.address ? escapeHtml(student.address) : '<span style="color:var(--text-muted);">None</span>'}</div>

                <div class="details-label">Created At:</div>
                <div class="details-value">${student.created_at ? new Date(student.created_at).toLocaleString() : '—'}</div>

                <div class="details-label">Last Updated:</div>
                <div class="details-value">${student.updated_at ? new Date(student.updated_at).toLocaleString() : '—'}</div>
            </div>
        `;

        detailsModal.classList.add('active');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function closeDetailsModal() {
    detailsModal.classList.remove('active');
}

// Delete confirmation
function promptDelete(studentId, studentName) {
    state.deleteCandidate = { id: studentId, name: studentName };
    document.getElementById('deleteTargetName').textContent = studentName;
    document.getElementById('deleteTargetId').textContent = studentId;
    deleteModal.classList.add('active');
}

function closeDeleteModal() {
    deleteModal.classList.remove('active');
    state.deleteCandidate = null;
}

async function executeDelete() {
    if (!state.deleteCandidate) return;

    const studentId = state.deleteCandidate.id;
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    confirmBtn.disabled = true;
    confirmBtn.textContent = 'Deleting...';

    try {
        const res = await fetch(`${API_BASE}/students/${studentId}`, {
            method: 'DELETE'
        });

        if (res.status === 204) {
            showToast('Student deleted successfully.', 'success');
            closeDeleteModal();
            // If deleting the last item on a page, adjust offset
            if (state.students.length === 1 && state.offset > 0) {
                state.offset = Math.max(0, state.offset - state.limit);
            }
            loadStudents();
        } else if (res.status === 404) {
            showToast('Student not found or already deleted.', 'error');
            closeDeleteModal();
            loadStudents();
        } else {
            const data = await res.json().catch(() => ({}));
            showToast(data.detail || 'Failed to delete student.', 'error');
        }
    } catch (err) {
        showToast(err.message || 'Network error occurred.', 'error');
    } finally {
        confirmBtn.disabled = false;
        confirmBtn.textContent = 'Delete Student';
    }
}

// UI Helpers
function showLoading(show) {
    loadingIndicator.style.display = show ? 'flex' : 'none';
    if (show) {
        emptyState.style.display = 'none';
    }
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    let icon = '';
    if (type === 'success') {
        icon = `<svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>`;
    } else if (type === 'error') {
        icon = `<svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>`;
    } else {
        icon = `<svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>`;
    }

    toast.innerHTML = `${icon}<span>${escapeHtml(message)}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
