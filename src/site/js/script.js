var refreshInterval;

//# DOM bloks
var textarea;
// var isPaused = false;

console.log("[Bot] Run...")

// Красивый ввод текса
const typeWriter = {
    timer: null,
    speed: 18,
    msg: null,

    write: function(msg) {
        if (!msg.analysis || !msg.analysis.length || !textarea) return;
        if (this.timer && textarea.getAttribute("data-ansvers-id") == msg.id) return;

        if (this.timer) {
            clearInterval(this.timer);
            this.wrtieTextChat(this.msg);
            this.msg = null;
        }
        const message = msg.analysis;
        const length = msg.analysis.length;
        var i = 0;

        textarea.value = "";
        textarea.setAttribute("data-ansvers-id", msg.id);

        this.msg = msg;
        this.timer = setInterval(() => {
            if (i < length) {
                textarea.value += message.charAt(i);
                i++;
            }
            else {
                clearInterval(this.timer);
                this.timer = null;
                this.wrtieTextChat(this.msg);
                this.msg = null;
            }
        }, this.speed);
    },

    wrtieTextChat: function(msg) {
        if (!msg.analysis || !msg.analysis.length) return;

        const container = document.getElementById('analysis-container');
        container.insertAdjacentHTML('beforeend', this.renderMessage(msg));

        setTimeout(() => {
            textarea.value = "";
            if (container.lastElementChild) {
                container.lastElementChild.scrollIntoView({ behavior: 'smooth' });
            }
        }, 150);
    },

    renderMessage: function(msg) {
        if (!msg.analysis || !msg.analysis.length) return "";
        return `
            <div class="message-item" data-mess-id="${msg.id}">
                <div class="message-meta">
                    <span>${new Date(msg.timestamp * 1000).toLocaleString()}</span>
                    <span style="color: #00d4ff;">${msg.message_count} messages</span>
                </div>
                <div class="analysis-content">${msg.analysis}</div>
            </div>`;
    }
}

function animateDots() {
    const dots = document.querySelectorAll('.dot');
    let count = 1;

    function animateRun() {
        dots.forEach((dot, index) => {
            if (index < count) {
                dot.classList.add('visible');
            } else {
                dot.classList.remove('visible');
            }
        });

        count++;
        if (count > dots.length) {
            count = 1;
        }
    }

    setInterval(animateRun, 500);

    // Запускаем сразу
    animateRun();
}

function startAutoRefresh() {
    refreshInterval = setInterval(loadAllData, 5500); // Refresh every 3 seconds
}

function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
}

async function loadAllData() {
    await Promise.all([
        loadStatus(),
        // loadMessages(),
        loadAnalysis(),
        // loadStatistics()
        // loadCountLiveChat()
    ]);
}

async function loadCountLiveChat() {
    try {
        const response = await fetch('https://frontend-api-v3.pump.fun/replies/9h5y3WCqfeNt2fiAP7iM2ZRp9apFb58ipvTzcWi9pump?limit=1000&offset=0&reverseOrder=true');
        const data = await response.json();

        console.log("loadCountLiveChat", data, data?.num_participants);
    } catch (error) {
        console.error("loadCountLiveChat");
    }
}

async function loadStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        if (data.success) {
            const status = data.data;
            updateBotStatus(status);
            // updateConnectionStatus(status);
            // updateControlButtons(status);
        } else {
            showError('bot-status', data.error);
        }
        if (data.mode) {
            updateBotMode(data.mode);
        }
    } catch (error) {
        showError('bot-status', 'Failed to load status');
        updateBotMode("error");
    }
}

function updateBotMode(mode) {
    function setMode(icon, text) {
        modeBlock.querySelector("[data-bot-mood-icon]").innerText = icon;
        modeBlock.querySelector("[data-bot-mood-status]").innerText = text;
    }

    // console.log("[Mode]", mode);
    const modeBlock = document.querySelector("[data-bot-mood]");

    if (!modeBlock || modeBlock.getAttribute("data-bot-mood") == mode) return;
    if (!mode || mode == "error") {
        setMode("😴", "Sleep");
    }
    else if (mode == "normal") {
        setMode("😎", "Normal");
    }
    else if (mode == "music") {
        setMode("🥳", "Music");
    }
    else {
        setMode("😎", "Normal");
    }
    modeBlock.setAttribute("data-bot-mood", mode);
}

function updateBotStatus(status) {
    const botStatus = document.getElementById('bot-status');
    // const botDetails = document.getElementById('bot-details');

    if (status.is_paused) {
        botStatus.innerHTML = '<span class="status-indicator status-paused"></span><span>Paused</span>';
        // botDetails.innerHTML = `Uptime: ${status.statistics.uptime_formatted || 'Unknown'}<br>Status: Paused by user`;
    } else if (status.is_running) {
        botStatus.innerHTML = '<span class="status-indicator status-online"></span><span>Running</span>';
        // botDetails.innerHTML = `Uptime: ${status.statistics.uptime_formatted || 'Unknown'}<br>Last Analysis: ${status.last_analysis_time ? new Date(status.last_analysis_time * 1000).toLocaleTimeString() : 'Never'}`;
    } else {
        botStatus.innerHTML = '<span class="status-indicator status-offline"></span><span>Stopped</span>';
        // botDetails.innerHTML = status.last_error ? `Error: ${status.last_error}` : 'Bot is not running';
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
    var countAdd = 0,
        firsMessage;
    const html = messages.map(msg => {
        if (container.querySelector(`> [data-mess-id="${msg.id}"]`)) return "";
        countAdd += 1;

        if (countAdd == 1) {
            firsMessage = msg;
            return "";
        }
        return typeWriter.renderMessage(msg);
    }).join('');

    if (firsMessage) {
        firsMessage
        typeWriter.write(firsMessage);
    }
    if ((container.childElementCount + countAdd) > 30) {
        container.innerHTML = html;
    }
    else {
        container.insertAdjacentHTML('beforeend', html);
    }

    setTimeout(() => {
        if (container.lastElementChild) {
            container.lastElementChild.scrollIntoView({ behavior: 'smooth' });
        }
    }, 150);
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
        container.innerHTML = '<div class="loading">I am waiting for messages</div>';
        return;
    }

    var countAdd = 0,
        firsMessage;
    const html = analyses.map(analysis => {
        if (container.querySelector(`* > [data-mess-id="${analysis.id}"]`)) return "";
        countAdd += 1;

        if (countAdd == 1) {
            firsMessage = analysis;
            return "";
        }
        return typeWriter.renderMessage(analysis);
    }).join('');

    if (firsMessage) {
        firsMessage
        typeWriter.write(firsMessage);
    }
    if ((container.childElementCount + countAdd) > 30) {
        container.innerHTML = html;
    }
    else {
        container.insertAdjacentHTML('beforeend', html);
    }

    setTimeout(() => {
        if (container.lastElementChild) {
            container.lastElementChild.scrollIntoView({ behavior: 'smooth' });
        }
    }, 150);
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
    if (container) {
        container.innerHTML = `<div class="error">${message}</div>`;
    }
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
    }, 500);
}

if (document.hidden) {
    stopAutoRefresh();
} else {
    startAutoRefresh();
}
// Handle page visibility change

document.addEventListener('DOMContentLoaded', function () {
    textarea = document.getElementById("alien-ansvers");

    try {
        animateDots();
    }
    catch (e) {}
    loadAllData();
    startAutoRefresh();
});

// Handle page visibility change
document.addEventListener('visibilitychange', function () {
    if (document.hidden) {
        stopAutoRefresh();
    } else {
        startAutoRefresh();
    }
});