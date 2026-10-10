// Retirement Planning Page JavaScript

let plans = [];

// Initialize page
document.addEventListener('DOMContentLoaded', async function() {
    await loadPlans();
    setupEventListeners();
});

// Load retirement plans
async function loadPlans() {
    try {
        const response = await apiRequest('/api/retirement/plans');
        if (response) {
            plans = response;
            renderPlans();
        }
    } catch (error) {
        console.error('Failed to load retirement plans:', error);
        showNotification('Failed to load retirement plans', 'error');
    }
}

// Render plans
function renderPlans() {
    const container = document.getElementById('plans-container');
    
    if (plans.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-calendar-alt"></i>
                <p>No retirement plans found. Create a plan to get started.</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = '';
    
    plans.forEach(plan => {
        const planCard = document.createElement('div');
        planCard.className = 'plan-card';
        planCard.innerHTML = `
            <h3>${plan.plan_name}</h3>
            <div class="plan-stats">
                ${plan.usa_target_age ? `
                    <div class="plan-stat">
                        <div class="plan-stat-label">Primary target age</div>
                        <div class="plan-stat-value">${plan.usa_target_age}</div>
                    </div>
                ` : ''}
                ${plan.india_target_age ? `
                    <div class="plan-stat">
                        <div class="plan-stat-label">Secondary target age</div>
                        <div class="plan-stat-value">${plan.india_target_age}</div>
                    </div>
                ` : ''}
            </div>
            <div style="margin-top: 15px; display: flex; gap: 10px;">
                <button class="btn-primary" onclick="calculatePlan(${plan.id})">Calculate</button>
                <button class="btn-secondary" onclick="editPlan(${plan.id})">Edit</button>
            </div>
        `;
        container.appendChild(planCard);
    });
}

// Setup event listeners
function setupEventListeners() {
    const createPlanBtn = document.getElementById('create-plan-btn');
    const planForm = document.getElementById('plan-form');
    const calculateBtn = document.getElementById('calculate-plan-btn');
    
    if (createPlanBtn) {
        createPlanBtn.addEventListener('click', () => openModal('plan-modal'));
    }
    
    if (planForm) {
        planForm.addEventListener('submit', handlePlanSubmit);
    }
    
    if (calculateBtn) {
        calculateBtn.addEventListener('click', async function() {
            const formData = new FormData(planForm);
            await calculatePlanFromForm(formData);
        });
    }
}

// Handle plan form submission
async function handlePlanSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const planData = {
        plan_name: formData.get('plan_name'),
        usa_target_age: formData.get('usa_target_age') ? parseInt(formData.get('usa_target_age')) : null,
        usa_current_age: formData.get('usa_current_age') ? parseInt(formData.get('usa_current_age')) : null,
        usa_current_savings_usd: formData.get('usa_current_savings_usd') ? parseFloat(formData.get('usa_current_savings_usd')) : null,
        usa_monthly_contribution_usd: formData.get('usa_monthly_contribution_usd') ? parseFloat(formData.get('usa_monthly_contribution_usd')) : null,
        usa_monthly_expense_usd: formData.get('usa_monthly_expense_usd') ? parseFloat(formData.get('usa_monthly_expense_usd')) : null,
        usa_expected_return_pct: formData.get('usa_expected_return_pct') ? parseFloat(formData.get('usa_expected_return_pct')) : 7.0,
        usa_inflation_pct: formData.get('usa_inflation_pct') ? parseFloat(formData.get('usa_inflation_pct')) : 3.0,
        india_target_age: formData.get('india_target_age') ? parseInt(formData.get('india_target_age')) : null,
        india_current_age: formData.get('india_current_age') ? parseInt(formData.get('india_current_age')) : null,
        india_current_savings_inr: formData.get('india_current_savings_inr') ? parseFloat(formData.get('india_current_savings_inr')) : null,
        india_monthly_contribution_inr: formData.get('india_monthly_contribution_inr') ? parseFloat(formData.get('india_monthly_contribution_inr')) : null,
        india_monthly_expense_inr: formData.get('india_monthly_expense_inr') ? parseFloat(formData.get('india_monthly_expense_inr')) : null,
        india_expected_return_pct: formData.get('india_expected_return_pct') ? parseFloat(formData.get('india_expected_return_pct')) : 8.0,
        india_inflation_pct: formData.get('india_inflation_pct') ? parseFloat(formData.get('india_inflation_pct')) : 6.0,
        notes: formData.get('notes') || null
    };
    
    try {
        const response = await apiRequest('/api/retirement/plans', {
            method: 'POST',
            body: JSON.stringify(planData)
        });
        
        if (response) {
            showNotification('Retirement plan created successfully', 'success');
            closeModal('plan-modal');
            e.target.reset();
            await loadPlans();
        }
    } catch (error) {
        console.error('Failed to create retirement plan:', error);
        showNotification('Failed to create retirement plan', 'error');
    }
}

