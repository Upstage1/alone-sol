var refreshInterval;
// var isPaused = false;

// Load initial data
document.addEventListener('DOMContentLoaded', function () {
    loadAllData();
    startAutoRefresh();

    document.getElementById("mode").addEventListener("change", changeMode);
});

async function changeMode(e) {
    const mode = e.target.value;

    if (mode) {
        try {
            const response = await fetch('/api/mode', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json;charset=utf-8'
                },
                body: JSON.stringify({
                    mode: mode
                })
            });
            const data = await response.json();

            if (data.success) {
                showNotification('Режим успешно изменен на: ' + mode, 'success');
            } else {
                showNotification('Ошибка смены режима: ' + mode, 'error');
            }
        } catch (error) {
            showNotification('Ошибка запроса на смену режима: ' + mode, 'error');
        }
    }
}

function startAutoRefresh() {
    refreshInterval = setInterval(loadAllData, 60000); // Refresh every 3 seconds
}

function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
}

async function loadAllData() {
    await Promise.all([
        loadStatus(),
        loadMessages(),
        loadAnalysis(),
        loadStatistics()
    ]);
}

async function loadStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        if (data.success) {
            const status = data.data;
            updateBotStatus(status);
            updateConnectionStatus(status);
            updateControlButtons(status);
            updateBotMode(data.mode);
        } else {
            showError('bot-status', data.error);
        }
    } catch (error) {
        showError('bot-status', 'Failed to load status');
    }
}

function updateBotStatus(status) {
    const botStatus = document.getElementById('bot-status');
    const botDetails = document.getElementById('bot-details');

    if (status.is_paused) {
        botStatus.innerHTML = '<span class="status-indicator status-paused"></span><span>Paused</span>';
        botDetails.innerHTML = `Uptime: ${status.statistics.uptime_formatted || 'Unknown'}<br>Status: Paused by user`;
    } else if (status.is_running) {
        botStatus.innerHTML = '<span class="status-indicator status-online"></span><span>Running</span>';
        botDetails.innerHTML = `Uptime: ${status.statistics.uptime_formatted || 'Unknown'}<br>Last Analysis: ${status.last_analysis_time ? new Date(status.last_analysis_time * 1000).toLocaleTimeString() : 'Never'}`;
    } else {
        botStatus.innerHTML = '<span class="status-indicator status-offline"></span><span>Stopped</span>';
        botDetails.innerHTML = status.last_error ? `Error: ${status.last_error}` : 'Bot is not running';
    }
}

function updateConnectionStatus(status) {
    const connStatus = document.getElementById('connection-status');
    const connDetails = document.getElementById('connection-details');

    if (status.pump_connection) {
        connStatus.innerHTML = '<span class="status-indicator status-online"></span><span>Connected</span>';
        connDetails.innerHTML = `Token: ${status.token_address}<br>Messages: ${status.pump_connection.message_count}<br>Room: ${status.pump_connection.room_id || 'N/A'}`;
    } else {
        connStatus.innerHTML = '<span class="status-indicator status-offline"></span><span>Disconnected</span>';
        connDetails.innerHTML = 'Not connected to pump.fun<br>Attempts: ' + (status.pump_connection.connection_attempts || 0);
    }
}

function updateControlButtons(status) {
    const pauseBtn = document.getElementById('pause-btn');
    const resumeBtn = document.getElementById('resume-btn');

    if (status.is_paused) {
        pauseBtn.disabled = true;
        resumeBtn.disabled = false;
    } else if (status.is_running) {
        pauseBtn.disabled = false;
        resumeBtn.disabled = true;
    } else {
        pauseBtn.disabled = true;
        resumeBtn.disabled = true;
    }
}

