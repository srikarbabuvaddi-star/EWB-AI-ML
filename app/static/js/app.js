/**
 * Students Database Management Application
 * Academic Administration Dashboard Client Script
 * Internship Assignment — EWB Edu Tech Pvt. Ltd.
 *
 * Connects directly to the FastAPI REST API backed by persistent SQLite storage.
 */

const API_BASE = window.location.origin;

// Application State
const state = {
    students: [],
    totalCount: 0,
    limit: 10,
    offset: 0,
    search: '',
    course: '',
    activeStudentId: null,
    deleteCandidate: null,
    currentDetailStudent: null,
    apiHealthy: false
};

// DOM Elements
const studentsTableBody = document.getElementById('studentsTableBody');
const emptyState = document.getElementById('emptyState');
const emptyStateHeading = document.getElementById('emptyStateHeading');
const emptyStateText = document.getElementById('emptyStateText');
const loadingIndicator = document.getElementById('loadingIndicator');
const searchInput = document.getElementById('searchInput');
const courseFilter = document.getElementById('courseFilter');
const pageSizeSelect = document.getElementById('pageSizeSelect');
const paginationInfo = document.getElementById('paginationInfo');
const pageIndicator = document.getElementById('pageIndicator');
const prevPageBtn = document.getElementById('prevPageBtn');
const nextPageBtn = document.getElementById('nextPageBtn');
const refreshBtn = document.getElementById('refreshBtn');
const resetFiltersBtn = document.getElementById('resetFiltersBtn');
const connectionAlert = document.getElementById('connectionAlert');
const connectionAlertText = document.getElementById('connectionAlertText');

// Modals & Forms
const studentModal = document.getElementById('studentModal');
const studentForm = document.getElementById('studentForm');
const modalTitle = document.getElementById('modalTitle');
const saveStudentBtn = document.getElementById('saveStudentBtn');
const deleteModal = document.getElementById('deleteModal');
const detailsModal = document.getElementById('detailsModal');
const detailsContent = document.getElementById('detailsContent');
const detailsEditBtn = document.getElementById('detailsEditBtn');
const detailsDeleteBtn = document.getElementById('detailsDeleteBtn');

// KPI Counters
const totalStudentsCount = document.getElementById('totalStudentsCount');
const activeCoursesCount = document.getElementById('activeCoursesCount');
const currentYearCount = document.getElementById('currentYearCount');
const healthStatusBadge = document.getElementById('healthStatusBadge');

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

async function initApp() {
    setupEventListeners();
    await checkHealth();
    await loadStudents();
}

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

    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            clearTimeout(debounceTimer);
            state.search = e.target.value.trim();
            state.offset = 0;
            loadStudents();
        }
    });

    // Course filter
    courseFilter.addEventListener('change', (e) => {
        state.course = e.target.value;
        state.offset = 0;
        loadStudents();
    });

    // Page size selector
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

    // Refresh & Reset buttons
    refreshBtn.addEventListener('click', () => {
        checkHealth();
        loadStudents();
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

    // Delete confirmation button
    document.getElementById('confirmDeleteBtn').addEventListener('click', executeDelete);

    // Details modal action buttons
    detailsEditBtn.addEventListener('click', () => {
        if (state.currentDetailStudent) {
            const id = state.currentDetailStudent.id;
            closeDetailsModal();
            openEditModal(id);
        }
    });

    detailsDeleteBtn.addEventListener('click', () => {
        if (state.currentDetailStudent) {
            const student = state.currentDetailStudent;
            closeDetailsModal();
            promptDelete(student.id, student.name);
        }
    });

    // Keyboard accessibility: ESC key closes open modals
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (studentModal.classList.contains('active')) closeStudentModal();
            if (detailsModal.classList.contains('active')) closeDetailsModal();
            if (deleteModal.classList.contains('active')) closeDeleteModal();
        }
    });

    // Backdrop click dismissals
    [studentModal, detailsModal, deleteModal].forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
}

