(function () {
    function authHeaders() {
        const token = typeof getCookie === 'function' ? getCookie('access_token') : null;
        const h = { 'Content-Type': 'application/json' };
        if (token) h.Authorization = 'Bearer ' + token;
        return h;
    }

    function toast(msg, kind) {
        if (typeof showNotification === 'function') {
            showNotification(msg, kind || 'success');
            return;
        }
        alert(msg);
    }

    async function api(method, url, body) {
        const opt = { method: method, credentials: 'include', headers: authHeaders() };
        if (body != null) opt.body = JSON.stringify(body);
        const r = await fetch(url, opt);
        if (!r.ok) {
            const j = await r.json().catch(function () { return {}; });
            const d = j.detail || r.statusText;
            throw new Error(typeof d === 'string' ? d : JSON.stringify(d));
        }
        return r.json();
    }

    async function loadIntegration() {
        const data = await api('GET', '/api/trading/integration');
        document.getElementById('n8n-webhook-url').value = data.n8n_webhook_url || '';
        document.getElementById('tradpulse-base').value = data.tradpulse_base_url || 'http://127.0.0.1:8888';
        document.getElementById('n8n-pull-token').textContent = data.n8n_pull_token || '—';
    }

    async function loadWatchlist() {
        const rows = await api('GET', '/api/trading/watchlist');
        const ul = document.getElementById('wl-list');
        ul.innerHTML = '';
        rows.forEach(function (r) {
            const li = document.createElement('li');
            li.style.cssText = 'display:flex;align-items:center;gap:12px;padding:8px 0;border-bottom:1px solid #e5e7eb;';
            li.innerHTML =
                '<strong>' + r.symbol + '</strong>' +
                (r.notes ? ' <span style="color:#64748b;">' + r.notes + '</span>' : '') +
                ' <button type="button" class="icon-btn" data-del="' + r.symbol + '">Remove</button>';
            ul.appendChild(li);
        });
        ul.querySelectorAll('[data-del]').forEach(function (btn) {
            btn.addEventListener('click', async function () {
                try {
                    await api('DELETE', '/api/trading/watchlist/' + encodeURIComponent(btn.getAttribute('data-del')));
                    await loadWatchlist();
                    toast('Removed', 'success');
                } catch (e) {
                    toast(e.message, 'error');
                }
            });
        });
    }

    async function init() {
        try {
            await loadIntegration();
            await loadWatchlist();
        } catch (e) {
            toast(e.message || 'Load failed', 'error');
        }

        document.getElementById('btn-save-integration').addEventListener('click', async function () {
            try {
                await api('PUT', '/api/trading/integration', {
                    n8n_webhook_url: document.getElementById('n8n-webhook-url').value.trim() || null,
                    tradpulse_base_url: document.getElementById('tradpulse-base').value.trim() || null,
                    enabled: true,
                });
                await loadIntegration();
                toast('Saved', 'success');
            } catch (e) {
                toast(e.message, 'error');
            }
        });

        document.getElementById('btn-rotate-token').addEventListener('click', async function () {
            if (!confirm('Rotate pull token? Update n8n with the new X-N8N-Token value.')) return;
            try {
                const d = await api('POST', '/api/trading/integration/rotate-token', {});
                document.getElementById('n8n-pull-token').textContent = d.n8n_pull_token;
                toast('Token rotated', 'success');
            } catch (e) {
                toast(e.message, 'error');
            }
        });

        document.getElementById('btn-push-n8n').addEventListener('click', async function () {
            try {
                await api('POST', '/api/trading/push-n8n', {});
                toast('Sent to n8n', 'success');
            } catch (e) {
                toast(e.message, 'error');
            }
        });

        document.getElementById('btn-save-cash').addEventListener('click', async function () {
            const bal = document.getElementById('cash-balance').value;
            const cur = document.getElementById('cash-currency').value;
            try {
                await api('PUT', '/api/trading/portfolio-cash', {
                    cash_balance: bal === '' ? null : parseFloat(bal),
                    cash_currency: cur,
                });
                toast('Cash saved', 'success');
            } catch (e) {
                toast(e.message, 'error');
            }
        });

        document.getElementById('btn-add-wl').addEventListener('click', async function () {
            const sym = document.getElementById('wl-symbol').value.trim();
            const notes = document.getElementById('wl-notes').value.trim() || null;
            if (!sym) return;
            try {
                await api('POST', '/api/trading/watchlist', { symbol: sym, notes: notes });
                document.getElementById('wl-symbol').value = '';
                document.getElementById('wl-notes').value = '';
                await loadWatchlist();
                toast('Added', 'success');
            } catch (e) {
                toast(e.message, 'error');
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
