// Paddi Dashboard JavaScript

// Global variables
let severityChart = null;
let timelineChart = null;
let darkMode = false;

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeDarkMode();
    loadFindings();
    initializeCharts();
    setupEventListeners();
    
    // Auto-refresh every 30 seconds
    setInterval(refreshFindings, 30000);
});

// Dark mode toggle
function initializeDarkMode() {
    const savedMode = localStorage.getItem('darkMode');
    if (savedMode === 'true') {
        document.body.classList.add('dark-mode');
        darkMode = true;
    }
    
    document.getElementById('darkModeToggle').addEventListener('click', function(e) {
        e.preventDefault();
        toggleDarkMode();
    });
}

function toggleDarkMode() {
    darkMode = !darkMode;
    document.body.classList.toggle('dark-mode');
    localStorage.setItem('darkMode', darkMode);
    
    // Update charts theme
    if (severityChart) {
        updateChartTheme(severityChart);
    }
    if (timelineChart) {
        updateChartTheme(timelineChart);
    }
}

// Initialize charts
function initializeCharts() {
    // Severity Distribution Chart
    const severityCtx = document.getElementById('severityChart').getContext('2d');
    severityChart = new Chart(severityCtx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: []
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        font: {
                            size: 14
                        }
                    }
                }
            }
        }
    });
    
    // Timeline Chart
    const timelineCtx = document.getElementById('timelineChart').getContext('2d');
    timelineChart = new Chart(timelineCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: []
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    position: 'bottom'
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Finding Count'
                    },
                    beginAtZero: true
                }
            }
        }
    });
    
    loadSeverityDistribution();
    loadTimelineData();
}

// Load findings data
async function loadFindings() {
    try {
        const response = await fetch('/api/findings');
        const data = await response.json();
        
        displayFindings(data.findings);
        updateSummaryCounts(data.findings);
        
    } catch (error) {
        console.error('Error loading findings:', error);
        showToast('Error loading findings', 'danger');
    }
}