async function pauseBot() {
    try {
        const response = await fetch('/api/pause', { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            showNotification('Bot paused successfully', 'success');
            loadStatus();
        } else {
            showNotification('Failed to pause bot: ' + data.error, 'error');
        }
    } catch (error) {
        showNotification('Failed to pause bot', 'error');
    }
}

async function resumeBot() {
    try {
        const response = await fetch('/api/resume', { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            showNotification('Bot resumed successfully', 'success');
            loadStatus();
        } else {
            showNotification('Failed to resume bot: ' + data.error, 'error');
        }
    } catch (error) {
        showNotification('Failed to resume bot', 'error');
    }
}

async function loadMessages() {
    try {
        const response = await fetch('/api/messages?limit=15');
        const data = await response.json();

        if (data.success) {
            displayMessages(data.data.messages);
        } else {
            showError('messages-container', data.error);
        }
    } catch (error) {
        showError('messages-container', 'Failed to load messages');
    }
}

function displayMessages(messages) {
    const container = document.getElementById('messages-container');

    if (messages.length === 0) {
        container.innerHTML = '<div class="loading">No messages available</div>';
        return;
    }

    const html = messages.map(msg => {
        const timestamp = new Date(msg.timestamp * 1000).toLocaleTimeString();

        return `
            <div class="message-item">
                <div class="message-meta">
                    <span>${timestamp}</span>
                    <span style="color: #00d4ff; font-weight: 600;">${msg.username || 'Unknown'}</span>
                </div>
                <div class="message-content">${msg.message}</div>
            </div>
        `;
    }).join('');

    container.innerHTML = html;
}

async function loadAnalysis() {
    try {
        const response = await fetch('/api/analysis?limit=8');
        const data = await response.json();

        if (data.success) {
            displayAnalysis(data.data.analyses);
        } else {
            showError('analysis-container', data.error);
        }
    } catch (error) {
        showError('analysis-container', 'Failed to load analysis');
    }
}

function displayAnalysis(analyses) {
    const container = document.getElementById('analysis-container');

    if (analyses.length === 0) {
        container.innerHTML = '<div class="loading">No analysis available</div>';
        return;
    }

    const html = analyses.map(analysis => {
        const timestamp = new Date(analysis.timestamp * 1000).toLocaleString();

        return `
            <div class="analysis-item">
                <div class="message-meta">
                    <span>${timestamp}</span>
                    <span style="color: #00d4ff;">${analysis.message_count} messages</span>
                </div>
                <div class="analysis-content">${analysis.analysis}</div>
            </div>
        `;
    }).join('');

    container.innerHTML = html;
}

async function loadStatistics() {
    try {
        const response = await fetch('/api/statistics');
        const data = await response.json();

        if (data.success) {
            displayStatistics(data.data);
        } else {
            showError('stats-container', data.error);
        }
    } catch (error) {
        showError('stats-container', 'Failed to load statistics');
    }
}

function displayStatistics(stats) {
    const container = document.getElementById('stats-container');

    const statItems = [
        { label: 'Uptime', value: stats.uptime_formatted || 'Unknown' },
        { label: 'Messages', value: stats.total_messages || 0 },
        { label: 'Analyses', value: stats.total_analyses || 0 },
        { label: 'Success Rate', value: `${stats.success_rate?.toFixed(1) || 0}%` },
        { label: 'Msg/Min', value: stats.messages_per_minute?.toFixed(1) || 0 },
        { label: 'API Errors', value: stats.api_errors || 0 }
    ];

    const html = statItems.map(stat => `
        <div class="stat-item">
            <div class="stat-value">${stat.value}</div>
            <div class="stat-label">${stat.label}</div>
        </div>
    `).join('');

    container.innerHTML = html;
}

function showError(containerId, message) {
    const container = document.getElementById(containerId);
    container.innerHTML = `<div class="error">${message}</div>`;
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#00ff88' : type === 'error' ? '#ff6b6b' : '#00d4ff'};
        color: white;
        padding: 15px 20px;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        z-index: 1000;
        animation: slideInRight 0.3s ease-out;
    `;
    notification.textContent = message;

    document.body.appendChild(notification);

    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease-in';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 5000);
}

// Add CSS for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

// Handle page visibility change
document.addEventListener('visibilitychange', function () {
    if (document.hidden) {
        stopAutoRefresh();
    } else {
        startAutoRefresh();
    }
});