// --------------------------------------------------------------------------
// API Health Check
// --------------------------------------------------------------------------
async function checkHealth() {
    try {
        const res = await fetch(`${API_BASE}/health`, { cache: 'no-store' });
        if (!res.ok) throw new Error(`Health status ${res.status}`);

        const data = await res.json();
        if (data.status === 'healthy') {
            state.apiHealthy = true;
            healthStatusBadge.className = 'status-badge';
            healthStatusBadge.innerHTML = `<span class="status-dot"></span> System Online • SQLite Connected`;
            hideConnectionAlert();
            return true;
        }
        throw new Error('Database service reporting unhealthy state');
    } catch (err) {
        state.apiHealthy = false;
        healthStatusBadge.className = 'status-badge offline';
        healthStatusBadge.innerHTML = `<span class="status-dot"></span> System Offline`;
        showConnectionAlert(`API Connection Error: Unable to reach backend server at ${API_BASE}.`);
        return false;
    }
}

function showConnectionAlert(message) {
    if (connectionAlertText) connectionAlertText.textContent = message;
    if (connectionAlert) connectionAlert.style.display = 'flex';
}

function hideConnectionAlert() {
    if (connectionAlert) connectionAlert.style.display = 'none';
}

async function retryConnection() {
    showToast('Retrying connection to backend API...', 'info');
    const healthy = await checkHealth();
    if (healthy) {
        showToast('Successfully reconnected to API server!', 'success');
        loadStudents();
    } else {
        showToast('Connection attempt failed. Ensure uvicorn is running.', 'error');
    }
}

// --------------------------------------------------------------------------
// Load Students (GET /students)
// --------------------------------------------------------------------------
async function loadStudents() {
    showLoading(true);
    clearFormErrors();

    try {
        const params = new URLSearchParams();
        params.append('limit', state.limit);
        params.append('offset', state.offset);
        if (state.search) params.append('search', state.search);
        if (state.course) params.append('course', state.course);

        const res = await fetch(`${API_BASE}/students?${params.toString()}`, {
            headers: { 'Accept': 'application/json' },
            cache: 'no-store'
        });

        if (!res.ok) {
            throw new Error(`Failed to retrieve student records (HTTP ${res.status})`);
        }

        const data = await res.json();

        // Total count from X-Total-Count response header
        const totalHeader = res.headers.get('X-Total-Count');
        state.totalCount = totalHeader !== null ? parseInt(totalHeader, 10) : data.length;
        state.students = data;

        renderStudentsTable();
        updatePaginationControls();
        updateKPICounters();
        hideConnectionAlert();
    } catch (err) {
        console.error('Error fetching students:', err);
        showLoading(false);
        showConnectionAlert(`Error loading student records: ${err.message}`);
        showToast(err.message, 'error');
    }
}

