/**
 * Sentinel Dashboard - Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    })
    
    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    })
    
    // Handle sidebar toggle on mobile
    var sidebarToggle = document.querySelector('.navbar-toggler')
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            document.querySelector('.sidebar').classList.toggle('show')
        })
    }
    
    // Handle alert dismissal
    var alertList = document.querySelectorAll('.alert')
    alertList.forEach(function(alert) {
        new bootstrap.Alert(alert);
    })
    
    // Add animation to stat cards
    var statCards = document.querySelectorAll('.number-stat')
    statCards.forEach(function(card, index) {
        setTimeout(function() {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    })
    
    // Format numbers
    var numberElements = document.querySelectorAll('.format-number')
    numberElements.forEach(function(el) {
        var num = parseFloat(el.textContent)
        if (!isNaN(num)) {
            el.textContent = formatNumber(num)
        }
    })
    
    // Format dates
    var dateElements = document.querySelectorAll('.format-date')
    dateElements.forEach(function(el) {
        var date = new Date(el.textContent)
        if (date instanceof Date && !isNaN(date)) {
            el.textContent = formatDate(date.toISOString())
        }
    })
    
    // Initialize any analysis forms
    initAnalysisForm();
    
    // Add event listeners for alert acknowledgment
    setupAlertActions();
});

/**
 * Initialize Bootstrap tooltips
 */
function setupTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize document analysis form
 */
function initAnalysisForm() {
    const analysisForm = document.getElementById('analysisForm');
    if (!analysisForm) return;
    
    const submitButton = document.getElementById('submitAnalysis');
    const resultContainer = document.getElementById('analysisResult');
    const loadingSpinner = document.getElementById('loadingSpinner');
    
    analysisForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Show loading spinner
        if (loadingSpinner) {
            loadingSpinner.classList.remove('d-none');
        }
        
        // Disable submit button
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
        }
        
        // Get form data
        const formData = {
            title: document.getElementById('documentTitle').value,
            content: document.getElementById('documentContent').value,
            source_type: document.getElementById('sourceType').value
        };
        
        // Send API request
        fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            displayAnalysisResult(data, resultContainer);
        })
        .catch(error => {
            console.error('Error:', error);
            if (resultContainer) {
                resultContainer.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-circle"></i> 
                        Error analyzing document: ${error.message}
                    </div>
                `;
            }
        })
        .finally(() => {
            // Hide loading spinner
            if (loadingSpinner) {
                loadingSpinner.classList.add('d-none');
            }
            
            // Re-enable submit button
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.innerHTML = '<i class="fas fa-search"></i> Analyze Document';
            }
        });
    });
}

/**
 * Display document analysis results
 */
function displayAnalysisResult(result, container) {
    if (!container) return;
    
    // Determine threat level class
    let threatClass = 'success';
    if (result.threat_score >= 0.7) {
        threatClass = 'danger';
    } else if (result.threat_score >= 0.4) {
        threatClass = 'warning';
    }
    
    // Format categories
    const categoryHtml = Object.entries(result.categories)
        .sort((a, b) => b[1] - a[1])
        .map(([category, score]) => {
            const formattedCategory = category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            return `
                <div class="mb-2">
                    <strong>${formattedCategory}:</strong>
                    <div class="progress">
                        <div class="progress-bar bg-${score >= 0.7 ? 'danger' : score >= 0.4 ? 'warning' : 'success'}" 
                            role="progressbar" style="width: ${Math.round(score * 100)}%" 
                            aria-valuenow="${Math.round(score * 100)}" aria-valuemin="0" aria-valuemax="100">
                            ${score.toFixed(2)}
                        </div>
                    </div>
                </div>
            `;
        })
        .join('');
    
    // Format entity list
    const entityHtml = Object.entries(result.entities)
        .map(([entityType, entities]) => {
            const formattedType = entityType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            return `
                <div class="mb-3">
                    <h6>${formattedType}</h6>
                    <div class="d-flex flex-wrap gap-2">
                        ${entities.map(e => `<span class="badge bg-primary">${e.text}</span>`).join('')}
                    </div>
                </div>
            `;
        })
        .join('');
    
    // Build result HTML
    container.innerHTML = `
        <div class="card mb-4 border-${threatClass} fade-in">
            <div class="card-header bg-${threatClass} ${threatClass === 'warning' ? 'text-dark' : 'text-white'}">
                <h5 class="mb-0">
                    <i class="fas fa-shield-alt me-2"></i>
                    Analysis Results
                    <span class="float-end">
                        Threat Score: ${result.threat_score.toFixed(2)}
                    </span>
                </h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <h5>Summary</h5>
                        <p>${result.summary}</p>
                        
                        <h5>Threat Categories</h5>
                        ${categoryHtml}
                    </div>
                    <div class="col-md-6">
                        <h5>Entities Detected</h5>
                        ${entityHtml}
                        
                        <h5>Relationships</h5>
                        <ul class="list-group">
                            ${result.relationships.map(rel => `
                                <li class="list-group-item">
                                    <strong>${rel.subject}</strong> ${rel.relation} <strong>${rel.object}</strong>
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Setup alert acknowledgment actions
 */
function setupAlertActions() {
    const acknowledgeButtons = document.querySelectorAll('.btn-acknowledge');
    
    acknowledgeButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const alertId = this.dataset.alertId;
            
            fetch(`/api/alerts/${alertId}/acknowledge`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Update UI
                const alertRow = this.closest('tr');
                if (alertRow) {
                    alertRow.classList.add('table-secondary');
                    this.innerHTML = '<i class="fas fa-check"></i> Acknowledged';
                    this.classList.remove('btn-warning');
                    this.classList.add('btn-secondary');
                    this.disabled = true;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error acknowledging alert: ' + error.message);
            });
        });
    });
}

/**
 * Format a date string
 */
function formatDate(dateStr) {
    var date = new Date(dateStr);
    return date.toLocaleDateString();
}

/**
 * Show a loading spinner
 */
function showLoading(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = `
        <div class="d-flex justify-content-center my-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;
}

/**
 * Show an error message
 */
function showError(containerId, message) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = `
        <div class="alert alert-danger">
            <i class="fas fa-exclamation-circle me-2"></i>
            ${message}
        </div>
    `;
}

/**
 * Download data as JSON file
 */
function downloadJson(data, filename) {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    
    a.href = url;
    a.download = filename || 'download.json';
    document.body.appendChild(a);
    a.click();
    
    // Cleanup
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * Format a number
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
} 