// Display findings in table
function displayFindings(findings) {
    const tableBody = document.getElementById('findingsTableBody');
    tableBody.innerHTML = '';
    
    if (findings.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="5" class="text-center">No findings found</td></tr>';
        return;
    }
    
    findings.forEach(finding => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><span class="severity-badge severity-${finding.severity.toLowerCase()}">${finding.severity}</span></td>
            <td>${finding.title}</td>
            <td>${finding.explanation}</td>
            <td>${finding.recommendation}</td>
            <td><span class="badge bg-secondary">${finding.count}</span></td>
        `;
        tableBody.appendChild(row);
    });
}

// Update summary counts
function updateSummaryCounts(findings) {
    const counts = {
        critical: 0,
        high: 0,
        medium: 0,
        low: 0
    };
    
    findings.forEach(finding => {
        const severity = finding.severity.toLowerCase();
        if (counts.hasOwnProperty(severity)) {
            counts[severity] += finding.count || 1;
        }
    });
    
    document.getElementById('criticalCount').textContent = counts.critical;
    document.getElementById('highCount').textContent = counts.high;
    document.getElementById('mediumCount').textContent = counts.medium;
    document.getElementById('lowCount').textContent = counts.low;
}

// Load severity distribution data
async function loadSeverityDistribution() {
    try {
        const response = await fetch('/api/findings/severity-distribution');
        const data = await response.json();
        
        severityChart.data.labels = data.labels;
        severityChart.data.datasets[0].data = data.data;
        severityChart.data.datasets[0].backgroundColor = data.colors;
        severityChart.update();
        
    } catch (error) {
        console.error('Error loading severity distribution:', error);
    }
}

// Load timeline data
async function loadTimelineData() {
    try {
        const response = await fetch('/api/findings/timeline');
        const data = await response.json();
        
        const labels = data.map(item => new Date(item.date).toLocaleDateString());
        
        timelineChart.data.labels = labels;
        timelineChart.data.datasets = [
            {
                label: 'Critical',
                data: data.map(item => item.critical),
                borderColor: '#dc3545',
                backgroundColor: 'rgba(220, 53, 69, 0.1)',
                tension: 0.1
            },
            {
                label: 'High',
                data: data.map(item => item.high),
                borderColor: '#fd7e14',
                backgroundColor: 'rgba(253, 126, 20, 0.1)',
                tension: 0.1
            },
            {
                label: 'Medium',
                data: data.map(item => item.medium),
                borderColor: '#ffc107',
                backgroundColor: 'rgba(255, 193, 7, 0.1)',
                tension: 0.1
            },
            {
                label: 'Low',
                data: data.map(item => item.low),
                borderColor: '#28a745',
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                tension: 0.1
            }
        ];
        
        timelineChart.update();
        
    } catch (error) {
        console.error('Error loading timeline data:', error);
    }
}

// Start a new audit
async function startAudit() {
    try {
        showToast('Starting audit...', 'info');
        
        const response = await fetch('/api/audit/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                project_id: 'demo-project'  // In production, get from UI
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Audit started successfully!', 'success');
            setTimeout(() => refreshFindings(), 2000);
        } else {
            showToast('Failed to start audit', 'danger');
        }
        
    } catch (error) {
        console.error('Error starting audit:', error);
        showToast('Error starting audit', 'danger');
    }
}

// Refresh findings
function refreshFindings() {
    loadFindings();
    loadSeverityDistribution();
    loadTimelineData();
    showToast('Data refreshed', 'success');
}

// Export report
async function exportReport(format) {
    try {
        const response = await fetch(`/api/export/${format}`);
        const data = await response.json();
        
        if (data.success) {
            showToast(`Report exported as ${format.toUpperCase()}`, 'success');
            // In production, trigger download
        } else {
            showToast('Failed to export report', 'danger');
        }
        
    } catch (error) {
        console.error('Error exporting report:', error);
        showToast('Error exporting report', 'danger');
    }
}

// Chat functionality
async function sendChat() {
    const input = document.getElementById('chatInput');
    const question = input.value.trim();
    
    if (!question) return;
    
    // Add user message to chat
    addChatMessage(question, 'user');
    input.value = '';
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question })
        });
        
        const data = await response.json();
        addChatMessage(data.response, 'bot');
        
    } catch (error) {
        console.error('Error sending chat:', error);
        addChatMessage('Sorry, I encountered an error. Please try again.', 'bot');
    }
}

// Add message to chat
function addChatMessage(message, sender) {
    const chatContainer = document.getElementById('chatContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}`;
    
    const icon = sender === 'user' ? 'person' : 'smart_toy';
    messageDiv.innerHTML = `
        <span class="material-icons">${icon}</span>
        <p>${message}</p>
    `;
    
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.getElementById('liveToast');
    const toastMessage = document.getElementById('toastMessage');
    
    toastMessage.textContent = message;
    toast.classList.remove('text-bg-primary', 'text-bg-success', 'text-bg-danger', 'text-bg-info');
    
    const typeClass = {
        'primary': 'text-bg-primary',
        'success': 'text-bg-success',
        'danger': 'text-bg-danger',
        'info': 'text-bg-info'
    }[type] || 'text-bg-info';
    
    toast.classList.add(typeClass);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

// Update chart theme for dark mode
function updateChartTheme(chart) {
    const textColor = darkMode ? '#ffffff' : '#212121';
    const gridColor = darkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
    
    chart.options.plugins.legend.labels.color = textColor;
    
    if (chart.options.scales) {
        Object.values(chart.options.scales).forEach(scale => {
            scale.ticks = { ...scale.ticks, color: textColor };
            scale.grid = { ...scale.grid, color: gridColor };
            if (scale.title) {
                scale.title.color = textColor;
            }
        });
    }
    
    chart.update();
}

// Setup event listeners
function setupEventListeners() {
    // Enter key in chat input
    document.getElementById('chatInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendChat();
        }
    });
}