// --------------------------------------------------------------------------
// Render Table
// --------------------------------------------------------------------------
function renderStudentsTable() {
    showLoading(false);
    studentsTableBody.innerHTML = '';

    if (state.students.length === 0) {
        emptyState.style.display = 'block';
        if (state.search || state.course) {
            emptyStateHeading.textContent = 'No Matching Records';
            emptyStateText.textContent = `No students found matching your search "${state.search || state.course}". Try clearing filters.`;
        } else {
            emptyStateHeading.textContent = 'No Students Registered';
            emptyStateText.textContent = 'The SQLite database currently contains no student records. Add your first student to begin.';
        }
        return;
    }

    emptyState.style.display = 'none';

    state.students.forEach((student) => {
        const tr = document.createElement('tr');

        // Initials avatar
        const initials = student.name
            .trim()
            .split(/\s+/)
            .map(part => part[0])
            .join('')
            .substring(0, 2)
            .toUpperCase() || 'ST';

        // Course styling class
        let courseClass = '';
        const cLower = (student.course || '').toLowerCase();
        if (cLower.includes('computer')) courseClass = 'cs';
        else if (cLower.includes('data')) courseClass = 'ds';
        else if (cLower.includes('intelligence') || cLower.includes('ai')) courseClass = 'ai';
        else if (cLower.includes('information')) courseClass = 'it';

        const courseDisplay = student.course
            ? `<span class="course-badge ${courseClass}">${escapeHtml(student.course)}</span>`
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
                    <div class="avatar-badge" aria-hidden="true">${initials}</div>
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
                    <button type="button" class="btn btn-secondary btn-icon" title="View Profile" onclick="viewStudentDetails(${student.id})" aria-label="View profile for ${escapeHtml(student.name)}">
                        <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                        </svg>
                    </button>
                    <button type="button" class="btn btn-secondary btn-icon" title="Edit Student" onclick="openEditModal(${student.id})" aria-label="Edit student ${escapeHtml(student.name)}">
                        <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                        </svg>
                    </button>
                    <button type="button" class="btn btn-outline-danger btn-icon" title="Delete Student" onclick="promptDelete(${student.id}, '${escapeHtml(student.name)}')" aria-label="Delete student ${escapeHtml(student.name)}">
                        <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                        </svg>
                    </button>
                </div>
            </td>
        `;

        studentsTableBody.appendChild(tr);
    });
}

// --------------------------------------------------------------------------
// Pagination Controls
// --------------------------------------------------------------------------
function updatePaginationControls() {
    const total = state.totalCount;
    const start = total === 0 ? 0 : state.offset + 1;
    const end = Math.min(state.offset + state.limit, total);

    paginationInfo.textContent = `Showing ${start}–${end} of ${total} students`;

    const currentPage = total === 0 ? 1 : Math.floor(state.offset / state.limit) + 1;
    const totalPages = Math.max(1, Math.ceil(total / state.limit));
    pageIndicator.textContent = `Page ${currentPage} of ${totalPages}`;

    prevPageBtn.disabled = state.offset === 0;
    nextPageBtn.disabled = state.offset + state.limit >= total;
}

// --------------------------------------------------------------------------
// KPI Statistics Overview
// --------------------------------------------------------------------------
function updateKPICounters() {
    totalStudentsCount.textContent = state.totalCount;

    // Distinct courses currently represented
    const courses = new Set(state.students.map(s => s.course).filter(Boolean));
    activeCoursesCount.textContent = courses.size;

    // Enrolled in current year
    const currentYear = new Date().getFullYear().toString();
    const currentYearStudents = state.students.filter(
        s => s.enrollment_date && s.enrollment_date.startsWith(currentYear)
    );
    currentYearCount.textContent = currentYearStudents.length;
}

// --------------------------------------------------------------------------
// Modal Controls & Form Logic (Add / Edit)
// --------------------------------------------------------------------------
function openAddModal() {
    state.activeStudentId = null;
    modalTitle.textContent = 'Add New Student';
    saveStudentBtn.textContent = 'Save Student';
    clearFormErrors();
    studentForm.reset();

    const todayStr = new Date().toISOString().split('T')[0];
    document.getElementById('enrollmentDateInput').value = todayStr;
    document.getElementById('dobInput').max = todayStr;

    studentModal.classList.add('active');
    setTimeout(() => document.getElementById('nameInput').focus(), 100);
}

async function openEditModal(studentId) {
    state.activeStudentId = studentId;
    modalTitle.textContent = `Edit Student #${studentId}`;
    saveStudentBtn.textContent = 'Update Student';
    clearFormErrors();
    studentForm.reset();

    try {
        const res = await fetch(`${API_BASE}/students/${studentId}`, { cache: 'no-store' });
        if (!res.ok) {
            if (res.status === 404) throw new Error(`Student #${studentId} was not found.`);
            throw new Error(`Failed to load student data (HTTP ${res.status})`);
        }

        const student = await res.json();
        document.getElementById('nameInput').value = student.name || '';
        document.getElementById('emailInput').value = student.email || '';
        document.getElementById('dobInput').value = student.date_of_birth || '';
        document.getElementById('dobInput').max = new Date().toISOString().split('T')[0];
        document.getElementById('courseInput').value = student.course || '';
        document.getElementById('phoneInput').value = student.phone || '';
        document.getElementById('enrollmentDateInput').value = student.enrollment_date || '';
        document.getElementById('addressInput').value = student.address || '';

        studentModal.classList.add('active');
        setTimeout(() => document.getElementById('nameInput').focus(), 100);
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function closeStudentModal() {
    studentModal.classList.remove('active');
    state.activeStudentId = null;
    clearFormErrors();
}

function clearFormErrors() {
    document.querySelectorAll('.field-error').forEach(el => {
        el.textContent = '';
        el.classList.remove('active');
    });
    document.querySelectorAll('.form-input, .form-select').forEach(el => {
        el.classList.remove('is-invalid');
    });
}

function showFieldError(fieldId, errorId, message) {
    const input = document.getElementById(fieldId);
    const err = document.getElementById(errorId);
    if (input) input.classList.add('is-invalid');
    if (err) {
        err.textContent = message;
        err.classList.add('active');
    }
}

async function handleFormSubmit(e) {
    e.preventDefault();
    clearFormErrors();

    const name = document.getElementById('nameInput').value.trim();
    const email = document.getElementById('emailInput').value.trim();
    const date_of_birth = document.getElementById('dobInput').value;
    const course = document.getElementById('courseInput').value.trim() || null;
    const phone = document.getElementById('phoneInput').value.trim() || null;
    const enrollment_date = document.getElementById('enrollmentDateInput').value || null;
    const address = document.getElementById('addressInput').value.trim() || null;

    let hasClientErrors = false;

    // Client-side validations
    if (!name) {
        showFieldError('nameInput', 'nameError', 'Student full name is required.');
        hasClientErrors = true;
    } else if (name.length < 2) {
        showFieldError('nameInput', 'nameError', 'Name must contain at least 2 characters.');
        hasClientErrors = true;
    }

    if (!email) {
        showFieldError('emailInput', 'emailError', 'Student email address is required.');
        hasClientErrors = true;
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        showFieldError('emailInput', 'emailError', 'Enter a valid email address (e.g. name@domain.com).');
        hasClientErrors = true;
    }

    if (!date_of_birth) {
        showFieldError('dobInput', 'dobError', 'Date of birth is required.');
        hasClientErrors = true;
    } else {
        const dobDate = new Date(date_of_birth);
        const today = new Date();
        if (dobDate > today) {
            showFieldError('dobInput', 'dobError', 'Date of birth cannot be in the future.');
            hasClientErrors = true;
        } else if (dobDate.getFullYear() < 1900) {
            showFieldError('dobInput', 'dobError', 'Date of birth cannot be prior to the year 1900.');
            hasClientErrors = true;
        }
    }

    if (phone && !/^\+?[0-9\s\-().]{7,25}$/.test(phone)) {
        showFieldError('phoneInput', 'phoneError', 'Phone number must contain between 7 and 25 valid digits/symbols.');
        hasClientErrors = true;
    }

    if (hasClientErrors) return;

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
    saveStudentBtn.textContent = 'Saving to SQLite...';

    try {
        let res;
        if (state.activeStudentId) {
            // PUT /students/{student_id}
            res = await fetch(`${API_BASE}/students/${state.activeStudentId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        } else {
            // POST /students
            res = await fetch(`${API_BASE}/students`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        }

        const data = await res.json();

        if (res.status === 201 || res.status === 200) {
            showToast(state.activeStudentId ? 'Student record updated successfully!' : 'Student record created successfully!', 'success');
            closeStudentModal();
            loadStudents();
        } else if (res.status === 409) {
            showFieldError('emailInput', 'emailError', data.detail || 'Email is already taken by another student.');
            showToast(data.detail || 'Duplicate email conflict.', 'error');
        } else if (res.status === 422) {
            if (Array.isArray(data.detail)) {
                data.detail.forEach(errItem => {
                    const field = errItem.loc[errItem.loc.length - 1];
                    if (field === 'name') showFieldError('nameInput', 'nameError', errItem.msg);
                    else if (field === 'email') showFieldError('emailInput', 'emailError', errItem.msg);
                    else if (field === 'date_of_birth') showFieldError('dobInput', 'dobError', errItem.msg);
                    else if (field === 'phone') showFieldError('phoneInput', 'phoneError', errItem.msg);
                });
                showToast('Please correct the validation errors in the form.', 'error');
            } else {
                showToast(data.detail || 'Validation error occurred.', 'error');
            }
        } else {
            showToast(data.detail || 'An unexpected server error occurred.', 'error');
        }
    } catch (err) {
        console.error('API submission error:', err);
        showToast('Network error: Unable to contact the backend server.', 'error');
    } finally {
        saveStudentBtn.disabled = false;
        saveStudentBtn.textContent = state.activeStudentId ? 'Update Student' : 'Save Student';
    }
}

// --------------------------------------------------------------------------
// Student Detail View (GET /students/{id})
// --------------------------------------------------------------------------
async function viewStudentDetails(studentId) {
    try {
        const res = await fetch(`${API_BASE}/students/${studentId}`, { cache: 'no-store' });
        if (!res.ok) {
            if (res.status === 404) throw new Error('Student profile was not found.');
            throw new Error(`Failed to retrieve profile (HTTP ${res.status})`);
        }

        const student = await res.json();
        state.currentDetailStudent = student;

        const initials = student.name
            .trim()
            .split(/\s+/)
            .map(part => part[0])
            .join('')
            .substring(0, 2)
            .toUpperCase() || 'ST';

        detailsContent.innerHTML = `
            <div class="details-profile-header">
                <div class="details-avatar">${initials}</div>
                <div class="details-headline">
                    <h3>${escapeHtml(student.name)}</h3>
                    <p>${student.course ? escapeHtml(student.course) : 'Enrolled Student'} &bull; ID #${student.id}</p>
                </div>
            </div>

            <div class="details-list">
                <div class="details-label">Student ID:</div>
                <div class="details-value">#${student.id}</div>

                <div class="details-label">Full Name:</div>
                <div class="details-value" style="font-weight: 600;">${escapeHtml(student.name)}</div>

                <div class="details-label">Email Address:</div>
                <div class="details-value"><a href="mailto:${escapeHtml(student.email)}" style="color:var(--primary-600);">${escapeHtml(student.email)}</a></div>

                <div class="details-label">Date of Birth:</div>
                <div class="details-value">${student.date_of_birth}</div>

                <div class="details-label">Course / Program:</div>
                <div class="details-value">${student.course ? `<span class="course-badge">${escapeHtml(student.course)}</span>` : '<span style="color:var(--text-muted);">None</span>'}</div>

                <div class="details-label">Phone Number:</div>
                <div class="details-value">${student.phone ? escapeHtml(student.phone) : '<span style="color:var(--text-muted);">None</span>'}</div>

                <div class="details-label">Enrollment Date:</div>
                <div class="details-value">${student.enrollment_date || '<span style="color:var(--text-muted);">None</span>'}</div>

                <div class="details-label">Residential Address:</div>
                <div class="details-value">${student.address ? escapeHtml(student.address) : '<span style="color:var(--text-muted);">None</span>'}</div>

                <div class="details-label">Record Created:</div>
                <div class="details-value">${student.created_at ? new Date(student.created_at).toLocaleString() : '—'}</div>

                <div class="details-label">Last Modified:</div>
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
    state.currentDetailStudent = null;
}

// --------------------------------------------------------------------------
// Delete Confirmation & Execution (DELETE /students/{id})
// --------------------------------------------------------------------------
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
    confirmBtn.textContent = 'Deleting from SQLite...';

    try {
        const res = await fetch(`${API_BASE}/students/${studentId}`, {
            method: 'DELETE'
        });

        if (res.status === 204) {
            showToast('Student record deleted permanently from SQLite.', 'success');
            closeDeleteModal();

            // Adjust offset if last item on page deleted
            if (state.students.length === 1 && state.offset > 0) {
                state.offset = Math.max(0, state.offset - state.limit);
            }
            loadStudents();
        } else if (res.status === 404) {
            showToast('Student was not found or was already deleted.', 'error');
            closeDeleteModal();
            loadStudents();
        } else {
            const data = await res.json().catch(() => ({}));
            showToast(data.detail || 'Failed to delete student record.', 'error');
        }
    } catch (err) {
        showToast('Network error while deleting student.', 'error');
    } finally {
        confirmBtn.disabled = false;
        confirmBtn.textContent = 'Delete Student';
    }
}

// --------------------------------------------------------------------------
// UI Helpers & Utilities
// --------------------------------------------------------------------------
function showLoading(show) {
    if (loadingIndicator) loadingIndicator.style.display = show ? 'flex' : 'none';
    if (show && emptyState) emptyState.style.display = 'none';
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    let icon = '';
    if (type === 'success') {
        icon = `<svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>`;
    } else if (type === 'error') {
        icon = `<svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>`;
    } else {
        icon = `<svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>`;
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
    if (!str && str !== 0) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
