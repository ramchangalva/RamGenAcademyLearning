// Portfolio Summary Page JavaScript

let portfolioData = null;
let assetAllocationChart = null;
let selectedCurrency = 'USD';
let lastBenchmarkPayload = null;

// Initialize page - prevent multiple initializations
let pageInitialized = false;
document.addEventListener('DOMContentLoaded', async function() {
    if (pageInitialized) return;
    pageInitialized = true;
    
    try {
        await Promise.allSettled([loadPortfolioSummary(), loadMarketBenchmarks()]);
        setupCurrencySelector();
        setupMarketTabs();
    } catch (error) {
        console.error('Page initialization error:', error);
    }
});

function formatIndexPrice(value) {
    if (value == null || Number.isNaN(Number(value))) {
        return '—';
    }
    return new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 }).format(Number(value));
}

function formatPctChange(pct) {
    const n = Number(pct);
    if (Number.isNaN(n)) {
        return { text: '—', cls: 'neutral' };
    }
    const sign = n > 0 ? '+' : '';
    const text = sign + n.toFixed(2) + '%';
    const cls = n > 0 ? 'positive' : (n < 0 ? 'negative' : 'neutral');
    return { text, cls };
}

function escapeHtml(str) {
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

function renderEquityIndicesUI(payload) {
    const marketContent = document.getElementById('market-content');
    if (!marketContent) {
        return;
    }

    if (!payload || !payload.indices || payload.indices.length === 0) {
        marketContent.innerHTML =
            '<p class="market-error">Live benchmarks unavailable. Check your network or try again later.</p>';
        return;
    }

    if (payload.as_of) {
        const dateEl = document.getElementById('market-date-display');
        if (dateEl) {
            dateEl.textContent = payload.as_of;
        }
    }

    marketContent.innerHTML = payload.indices.map((idx) => {
        const { text, cls } = formatPctChange(idx.percent_change);
        return `
                    <div class="market-item">
                        <div class="market-name">${escapeHtml(idx.name)}</div>
                        <div class="market-value">
                            <span class="market-change ${cls}">${escapeHtml(text)}</span>
                            <span class="market-price">${formatIndexPrice(idx.last)}</span>
                        </div>
                    </div>
                `;
    }).join('');
}

async function loadMarketBenchmarks() {
    try {
        const response = await fetch('/api/market/benchmarks', { credentials: 'include' });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || !data.live) {
            lastBenchmarkPayload = data.indices && data.indices.length ? data : null;
            renderEquityIndicesUI(lastBenchmarkPayload);
            return;
        }
        lastBenchmarkPayload = data;
        renderEquityIndicesUI(data);
    } catch (e) {
        console.error('Failed to load market benchmarks:', e);
        lastBenchmarkPayload = null;
        renderEquityIndicesUI(null);
    }
}

// Load portfolio summary
async function loadPortfolioSummary() {
    try {
        const response = await apiRequest('/api/portfolio/summary?base_currency=' + selectedCurrency);
        if (response) {
            portfolioData = response;
            updatePortfolioDisplay(response);
            updateAssetAllocationChart(response);
        }
    } catch (error) {
        console.error('Failed to load portfolio summary:', error);
        showNotification('Failed to load portfolio data', 'error');
    }
}

// Update portfolio display
function updatePortfolioDisplay(data) {
    const netWorth = selectedCurrency === 'INR' ? data.net_worth.inr : data.net_worth.usd;
    const assetsTotal = selectedCurrency === 'INR' ? data.assets.total_inr : data.assets.total_usd;
    const liabilitiesTotal = selectedCurrency === 'INR' ? data.liabilities.total_inr : data.liabilities.total_usd;
    const insuranceTotal = selectedCurrency === 'INR' ? data.insurance.total_inr : data.insurance.total_usd;
    
    // Update net worth
    document.getElementById('net-worth-display').textContent = 
        selectedCurrency === 'INR' ? formatIndianCurrency(netWorth) : formatCurrency(netWorth, 'USD');
    
    // Update totals
    document.getElementById('assets-total').textContent = 
        selectedCurrency === 'INR' ? formatIndianCurrency(assetsTotal) : formatCurrency(assetsTotal, 'USD');
    document.getElementById('liabilities-total').textContent = 
        selectedCurrency === 'INR' ? formatIndianCurrency(liabilitiesTotal) : formatCurrency(liabilitiesTotal, 'USD');
    document.getElementById('insurance-total').textContent = 
        selectedCurrency === 'INR' ? formatIndianCurrency(insuranceTotal) : formatCurrency(insuranceTotal, 'USD');
    
    // Update asset breakdown
    updateAssetBreakdown(data.assets.by_type);
}

