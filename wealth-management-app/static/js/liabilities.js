// Liabilities Page JavaScript

let liabilities = [];

// Initialize page
document.addEventListener('DOMContentLoaded', async function() {
    await loadLiabilities();
    setupEventListeners();
});

// Load liabilities
async function loadLiabilities() {
    try {
        const response = await apiRequest('/api/portfolio/liabilities');
        if (response) {
            liabilities = response;
            await renderLiabilitiesTable();
        }
    } catch (error) {
        console.error('Failed to load liabilities:', error);
        showNotification('Failed to load liabilities', 'error');
    }
}

// Render liabilities table (same conversion rules as assets / server)
async function renderLiabilitiesTable() {
    const tbody = document.getElementById('liabilities-table-body');
    
    if (liabilities.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="empty-state">No liabilities found. Click "Add Liability" to get started.</td></tr>';
        return;
    }
    
    tbody.innerHTML = '';
    
    for (const liability of liabilities) {
        const amountInUSD = await convertCurrencyAmount(liability.outstanding_amount, liability.currency, 'USD');
        const amountInINR = await convertCurrencyAmount(liability.outstanding_amount, liability.currency, 'INR');
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td>${formatLiabilityType(liability.liability_type)}</td>
            <td>${liability.name}</td>
            <td>${formatCurrency(amountInUSD, 'USD')}</td>
            <td>${formatIndianCurrency(amountInINR)}</td>
            <td>${liability.currency}</td>
            <td>${liability.interest_rate ? liability.interest_rate + '%' : '-'}</td>
            <td>${liability.due_date ? new Date(liability.due_date).toLocaleDateString() : '-'}</td>
            <td>
                <button class="icon-btn" onclick="deleteLiability(${liability.id})" title="Delete">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    }
}

// Format liability type
function formatLiabilityType(type) {
    return type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
}

// Setup event listeners
function setupEventListeners() {
    const addLiabilityBtn = document.getElementById('add-liability-btn');
    const liabilityForm = document.getElementById('liability-form');
    
    if (addLiabilityBtn) {
        addLiabilityBtn.addEventListener('click', () => openModal('liability-modal'));
    }
    
    if (liabilityForm) {
        liabilityForm.addEventListener('submit', handleLiabilitySubmit);
    }
}

// Handle liability form submission
async function handleLiabilitySubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const liabilityData = {
        liability_type: formData.get('liability_type'),
        name: formData.get('name'),
        description: formData.get('description'),
        outstanding_amount: parseFloat(formData.get('outstanding_amount')),
        currency: formData.get('currency'),
        interest_rate: formData.get('interest_rate') ? parseFloat(formData.get('interest_rate')) : null,
        due_date: formData.get('due_date') || null
    };
    
    try {
        const response = await apiRequest('/api/portfolio/liabilities', {
            method: 'POST',
            body: JSON.stringify(liabilityData)
        });
        
        if (response) {
            showNotification('Liability added successfully', 'success');
            closeModal('liability-modal');
            e.target.reset();
            await loadLiabilities();
        }
    } catch (error) {
        console.error('Failed to add liability:', error);
        showNotification('Failed to add liability', 'error');
    }
}

// Delete liability
async function deleteLiability(liabilityId) {
    if (!confirm('Are you sure you want to delete this liability?')) {
        return;
    }
    
    try {
        const response = await apiRequest(`/api/portfolio/liabilities/${liabilityId}`, {
            method: 'DELETE'
        });
        
        if (response) {
            showNotification('Liability deleted successfully', 'success');
            await loadLiabilities();
        }
    } catch (error) {
        console.error('Failed to delete liability:', error);
        showNotification('Failed to delete liability', 'error');
    }
}

