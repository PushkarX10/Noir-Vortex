/**
 * The Loop — Client-Side Application Logic
 * Skills Applied:
 * - animejs-animation: Staggered card entrances, spring easing, animated counters
 * - analytics-tracking: Event-based activity logging with decision-grade signals
 * - agent-orchestration: Real-time agent status tracking with parallel profiling
 */

(function () {
    'use strict';

    // =========================================================================
    // Activity Feed (analytics-tracking: meaningful state change logging)
    // =========================================================================
    const activityLog = [];

    function logActivity(type, message) {
        const now = new Date();
        const time = now.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
        const entry = { type, message, time, timestamp: now.toISOString() };
        activityLog.unshift(entry);
        if (activityLog.length > 50) activityLog.pop();

        const feed = document.getElementById('activity-feed');
        if (feed) {
            const item = document.createElement('div');
            item.className = 'activity-item';
            item.innerHTML = `
                <span class="activity-time">${time}</span>
                <span class="activity-dot ${type}"></span>
                <span>${message}</span>
            `;
            feed.prepend(item);

            // Keep feed capped at 20 visible
            while (feed.children.length > 20) {
                feed.removeChild(feed.lastChild);
            }
        }
    }

    // =========================================================================
    // WebSocket Manager
    // =========================================================================
    class LoopWebSocket {
        constructor() {
            this.ws = null;
            this.reconnectAttempts = 0;
            this.maxReconnectAttempts = 10;
            this.reconnectDelay = 2000;
            this.listeners = {};
        }

        connect() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const url = `${protocol}//${window.location.host}/ws`;

            try {
                this.ws = new WebSocket(url);

                this.ws.onopen = () => {
                    console.log('[WS] Connected');
                    this.reconnectAttempts = 0;
                    this._emit('connected');
                    updateConnectionStatus('online');
                    logActivity('agent', 'WebSocket connected to The Loop');
                    this._startPing();
                };

                this.ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        this._handleMessage(data);
                    } catch (e) {
                        console.error('[WS] Parse error:', e);
                    }
                };

                this.ws.onclose = () => {
                    console.log('[WS] Disconnected');
                    updateConnectionStatus('offline');
                    logActivity('error', 'WebSocket disconnected');
                    this._stopPing();
                    this._reconnect();
                };

                this.ws.onerror = (error) => {
                    console.error('[WS] Error:', error);
                    updateConnectionStatus('error');
                };
            } catch (e) {
                console.error('[WS] Connection failed:', e);
                this._reconnect();
            }
        }

        _handleMessage(data) {
            console.log('[WS] Message:', data.type, data);
            this._emit(data.type, data);

            switch (data.type) {
                case 'state_sync':
                    updateDashboardState(data.state);
                    break;
                case 'pipeline_started':
                    showToast(`Pipeline cycle #${data.cycle} started!`, 'info');
                    updatePipelineStatus(true);
                    logActivity('agent', `Pipeline cycle #${data.cycle} started`);
                    break;
                case 'agent_started':
                    showToast(data.message, 'info');
                    updateAgentStatus(data.agent, 'active');
                    logActivity('agent', `${data.agent} is working...`);
                    break;
                case 'approval_required':
                    showToast(`Approval needed: ${data.agent}`, 'warning');
                    updateAgentStatus(data.agent, 'awaiting_approval');
                    showApprovalBadge(true);
                    logActivity('approval', `${data.agent} awaiting human review`);
                    if (data.state) updateDashboardState(data.state);
                    break;
                case 'approval_processed':
                    showToast(data.message, 'success');
                    if (data.next_agent) updateAgentStatus(data.next_agent, 'active');
                    logActivity('approval', `Approval: ${data.action} for ${data.agent}`);
                    break;
                case 'pipeline_completed':
                    showToast(`Cycle #${data.cycle} complete!`, 'success');
                    updatePipelineStatus(false);
                    logActivity('publish', `Pipeline cycle #${data.cycle} completed!`);
                    if (data.state) updateDashboardState(data.state);
                    break;
                case 'pipeline_error':
                    showToast(`Error: ${data.error}`, 'error');
                    updatePipelineStatus(false);
                    logActivity('error', `Pipeline error: ${data.error}`);
                    break;
                case 'pong':
                    break;
                default:
                    console.log('[WS] Unhandled:', data.type);
            }
        }

        _reconnect() {
            if (this.reconnectAttempts >= this.maxReconnectAttempts) return;
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts - 1);
            setTimeout(() => this.connect(), delay);
        }

        _startPing() {
            this._pingInterval = setInterval(() => {
                if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send(JSON.stringify({ type: 'ping' }));
                }
            }, 30000);
        }

        _stopPing() {
            if (this._pingInterval) clearInterval(this._pingInterval);
        }

        on(event, callback) {
            if (!this.listeners[event]) this.listeners[event] = [];
            this.listeners[event].push(callback);
        }

        _emit(event, data) {
            (this.listeners[event] || []).forEach(cb => cb(data));
        }
    }

    // =========================================================================
    // Toast Notifications (glassmorphic, spring-animated)
    // =========================================================================
    function showToast(message, type = 'info', duration = 5000) {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const icons = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' };
        toast.innerHTML = `
            <span style="font-size:1.1rem">${icons[type] || 'ℹ'}</span>
            <span class="toast-message">${message}</span>
        `;

        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            toast.style.transition = 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    // =========================================================================
    // Animated Counter (anime.js-inspired ease-out-cubic)
    // =========================================================================
    function animateCounter(element, from, to) {
        if (from === to) return;
        const duration = 800;
        const start = performance.now();

        function step(timestamp) {
            const progress = Math.min((timestamp - start) / duration, 1);
            // ease-out cubic (anime.js default)
            const eased = 1 - Math.pow(1 - progress, 3);
            element.textContent = Math.round(from + (to - from) * eased);
            if (progress < 1) requestAnimationFrame(step);
        }

        requestAnimationFrame(step);
    }

    // =========================================================================
    // UI Update Functions
    // =========================================================================
    function updateConnectionStatus(status) {
        const dot = document.getElementById('connection-dot');
        const label = document.getElementById('connection-label');
        if (dot) {
            dot.className = `status-dot ${status === 'online' ? 'online' : status === 'error' ? 'error' : ''}`;
        }
        if (label) {
            const labels = { online: 'Connected', offline: 'Disconnected', error: 'Error' };
            label.textContent = labels[status] || status;
        }
    }

    function updatePipelineStatus(running) {
        const dot = document.getElementById('pipeline-status-dot');
        if (dot) dot.className = `status-dot ${running ? 'running' : 'online'}`;

        const btn = document.getElementById('start-pipeline-btn');
        if (btn) {
            btn.disabled = running;
            btn.textContent = running ? '⟳ Running...' : '▶ Start Pipeline';
        }

        // Update uptime ticker
        if (running) startUptimeTicker();
    }

    function updateAgentStatus(agentName, status) {
        const card = document.querySelector(`[data-agent="${agentName}"]`);
        if (card) {
            card.classList.remove('idle', 'active', 'completed', 'awaiting_approval', 'queued', 'error');
            card.classList.add(status);

            const badge = card.querySelector('.agent-status');
            if (badge) {
                badge.className = `agent-status ${status}`;
                const labels = {
                    idle: '● Idle',
                    active: '◉ Active',
                    completed: '✓ Done',
                    awaiting_approval: '⏸ Awaiting Approval',
                    queued: '○ Queued',
                    error: '✕ Error',
                    revision_in_progress: '↻ Revising',
                };
                badge.textContent = labels[status] || status;
            }
        }

        // Update pipeline visualizer step nodes
        const stepNode = document.querySelector(`.step-node[data-step="${agentName}"]`);
        if (stepNode) {
            stepNode.classList.remove('idle', 'active', 'completed', 'awaiting_approval');
            stepNode.classList.add(status);
        }
    }

    function updateDashboardState(state) {
        if (!state) return;

        const statMap = {
            'stat-trends': state.trends_count || 0,
            'stat-ideas': state.ideas_count || 0,
            'stat-hooks': state.hooks_count || 0,
            'stat-published': state.published_count || 0,
        };

        for (const [id, value] of Object.entries(statMap)) {
            const el = document.getElementById(id);
            if (el) animateCounter(el, parseInt(el.textContent) || 0, value);
        }

        if (state.current_agent) {
            const agentNames = {
                researcher: 'The Researcher',
                hook_writer: 'The Hook Writer',
                script_writer: 'The Script Writer',
                designer: 'The Designer',
                publisher: 'The Publisher',
                analyst: 'The Analyst',
            };
            const el = document.getElementById('current-agent-name');
            if (el) el.textContent = agentNames[state.current_agent] || state.current_agent;
        }
    }

    function showApprovalBadge(show) {
        const badge = document.getElementById('approval-badge');
        if (badge) badge.style.display = show ? 'inline-flex' : 'none';
    }

    // =========================================================================
    // Uptime Ticker
    // =========================================================================
    let uptimeInterval = null;
    let uptimeStart = null;

    function startUptimeTicker() {
        if (uptimeInterval) return;
        uptimeStart = Date.now();
        const el = document.getElementById('uptime-value');
        if (!el) return;

        uptimeInterval = setInterval(() => {
            const elapsed = Math.floor((Date.now() - uptimeStart) / 1000);
            const m = Math.floor(elapsed / 60);
            const s = elapsed % 60;
            el.textContent = `${m}m ${s}s`;
        }, 1000);
    }

    // =========================================================================
    // Pipeline Control
    // =========================================================================
    async function startPipeline() {
        try {
            const resp = await fetch('/api/pipeline/start', { method: 'POST' });
            const data = await resp.json();
            if (data.status === 'started') {
                showToast('Pipeline started!', 'success');
                logActivity('agent', 'Pipeline manually triggered');
            } else {
                showToast(data.message || 'Could not start', 'warning');
            }
        } catch (e) {
            showToast('Failed to start: ' + e.message, 'error');
        }
    }

    async function stopPipeline() {
        try {
            await fetch('/api/pipeline/stop', { method: 'POST' });
            showToast('Pipeline stopped', 'info');
            updatePipelineStatus(false);
            logActivity('agent', 'Pipeline manually stopped');
        } catch (e) {
            showToast('Failed to stop', 'error');
        }
    }

    // =========================================================================
    // Approval Handling
    // =========================================================================
    async function submitApproval(action) {
        const feedbackInput = document.getElementById('approval-feedback');
        const feedback = feedbackInput ? feedbackInput.value : '';

        try {
            const formData = new FormData();
            formData.append('action', action);
            formData.append('feedback', feedback);

            const resp = await fetch('/api/approve', { method: 'POST', body: formData });
            const data = await resp.json();

            if (data.status === 'processed') {
                showToast(`${action === 'approve' ? 'Approved' : 'Sent for revision'}!`, 'success');
                if (feedbackInput) feedbackInput.value = '';
                showApprovalBadge(false);
                logActivity('approval', `Human ${action}: ${data.agent}`);
                setTimeout(() => window.location.reload(), 1500);
            }
        } catch (e) {
            showToast('Approval failed: ' + e.message, 'error');
        }
    }

    // =========================================================================
    // Periodic Status Refresh (fallback when WS is down)
    // =========================================================================
    async function refreshStatus() {
        try {
            const resp = await fetch('/api/pipeline/status');
            const data = await resp.json();

            if (data.agent_statuses) {
                for (const [agent, status] of Object.entries(data.agent_statuses)) {
                    updateAgentStatus(agent, status);
                }
            }

            if (data.pipeline_running !== undefined) {
                updatePipelineStatus(data.pipeline_running);
            }
        } catch (e) {
            // Silent fail
        }
    }

    // =========================================================================
    // Staggered Card Entrance Animation (anime.js stagger principle via CSS)
    // =========================================================================
    function animateCardEntrance() {
        const cards = document.querySelectorAll('.fade-in');
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry, i) => {
                if (entry.isIntersecting) {
                    entry.target.style.animationDelay = `${i * 60}ms`;
                    entry.target.classList.add('visible');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        cards.forEach(card => observer.observe(card));
    }

    // =========================================================================
    // Initialize
    // =========================================================================
    function init() {
        const ws = new LoopWebSocket();
        ws.connect();

        // Bind buttons
        const startBtn = document.getElementById('start-pipeline-btn');
        if (startBtn) startBtn.addEventListener('click', startPipeline);

        const stopBtn = document.getElementById('stop-pipeline-btn');
        if (stopBtn) stopBtn.addEventListener('click', stopPipeline);

        const approveBtn = document.getElementById('approve-btn');
        if (approveBtn) approveBtn.addEventListener('click', () => submitApproval('approve'));

        const rejectBtn = document.getElementById('reject-btn');
        if (rejectBtn) rejectBtn.addEventListener('click', () => submitApproval('reject'));

        const reviseBtn = document.getElementById('revise-btn');
        if (reviseBtn) reviseBtn.addEventListener('click', () => submitApproval('revision_requested'));

        // Staggered card entrance
        animateCardEntrance();

        // Periodic refresh
        setInterval(refreshStatus, 15000);
        refreshStatus();

        // Log initial
        logActivity('agent', 'Dashboard initialized');

        console.log('[TheLoop] Dashboard initialized with skill bundle enhancements');
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    window.TheLoop = { startPipeline, stopPipeline, submitApproval, showToast, logActivity };
})();