// Update asset breakdown list
function updateAssetBreakdown(assetsByType) {
    const assetList = document.getElementById('asset-list');
    const assetTypeMap = {
        'mutual_funds': 'Mutual funds',
        'stocks': 'Stocks',
        'fixed_income': 'Fixed Income',
        'real_estate': 'Real estate',
        'retirement_account': 'Retirement a/c',
        'small_savings': 'Small savings'
    };
    
    // Clear existing items
    assetList.innerHTML = '';
    
    // Create items for each asset type
    Object.keys(assetTypeMap).forEach(type => {
        const assetItem = document.createElement('div');
        assetItem.className = 'asset-item';
        
        const assetName = document.createElement('span');
        assetName.className = 'asset-name';
        assetName.textContent = assetTypeMap[type];
        
        const assetValue = document.createElement('span');
        assetValue.className = 'asset-value';
        
        if (assetsByType[type]) {
            const value = selectedCurrency === 'INR' ? assetsByType[type].inr : assetsByType[type].usd;
            assetValue.textContent = selectedCurrency === 'INR' ? formatIndianCurrency(value) : formatCurrency(value, 'USD');
        } else {
            assetValue.textContent =
                selectedCurrency === 'INR' ? formatIndianCurrency(0) : formatCurrency(0, 'USD');
        }
        
        assetItem.appendChild(assetName);
        assetItem.appendChild(assetValue);
        assetList.appendChild(assetItem);
    });
}

// Update asset allocation chart
function updateAssetAllocationChart(data) {
    const ctx = document.getElementById('asset-allocation-chart');
    if (!ctx) return;
    
    const allocation = data.assets.allocation || {};
    const labels = [];
    const values = [];
    const colors = ['#0066cc', '#ffc107', '#28a745', '#dc3545', '#6f42c1', '#fd7e14', '#20c997'];
    
    Object.keys(allocation).forEach((type, index) => {
        labels.push(type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()));
        values.push(allocation[type].percentage);
    });
    
    if (assetAllocationChart) {
        assetAllocationChart.destroy();
    }
    
    if (values.length === 0) {
        ctx.parentElement.innerHTML = '<div class="chart-placeholder"><i class="fas fa-chart-pie"></i><p>No asset data available</p></div>';
        return;
    }
    
    assetAllocationChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors.slice(0, values.length),
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#cccccc',
                        padding: 15,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            return label + ': ' + value.toFixed(2) + '%';
                        }
                    }
                }
            }
        }
    });
}

// Setup currency selector - prevent duplicate listeners
let currencySelectorSetup = false;
function setupCurrencySelector() {
    if (currencySelectorSetup) return; // Prevent duplicate event listeners
    
    const selector = document.getElementById('currency-selector');
    if (selector) {
        selector.value = selectedCurrency;
        // Remove existing listeners by cloning
        const newSelector = selector.cloneNode(true);
        selector.parentNode.replaceChild(newSelector, selector);
        
        newSelector.addEventListener('change', async function(e) {
            e.preventDefault();
            e.stopPropagation();
            selectedCurrency = this.value;
            await loadPortfolioSummary();
        });
        currencySelectorSetup = true;
    }
}

// Setup market tabs - prevent duplicate listeners
let marketTabsSetup = false;
function setupMarketTabs() {
    if (marketTabsSetup) return; // Prevent duplicate event listeners
    marketTabsSetup = true;
    
    const marketContent = document.getElementById('market-content');
    if (!marketContent) return;
    
    // Use event delegation to handle clicks on all tab buttons
    const marketTabsContainer = document.querySelector('.market-tabs');
    if (marketTabsContainer) {
        marketTabsContainer.addEventListener('click', function(e) {
            const btn = e.target.closest('.tab-btn');
            if (!btn) return;
            
            e.preventDefault();
            e.stopPropagation();
            
            // Remove active class from all tabs
            const allTabs = document.querySelectorAll('.tab-btn');
            allTabs.forEach(b => b.classList.remove('active'));
            // Add active class to clicked tab
            btn.classList.add('active');
            
            const tab = btn.dataset.tab;
            if (tab === 'equities') {
                if (lastBenchmarkPayload && lastBenchmarkPayload.indices &&
                    lastBenchmarkPayload.indices.length) {
                    renderEquityIndicesUI(lastBenchmarkPayload);
                } else {
                    marketContent.innerHTML = '<p class="market-loading">Loading market data…</p>';
                    loadMarketBenchmarks();
                }
            } else {
                marketContent.innerHTML = '<div class="empty-state">Market data for ' + tab.toUpperCase() + ' coming soon</div>';
            }
        });
    }
}
