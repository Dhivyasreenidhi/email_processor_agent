// API Configuration
const API_BASE_URL = 'http://localhost:5000';

// State management
let currentBillId = null;
let bills = [];
let allBills = []; // Store all bills for filtering
let isEditMode = false;
let originalEmailContent = '';

// Initialize the application
document.addEventListener('DOMContentLoaded', async () => {
    await fetchBills();
    renderBillsList();
    updateStats();
});

// Fetch bills from API
async function fetchBills() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/pending-approvals`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        bills = data.bills || [];
        allBills = [...bills]; // Store for search filtering
    } catch (error) {
        console.error('Error fetching bills:', error);
        showNotification('Failed to load bills. Please refresh the page.', 'error');
        bills = [];
        allBills = [];
    }
}

// Render bills list
function renderBillsList() {
    const billsList = document.getElementById('bills-list');
    const billsCount = document.getElementById('bills-count');
    const totalAmount = document.getElementById('total-amount');

    if (!bills || bills.length === 0) {
        billsList.innerHTML = `
            <div style="text-align: center; padding: 3rem; color: var(--text-light);">
                <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin: 0 auto 1rem; opacity: 0.3;">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                </svg>
                <p style="font-weight: 500; margin-bottom: 0.5rem;">No bills to review</p>
                <p style="font-size: 0.875rem;">All pending approvals have been processed</p>
            </div>
        `;
        billsCount.textContent = '0 bills';
        totalAmount.textContent = '$0';
        return;
    }

    billsList.innerHTML = bills.map(bill => `
        <div class="bill-item ${currentBillId === bill.id ? 'active' : ''}" onclick="selectBill('${bill.id}')">
            <div class="bill-icon">${getVendorInitials(bill.vendor)}</div>
            <div class="bill-content">
                <div class="bill-header">
                    <div>
                        <div class="bill-vendor">${bill.vendor}</div>
                        <div class="bill-number">${bill.id}</div>
                    </div>
                    <div class="bill-amount">$${bill.amount.toLocaleString()}</div>
                </div>
                <div class="bill-badges">
                    <span class="badge badge-status">${bill.status}</span>
                    <span class="badge badge-pending">${bill.emailStatus}</span>
                </div>
                <div class="bill-date">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                        <line x1="16" y1="2" x2="16" y2="6"></line>
                        <line x1="8" y1="2" x2="8" y2="6"></line>
                        <line x1="3" y1="10" x2="21" y2="10"></line>
                    </svg>
                    ${bill.date}
                </div>
            </div>
        </div>
    `).join('');

    // Update footer
    billsCount.textContent = `${bills.length} bill${bills.length !== 1 ? 's' : ''}`;
    const total = bills.reduce((sum, bill) => sum + bill.amount, 0);
    totalAmount.textContent = `$${total.toLocaleString()}`;
}

// Get vendor initials
function getVendorInitials(vendorName) {
    const words = vendorName.split(' ');
    if (words.length >= 2) {
        return (words[0][0] + words[1][0]).toUpperCase();
    }
    return vendorName.substring(0, 2).toUpperCase();
}

// Select a bill
function selectBill(billId) {
    currentBillId = billId;
    renderBillsList();
    showBillDetail(billId);
}

// Show bill detail
function showBillDetail(billId) {
    const bill = bills.find(b => b.id === billId);
    if (!bill) return;

    const detailPanel = document.getElementById('bill-detail');
    const emailContent = bill.emailContent || {};
    const hasEmailContent = emailContent.intro || emailContent.requestItems;

    detailPanel.innerHTML = `
        <div class="detail-header">
            <div class="detail-title">
                <h2>${bill.id}</h2>
                <div class="detail-actions">
                    <button class="btn btn-success" onclick="showEmailModal('${bill.id}')">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                        Ready to Pay
                    </button>
                    <button class="btn btn-reject" onclick="rejectBill('${bill.id}')">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M18 6L6 18M6 6l12 12"></path>
                        </svg>
                        Reject
                    </button>
                </div>
            </div>
            <div class="detail-meta">
                <div class="meta-item">
                    <div class="meta-label">Vendor</div>
                    <div class="meta-value">${bill.vendor || 'N/A'}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Amount</div>
                    <div class="meta-value">$${(bill.amount || 0).toLocaleString()}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Status</div>
                    <div class="meta-value">${bill.status || 'Pending'}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Date</div>
                    <div class="meta-value">${bill.date || 'N/A'}</div>
                </div>
            </div>
        </div>
        
        <div class="detail-tabs">
            <button class="tab-btn" onclick="switchTab('details')">Details</button>
            <button class="tab-btn" onclick="switchTab('matching')">Matching</button>
            <button class="tab-btn active" onclick="switchTab('communication')">Communication</button>
        </div>
        
        <div class="detail-content">
            ${hasEmailContent ? `
                <div class="email-draft-card">
                    <div class="draft-header">
                        <div class="draft-icon">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                                <polyline points="22,6 12,13 2,6"></polyline>
                            </svg>
                        </div>
                        <div class="draft-title">
                            <h3>Email Draft Ready for Your Approval</h3>
                            <p class="draft-subtitle">Our AI detected discrepancies in this bill during the matching process and has composed an email draft</p>
                        </div>
                    </div>
                    
                    <div class="draft-content">
                        <div class="draft-intro">
                            ${emailContent.intro || 'Email draft available for review.'}
                        </div>
                        
                        ${emailContent.requestItems && emailContent.requestItems.length > 0 ? `
                            <p style="margin-top: 1rem; font-weight: 600;">While you need to do:</p>
                            <ul class="draft-list">
                                ${emailContent.requestItems.map(item => `<li>${item}</li>`).join('')}
                            </ul>
                        ` : ''}
                        
                        ${emailContent.warning ? `
                            <div class="email-warning">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                                    <line x1="12" y1="9" x2="12" y2="13"></line>
                                    <line x1="12" y1="17" x2="12.01" y2="17"></line>
                                </svg>
                                <span>${emailContent.warning}</span>
                            </div>
                        ` : ''}
                    </div>
                    
                    <div class="draft-footer">
                        <button class="btn btn-primary" onclick="showEmailModal('${bill.id}')">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M22 2L11 13"></path>
                                <path d="M22 2L15 22L11 13L2 9L22 2Z"></path>
                            </svg>
                            Review Email
                        </button>
                    </div>
                </div>
            ` : ''}
            
            <div class="communication-empty">
                <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                    <polyline points="22,6 12,13 2,6"></polyline>
                </svg>
                <h3>No communication history</h3>
            </div>
        </div>
    `;
}

// Show email modal
function showEmailModal(billId) {
    const bill = bills.find(b => b.id === billId);
    if (!bill) return;

    const modal = document.getElementById('email-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalVendorName = document.getElementById('modal-vendor-name');
    const modalBillNumber = document.getElementById('modal-bill-number');
    const modalDiscrepancies = document.getElementById('modal-discrepancies');
    const modalDiscrepancyList = document.getElementById('modal-discrepancy-list');
    const modalEmailContent = document.getElementById('modal-email-content');

    // Reset edit mode
    isEditMode = false;
    updateEditButton();

    modalTitle.textContent = 'Review Email to Vendor';
    modalVendorName.textContent = bill.vendor || 'Unknown Vendor';
    modalBillNumber.textContent = `${bill.id} • $${(bill.amount || 0).toLocaleString()}`;

    // Render discrepancy badges
    const discrepancyCount = bill.discrepancies?.length || 0;
    modalDiscrepancies.innerHTML = `
        <span class="discrepancy-badge">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
            ${discrepancyCount} Discrepanc${discrepancyCount !== 1 ? 'ies' : 'y'}
        </span>
    `;

    // Render discrepancy list
    modalDiscrepancyList.innerHTML = (bill.emailContent?.discrepancySummary || bill.discrepancies || []).map(disc => `
        <div class="discrepancy-item">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="15" y1="9" x2="9" y2="15"></line>
                <line x1="9" y1="9" x2="15" y2="15"></line>
            </svg>
            <div class="discrepancy-content">
                <strong>${disc.title || disc.type || 'Unknown Issue'}</strong>
                <small>${disc.details || ''}</small>
            </div>
        </div>
    `).join('');

    // Generate and store email content
    const emailContent = bill.emailContent || {};
    const emailHTML = generateEmailHTML(bill);
    originalEmailContent = emailHTML;

    modalEmailContent.innerHTML = emailHTML;
    modalEmailContent.setAttribute('contenteditable', 'false');

    modal.classList.add('active');
}

// Generate email HTML
function generateEmailHTML(bill) {
    const emailContent = bill.emailContent || {};

    console.log('generateEmailHTML called');
    console.log('emailContent:', emailContent);
    console.log('htmlBody exists?', !!emailContent.htmlBody);
    console.log('htmlBody length:', emailContent.htmlBody ? emailContent.htmlBody.length : 0);

    // If we have the actual HTML body from the template, use it!
    if (emailContent.htmlBody && emailContent.htmlBody.trim().length > 0) {
        console.log('Using actual HTML body from backend');
        return emailContent.htmlBody;
    }

    console.log('Falling back to simple preview');
    // Otherwise, fall back to the simple preview (for backward compatibility)
    const greeting = emailContent.greeting || `Dear ${bill.vendor || 'Vendor'} Team,`;
    const intro = emailContent.intro || 'We have identified discrepancies in your recent bill submission.';
    const discrepancies = emailContent.discrepancySummary || bill.discrepancies || [];

    return `
        <div class="email-greeting">${greeting}</div>
        <div class="email-body">
            <p>${intro}</p>
        </div>
        
        <h4 class="email-section-title">DISCREPANCY SUMMARY</h4>
        <ul class="email-list">
            ${discrepancies.map((disc) => `
                <li><strong>${disc.title || disc.type}:</strong> ${disc.details || ''}</li>
            `).join('')}
        </ul>
        
        <h4 class="email-section-title">REQUEST FOR ACTION</h4>
        <div class="email-body">
            <p>To proceed with payment processing, please provide the missing information at your earliest convenience. You can reply to this email with the required details or contact our accounts payable team.</p>
            <p style="margin-top: 1rem;">Thank you for your prompt attention to this matter.</p>
        </div>
        
        <div class="email-body" style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--gray-200);">
            <p style="margin-bottom: 0.5rem;"><strong>Best regards,</strong></p>
            <p style="margin-bottom: 0.25rem;">GenBooks Accounts Payable Team</p>
            <p style="font-size: 0.875rem; color: var(--text-secondary);">Automated by DRA System</p>
        </div>
    `;
}

// Toggle email editing
function toggleEditEmail() {
    const modalEmailContent = document.getElementById('modal-email-content');
    const editBtn = document.getElementById('edit-btn');
    const editBtnText = document.getElementById('edit-btn-text');

    isEditMode = !isEditMode;

    if (isEditMode) {
        // Enter edit mode
        originalEmailContent = modalEmailContent.innerHTML;
        modalEmailContent.setAttribute('contenteditable', 'true');
        modalEmailContent.classList.add('editing');
        modalEmailContent.focus();
        editBtnText.textContent = 'Save Changes';
        editBtn.classList.add('btn-success');
        editBtn.classList.remove('btn-secondary');
    } else {
        // Exit edit mode (save changes)
        modalEmailContent.setAttribute('contenteditable', 'false');
        modalEmailContent.classList.remove('editing');
        editBtnText.textContent = 'Edit Email';
        editBtn.classList.remove('btn-success');
        editBtn.classList.add('btn-secondary');
        showNotification('Email changes saved', 'success');
    }
}

// Update edit button state
function updateEditButton() {
    const editBtn = document.getElementById('edit-btn');
    const editBtnText = document.getElementById('edit-btn-text');

    if (editBtn && editBtnText) {
        editBtnText.textContent = 'Edit Email';
        editBtn.classList.remove('btn-success');
        editBtn.classList.add('btn-secondary');
    }
}

// Close email modal
function closeEmailModal() {
    const modal = document.getElementById('email-modal');
    modal.classList.remove('active');
}

// Approve and send email
async function approveAndSend() {
    const billId = currentBillId;
    const bill = bills.find(b => b.id === billId);

    if (!bill) {
        showNotification('Bill not found', 'error');
        return;
    }

    // Get the email content (may have been edited)
    const modalEmailContent = document.getElementById('modal-email-content');
    const emailContent = modalEmailContent.innerHTML;

    // Get buttons
    const approveBtn = document.getElementById('approve-btn');
    const rejectBtn = document.getElementById('reject-btn');
    const editBtn = document.getElementById('edit-btn');

    // Set loading state
    setButtonLoading(approveBtn, true, 'Sending Email...');
    rejectBtn.disabled = true;
    editBtn.disabled = true;

    try {
        // Send approval to backend
        const response = await fetch(`${API_BASE_URL}/api/approve`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                bill_id: billId,
                request_id: bill.request_id || billId,
                email_content: emailContent,
                vendor_email: bill.vendor_email || '',
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        // Success! Change button to success state briefly
        setButtonLoading(approveBtn, false);
        setButtonSuccess(approveBtn, 'Email Sent!');

        // Wait a moment to show success state
        await new Promise(resolve => setTimeout(resolve, 1000));

        showNotification(`Email approved and sent to ${bill.vendor}`, 'success');

        // Remove from bills list
        bills = bills.filter(b => b.id !== billId);
        currentBillId = null;

        // Update UI
        renderBillsList();
        updateStats();

        // Show empty state in detail panel
        document.getElementById('bill-detail').innerHTML = `
            <div class="empty-detail">
                <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                </svg>
                <p>Select a bill to view details</p>
            </div>
        `;

        closeEmailModal();
    } catch (error) {
        console.error('Error approving email:', error);

        // Reset button state on error
        setButtonLoading(approveBtn, false);
        rejectBtn.disabled = false;
        editBtn.disabled = false;

        showNotification('Failed to approve and send email. Please try again.', 'error');
    }
}

// Helper function to set button loading state
function setButtonLoading(button, isLoading, loadingText = 'Loading...') {
    if (isLoading) {
        button.disabled = true;
        button.classList.add('btn-loading');
        button.innerHTML = `
            <svg class="spinner" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10" opacity="0.25"/>
                <path d="M12 2 A10 10 0 0 1 22 12" opacity="0.75"/>
            </svg>
            ${loadingText}
        `;
    } else {
        button.disabled = false;
        button.classList.remove('btn-loading');
        button.innerHTML = `
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
            Approve & Send Email
        `;
    }
}

// Helper function to set button success state
function setButtonSuccess(button, successText = 'Success!') {
    button.classList.remove('btn-loading');
    button.classList.add('btn-success-state');
    button.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
        ${successText}
    `;
}

