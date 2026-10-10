// Assets Page JavaScript

let assets = [];

// Initialize page
document.addEventListener('DOMContentLoaded', async function() {
    await loadAssets();
    setupEventListeners();
});

// Load assets
async function loadAssets() {
    try {
        const response = await apiRequest('/api/portfolio/assets');
        if (response) {
            assets = response;
            await renderAssetsTable();
        }
    } catch (error) {
        console.error('Failed to load assets:', error);
        showNotification('Failed to load assets', 'error');
    }
}

// Render assets table (uses convertCurrencyAmount from main.js — same math as portfolio summary API)
async function renderAssetsTable() {
    const tbody = document.getElementById('assets-table-body');
    
    if (assets.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No assets found. Click "Add Asset" to get started.</td></tr>';
        return;
    }
    
    tbody.innerHTML = '';
    
    for (const asset of assets) {
        const valueInUSD = await convertCurrencyAmount(asset.value, asset.currency, 'USD');
        const valueInINR = await convertCurrencyAmount(asset.value, asset.currency, 'INR');
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td>${formatAssetType(asset.asset_type)}</td>
            <td>${asset.name}</td>
            <td>${formatCurrency(valueInUSD, 'USD')}</td>
            <td>${formatIndianCurrency(valueInINR)}</td>
            <td>${asset.currency}</td>
            <td>${asset.quantity || '-'}</td>
            <td>
                <button class="icon-btn" onclick="deleteAsset(${asset.id})" title="Delete">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    }
}

// Format asset type
function formatAssetType(type) {
    return type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
}

// Setup event listeners
function setupEventListeners() {
    const addAssetBtn = document.getElementById('add-asset-btn');
    const assetForm = document.getElementById('asset-form');
    
    if (addAssetBtn) {
        addAssetBtn.addEventListener('click', () => openModal('asset-modal'));
    }
    
    if (assetForm) {
        assetForm.addEventListener('submit', handleAssetSubmit);
    }
}

// Handle asset form submission
async function handleAssetSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const ticker = (formData.get('ticker_symbol') || '').trim();
    const assetData = {
        asset_type: formData.get('asset_type'),
        name: formData.get('name'),
        ticker_symbol: ticker || null,
        description: formData.get('description'),
        value: parseFloat(formData.get('value')),
        currency: formData.get('currency'),
        quantity: formData.get('quantity') ? parseFloat(formData.get('quantity')) : null,
        purchase_date: formData.get('purchase_date') || null
    };
    
    try {
        const response = await apiRequest('/api/portfolio/assets', {
            method: 'POST',
            body: JSON.stringify(assetData)
        });
        
        if (response) {
            showNotification('Asset added successfully', 'success');
            closeModal('asset-modal');
            e.target.reset();
            await loadAssets();
        }
    } catch (error) {
        console.error('Failed to add asset:', error);
        showNotification('Failed to add asset', 'error');
    }
}

// Delete asset
async function deleteAsset(assetId) {
    if (!confirm('Are you sure you want to delete this asset?')) {
        return;
    }
    
    try {
        const response = await apiRequest(`/api/portfolio/assets/${assetId}`, {
            method: 'DELETE'
        });
        
        if (response) {
            showNotification('Asset deleted successfully', 'success');
            await loadAssets();
        }
    } catch (error) {
        console.error('Failed to delete asset:', error);
        showNotification('Failed to delete asset', 'error');
    }
}

