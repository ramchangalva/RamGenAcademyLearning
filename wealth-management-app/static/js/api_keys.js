(function () {
    function authHeaders() {
        const token = typeof getCookie === 'function' ? getCookie('access_token') : null;
        const h = { 'Content-Type': 'application/json' };
        if (token) h.Authorization = 'Bearer ' + token;
        return h;
    }

    function toast(msg, kind) {
        const el = document.createElement('div');
        el.className = 'api-keys-toast ' + (kind || 'success');
        el.textContent = msg;
        document.body.appendChild(el);
        setTimeout(function () {
            el.remove();
        }, 3200);
    }

    function applyBadges(state) {
        if (!state || !state.providers) return;
        document.querySelectorAll('.api-key-card[data-provider]').forEach(function (card) {
            const id = card.getAttribute('data-provider');
            const badge = card.querySelector('[data-badge]');
            const configured = state.providers[id] && state.providers[id].configured;
            if (!badge) return;
            badge.classList.remove('configured', 'not-configured');
            if (configured) {
                badge.classList.add('configured');
                badge.textContent = 'Configured';
            } else {
                badge.classList.add('not-configured');
                badge.textContent = 'Not configured';
            }
        });

        const baseInput = document.getElementById('openai-base-url');
        if (baseInput && typeof state.openai_base_url === 'string') {
            baseInput.value = state.openai_base_url;
        }

        const prov = document.getElementById('active-provider');
        const model = document.getElementById('active-model');
        if (prov && state.active_provider) prov.value = state.active_provider;
        if (model && state.active_model) model.value = state.active_model;
    }

    async function loadState() {
        const r = await fetch('/api/settings/ai', {
            credentials: 'include',
            headers: authHeaders(),
        });
        if (!r.ok) {
            throw new Error('Could not load settings');
        }
        const data = await r.json();
        applyBadges(data);
        return data;
    }

    async function postJson(url, body) {
        const r = await fetch(url, {
            method: 'POST',
            credentials: 'include',
            headers: authHeaders(),
            body: JSON.stringify(body || {}),
        });
        if (!r.ok) {
            let detail = 'Request failed';
            try {
                const j = await r.json();
                if (j.detail) detail = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail);
            } catch (e) { /* ignore */ }
            throw new Error(detail);
        }
        return r.json();
    }

    async function putJson(url, body) {
        const r = await fetch(url, {
            method: 'PUT',
            credentials: 'include',
            headers: authHeaders(),
            body: JSON.stringify(body || {}),
        });
        if (!r.ok) {
            let detail = 'Request failed';
            try {
                const j = await r.json();
                if (j.detail) detail = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail);
            } catch (e) { /* ignore */ }
            throw new Error(detail);
        }
        return r.json();
    }

    function wireEye(card) {
        const input = card.querySelector('.api-key-input');
        const btn = card.querySelector('.api-key-eye');
        if (!input || !btn) return;
        btn.addEventListener('click', function () {
            const show = input.type === 'password';
            input.type = show ? 'text' : 'password';
            const i = btn.querySelector('i');
            if (i) {
                i.className = show ? 'fas fa-eye-slash' : 'fas fa-eye';
            }
        });
    }

    function wireSave(card) {
        const provider = card.getAttribute('data-provider');
        const input = card.querySelector('.api-key-input');
        const btn = card.querySelector('.api-key-save');
        if (!input || !btn) return;

        btn.addEventListener('click', async function () {
            const keyVal = (input.value || '').trim();
            const body = { provider: provider };

            if (keyVal) {
                body.api_key = keyVal;
            }

            const buEl = provider === 'openai' ? document.getElementById('openai-base-url') : null;
            const hasBaseOnly = buEl && (buEl.value || '').trim();

            if (provider === 'openai' && (keyVal || hasBaseOnly)) {
                body.base_url = buEl ? (buEl.value || '').trim() : '';
            }

            if (!keyVal && provider !== 'openai') {
                toast('Enter an API key to save, or leave unchanged.', 'error');
                return;
            }

            if (!keyVal && provider === 'openai' && !hasBaseOnly) {
                toast('Enter an API key and/or base URL to update.', 'error');
                return;
            }

            btn.disabled = true;
            try {
                const state = await postJson('/api/settings/ai/key', body);
                applyBadges(state);
                input.value = '';
                toast('Saved', 'success');
            } catch (e) {
                toast((e && e.message) || 'Save failed', 'error');
            } finally {
                btn.disabled = false;
            }
        });
    }

    function wireCollapse() {
        const body = document.getElementById('api-keys-panel-body');
        const label = document.getElementById('api-keys-toggle-label');
        const chevron = document.getElementById('api-keys-chevron');
        const trigger = document.getElementById('api-keys-collapse-trigger');
        const toggleBtn = document.getElementById('api-keys-toggle');

        function setCollapsed(on) {
            if (!body) return;
            body.classList.toggle('collapsed', on);
            if (label) label.textContent = on ? 'Show' : 'Hide';
            if (chevron) {
                chevron.className = on ? 'fas fa-chevron-down' : 'fas fa-chevron-up';
            }
            if (trigger) trigger.setAttribute('aria-expanded', on ? 'false' : 'true');
        }

        function flip() {
            const on = body && body.classList.contains('collapsed');
            setCollapsed(!on);
        }

        if (trigger) {
            trigger.addEventListener('click', function (e) {
                if (e.target.closest('#api-keys-toggle')) return;
                flip();
            });
            trigger.addEventListener('keydown', function (e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    flip();
                }
            });
        }
        if (toggleBtn) {
            toggleBtn.addEventListener('click', function (e) {
                e.stopPropagation();
                flip();
            });
        }
    }

    async function init() {
        wireCollapse();
        document.querySelectorAll('.api-key-card[data-provider]').forEach(function (card) {
            wireEye(card);
            wireSave(card);
        });

        const clearBtn = document.getElementById('api-keys-clear-all');
        if (clearBtn) {
            clearBtn.addEventListener('click', async function () {
                if (!window.confirm('Remove all stored API keys and OpenAI base URL for your account?')) return;
                clearBtn.disabled = true;
                try {
                    const state = await postJson('/api/settings/ai/clear', {});
                    applyBadges(state);
                    document.querySelectorAll('.api-key-input').forEach(function (inp) {
                        inp.value = '';
                    });
                    toast('All keys cleared', 'success');
                } catch (e) {
                    toast((e && e.message) || 'Clear failed', 'error');
                } finally {
                    clearBtn.disabled = false;
                }
            });
        }

        const prefBtn = document.getElementById('api-keys-save-preferences');
        if (prefBtn) {
            prefBtn.addEventListener('click', async function () {
                const prov = document.getElementById('active-provider');
                const model = document.getElementById('active-model');
                if (!prov || !model) return;
                const m = (model.value || '').trim();
                if (!m) {
                    toast('Model is required', 'error');
                    return;
                }
                prefBtn.disabled = true;
                try {
                    const state = await putJson('/api/settings/ai/preferences', {
                        active_provider: prov.value,
                        active_model: m,
                    });
                    applyBadges(state);
                    toast('Preferences saved', 'success');
                } catch (e) {
                    toast((e && e.message) || 'Save failed', 'error');
                } finally {
                    prefBtn.disabled = false;
                }
            });
        }

        try {
            await loadState();
        } catch (e) {
            toast((e && e.message) || 'Could not load API settings', 'error');
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
