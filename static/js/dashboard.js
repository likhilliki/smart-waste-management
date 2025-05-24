/**
 * Dashboard charts and data visualization
 */

/**
 * Initialize dashboard charts
 */
function initDashboardCharts() {
    // Waste type distribution chart
    createWasteTypeChart();
    
    // Activity timeline chart
    createActivityChart();
    
    // Credits earned chart (for users)
    createCreditsChart();
    
    // Processing rate chart (for admin)
    createProcessingRateChart();
}

/**
 * Create waste type distribution chart
 */
function createWasteTypeChart() {
    const wasteTypeElement = document.getElementById('waste-type-chart');
    if (!wasteTypeElement) return;
    
    // Get waste type data from the element's data attributes
    const wasteTypeData = JSON.parse(wasteTypeElement.getAttribute('data-waste-types') || '{}');
    
    // Prepare data for chart
    const labels = Object.keys(wasteTypeData);
    const data = Object.values(wasteTypeData);
    
    // Color mapping for waste types
    const colorMap = {
        'plastic': '#ff6384',
        'metal': '#36a2eb',
        'paper': '#ffce56',
        'glass': '#4bc0c0',
        'electronic': '#9966ff',
        'organic': '#66ff99',
        'other': '#c9cbcf'
    };
    
    // Generate colors array
    const colors = labels.map(label => colorMap[label] || '#c9cbcf');
    
    // Create chart
    new Chart(wasteTypeElement, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: '#ffffff'
                    }
                },
                title: {
                    display: true,
                    text: 'Waste Type Distribution',
                    color: '#ffffff',
                    font: {
                        size: 16
                    }
                }
            }
        }
    });
}

/**
 * Create activity timeline chart
 */
function createActivityChart() {
    const activityElement = document.getElementById('activity-chart');
    if (!activityElement) return;
    
    // Get activity data from the element's data attributes
    const activityData = JSON.parse(activityElement.getAttribute('data-activity') || '[]');
    
    // Group activities by date
    const activityByDate = {};
    
    activityData.forEach(activity => {
        const date = new Date(activity.timestamp);
        const dateStr = date.toLocaleDateString();
        
        if (!activityByDate[dateStr]) {
            activityByDate[dateStr] = 0;
        }
        
        activityByDate[dateStr]++;
    });
    
    // Prepare data for chart
    const labels = Object.keys(activityByDate);
    const data = Object.values(activityByDate);
    
    // Create chart
    new Chart(activityElement, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Activity',
                data: data,
                borderColor: '#4bc0c0',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.1,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'Activity Timeline',
                    color: '#ffffff',
                    font: {
                        size: 16
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: '#cccccc'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0,
                        color: '#cccccc'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            }
        }
    });
}

/**
 * Create credits earned chart (for users)
 */
function createCreditsChart() {
    const creditsElement = document.getElementById('credits-chart');
    if (!creditsElement) return;
    
    // Get credits data from the element's data attributes
    const creditsData = JSON.parse(creditsElement.getAttribute('data-credits') || '[]');
    
    // Group credits by date
    const creditsByDate = {};
    
    creditsData.forEach(credit => {
        const date = new Date(credit.timestamp);
        const dateStr = date.toLocaleDateString();
        
        if (!creditsByDate[dateStr]) {
            creditsByDate[dateStr] = 0;
        }
        
        creditsByDate[dateStr] += credit.amount;
    });
    
    // Prepare data for chart
    const labels = Object.keys(creditsByDate);
    const data = Object.values(creditsByDate);
    
    // Calculate cumulative sum
    const cumulativeData = [];
    let sum = 0;
    
    data.forEach(value => {
        sum += value;
        cumulativeData.push(sum);
    });
    
    // Create chart
    new Chart(creditsElement, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Credits Earned',
                    data: data,
                    backgroundColor: 'rgba(255, 206, 86, 0.5)',
                    borderColor: 'rgba(255, 206, 86, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Total Credits',
                    data: cumulativeData,
                    type: 'line',
                    borderColor: 'rgba(153, 102, 255, 1)',
                    backgroundColor: 'rgba(153, 102, 255, 0.2)',
                    borderWidth: 2,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#ffffff'
                    }
                },
                title: {
                    display: true,
                    text: 'Recycling Credits Earned',
                    color: '#ffffff',
                    font: {
                        size: 16
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: '#cccccc'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#cccccc'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            }
        }
    });
}

/**
 * Create processing rate chart (for admin)
 */
function createProcessingRateChart() {
    const processingRateElement = document.getElementById('processing-rate-chart');
    if (!processingRateElement) return;
    
    // Get processing rate from the element's data attribute
    const processingRate = parseFloat(processingRateElement.getAttribute('data-rate') || '0');
    
    // Create chart
    new Chart(processingRateElement, {
        type: 'gauge',
        data: {
            datasets: [{
                value: processingRate,
                minValue: 0,
                maxValue: 100,
                backgroundColor: ['#ff6384', '#ffce56', '#36a2eb', '#4bc0c0'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            valueLabel: {
                display: true,
                formatter: function(value) {
                    return value.toFixed(1) + '%';
                },
                color: '#ffffff',
                fontSize: 16,
                fontStyle: 'bold'
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Waste Processing Rate',
                    color: '#ffffff',
                    font: {
                        size: 16
                    }
                }
            }
        }
    });
}

/**
 * Load transaction history data
 */
function loadTransactionHistory() {
    const transactionTable = document.getElementById('transaction-table');
    if (!transactionTable) return;
    
    // Show loading spinner
    const loadingIndicator = document.getElementById('loading-indicator');
    if (loadingIndicator) {
        loadingIndicator.classList.remove('d-none');
    }
    
    // Get user role from data attribute
    const userRole = transactionTable.getAttribute('data-role');
    
    // Determine API endpoint based on role
    let endpoint;
    switch (userRole) {
        case 'admin':
            endpoint = '/admin/transactions';
            break;
        case 'user':
            endpoint = '/user/history';
            break;
        case 'recycler':
            endpoint = '/recycler/history';
            break;
        default:
            endpoint = '/dashboard';
    }
    
    // In this simplified version, we'll just redirect to the appropriate page
    // In a real app, you'd make an AJAX request to get the data and update the table
    window.location.href = endpoint;
}