// Calculate plan
async function calculatePlan(planId) {
    try {
        const response = await apiRequest(`/api/retirement/plans/${planId}/calculate`);
        if (response) {
            displayResults(response);
        }
    } catch (error) {
        console.error('Failed to calculate plan:', error);
        showNotification('Failed to calculate retirement plan', 'error');
    }
}

// Calculate plan from form
async function calculatePlanFromForm(formData) {
    // This would create a temporary plan and calculate
    // For now, just show a message
    showNotification('Please save the plan first, then calculate', 'info');
}

// Display results
function displayResults(results) {
    const resultsContent = document.getElementById('results-content');
    let html = '';
    
    if (results.usa) {
        html += `
            <div class="result-section">
                <h3>Primary plan (USD)</h3>
                <div class="result-grid">
                    <div class="result-item">
                        <div class="result-label">Corpus Needed</div>
                        <div class="result-value">${formatCurrency(results.usa.corpus_needed_usd, 'USD')}</div>
                    </div>
                    <div class="result-item">
                        <div class="result-label">Projected Corpus</div>
                        <div class="result-value">${formatCurrency(results.usa.projected_corpus_usd, 'USD')}</div>
                    </div>
                    <div class="result-item">
                        <div class="result-label">Shortfall</div>
                        <div class="result-value" style="color: ${results.usa.shortfall_usd > 0 ? '#dc3545' : '#28a745'}">
                            ${formatCurrency(results.usa.shortfall_usd, 'USD')}
                        </div>
                    </div>
                    <div class="result-item">
                        <div class="result-label">Required Monthly Contribution</div>
                        <div class="result-value">${formatCurrency(results.usa.required_monthly_contribution_usd, 'USD')}</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    if (results.india) {
        html += `
            <div class="result-section">
                <h3>Secondary plan (INR)</h3>
                <div class="result-grid">
                    <div class="result-item">
                        <div class="result-label">Corpus Needed</div>
                        <div class="result-value">${formatIndianCurrency(results.india.corpus_needed_inr)}</div>
                    </div>
                    <div class="result-item">
                        <div class="result-label">Projected Corpus</div>
                        <div class="result-value">${formatIndianCurrency(results.india.projected_corpus_inr)}</div>
                    </div>
                    <div class="result-item">
                        <div class="result-label">Shortfall</div>
                        <div class="result-value" style="color: ${results.india.shortfall_inr > 0 ? '#dc3545' : '#28a745'}">
                            ${formatIndianCurrency(results.india.shortfall_inr)}
                        </div>
                    </div>
                    <div class="result-item">
                        <div class="result-label">Required Monthly Contribution</div>
                        <div class="result-value">${formatIndianCurrency(results.india.required_monthly_contribution_inr)}</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    resultsContent.innerHTML = html;
    openModal('results-modal');
}

// Edit plan
function editPlan(planId) {
    const plan = plans.find(p => p.id === planId);
    if (!plan) return;
    
    // Populate form with plan data
    document.getElementById('plan-name').value = plan.plan_name;
    document.getElementById('usa-current-age').value = plan.usa_current_age || '';
    document.getElementById('usa-target-age').value = plan.usa_target_age || '';
    // ... populate other fields
    
    openModal('plan-modal');
}
