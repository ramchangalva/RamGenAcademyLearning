(function () {
    const history = [];
    var advisorAvailable = false;

    function getBaseCurrency() {
        const sel = document.getElementById('currency-selector');
        if (sel && sel.value) {
            return sel.value;
        }
        return 'USD';
    }

    function el(tag, className, text) {
        const n = document.createElement(tag);
        if (className) n.className = className;
        if (text != null) n.textContent = text;
        return n;
    }

    function escapeHtml(str) {
        const d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
    }

    function appendMessage(role, text) {
        const box = document.getElementById('advisor-messages');
        if (!box) return;
        const m = el('div', 'advisor-msg ' + role, text);
        box.appendChild(m);
        box.scrollTop = box.scrollHeight;
        return m;
    }

    function setLoading(on) {
        const btn = document.getElementById('advisor-send');
        const typing = document.getElementById('advisor-typing');
        if (btn) btn.disabled = on;
        if (typing) typing.classList.toggle('active', on);
    }

    function clearDraftsUi() {
        const draftsEl = document.getElementById('advisor-drafts');
        if (!draftsEl) return;
        draftsEl.innerHTML = '';
        draftsEl.hidden = true;
    }

    function draftLabel(d) {
        const p = d.payload || {};
        switch (d.action) {
            case 'create_asset':
                return 'Add asset: ' + (p.name || '') + ' (' + (p.asset_type || '') + ') — ' + String(p.value) + ' ' + (p.currency || '');
            case 'update_asset':
                return 'Update asset #' + p.asset_id;
            case 'delete_asset':
                return 'Delete asset #' + p.asset_id;
            case 'create_liability':
                return 'Add liability: ' + (p.name || '') + ' — ' + String(p.outstanding_amount) + ' ' + (p.currency || '');
            case 'update_liability':
                return 'Update liability #' + p.liability_id;
            case 'delete_liability':
                return 'Delete liability #' + p.liability_id;
            default:
                return d.action;
        }
    }

    function renderDrafts(items) {
        const draftsEl = document.getElementById('advisor-drafts');
        if (!draftsEl || !items || !items.length) {
            if (draftsEl) draftsEl.hidden = true;
            return;
        }
        draftsEl.hidden = false;
        draftsEl.innerHTML = '<div class="advisor-drafts-title">Confirm portfolio changes</div>';

        items.forEach(function (d) {
            const row = document.createElement('div');
            row.className = 'advisor-draft-row';
            row.dataset.draftId = d.draft_id || '';
            const span = document.createElement('span');
            span.innerHTML = escapeHtml(draftLabel(d));
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.textContent = 'Confirm';
            btn.addEventListener('click', function () {
                applyDraft(d, row, btn);
            });
            row.appendChild(span);
            row.appendChild(btn);
            draftsEl.appendChild(row);
        });
    }

    async function applyDraft(draft, row, btn) {
        btn.disabled = true;
        try {
            await apiRequest('/api/advisor/apply', {
                method: 'POST',
                body: JSON.stringify({
                    action: draft.action,
                    payload: draft.payload
                })
            });
            if (typeof showNotification === 'function') {
                showNotification('Change applied to your portfolio', 'success');
            }
            row.remove();
            const draftsEl = document.getElementById('advisor-drafts');
            if (draftsEl && !draftsEl.querySelector('.advisor-draft-row')) {
                draftsEl.hidden = true;
                draftsEl.innerHTML = '';
            }
        } catch (e) {
            btn.disabled = false;
            if (typeof showNotification === 'function') {
                showNotification((e && e.message) ? e.message : 'Could not apply change', 'error');
            }
        }
    }

    function authHeaders() {
        const token = typeof getCookie === 'function' ? getCookie('access_token') : null;
        const h = { 'Content-Type': 'application/json' };
        if (token) h.Authorization = 'Bearer ' + token;
        return h;
    }

    async function sendUserMessageStream() {
        const input = document.getElementById('advisor-input');
        if (!input) return;
        const text = (input.value || '').trim();
        if (!text) return;

        input.value = '';
        history.push({ role: 'user', content: text });
        appendMessage('user', text);
        clearDraftsUi();
        setLoading(true);

        var assistantBubble = null;
        var fullReply = '';
        try {
            const response = await fetch('/api/advisor/chat/stream', {
                method: 'POST',
                credentials: 'include',
                headers: authHeaders(),
                body: JSON.stringify({
                    messages: history.map(function (m) {
                        return { role: m.role, content: m.content };
                    }),
                    base_currency: getBaseCurrency()
                })
            });

            if (!response.ok) {
                const errBody = await response.json().catch(function () { return {}; });
                const detail = errBody.detail || ('HTTP ' + response.status);
                throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const parts = buffer.split('\n\n');
                buffer = parts.pop() || '';

                for (let i = 0; i < parts.length; i++) {
                    const block = parts[i].trim();
                    if (!block.startsWith('data:')) continue;
                    let payload;
                    try {
                        payload = JSON.parse(block.slice(5).trim());
                    } catch (err) {
                        continue;
                    }
                    if (payload.type === 'token' && payload.text) {
                        if (!assistantBubble) {
                            assistantBubble = appendMessage('assistant', '');
                        }
                        fullReply += payload.text;
                        assistantBubble.textContent = fullReply;
                        const box = document.getElementById('advisor-messages');
                        if (box) box.scrollTop = box.scrollHeight;
                    } else if (payload.type === 'drafts') {
                        renderDrafts(payload.items || []);
                    } else if (payload.type === 'error') {
                        throw new Error(payload.message || 'Stream error');
                    }
                }
            }

            if (buffer.trim()) {
                const block = buffer.trim();
                if (block.startsWith('data:')) {
                    try {
                        const payload = JSON.parse(block.slice(5).trim());
                        if (payload.type === 'drafts') {
                            renderDrafts(payload.items || []);
                        }
                    } catch (err) { /* ignore */ }
                }
            }

            if (fullReply) {
                history.push({ role: 'assistant', content: fullReply });
            } else if (!assistantBubble) {
                appendMessage('assistant', '(No response text)');
            }
        } catch (e) {
            if (assistantBubble && assistantBubble.parentNode) {
                assistantBubble.parentNode.removeChild(assistantBubble);
            }
            try {
                const res = await apiRequest('/api/advisor/chat', {
                    method: 'POST',
                    body: JSON.stringify({
                        messages: history.filter(function (m) {
                            return m.role === 'user' || m.role === 'assistant';
                        }),
                        base_currency: getBaseCurrency()
                    })
                });
                if (res && res.content) {
                    if (history.length && history[history.length - 1].role === 'user') {
                        history.push({ role: 'assistant', content: res.content });
                    }
                    appendMessage('assistant', res.content);
                    renderDrafts(res.drafts || []);
                }
            } catch (e2) {
                appendMessage('error', (e2 && e2.message) ? e2.message : (e && e.message) || 'Request failed');
            }
        } finally {
            setLoading(false);
        }
    }

    function init() {
        const fab = document.getElementById('advisor-fab');
        const panel = document.getElementById('advisor-panel');
        const closeBtn = document.getElementById('advisor-close');
        const sendBtn = document.getElementById('advisor-send');
        const input = document.getElementById('advisor-input');

        if (!fab || !panel) return;

        var banner = document.getElementById('advisor-setup-banner');

        function refreshAdvisorStatus(isInitial) {
            fetch('/api/advisor/status', { credentials: 'include', headers: authHeaders() })
                .then(function (r) {
                    if (!r.ok) {
                        throw new Error('status_http_' + r.status);
                    }
                    return r.json();
                })
                .then(function (data) {
                    advisorAvailable = !!(data && data.available);
                    fab.classList.toggle('advisor-fab-needs-key', !advisorAvailable);
                    fab.title = advisorAvailable
                        ? 'Wealth advisor — click to chat'
                        : 'Wealth advisor — add an API key in Settings to chat';
                    if (banner) {
                        banner.hidden = advisorAvailable;
                    }
                })
                .catch(function () {
                    if (isInitial) {
                        advisorAvailable = false;
                        fab.classList.add('advisor-fab-needs-key');
                        if (banner) {
                            banner.hidden = false;
                        }
                    }
                });
        }

        refreshAdvisorStatus(true);

        fab.addEventListener('click', function () {
            panel.classList.toggle('open');
            if (panel.classList.contains('open')) {
                refreshAdvisorStatus(false);
                if (input) {
                    input.focus();
                }
            }
        });

        if (closeBtn) {
            closeBtn.addEventListener('click', function () {
                panel.classList.remove('open');
            });
        }

        if (sendBtn) {
            sendBtn.addEventListener('click', sendUserMessageStream);
        }

        if (input) {
            input.addEventListener('keydown', function (e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendUserMessageStream();
                }
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