// Reject a bill
async function rejectBill(billId) {
    console.log('rejectBill called with billId:', billId);
    console.log('Current bills array:', bills);

    const bill = bills.find(b => b.id === billId);

    if (!bill) {
        console.error('Bill not found! billId:', billId, 'bills:', bills);
        showNotification('Bill not found. Please refresh the page.', 'error');
        return;
    }

    // Show confirmation dialog
    const confirmed = confirm(
        `Are you sure you want to reject this email?\n\n` +
        `Vendor: ${bill.vendor}\n` +
        `Amount: $${bill.amount.toLocaleString()}\n\n` +
        `This email will NOT be sent to the vendor.`
    );

    if (!confirmed) {
        console.log('Rejection cancelled by user');
        return;
    }

    // Optional: Ask for rejection reason
    const reason = prompt('Rejection reason (optional):');

    try {
        console.log('Sending rejection request to API...');
        // Send rejection to backend
        const response = await fetch(`${API_BASE_URL}/api/reject`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                bill_id: billId,
                request_id: bill.request_id || billId,
                reason: reason || 'No reason provided',
            }),
        });

        console.log('API response status:', response.status);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('API error:', errorText);
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        console.log('Rejection successful:', result);
        showNotification(`Email to ${bill.vendor} has been rejected and removed`, 'success');

        // Remove from bills list
        bills = bills.filter(b => b.id !== billId);
        currentBillId = null;

        // Update UI
        renderBillsList();
        updateStats();

        // Show empty state in detail panel
        document.getElementById('bill-detail').innerHTML = `
            <div class="empty-detail">
                <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                </svg>
                <p>Select a bill to view details</p>
            </div>
        `;

    } catch (error) {
        console.error('Error rejecting bill:', error);
        showNotification('Failed to reject. Please try again.', 'error');
    }
}

