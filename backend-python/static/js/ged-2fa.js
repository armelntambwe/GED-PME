/**
 * Double authentification (TOTP) — module partagé dashboards GED-PME
 */
const Ged2FA = (function () {
    let getToken = () => localStorage.getItem('token');
    let showToast = (msg) => alert(msg);
    let onProfileRefresh = null;

    function authHeaders(json) {
        const h = { Authorization: 'Bearer ' + getToken() };
        if (json) h['Content-Type'] = 'application/json';
        return h;
    }

    function apiFetch(url, opts) {
        return fetch(url, opts).then(async (res) => {
            let json = {};
            try { json = await res.json(); } catch (e) {}
            return { ok: res.ok, json };
        });
    }

    function updateUI(profile) {
        const status = document.getElementById('twofaStatus');
        const setupPanel = document.getElementById('twofaSetupPanel');
        const disablePanel = document.getElementById('twofaDisablePanel');
        const setupBtn = document.getElementById('twofaSetupBtn');
        if (!status) return;
        const enabled = !!profile?.totp_enabled;
        if (enabled) {
            status.innerHTML = '<span class="badge bg-success"><i class="fas fa-shield-alt me-1"></i>2FA activée</span>';
            setupPanel?.classList.add('d-none');
            disablePanel?.classList.remove('d-none');
            setupBtn?.classList.add('d-none');
        } else {
            status.innerHTML = '<span class="badge bg-warning text-dark"><i class="fas fa-unlock me-1"></i>2FA désactivée — recommandée pour sécuriser votre compte</span>';
            disablePanel?.classList.add('d-none');
            setupPanel?.classList.add('d-none');
            setupBtn?.classList.remove('d-none');
        }
    }

    async function startSetup() {
        const { ok, json } = await apiFetch('/api/user/2fa/setup', { method: 'POST', headers: authHeaders(true) });
        if (!ok || !json.success) { showToast(json.message || 'Erreur configuration 2FA', true); return; }
        const secretEl = document.getElementById('twofaSecretDisplay');
        if (secretEl) secretEl.textContent = json.secret || '';
        const qrImg = document.getElementById('twofaQrImg');
        if (qrImg && json.otpauth_uri) {
            qrImg.src = 'https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=' + encodeURIComponent(json.otpauth_uri);
            qrImg.classList.remove('d-none');
        }
        document.getElementById('twofaSetupPanel')?.classList.remove('d-none');
        document.getElementById('twofaSetupBtn')?.classList.add('d-none');
        showToast('Scannez le QR code avec Google Authenticator ou Microsoft Authenticator');
    }

    async function confirmEnable() {
        const codeEl = document.getElementById('twofaEnableCode');
        const code = (codeEl?.value || '').trim();
        if (!code) { showToast('Saisissez le code à 6 chiffres', true); return; }
        const { ok, json } = await apiFetch('/api/user/2fa/enable', {
            method: 'POST', headers: authHeaders(true), body: JSON.stringify({ code }),
        });
        if (ok && json.success) {
            showToast('Double authentification activée');
            if (codeEl) codeEl.value = '';
            if (typeof onProfileRefresh === 'function') await onProfileRefresh();
        } else showToast(json.message || 'Code incorrect', true);
    }

    async function disable() {
        const code = (document.getElementById('twofaDisableCode')?.value || '').trim();
        const password = document.getElementById('twofaDisablePassword')?.value || '';
        if (!code || !password) { showToast('Mot de passe et code requis', true); return; }
        const { ok, json } = await apiFetch('/api/user/2fa/disable', {
            method: 'POST', headers: authHeaders(true), body: JSON.stringify({ code, password }),
        });
        if (ok && json.success) {
            showToast('Double authentification désactivée');
            const codeEl = document.getElementById('twofaDisableCode');
            const pwdEl = document.getElementById('twofaDisablePassword');
            if (codeEl) codeEl.value = '';
            if (pwdEl) pwdEl.value = '';
            if (typeof onProfileRefresh === 'function') await onProfileRefresh();
        } else showToast(json.message || 'Erreur', true);
    }

    function init(opts) {
        if (opts?.getToken) getToken = opts.getToken;
        if (opts?.showToast) showToast = opts.showToast;
        if (opts?.onProfileRefresh) onProfileRefresh = opts.onProfileRefresh;
        window.start2FASetup = startSetup;
        window.confirmEnable2FA = confirmEnable;
        window.disable2FA = disable;
    }

    return { init, updateUI, startSetup, confirmEnable, disable };
})();