// Reject current bill from modal
async function rejectCurrentBill() {
    if (!currentBillId) {
        showNotification('No bill selected', 'error');
        return;
    }

    // Store the bill ID before closing modal (modal might reset currentBillId)
    const billIdToReject = currentBillId;

    // Close the modal first
    closeEmailModal();

    // Then reject the bill with the stored ID
    await rejectBill(billIdToReject);
}

// Update stats
function updateStats() {
    // This would be populated from actual data
    // For now, just showing the count of bills
}

// Switch tab
function switchTab(tabName) {
    const tabs = document.querySelectorAll('.tab-btn');
    tabs.forEach(tab => tab.classList.remove('active'));

    const activeTab = Array.from(tabs).find(tab =>
        tab.textContent.toLowerCase().includes(tabName)
    );
    if (activeTab) {
        activeTab.classList.add('active');
    }
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    const notificationMessage = document.getElementById('notification-message');

    notificationMessage.textContent = message;
    notification.classList.add('show');

    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// Search functionality
const searchInput = document.getElementById('search-input');
if (searchInput) {
    searchInput.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase().trim();

        if (searchTerm === '') {
            bills = [...allBills];
        } else {
            bills = allBills.filter(bill =>
                (bill.vendor || '').toLowerCase().includes(searchTerm) ||
                (bill.id || '').toLowerCase().includes(searchTerm) ||
                (bill.status || '').toLowerCase().includes(searchTerm)
            );
        }

        renderBillsList();
    });
}

// Handle view toggle
const viewToggleBtns = document.querySelectorAll('.view-toggle-btn');
viewToggleBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        viewToggleBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
    });
});

// Close modal on escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeEmailModal();
    }
});

// Auto-select first bill on load
if (bills.length > 0) {
    setTimeout(() => {
        selectBill(bills[0].id);
    }, 100);
}
