/**
 * GED-PME - Dashboard Employé
 * API, cache, mode hors-ligne, documents
 */
(function () {
    'use strict';

    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/login';
        return;
    }

    let currentUser = null;
    try { currentUser = JSON.parse(localStorage.getItem('user') || 'null'); } catch (e) { currentUser = null; }
    if (currentUser && currentUser.role && currentUser.role !== 'employe') {
        if (currentUser.role === 'admin_global') window.location.href = '/dashboard-admin-global';
        else if (currentUser.role === 'admin_pme') window.location.href = '/dashboard-pme';
        else window.location.href = '/login';
        return;
    }

    const API = window.location.origin;
    let currentDocId = null;
    let currentDocMeta = null;
    let docPage = 1;
    let docTotalPages = 1;
    let evolutionChart = null;
    let statusChart = null;
    let categoriesCache = null;
    let documentsCache = {};
    let isLoadingDocs = false;
    let currentCategoryFilter = '';

    function escapeHtml(str) {
        return String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    function getFileIcon(ext) {
        const m = {
            pdf: 'fa-file-pdf text-danger', doc: 'fa-file-word text-primary', docx: 'fa-file-word text-primary',
            xls: 'fa-file-excel text-success', xlsx: 'fa-file-excel text-success',
            ppt: 'fa-file-powerpoint text-warning', pptx: 'fa-file-powerpoint text-warning',
            zip: 'fa-file-archive text-secondary', rar: 'fa-file-archive text-secondary',
            mp4: 'fa-file-video text-info', mp3: 'fa-file-audio text-info',
            jpg: 'fa-file-image text-primary', jpeg: 'fa-file-image text-primary', png: 'fa-file-image text-primary',
        };
        return m[ext] || 'fa-file-alt text-muted';
    }

    const PREVIEW_IMAGE_EXT = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg', 'ico', 'tif', 'tiff'];
    const PREVIEW_TEXT_EXT = ['txt', 'md', 'csv', 'json', 'xml', 'html', 'htm', 'css', 'js', 'py', 'sql', 'log', 'yaml', 'yml', 'ini', 'cfg', 'rtf'];
    const PREVIEW_VIDEO_EXT = ['mp4', 'webm', 'ogg', 'mov', 'avi'];
    const PREVIEW_AUDIO_EXT = ['mp3', 'wav', 'ogg', 'aac', 'm4a', 'flac'];

    const MIME_BY_EXT = {
        pdf: 'application/pdf', doc: 'application/msword', docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        xls: 'application/vnd.ms-excel', xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        ppt: 'application/vnd.ms-powerpoint', pptx: 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        txt: 'text/plain', md: 'text/markdown', csv: 'text/csv', json: 'application/json', xml: 'application/xml',
        html: 'text/html', htm: 'text/html', jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png',
        gif: 'image/gif', webp: 'image/webp', mp4: 'video/mp4', mp3: 'audio/mpeg', wav: 'audio/wav', zip: 'application/zip',
    };

    function fileExtension(filename) {
        return (filename || '').split('.').pop().toLowerCase();
    }

    function inferMime(filename, mime) {
        const ext = fileExtension(filename);
        if (mime && !['application/octet-stream', 'binary/octet-stream', ''].includes(mime)) return mime;
        return MIME_BY_EXT[ext] || mime || 'application/octet-stream';
    }

    function documentPreviewUrl(docId) {
        return `${API}/documents/${docId}/preview?token=${encodeURIComponent(token)}`;
    }

    function canUseDirectPreview(filename, mime) {
        const ext = fileExtension(filename);
        const m = inferMime(filename, mime);
        return ext === 'pdf' || m.includes('pdf') || m.startsWith('image/') || PREVIEW_IMAGE_EXT.includes(ext);
    }

    function buildDirectPreviewHtml(docId, filename, mime) {
        const url = documentPreviewUrl(docId);
        const ext = fileExtension(filename);
        const m = inferMime(filename, mime);
        if (ext === 'pdf' || m.includes('pdf')) {
            return `<iframe src="${url}" class="pdf-preview w-100" style="height:480px;border:1px solid #e2e8f0;border-radius:8px;" title="Aperçu PDF"></iframe>`;
        }
        return `<div class="text-center"><img src="${url}" class="img-fluid rounded border shadow-sm" style="max-height:480px" alt="Aperçu"></div>`;
    }

    async function buildDocumentPreview(blob, mime, filename, doc) {
        const ext = fileExtension(filename);
        const blobUrl = URL.createObjectURL(blob);
        const resolvedMime = inferMime(filename, mime);

        if (resolvedMime.includes('pdf') || ext === 'pdf') {
            return `<iframe src="${blobUrl}" class="pdf-preview w-100" style="height:480px;border:1px solid #e2e8f0;border-radius:8px;" title="Aperçu PDF"></iframe>`;
        }
        if (resolvedMime.includes('image') || PREVIEW_IMAGE_EXT.includes(ext)) {
            return `<div class="text-center"><img src="${blobUrl}" class="img-fluid rounded border shadow-sm" style="max-height:480px" alt="Aperçu"></div>`;
        }
        if (PREVIEW_VIDEO_EXT.includes(ext) || resolvedMime.startsWith('video/')) {
            return `<video src="${blobUrl}" controls class="w-100 rounded border" style="max-height:480px"></video>`;
        }
        if (PREVIEW_AUDIO_EXT.includes(ext) || resolvedMime.startsWith('audio/')) {
            return `<div class="text-center py-3"><i class="fas fa-music fa-2x text-primary mb-2"></i><audio src="${blobUrl}" controls class="w-100"></audio></div>`;
        }
        if (resolvedMime.includes('text') || PREVIEW_TEXT_EXT.includes(ext)) {
            try {
                const text = await blob.text();
                return `<pre class="ocr-text border rounded p-3 bg-white mb-0" style="max-height:480px;overflow:auto;white-space:pre-wrap;">${escapeHtml(text.substring(0, 80000))}</pre>`;
            } catch (e) { /* fallthrough */ }
        }
        if (ext === 'docx' && window.mammoth) {
            try {
                const arrayBuffer = await blob.arrayBuffer();
                const result = await window.mammoth.convertToHtml({ arrayBuffer });
                return `<div class="docx-preview border rounded p-3 bg-white" style="max-height:480px;overflow:auto;">${result.value || '<p class="text-muted">Document vide</p>'}</div>`;
            } catch (e) { /* fallthrough */ }
        }
        if (ext === 'svg' || ext === 'htm' || ext === 'html') {
            return `<iframe src="${blobUrl}" class="w-100 border rounded" style="height:480px"></iframe>`;
        }
        const icon = getFileIcon(ext);
        let ocrBlock = '';
        if (doc && doc.contenu_ocr) {
            ocrBlock = `<hr><p class="small fw-semibold text-start"><i class="fas fa-font me-1"></i>Texte extrait (OCR)</p><pre class="ocr-text text-start small">${escapeHtml(doc.contenu_ocr.substring(0, 5000))}</pre>`;
        }
        return `<div class="text-center py-4 border rounded bg-light">
            <i class="fas ${icon} fa-4x mb-3"></i>
            <p class="fw-semibold mb-1">${escapeHtml(filename)}</p>
            <p class="text-muted small">${escapeHtml(mime || ext.toUpperCase())} · ${formatSize(blob.size)}</p>
            <p class="small text-muted">Prévisualisation limitée pour ce format.</p>
            <button type="button" class="btn btn-sm btn-primary" onclick="downloadDocument(${doc.id})"><i class="fas fa-download me-1"></i>Télécharger pour ouvrir</button>
            ${ocrBlock}
        </div>`;
    }

    // ========== UTILITIES ==========
    window.showToast = function (msg, isError) {
        const toast = document.getElementById('toastMessage');
        if (!toast) return;
        toast.textContent = msg;
        toast.style.background = isError ? '#ef4444' : '#10b981';
        toast.style.display = 'block';
        toast.style.opacity = '1';
        setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => { toast.style.display = 'none'; }, 300); }, 3000);
    };

    function formatDate(dateStr) {
        if (!dateStr) return '-';
        return new Date(dateStr).toLocaleDateString('fr-FR');
    }

    function formatSize(bytes) {
        if (!bytes) return '-';
        if (bytes < 1024) return bytes + ' o';
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' Ko';
        return (bytes / 1048576).toFixed(1) + ' Mo';
    }

    function authHeaders(json) {
        const h = { Authorization: 'Bearer ' + token };
        if (json) h['Content-Type'] = 'application/json';
        return h;
    }

    async function queueWriteAction(method, options) {
        if (!window.offlineQueue) throw new Error('File hors-ligne indisponible');
        const actionMap = {
            PUT: options.offlineAction || 'SOUMISSION',
            POST: options.offlineAction || 'UPLOAD',
            DELETE: 'DELETE',
        };
        let offlineData = options.offlineData || {};

        if (options.offlineAction === 'UPLOAD' && options.offlineFile && window.gedOfflineStore) {
            const fileId = 'upload_' + Date.now();
            await window.gedOfflineStore.saveFile(fileId, options.offlineFile);
            offlineData = {
                ...offlineData,
                fileId,
                fichier: options.offlineFile.name,
            };
        }

        await window.offlineQueue.addAction(actionMap[method] || options.offlineAction || 'SOUMISSION', offlineData);
        await updateOfflineBanner();
        showToast('Action enregistrée — synchronisation au retour de connexion');
    }

    async function apiFetch(url, options = {}) {
        const method = (options.method || 'GET').toUpperCase();
        const fullUrl = url.startsWith('http') ? url : API + url;
        const isWrite = ['POST', 'PUT', 'DELETE', 'PATCH'].includes(method);
        const headers = {
            ...authHeaders(!!(options.body && typeof options.body === 'string')),
            ...(options.headers || {}),
        };
        const fetchOpts = { ...options, method, headers };

        if (isWrite) {
            if (!navigator.onLine) {
                await queueWriteAction(method, options);
                return { ok: true, offline: true, json: { success: true, message: 'En attente de sync' } };
            }
            try {
                const res = await fetch(fullUrl, fetchOpts);
                let json = {};
                try { json = await res.json(); } catch (e) { json = {}; }
                return { ok: res.ok, status: res.status, json };
            } catch (e) {
                await queueWriteAction(method, options);
                return { ok: true, offline: true, json: { success: true, message: 'En attente de sync' } };
            }
        }

        try {
            const res = await fetch(fullUrl, fetchOpts);
            let json = {};
            try { json = await res.json(); } catch (err) { json = {}; }
            if (res.ok && window.gedOfflineStore) {
                await window.gedOfflineStore.cacheApi(fullUrl, json);
            }
            return { ok: res.ok, status: res.status, json, fromCache: false };
        } catch (e) {
            if (window.gedOfflineStore) {
                const cached = await window.gedOfflineStore.getApi(fullUrl);
                if (cached) {
                    return { ok: true, status: 200, json: cached, fromCache: true };
                }
            }
            return { ok: false, status: 0, json: { success: false, message: 'Hors ligne — ouvrez l’app une fois en ligne pour charger les données' } };
        }
    }

    window.logout = function () {
        localStorage.clear();
        window.location.href = '/login';
    };

    function getBadge(statut) {
        const map = {
            brouillon: 'badge-brouillon', soumis: 'badge-revision', valide: 'badge-valide',
            rejete: 'badge-rejete', publie: 'badge-publie', obsolete: 'badge-obsolete', detruit: 'badge-detruit',
        };
        const label = {
            brouillon: 'Brouillon', soumis: 'En révision', valide: 'Validé', rejete: 'Rejeté',
            publie: 'Publié', obsolete: 'Obsolète', detruit: 'Détruit',
        };
        return `<span class="badge-custom ${map[statut] || 'badge-brouillon'}">${label[statut] || statut}</span>`;
    }

    function resolvePhotoUrl(url) {
        if (!url) return '/static/img/default-avatar.svg';
        if (url.startsWith('/api/user/photo')) {
            const sep = url.includes('?') ? '&' : '?';
            return url + sep + 'token=' + encodeURIComponent(token);
        }
        return url;
    }

    // ========== OFFLINE ==========
    async function updateOfflineBanner() {
        const banner = document.getElementById('offlineBanner');
        const countEl = document.getElementById('offlineCount');
        const syncBtn = document.getElementById('syncBtn');
        let count = 0;
        if (window.offlineQueue) count = await window.offlineQueue.getPendingCount();
        if (countEl) countEl.textContent = count;
        if (syncBtn) syncBtn.style.display = count > 0 ? 'inline-flex' : 'none';
        if (!banner) return;
        if (!navigator.onLine || count > 0) {
            banner.style.display = 'flex';
        } else {
            banner.style.display = 'none';
        }
    }

    window.syncOfflineActions = async function () {
        if (!window.offlineQueue) return;
        if (!navigator.onLine) { showToast('Connexion requise pour synchroniser', true); return; }
        const pending = await window.offlineQueue.getPendingCount();
        if (!pending) { showToast('Aucune action en attente'); return; }
        showToast('Synchronisation en cours...');
        const results = await window.offlineQueue.syncAll();
        const ok = results.filter(r => r.success).length;
        const fail = results.filter(r => !r.success && !r.conflict);
        const authFail = fail.find(r => r.auth);
        if (ok) showToast(`${ok} action(s) synchronisée(s)`);
        if (authFail) {
            showToast('Session expirée — reconnectez-vous puis cliquez Synchroniser', true);
        } else if (fail.length) {
            const detail = fail.map(r => `${r.action}: ${r.error || 'échec'}`).slice(0, 2).join(' · ');
            showToast(`${fail.length} échec(s) — ${detail}`, true);
            console.warn('Sync échecs:', fail);
        }
        categoriesCache = null;
        await updateOfflineBanner();
        refreshVisibleTab();
    };

    function updateConnectionStatus() {
        const s = document.getElementById('connectionStatus');
        if (!s) return;
        if (navigator.onLine) {
            s.className = 'status-online';
            s.innerHTML = '<span class="dot"></span> Connecté';
        } else {
            s.className = 'status-offline';
            s.innerHTML = '<span class="dot"></span> Hors ligne';
            const banner = document.getElementById('offlineBanner');
            if (banner) banner.style.display = 'flex';
        }
        updateOfflineBanner();
    }

    window.addEventListener('online', () => {
        updateConnectionStatus();
        setTimeout(() => syncOfflineActions(), 800);
    });
    window.addEventListener('offline', updateConnectionStatus);
    updateConnectionStatus();

    // ========== DOCUMENT BLOB ==========
    async function fetchDocumentBlob(docId, hintFilename) {
        const tryFetch = async (kind) => {
            const res = await fetch(`${API}/documents/${docId}/${kind}`, { headers: authHeaders() });
            if (!res.ok) return null;
            const ct = (res.headers.get('Content-Type') || '').toLowerCase();
            if (ct.includes('application/json')) return null;
            const blob = await res.blob();
            if (!blob || blob.size === 0) return null;
            let filename = hintFilename || documentsCache[docId]?.fichier_nom || 'document';
            const disp = res.headers.get('Content-Disposition');
            if (disp) {
                const m = disp.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                if (m) filename = decodeURIComponent(m[1].replace(/['"]/g, ''));
            }
            const mime = inferMime(filename, res.headers.get('Content-Type') || blob.type);
            if (window.gedOfflineStore) {
                await window.gedOfflineStore.saveDocBlob(docId, blob, filename, mime);
            }
            return { blob, filename, mime };
        };

        try {
            const fromPreview = await tryFetch('preview');
            if (fromPreview) return fromPreview;
            const fromDownload = await tryFetch('download');
            if (fromDownload) return fromDownload;
            throw new Error('Fichier inaccessible');
        } catch (e) {
            if (window.gedOfflineStore) {
                const cached = await window.gedOfflineStore.getDocBlob(docId);
                if (cached) return cached;
            }
            throw e;
        }
    }

    window.downloadDocument = async function (id) {
        try {
            const { blob, filename } = await fetchDocumentBlob(id);
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
            showToast('Téléchargement lancé : ' + filename);
        } catch (e) {
            showToast('Erreur de téléchargement', true);
        }
    };

    window.downloadCurrentDoc = function () {
        if (currentDocId) downloadDocument(currentDocId);
    };

    window.printCurrentDoc = async function () {
        if (!currentDocId) return;
        try {
            const { blob, filename, mime } = await fetchDocumentBlob(currentDocId);
            const url = URL.createObjectURL(blob);
            if (mime.includes('pdf') || mime.includes('image')) {
                const w = window.open(url, '_blank');
                if (w) w.onload = () => setTimeout(() => w.print(), 600);
            } else {
                printDocumentMeta(currentDocMeta);
            }
        } catch (e) {
            printDocumentMeta(currentDocMeta);
        }
    };

    function printDocumentMeta(doc) {
        if (!doc) return;
        const w = window.open('', '_blank');
        w.document.write(`<html><head><title>${doc.titre}</title><style>body{font-family:Segoe UI,Arial;margin:40px;}h1{color:#0891b2;}table{width:100%;border-collapse:collapse;}td{padding:8px;border-bottom:1px solid #eee;}</style></head><body>
            <h1>${doc.titre}</h1><hr>
            <table><tr><td><strong>Catégorie</strong></td><td>${doc.categorie_nom || '-'}</td></tr>
            <tr><td><strong>Auteur</strong></td><td>${doc.auteur_nom || '-'}</td></tr>
            <tr><td><strong>Date</strong></td><td>${formatDate(doc.date_creation)}</td></tr>
            <tr><td><strong>Statut</strong></td><td>${doc.statut}</td></tr>
            <tr><td><strong>Fichier</strong></td><td>${doc.fichier_nom || '-'}</td></tr>
            <tr><td><strong>Description</strong></td><td>${doc.description || '-'}</td></tr></table>
            <script>window.onload=function(){window.print();}<\/script></body></html>`);
        w.document.close();
    }

    window.printDocument = function (id) {
        currentDocId = id;
        printCurrentDoc();
    };

    // ========== VIEW DOCUMENT ==========
    window.viewDocument = async function (docId) {
        currentDocId = docId;
        const body = document.getElementById('viewDocBody');
        const modal = document.getElementById('viewDocumentModal');
        if (body) body.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary"></div><p class="mt-2 text-muted">Chargement...</p></div>';
        if (modal) new bootstrap.Modal(modal).show();

        try {
            let doc = null;
            const { ok, json, fromCache } = await apiFetch(`/documents/${docId}/contenu`, { headers: authHeaders() });
            if (ok && json.document) {
                doc = json.document;
            } else if (documentsCache[docId]) {
                doc = documentsCache[docId];
            }
            if (!doc) {
                if (body) body.innerHTML = '<div class="alert alert-warning"><i class="fas fa-wifi-slash me-2"></i>Document non disponible hors ligne. Ouvrez l’app en ligne une fois pour le mettre en cache.</div>';
                return;
            }
            currentDocMeta = doc;
            documentsCache[docId] = doc;
            document.getElementById('viewDocTitle').textContent = doc.titre;
            updateWorkflowVisual(doc.statut);

            let previewHtml = '<div class="alert alert-warning mb-0"><i class="fas fa-exclamation-triangle me-2"></i>Aucun fichier associé à ce document.</div>';
            const fname = doc.fichier_nom || '';
            if (fname) {
                try {
                    const { blob, mime, filename } = await fetchDocumentBlob(docId, fname);
                    previewHtml = await buildDocumentPreview(blob, mime, filename || fname, doc);
                } catch (e) {
                    if (doc.contenu_ocr) {
                        previewHtml = `<div class="border rounded p-3 bg-light"><p class="small fw-semibold mb-2"><i class="fas fa-font me-1"></i>Texte extrait (OCR)</p><pre class="ocr-text mb-0 small" style="max-height:420px;overflow:auto;">${escapeHtml(doc.contenu_ocr.substring(0, 8000))}</pre></div>`;
                    } else {
                        previewHtml = `<div class="alert alert-warning mb-0"><i class="fas fa-exclamation-triangle me-2"></i>Impossible de charger le fichier.<br><button type="button" class="btn btn-sm btn-primary mt-2" onclick="downloadDocument(${docId})"><i class="fas fa-download me-1"></i>Télécharger quand même</button></div>`;
                    }
                }
            }

            if (body) {
                body.innerHTML = `
                ${fromCache ? '<div class="alert alert-info py-2 small"><i class="fas fa-database me-1"></i>Données en cache (mode hors ligne)</div>' : ''}
                <div class="row g-3">
                    <div class="col-lg-5">
                        <div class="card border-0 bg-light h-100">
                            <div class="card-body">
                                <h6 class="fw-bold mb-3"><i class="fas fa-info-circle me-2 text-primary"></i>Métadonnées</h6>
                                <table class="table table-sm table-borderless mb-0">
                                    <tr><td class="text-muted">Titre</td><td class="fw-semibold">${doc.titre || '-'}</td></tr>
                                    <tr><td class="text-muted">Catégorie</td><td>${doc.categorie_nom || 'Sans'}</td></tr>
                                    <tr><td class="text-muted">Auteur</td><td>${doc.auteur_nom || '-'}</td></tr>
                                    <tr><td class="text-muted">Date</td><td>${formatDate(doc.date_creation)}</td></tr>
                                    <tr><td class="text-muted">Statut</td><td>${getBadge(doc.statut)}</td></tr>
                                    <tr><td class="text-muted">Version</td><td>V${doc.version_actuelle || 1}</td></tr>
                                    <tr><td class="text-muted">Fichier</td><td class="small">${doc.fichier_nom || '-'}</td></tr>
                                    <tr><td class="text-muted">Taille</td><td>${formatSize(doc.fichier_taille)}</td></tr>
                                </table>
                                ${doc.description ? `<hr><p class="small mb-0"><strong>Description :</strong> ${doc.description}</p>` : ''}
                                ${doc.commentaire_rejet ? `<div class="alert alert-danger py-2 mt-2 small"><i class="fas fa-times-circle me-1"></i>${doc.commentaire_rejet}</div>` : ''}
                            </div>
                        </div>
                    </div>
                    <div class="col-lg-7">
                        <h6 class="fw-bold mb-2"><i class="fas fa-eye me-2 text-primary"></i>Aperçu</h6>
                        ${previewHtml}
                    </div>
                </div>`;
            }
        } catch (e) {
            if (body) body.innerHTML = '<div class="alert alert-danger">Erreur de chargement</div>';
        }
    };

    // ========== SHARE / EMAIL / WHATSAPP ==========
    window.shareDocument = async function (id) {
        try {
            const { blob, filename } = await fetchDocumentBlob(id);
            const file = new File([blob], filename, { type: blob.type });
            if (navigator.canShare && navigator.canShare({ files: [file] })) {
                await navigator.share({ title: 'Document GED-PME', files: [file] });
                return;
            }
        } catch (e) { /* fallback */ }
        const url = `${API}/documents/${id}/download`;
        await navigator.clipboard.writeText(url);
        showToast('Lien copié — utilisez Partager natif si disponible');
    };

    window.shareCurrentDoc = function () {
        if (currentDocId) shareDocument(currentDocId);
    };

    window.shareWhatsAppDoc = async function (id) {
        const meta = documentsCache[id];
        const titre = meta?.titre || 'Document';
        try {
            const { blob, filename } = await fetchDocumentBlob(id);
            const file = new File([blob], filename, { type: blob.type });
            if (navigator.canShare && navigator.canShare({ files: [file] })) {
                await navigator.share({ title: `GED-PME : ${titre}`, text: `Document : ${titre}`, files: [file] });
                return;
            }
        } catch (e) { /* fallback wa.me */ }
        const msg = encodeURIComponent(`Document GED-PME : ${titre}\nTéléchargez-le depuis votre espace GED-PME.`);
        window.open(`https://wa.me/?text=${msg}`, '_blank');
        showToast('WhatsApp ouvert — joignez le fichier depuis Télécharger si besoin');
    };

    window.shareWhatsApp = function () {
        if (currentDocId) shareWhatsAppDoc(currentDocId);
    };

    window.openEmailModal = function () {
        if (!currentDocId) return;
        document.getElementById('emailDest').value = '';
        document.getElementById('emailMessage').value = `Veuillez trouver ci-joint le document « ${currentDocMeta?.titre || ''} ».`;
        new bootstrap.Modal(document.getElementById('emailModal')).show();
    };

    window.sendDocumentEmail = async function () {
        const email = document.getElementById('emailDest').value.trim();
        const message = document.getElementById('emailMessage').value.trim();
        if (!email) { showToast('Email requis', true); return; }
        try {
            const { ok, json } = await apiFetch(`/documents/${currentDocId}/envoyer-email`, {
                method: 'POST', headers: authHeaders(true),
                body: JSON.stringify({ email, message }),
            });
            if (ok && json.success) {
                showToast('Document envoyé par email');
                bootstrap.Modal.getInstance(document.getElementById('emailModal')).hide();
                return;
            }
            if (json.smtp_required) {
                await downloadDocument(currentDocId);
                window.location.href = `mailto:${encodeURIComponent(email)}?subject=${encodeURIComponent('Document GED-PME')}&body=${encodeURIComponent(message + '\n\n(Pièce jointe : fichier téléchargé)')}`;
                showToast('SMTP non configuré — mail ouvert avec fichier téléchargé');
                return;
            }
            showToast(json.message || 'Erreur envoi', true);
        } catch (e) {
            showToast('Erreur envoi email', true);
        }
    };

    // ========== WORKFLOW VISUAL ==========
    function updateWorkflowVisual(statut) {
        $('#workflowVisual .workflow-step').removeClass('active done rejected');
        if (statut === 'rejete') {
            $('#wfRejete').addClass('active rejected');
            $('#wfRejectArrow').show();
            return;
        }
        $('#wfRejectArrow').hide();
        const order = ['wfBrouillon', 'wfRevision', 'wfValide', 'wfPublie'];
        const steps = {
            brouillon: ['wfBrouillon'], soumis: ['wfBrouillon', 'wfRevision'],
            valide: ['wfBrouillon', 'wfRevision', 'wfValide'],
            publie: ['wfBrouillon', 'wfRevision', 'wfValide', 'wfPublie'],
        };
        const activeSet = steps[statut] || ['wfBrouillon'];
        order.forEach(id => {
            const el = $('#' + id);
            if (activeSet.includes(id) && id === activeSet[activeSet.length - 1]) el.addClass('active');
            else if (activeSet.includes(id)) el.addClass('done');
        });
    }

    // ========== DATA LOADING ==========
    async function loadUserInfo(skipWhatsapp) {
        try {
            const { json } = await apiFetch('/api/user/profile', { headers: authHeaders() });
            if (!json.success) return;
            $('#userName').text(json.nom);
            const avatar = document.getElementById('userAvatar');
            if (json.photo_url) {
                avatar.innerHTML = `<img src="${resolvePhotoUrl(json.photo_url)}" alt="" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">`;
            } else {
                avatar.textContent = (json.nom || 'U').charAt(0).toUpperCase();
            }
            $('#profileNom').val(json.nom);
            $('#profileEmail').val(json.email);
            $('#profileTelephone').val(json.telephone || '');
            $('#profilePoste').val(json.poste || '');
            $('#profileService').val(json.service || '');
            $('#profileNotifyWhatsapp').prop('checked', !!json.notify_whatsapp);
            if (json.whatsapp_api_key_set) {
                $('#profileWhatsappApiKey').attr('placeholder', 'Clé enregistrée — laissez vide pour conserver');
            }
            if (!skipWhatsapp) await updateWhatsappUI();
            const preview = document.getElementById('profilePhotoPreview');
            if (preview) preview.src = resolvePhotoUrl(json.photo_url);
            const displayName = document.getElementById('profileDisplayName');
            if (displayName) displayName.textContent = json.nom || '—';
            const displayRole = document.getElementById('profileDisplayRole');
            if (displayRole) {
                const parts = [json.poste, json.service].filter(Boolean);
                displayRole.textContent = parts.length ? parts.join(' · ') : (json.email || '—');
            }
            const badge = document.getElementById('profileDisplayBadge');
            if (badge) badge.textContent = (json.role || 'employe').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
            update2FAUI(json);
        } catch (e) { console.error(e); }
    }

    async function updateWhatsappUI() {
        const hint = document.getElementById('whatsappSetupHint');
        const keyField = document.getElementById('whatsappApiKeyField');
        const badge = document.getElementById('whatsappStatusBadge');
        try {
            const { json } = await apiFetch('/api/whatsapp/status', { headers: authHeaders() });
            if (!json.success) return;
            const provider = (json.provider || 'callmebot').toLowerCase();
            if (keyField) keyField.style.display = provider === 'callmebot' ? 'block' : 'none';
            if (hint) {
                hint.classList.remove('d-none');
                if (provider === 'twilio') {
                    hint.innerHTML = '<i class="fas fa-building me-1 text-primary"></i>Envoi via <strong>Twilio</strong> (configuré par l\'administrateur). Renseignez votre numéro au format international (+243…).';
                } else if (provider === 'meta') {
                    hint.innerHTML = '<i class="fas fa-building me-1 text-primary"></i>Envoi via <strong>WhatsApp Business (Meta)</strong>. Renseignez votre numéro (+243…).';
                } else {
                    hint.innerHTML = '<i class="fas fa-mobile-alt me-1 text-success"></i>Mode <strong>CallMeBot</strong> : chaque utilisateur active son numéro une fois (gratuit).';
                }
                if (!json.configured && json.enabled) {
                    hint.innerHTML += ' <span class="text-warning">Configuration serveur incomplète.</span>';
                }
                if (json.network_ok === false && json.network_detail) {
                    hint.innerHTML += '<br><span class="text-danger"><i class="fas fa-wifi me-1"></i>' + json.network_detail + '</span>';
                } else if (json.network_ok === true && provider === 'callmebot') {
                    hint.innerHTML += '<br><span class="text-success"><i class="fas fa-check-circle me-1"></i>Serveur connecté à CallMeBot</span>';
                }
            }
            if (badge) {
                const on = $('#profileNotifyWhatsapp').is(':checked');
                const tel = ($('#profileTelephone').val() || '').trim();
                const hasKey = $('#profileWhatsappApiKey').attr('placeholder')?.includes('enregistrée') || ($('#profileWhatsappApiKey').val() || '').trim();
                if (on && tel && (provider !== 'callmebot' || hasKey || json.configured)) {
                    badge.innerHTML = '<span class="badge bg-success"><i class="fab fa-whatsapp me-1"></i>Alertes WhatsApp prêtes</span>';
                } else if (on) {
                    badge.innerHTML = '<span class="badge bg-warning text-dark">Complétez téléphone + clé CallMeBot</span>';
                } else {
                    badge.innerHTML = '';
                }
            }
        } catch (e) { /* ignore */ }
    }

    window.testWhatsappAlert = async function () {
        if (!$('#profileNotifyWhatsapp').is(':checked')) {
            showToast('Cochez d\'abord « Recevoir les alertes via WhatsApp »', true);
            return;
        }
        if (!$('#profileTelephone').val()) {
            showToast('Renseignez votre numéro de téléphone', true);
            return;
        }
        await saveProfile();
        showToast('Envoi du message test…');
        const { ok, json } = await apiFetch('/api/user/whatsapp/test', { method: 'POST', headers: authHeaders(true) });
        if (ok && json.success) showToast(json.message || 'Message test envoyé sur WhatsApp');
        else showToast(json.message || 'Échec envoi WhatsApp', true);
    };

    function update2FAUI(profile) {
        const status = document.getElementById('twofaStatus');
        const setupPanel = document.getElementById('twofaSetupPanel');
        const disablePanel = document.getElementById('twofaDisablePanel');
        const setupBtn = document.getElementById('twofaSetupBtn');
        if (!status) return;
        const enabled = !!profile?.totp_enabled;
        if (enabled) {
            status.innerHTML = '<span class="badge bg-success"><i class="fas fa-shield-alt me-1"></i>2FA activée</span>';
            if (setupPanel) setupPanel.classList.add('d-none');
            if (disablePanel) disablePanel.classList.remove('d-none');
            if (setupBtn) setupBtn.classList.add('d-none');
        } else {
            status.innerHTML = '<span class="badge bg-warning text-dark"><i class="fas fa-unlock me-1"></i>2FA désactivée — recommandée pour sécuriser votre compte</span>';
            if (disablePanel) disablePanel.classList.add('d-none');
            if (setupPanel) setupPanel.classList.add('d-none');
            if (setupBtn) setupBtn.classList.remove('d-none');
        }
    }

    window.start2FASetup = async function () {
        const { ok, json } = await apiFetch('/api/user/2fa/setup', { method: 'POST', headers: authHeaders(true) });
        if (!ok || !json.success) { showToast(json.message || 'Erreur configuration 2FA', true); return; }
        document.getElementById('twofaSecretDisplay').textContent = json.secret || '';
        const qrImg = document.getElementById('twofaQrImg');
        if (qrImg && json.otpauth_uri) {
            qrImg.src = 'https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=' + encodeURIComponent(json.otpauth_uri);
            qrImg.classList.remove('d-none');
        }
        document.getElementById('twofaSetupPanel').classList.remove('d-none');
        document.getElementById('twofaSetupBtn').classList.add('d-none');
        showToast('Scannez le QR code avec Google Authenticator ou Microsoft Authenticator');
    };

    window.confirmEnable2FA = async function () {
        const code = ($('#twofaEnableCode').val() || '').trim();
        if (!code) { showToast('Saisissez le code à 6 chiffres', true); return; }
        const { ok, json } = await apiFetch('/api/user/2fa/enable', {
            method: 'POST', headers: authHeaders(true), body: JSON.stringify({ code }),
        });
        if (ok && json.success) {
            showToast('Double authentification activée');
            $('#twofaEnableCode').val('');
            loadUserInfo();
        } else showToast(json.message || 'Code incorrect', true);
    };

    window.disable2FA = async function () {
        const code = ($('#twofaDisableCode').val() || '').trim();
        const password = ($('#twofaDisablePassword').val() || '');
        if (!code || !password) { showToast('Mot de passe et code requis', true); return; }
        const { ok, json } = await apiFetch('/api/user/2fa/disable', {
            method: 'POST', headers: authHeaders(true), body: JSON.stringify({ code, password }),
        });
        if (ok && json.success) {
            showToast('Double authentification désactivée');
            $('#twofaDisableCode, #twofaDisablePassword').val('');
            loadUserInfo();
        } else showToast(json.message || 'Erreur', true);
    };

    window.loadDashboard = async function (silent) {
        try {
            const { json } = await apiFetch('/documents/stats', { headers: authHeaders() });
            const s = json.stats || {};
            $('#statTotal').text(s.total || 0);
            $('#statValides').text(s.valides || 0);
            $('#statRevision').text(s.en_attente || 0);
            $('#statRejetes').text(s.rejetes || 0);

            const lineData = [s.brouillons || 0, s.en_attente || 0, s.valides || 0, s.rejetes || 0, s.publies || 0];
            if (silent && evolutionChart && statusChart) {
                evolutionChart.data.datasets[0].data = lineData;
                evolutionChart.update('none');
                statusChart.data.datasets[0].data = lineData;
                statusChart.update('none');
                return;
            }

            if (evolutionChart) evolutionChart.destroy();
            evolutionChart = new Chart(document.getElementById('evolutionChart'), {
                type: 'line',
                data: {
                    labels: ['Brouillon', 'Révision', 'Validé', 'Rejeté', 'Publié'],
                    datasets: [{ label: 'Documents', data: [s.brouillons || 0, s.en_attente || 0, s.valides || 0, s.rejetes || 0, s.publies || 0], borderColor: '#0891b2', tension: 0.3, fill: true, backgroundColor: 'rgba(8,145,178,0.1)' }],
                },
                options: { responsive: true, plugins: { legend: { display: false } } },
            });
            if (statusChart) statusChart.destroy();
            statusChart = new Chart(document.getElementById('statusChart'), {
                type: 'doughnut',
                data: {
                    labels: ['Brouillon', 'En révision', 'Validé', 'Rejeté', 'Publié'],
                    datasets: [{ data: [s.brouillons || 0, s.en_attente || 0, s.valides || 0, s.rejetes || 0, s.publies || 0], backgroundColor: ['#64748b', '#f59e0b', '#10b981', '#ef4444', '#0ea5e9'] }],
                },
                options: { responsive: true },
            });
        } catch (e) { console.error(e); }
    };

    async function loadCategoriesOnce() {
        if (categoriesCache) return categoriesCache;
        const { json } = await apiFetch('/categories', { headers: authHeaders() });
        categoriesCache = json.categories || [];
        return categoriesCache;
    }

    window.loadCategories = async function (selectedId) {
        const cats = await loadCategoriesOnce();
        let opts = '<option value="">Sans catégorie</option>';
        cats.forEach(c => { opts += `<option value="${c.id}">${c.nom}</option>`; });
        $('#docCategorie').html(opts);
        if (selectedId) $('#docCategorie').val(String(selectedId));
        renderCategorySidebar(cats);
        loadCategoriesFilter(cats);
    };

    function loadCategoriesFilter(cats) {
        let opts = '<option value="">Toutes catégories</option><option value="0">Sans catégorie</option>';
        cats.forEach(c => { opts += `<option value="${c.id}">${c.nom}</option>`; });
        $('#docCategorieFilter').html(opts);
        if (currentCategoryFilter !== '') $('#docCategorieFilter').val(String(currentCategoryFilter));
    }

    function renderCategorySidebar(cats) {
        const activeAll = currentCategoryFilter === '' ? 'active' : '';
        const activeNone = currentCategoryFilter === '0' ? 'active' : '';
        let html = `
        <div class="category-item ${activeAll}">
            <a href="#" class="category-link" onclick="filterByCategory('');return false;"><i class="fas fa-folder-open"></i><span>Tous</span></a>
        </div>
        <div class="category-item ${activeNone}">
            <a href="#" class="category-link" onclick="filterByCategory('0');return false;"><i class="fas fa-folder"></i><span>Sans catégorie</span></a>
        </div>`;
        cats.forEach(c => {
            const active = String(currentCategoryFilter) === String(c.id) ? 'active' : '';
            html += `<div class="category-item ${active}">
                <a href="#" class="category-link" onclick="filterByCategory('${c.id}');return false;" title="${escapeHtml(c.nom)}">
                    <i class="fas fa-tag"></i><span class="text-truncate">${escapeHtml(c.nom)}</span>
                </a>
                <div class="category-btns">
                    <button type="button" title="Modifier" onclick="event.stopPropagation();openEditCategory(${c.id});"><i class="fas fa-pen fa-xs"></i></button>
                    <button type="button" class="btn-del" title="Supprimer" onclick="event.stopPropagation();deleteCategory(${c.id},'${escapeHtml(c.nom).replace(/'/g, "\\'")}');"><i class="fas fa-trash fa-xs"></i></button>
                </div>
            </div>`;
        });
        $('#categorySidebar').html(html);
        updateDocListSubtitle(cats);
    }

    function updateDocListSubtitle(cats) {
        const el = document.getElementById('docListSubtitle');
        if (!el) return;
        if (currentCategoryFilter === '') { el.textContent = 'Tous les documents'; return; }
        if (currentCategoryFilter === '0') { el.textContent = 'Documents sans catégorie'; return; }
        const cat = (cats || []).find(c => String(c.id) === String(currentCategoryFilter));
        el.textContent = cat ? `Catégorie : ${cat.nom}` : 'Documents filtrés';
    }

    window.createCategoryFromSidebar = async function () {
        const nom = ($('#sidebarNewCategorie').val() || '').trim();
        if (!nom) { showToast('Nom requis', true); return; }
        $('#newCategorieNom').val(nom);
        await createCategory();
        $('#sidebarNewCategorie').val('');
    };

    window.openEditCategory = async function (catId) {
        const cats = await loadCategoriesOnce();
        const cat = cats.find(c => c.id === catId);
        if (!cat) return;
        $('#editCategoryId').val(cat.id);
        $('#editCategoryNom').val(cat.nom);
        $('#editCategoryDesc').val(cat.description || '');
        new bootstrap.Modal(document.getElementById('editCategoryModal')).show();
    };

    window.saveCategoryEdit = async function () {
        const id = $('#editCategoryId').val();
        const nom = ($('#editCategoryNom').val() || '').trim();
        const description = ($('#editCategoryDesc').val() || '').trim();
        if (!nom) { showToast('Nom requis', true); return; }
        const { ok, json } = await apiFetch(`/categories/${id}`, {
            method: 'PUT',
            headers: authHeaders(true),
            body: JSON.stringify({ nom, description }),
        });
        if (ok) {
            showToast('Catégorie modifiée');
            categoriesCache = null;
            bootstrap.Modal.getInstance(document.getElementById('editCategoryModal'))?.hide();
            await loadCategories();
            loadCategoriesSearch();
            refreshVisibleTab();
        } else showToast(json.message || 'Erreur', true);
    };

    window.deleteCategory = async function (catId, catNom) {
        if (!confirm(`Supprimer la catégorie « ${catNom} » ?\n(Les documents ne seront pas supprimés)`)) return;
        const { ok, json } = await apiFetch(`/categories/${catId}`, { method: 'DELETE', headers: authHeaders() });
        if (ok) {
            showToast('Catégorie supprimée');
            categoriesCache = null;
            if (String(currentCategoryFilter) === String(catId)) currentCategoryFilter = '';
            await loadCategories();
            loadCategoriesSearch();
            refreshVisibleTab();
        } else showToast(json.message || 'Impossible de supprimer (documents associés ?)', true);
    };

    window.filterByCategory = function (catId) {
        currentCategoryFilter = catId === undefined || catId === null ? '' : String(catId);
        $('#docCategorieFilter').val(currentCategoryFilter);
        docPage = 1;
        loadCategoriesOnce().then(cats => renderCategorySidebar(cats));
        loadDocuments();
    };

    // ========== ÉPINGLES & PRESSE-PAPIER ==========
    function getEpinglesIds() {
        try { return JSON.parse(localStorage.getItem('ged_epingles') || '[]'); } catch (e) { return []; }
    }

    window.toggleEpingle = function (docId) {
        let pins = getEpinglesIds().map(String);
        const key = String(docId);
        pins = pins.includes(key) ? pins.filter(x => x !== key) : [key, ...pins];
        localStorage.setItem('ged_epingles', JSON.stringify(pins));
        showToast(pins.includes(key) ? 'Document épinglé en tête de liste' : 'Épingle retirée');
        loadDocuments(true);
    };

    function sortDocsWithPins(docs) {
        const pins = getEpinglesIds().map(String);
        return [...docs].sort((a, b) => {
            const ap = pins.indexOf(String(a.id));
            const bp = pins.indexOf(String(b.id));
            if (ap >= 0 && bp >= 0) return ap - bp;
            if (ap >= 0) return -1;
            if (bp >= 0) return 1;
            return 0;
        });
    }

    function getClipboard() {
        try { return JSON.parse(localStorage.getItem('ged_clipboard') || 'null'); } catch (e) { return null; }
    }

    function setClipboard(data) {
        localStorage.setItem('ged_clipboard', JSON.stringify(data));
        updateClipboardUI();
    }

    function updateClipboardUI() {
        const cb = getClipboard();
        const btn = document.getElementById('pasteBtn');
        const hint = document.getElementById('clipboardHint');
        if (btn) btn.disabled = !cb;
        if (hint) {
            hint.textContent = cb
                ? `${cb.mode === 'cut' ? 'Couper' : 'Copie'} : « ${cb.titre || 'Document' } » — sélectionnez une catégorie puis Coller`
                : 'Copiez ou coupez un document pour le coller dans une catégorie';
        }
    }

    window.copyDocumentRef = function (docId) {
        const doc = documentsCache[docId];
        setClipboard({ mode: 'copy', id: docId, titre: doc?.titre || 'Document' });
        showToast('Document copié — choisissez une catégorie et cliquez Coller');
    };

    window.cutDocumentRef = function (docId) {
        const doc = documentsCache[docId];
        setClipboard({ mode: 'cut', id: docId, titre: doc?.titre || 'Document' });
        showToast('Document coupé — choisissez une catégorie et cliquez Coller');
    };

    window.pasteDocument = async function () {
        const cb = getClipboard();
        if (!cb) return;
        const catId = currentCategoryFilter || $('#docCategorieFilter').val() || '';
        const targetCat = catId === '' ? null : catId;

        if (cb.mode === 'copy') {
            const { ok, json } = await apiFetch(`/documents/${cb.id}/copier`, {
                method: 'POST',
                headers: authHeaders(true),
                body: JSON.stringify({ categorie_id: targetCat }),
            });
            if (ok && json.success) {
                showToast('Document collé (copie créée)');
                localStorage.removeItem('ged_clipboard');
                updateClipboardUI();
                refreshVisibleTab();
            } else showToast(json.message || 'Erreur copie', true);
        } else if (cb.mode === 'cut') {
            const { ok, json } = await apiFetch(`/documents/${cb.id}/categorie`, {
                method: 'PUT',
                headers: authHeaders(true),
                body: JSON.stringify({ categorie_id: targetCat || null }),
            });
            if (ok && (json.success || json.message)) {
                showToast('Document déplacé');
                localStorage.removeItem('ged_clipboard');
                updateClipboardUI();
                refreshVisibleTab();
            } else showToast(json.error || json.message || 'Erreur déplacement', true);
        }
    };

    window.deplacerDocument = async function (docId) {
        const cats = await loadCategoriesOnce();
        let opts = '<option value="0">Sans catégorie</option>';
        cats.forEach(c => { opts += `<option value="${c.id}">${c.nom}</option>`; });
        $('#selectCategorieDeplacement').html(opts);
        $('#deplacerModal').data('docId', docId);
        new bootstrap.Modal(document.getElementById('deplacerModal')).show();
    };

    window.confirmerDeplacement = async function () {
        const docId = $('#deplacerModal').data('docId');
        const categorieId = $('#selectCategorieDeplacement').val();
        const { ok, json } = await apiFetch(`/documents/${docId}/categorie`, {
            method: 'PUT',
            headers: authHeaders(true),
            body: JSON.stringify({ categorie_id: categorieId === '0' ? null : categorieId }),
        });
        if (ok && (json.success || !json.error)) {
            showToast('Document déplacé');
            bootstrap.Modal.getInstance(document.getElementById('deplacerModal'))?.hide();
            refreshVisibleTab();
        } else showToast(json.error || json.message || 'Erreur', true);
    };

    window.copierTexteDocument = async function (docId) {
        try {
            const { blob, filename } = await fetchDocumentBlob(docId);
            const ext = (filename || '').split('.').pop().toLowerCase();
            if (['txt', 'md', 'csv', 'json', 'xml', 'html', 'htm', 'css', 'js', 'py', 'sql', 'log'].includes(ext)) {
                const text = await blob.text();
                await navigator.clipboard.writeText(text.substring(0, 100000));
                showToast('Contenu copié dans le presse-papier');
            } else if (documentsCache[docId]?.contenu_ocr) {
                await navigator.clipboard.writeText(documentsCache[docId].contenu_ocr);
                showToast('Texte OCR copié');
            } else {
                showToast('Copie texte disponible pour fichiers texte ou après OCR', true);
            }
        } catch (e) {
            showToast('Erreur de copie', true);
        }
    };

    window.createCategory = async function () {
        const nom = ($('#newCategorieNom').val() || '').trim();
        if (!nom) { showToast('Nom de catégorie requis', true); return; }
        const { ok, json, offline } = await apiFetch('/categories', {
            method: 'POST',
            headers: authHeaders(true),
            body: JSON.stringify({ nom, description: '' }),
            offlineAction: 'CREATE_CATEGORY',
            offlineData: { nom, description: '' },
        });
        if ((ok && json.category_id) || offline) {
            showToast(offline ? 'Catégorie en attente de sync' : 'Catégorie créée : ' + nom);
            $('#newCategorieNom').val('');
            $('#sidebarNewCategorie').val('');
            if (!offline) {
                categoriesCache = null;
                await loadCategories(json.category_id);
                await loadCategoriesSearch();
            }
        } else {
            showToast(json.message || 'Erreur création catégorie', true);
        }
    };

    window.loadCategoriesSearch = async function () {
        const cats = await loadCategoriesOnce();
        let opts = '<option value="">Toutes catégories</option>';
        cats.forEach(c => { opts += `<option value="${c.id}">${c.nom}</option>`; });
        $('#searchCategorie').html(opts);
    };

    function renderDocActions(doc) {
        return `<div class="doc-actions-cell">
            <button type="button" class="btn btn-action-icon" onclick="viewDocument(${doc.id})" title="Voir"><i class="fas fa-eye text-primary"></i></button>
            <button type="button" class="btn btn-action-icon" onclick="downloadDocument(${doc.id})" title="Télécharger"><i class="fas fa-download text-success"></i></button>
            <button type="button" class="btn btn-action-icon btn-action-more" onclick="openDocActionsModal(${doc.id})" title="Plus d'actions"><i class="fas fa-ellipsis-h"></i></button>
        </div>`;
    }

    window.openDocActionsModal = function (docId) {
        const doc = documentsCache[docId];
        if (!doc) return;
        const pinned = getEpinglesIds().includes(String(docId));
        document.getElementById('docActionsTitle').textContent = doc.titre || 'Document';
        let tiles = `
            <button type="button" class="action-tile" onclick="bootstrap.Modal.getInstance(document.getElementById('docActionsModal')).hide();viewDocument(${docId})"><i class="fas fa-eye text-primary"></i>Voir</button>
            <button type="button" class="action-tile" onclick="bootstrap.Modal.getInstance(document.getElementById('docActionsModal')).hide();downloadDocument(${docId})"><i class="fas fa-download text-success"></i>Télécharger</button>
            <button type="button" class="action-tile" onclick="bootstrap.Modal.getInstance(document.getElementById('docActionsModal')).hide();printDocument(${docId})"><i class="fas fa-print text-secondary"></i>Imprimer</button>
            <button type="button" class="action-tile" onclick="bootstrap.Modal.getInstance(document.getElementById('docActionsModal')).hide();deplacerDocument(${docId})"><i class="fas fa-folder text-warning"></i>Déplacer</button>
            <button type="button" class="action-tile" onclick="bootstrap.Modal.getInstance(document.getElementById('docActionsModal')).hide();copyDocumentRef(${docId})"><i class="fas fa-copy text-info"></i>Copier</button>
            <button type="button" class="action-tile" onclick="bootstrap.Modal.getInstance(document.getElementById('docActionsModal')).hide();cutDocumentRef(${docId})"><i class="fas fa-cut text-secondary"></i>Couper</button>
            <button type="button" class="action-tile" onclick="bootstrap.Modal.getInstance(document.getElementById('docActionsModal')).hide();copierTexteDocument(${docId})"><i class="fas fa-clipboard text-muted"></i>Copier texte</button>
            <button type="button" class="action-tile" onclick="bootstrap.Modal.getInstance(document.getElementById('docActionsModal')).hide();toggleEpingle(${docId})"><i class="fas fa-thumbtack ${pinned ? 'text-warning' : 'text-muted'}"></i>${pinned ? 'Désépingler' : 'Épingler'}</button>
            <button type="button" class="action-tile" onclick="bootstrap.Modal.getInstance(document.getElementById('docActionsModal')).hide();shareWhatsAppDoc(${docId})"><i class="fab fa-whatsapp text-success"></i>WhatsApp</button>
            <button type="button" class="action-tile" onclick="bootstrap.Modal.getInstance(document.getElementById('docActionsModal')).hide();shareDocument(${docId})"><i class="fas fa-share-alt text-primary"></i>Partager</button>
            <button type="button" class="action-tile" onclick="bootstrap.Modal.getInstance(document.getElementById('docActionsModal')).hide();viewHistoryDoc(${docId})"><i class="fas fa-history text-secondary"></i>Versions</button>
            <button type="button" class="action-tile" onclick="bootstrap.Modal.getInstance(document.getElementById('docActionsModal')).hide();toggleFavori(${docId})"><i class="fas fa-star text-warning"></i>Favori</button>`;
        if (doc.statut === 'brouillon') {
            tiles += `<button type="button" class="action-tile" onclick="bootstrap.Modal.getInstance(document.getElementById('docActionsModal')).hide();submitDocument(${docId})"><i class="fas fa-paper-plane text-warning"></i>Soumettre</button>`;
        }
        if (doc.statut === 'rejete') {
            tiles += `<button type="button" class="action-tile" onclick="bootstrap.Modal.getInstance(document.getElementById('docActionsModal')).hide();reprendreBrouillon(${docId})"><i class="fas fa-edit text-info"></i>Reprendre</button>`;
        }
        document.getElementById('docActionsBody').innerHTML = `<div class="actions-modal-grid">${tiles}</div>`;
        new bootstrap.Modal(document.getElementById('docActionsModal')).show();
    };

    window.loadDocuments = async function (silent) {
        if (isLoadingDocs) return;
        isLoadingDocs = true;
        const search = $('#docSearch').val();
        const statut = $('#docStatutFilter').val();
        const catFilter = $('#docCategorieFilter').val();
        if (catFilter !== undefined && catFilter !== null && catFilter !== '') currentCategoryFilter = String(catFilter);
        let url = `/documents?page=${docPage}&limit=15`;
        if (search) url += `&search=${encodeURIComponent(search)}`;
        if (statut) url += `&statut=${statut}`;
        if (currentCategoryFilter !== '') url += `&categorie_id=${encodeURIComponent(currentCategoryFilter)}`;

        if (!silent) {
            $('#documentsList').html('<tr><td colspan="6" class="loading"><div class="spinner-border spinner-border-sm text-primary"></div> Chargement...</td></tr>');
        }

        try {
            const { json, fromCache } = await apiFetch(url, { headers: authHeaders() });
            let docs = json.documents || [];
            docs = sortDocsWithPins(docs);
            docTotalPages = json.total_pages || 1;
            docs.forEach(d => { documentsCache[d.id] = d; });

            if (docs.length === 0) {
                const msg = fromCache ? 'Aucun document en cache' : 'Aucun document';
                $('#documentsList').html(`<tr><td colspan="6" class="text-center py-4 text-muted">${msg}</td></tr>`);
            } else {
                let html = '';
                const pins = getEpinglesIds().map(String);
                docs.forEach(doc => {
                    const pinCls = pins.includes(String(doc.id)) ? 'doc-pinned' : '';
                    const pinIcon = pins.includes(String(doc.id)) ? '<i class="fas fa-thumbtack pin-icon" title="Épinglé"></i>' : '';
                    html += `<tr class="${pinCls}">
                        <td class="fw-semibold text-truncate" style="max-width:200px;">${pinIcon}${escapeHtml(doc.titre || '-')}</td>
                        <td class="d-none d-md-table-cell">${escapeHtml(doc.categorie_nom || 'Sans')}</td>
                        <td class="d-none d-lg-table-cell">V${doc.version_actuelle || 1}</td>
                        <td class="d-none d-sm-table-cell text-muted small">${formatDate(doc.date_creation)}</td>
                        <td>${getBadge(doc.statut)}</td>
                        <td class="col-actions">${renderDocActions(doc)}</td>
                    </tr>`;
                });
                $('#documentsList').html(html);
            }
            if (fromCache && !silent) showToast('Documents affichés depuis le cache hors-ligne');
            renderDocPagination();
        } catch (e) {
            if (!silent) $('#documentsList').html('<tr><td colspan="6" class="text-danger text-center">Erreur de chargement</td></tr>');
        } finally {
            isLoadingDocs = false;
        }
    };

    function renderDocPagination() {
        if (docTotalPages <= 1) { $('#documentsPagination').empty(); return; }
        let html = '<nav><ul class="pagination pagination-sm justify-content-center">';
        for (let i = 1; i <= docTotalPages; i++) {
            html += `<li class="page-item ${i === docPage ? 'active' : ''}"><a class="page-link" href="#" data-page="${i}">${i}</a></li>`;
        }
        html += '</ul></nav>';
        $('#documentsPagination').html(html);
    }

    window.resetDocFilters = function () {
        $('#docSearch').val('');
        $('#docStatutFilter').val('');
        $('#docCategorieFilter').val('');
        currentCategoryFilter = '';
        docPage = 1;
        loadCategoriesOnce().then(cats => renderCategorySidebar(cats));
        loadDocuments();
    };

    window.openUpload = function () {
        $('.sidebar a[data-tab="upload"]').click();
    };

    // ========== ACTIONS ==========
    window.submitDocument = async function (id) {
        if (!confirm('Soumettre ce document pour validation ?')) return;
        const { ok, offline, json } = await apiFetch(`/documents/${id}/soumettre`, {
            method: 'PUT', headers: authHeaders(),
            offlineAction: 'SOUMISSION', offlineData: { doc_id: id },
        });
        if (ok || offline) {
            showToast(json.message || 'Document soumis');
            refreshVisibleTab();
        } else showToast(json.message || 'Erreur', true);
    };

    window.reprendreBrouillon = async function (id) {
        if (!confirm('Repasser en brouillon pour modification ?')) return;
        const { ok, offline, json } = await apiFetch(`/documents/${id}/reprendre-brouillon`, {
            method: 'PUT',
            headers: authHeaders(),
            offlineAction: 'REPRENDRE_BROUILLON',
            offlineData: { doc_id: id },
        });
        if ((ok && json.success) || offline) {
            showToast(offline ? 'Action en attente de sync' : 'Document en brouillon');
            refreshVisibleTab();
        } else showToast(json.message || 'Erreur', true);
    };

    window.submitDocumentUpload = async function () {
        const file = $('#docFile')[0].files[0];
        const titre = $('#docTitre').val();
        if (!file || !titre) { showToast('Fichier et titre requis', true); return; }
        const btn = document.getElementById('uploadBtn');
        if (btn) btn.disabled = true;
        try {
            if (!navigator.onLine) {
                await queueWriteAction('POST', {
                    offlineAction: 'UPLOAD',
                    offlineFile: file,
                    offlineData: {
                        titre,
                        description: $('#docDesc').val(),
                        categorie_id: $('#docCategorie').val(),
                        fichier: file.name,
                    },
                });
                $('#docFile').val('');
                $('#docTitre').val('');
                $('#docDesc').val('');
                $('#uploadFileName').text('');
                return;
            }
            const formData = new FormData();
            formData.append('file', file);
            formData.append('titre', titre);
            formData.append('description', $('#docDesc').val());
            formData.append('categorie_id', $('#docCategorie').val());
            const res = await fetch(API + '/documents/upload', { method: 'POST', headers: { Authorization: 'Bearer ' + token }, body: formData });
            const data = await res.json();
            if (data.success) {
                showToast('Document uploadé');
                $('#docFile').val('');
                $('#docTitre').val('');
                $('#docDesc').val('');
                $('#uploadFileName').text('');
                refreshVisibleTab();
            } else showToast(data.message || 'Erreur', true);
        } catch (e) {
            try {
                await queueWriteAction('POST', {
                    offlineAction: 'UPLOAD',
                    offlineFile: file,
                    offlineData: {
                        titre,
                        description: $('#docDesc').val(),
                        categorie_id: $('#docCategorie').val(),
                        fichier: file.name,
                    },
                });
                $('#docFile').val('');
                $('#docTitre').val('');
                $('#docDesc').val('');
                $('#uploadFileName').text('');
            } catch (err) {
                showToast('Erreur upload', true);
            }
        } finally {
            if (btn) btn.disabled = false;
        }
    };

    window.restaurerVersion = async function (docId, versionId) {
        if (!confirm('Restaurer cette version ?')) return;
        const { ok, json } = await apiFetch(`/documents/${docId}/versions/${versionId}/restaurer`, { method: 'PUT', headers: authHeaders() });
        if (ok && json.success) {
            showToast('Version restaurée');
            bootstrap.Modal.getInstance(document.getElementById('historyModal'))?.hide();
            refreshVisibleTab();
        } else showToast(json.message || 'Erreur', true);
    };

    window.viewHistoryDoc = window.viewHistory = function (id) {
        const docId = id || currentDocId;
        $('#historyBody').html('<div class="text-center py-4"><div class="spinner-border spinner-border-sm"></div></div>');
        new bootstrap.Modal(document.getElementById('historyModal')).show();
        apiFetch(`/documents/${docId}/versions`, { headers: authHeaders() }).then(({ json }) => {
            const versions = json.versions || [];
            if (!versions.length) {
                $('#historyBody').html('<div class="text-center py-4 text-muted">Aucune version</div>');
                return;
            }
            let html = '<ul class="list-group list-group-flush">';
            versions.forEach(v => {
                html += `<li class="list-group-item d-flex justify-content-between align-items-center px-0">
                    <div><strong>V${v.version_numero}</strong> <span class="text-muted small">${v.commentaire || ''}</span><br><small class="text-muted">${formatDate(v.date_creation)}</small></div>
                    <button class="btn btn-sm btn-outline-primary" onclick="restaurerVersion(${docId},${v.id})"><i class="fas fa-undo me-1"></i>Restaurer</button>
                </li>`;
            });
            html += '</ul>';
            $('#historyBody').html(html);
        });
    };

    window.runOCR = function () {
        if (!currentDocId) return;
        $('#ocrResult').html('<div class="text-center py-3"><div class="spinner-border spinner-border-sm text-primary"></div></div>');
        new bootstrap.Modal(document.getElementById('ocrModal')).show();
        apiFetch(`/documents/${currentDocId}/ocr`, { method: 'POST', headers: authHeaders() }).then(({ ok, json }) => {
            if (ok && json.success) $('#ocrResult').text(json.texte || 'Aucun texte détecté');
            else $('#ocrResult').html(`<div class="alert alert-warning mb-0">${json.message || 'Erreur OCR'}</div>`);
        });
    };

    window.searchOCR = function () {
        const q = $('#ocrSearch').val().toLowerCase();
        const text = $('#ocrResult').text().toLowerCase();
        if (q && text.includes(q)) showToast('Terme trouvé dans le texte');
        else if (q) showToast('Terme non trouvé', true);
    };

    window.showQRCode = function () {
        if (!currentDocId) return;
        const shareUrl = `${window.location.origin}/dashboard-employee?doc=${currentDocId}`;
        $('#qrCodeImage').attr('src', `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(shareUrl)}`);
        $('#qrShareUrl').text(shareUrl);
        new bootstrap.Modal(document.getElementById('qrModal')).show();
    };

    // ========== FAVORIS / RECHERCHE / HISTORIQUE / NOTIFS / PROFIL ==========
    function getFavorisIds() {
        try { return JSON.parse(localStorage.getItem('ged_favoris') || '[]'); } catch (e) { return []; }
    }

    window.toggleFavori = function (docId) {
        let favs = getFavorisIds();
        const key = String(docId);
        favs = favs.includes(key) ? favs.filter(x => x !== key) : [...favs, key];
        localStorage.setItem('ged_favoris', JSON.stringify(favs));
        showToast(favs.includes(key) ? 'Ajouté aux favoris' : 'Retiré des favoris');
        if ($('#tabFavoris').is(':visible')) loadFavoris();
    };

    window.loadFavoris = async function () {
        const ids = getFavorisIds();
        if (!ids.length) {
            $('#favorisList').html('<tr><td colspan="4" class="text-center py-4 text-muted">Aucun favori</td></tr>');
            return;
        }
        const { json } = await apiFetch('/documents?limit=200', { headers: authHeaders() });
        const docs = (json.documents || []).filter(d => ids.includes(String(d.id)));
        let html = '';
        docs.forEach(doc => {
            html += `<tr><td>${escapeHtml(doc.titre)}</td><td>${escapeHtml(doc.categorie_nom || '-')}</td><td>${getBadge(doc.statut)}</td>
                <td class="col-actions">${renderDocActions(doc)}</td></tr>`;
        });
        $('#favorisList').html(html || '<tr><td colspan="4" class="text-center text-muted">Aucun favori</td></tr>');
    };

    window.advancedSearch = async function () {
        let url = '/documents?limit=50';
        const t = $('#searchTitre').val();
        const st = $('#searchStatut').val();
        const ocr = $('#searchOCR').val();
        if (t) url += `&search=${encodeURIComponent(t)}`;
        if (st) url += `&statut=${st}`;
        if (ocr) url += `&ocr=${encodeURIComponent(ocr)}`;
        const { json } = await apiFetch(url, { headers: authHeaders() });
        const docs = json.documents || [];
        let html = '';
        docs.forEach(doc => {
            documentsCache[doc.id] = doc;
            html += `<tr><td>${escapeHtml(doc.titre)}</td><td>${escapeHtml(doc.categorie_nom || '-')}</td><td>${formatDate(doc.date_creation)}</td><td>${getBadge(doc.statut)}</td>
                <td class="col-actions">${renderDocActions(doc)}</td></tr>`;
        });
        $('#searchResults').html(html || '<tr><td colspan="5" class="text-center text-muted">Aucun résultat</td></tr>');
    };

    window.resetAdvancedSearch = function () {
        $('#searchTitre,#searchOCR').val('');
        $('#searchCategorie,#searchStatut').val('');
        $('#searchResults').html('<tr><td colspan="5" class="text-center text-muted py-4">Utilisez les filtres</td></tr>');
    };

    window.loadHistorique = async function () {
        const { json } = await apiFetch('/documents/historique', { headers: authHeaders() });
        const logs = json.logs || [];
        let html = '';
        logs.slice(0, 50).forEach(log => {
            html += `<tr><td>${log.document_titre || '-'}</td><td><span class="badge bg-light text-dark">${log.action}</span></td><td>${formatDate(log.date_action)}</td></tr>`;
        });
        $('#historiqueList').html(html || '<tr><td colspan="3" class="text-center text-muted">Aucun historique</td></tr>');
    };

    function notifIcon(type) {
        const m = {
            DOCUMENT_VALIDE: 'fa-check-circle text-success',
            DOCUMENT_REJETE: 'fa-times-circle text-danger',
            DOCUMENT_PUBLIE: 'fa-globe text-primary',
            DOCUMENT_SOUMIS: 'fa-paper-plane text-info',
        };
        return m[type] || 'fa-bell text-secondary';
    }

    window.loadNotifications = async function () {
        const { json } = await apiFetch('/notifications/all', { headers: authHeaders() });
        const notifs = json.notifications || [];
        const nonLues = notifs.filter(n => !n.lue).length;
        $('#notifBadge,#notifSidebarBadge').text(nonLues);
        $('#notifBadge').toggle(nonLues > 0);

        let listHtml = '';
        if (!notifs.length) {
            listHtml = '<div class="text-center py-5 text-muted"><i class="fas fa-bell-slash fa-2x mb-2 d-block"></i>Aucune notification</div>';
        } else {
            notifs.forEach(n => {
                const wa = n.message && n.message.includes('validé') ? `<button class="btn btn-sm btn-outline-success ms-2" onclick="event.stopPropagation();openNotifWhatsapp('${encodeURIComponent(n.message)}')"><i class="fab fa-whatsapp"></i></button>` : '';
                listHtml += `<div class="list-group-item list-group-item-action ${n.lue ? '' : 'list-group-item-primary'}" onclick="markNotifRead(${n.id})">
                    <div class="d-flex w-100 justify-content-between align-items-start">
                        <div><i class="fas ${notifIcon(n.type_notif || n.type)} me-2"></i>${n.message}${wa}</div>
                        <small class="text-muted">${formatDate(n.date_creation || n.created_at)}</small>
                    </div>
                </div>`;
            });
        }
        $('#notificationsList').html(`<div class="list-group list-group-flush border rounded shadow-sm">${listHtml}</div>`);
        const dropItems = notifs.slice(0, 8).map(n =>
            `<div class="notif-item ${n.lue ? '' : 'fw-semibold'}" onclick="markNotifRead(${n.id})"><i class="fas ${notifIcon(n.type_notif || n.type)} me-2"></i>${(n.message || '').substring(0, 80)}${(n.message || '').length > 80 ? '…' : ''}</div>`
        ).join('');
        $('#notifDropdown').html(
            `<div class="notif-dropdown-header"><span><i class="fas fa-bell me-2"></i>Notifications</span><a href="#" class="small text-primary" onclick="event.stopPropagation();$('.sidebar a[data-tab=notifications]').click();return false;">Tout voir</a></div>`
            + (dropItems || '<div class="p-3 text-muted small">Aucune notification</div>')
        );
    };

    window.openNotifWhatsapp = function (msgEnc) {
        window.open(`https://wa.me/?text=${msgEnc}`, '_blank');
    };

    window.markNotifRead = function (id) {
        apiFetch(`/notifications/${id}/lire`, { method: 'PUT', headers: authHeaders() }).then(() => loadNotifications());
    };

    window.markAllNotifsRead = function () {
        apiFetch('/notifications/lire-tout', { method: 'PUT', headers: authHeaders() }).then(() => loadNotifications());
    };

    window.loadProfile = async function () {
        await loadUserInfo(true);
        await updateWhatsappUI();
    };

    window.saveProfile = async function () {
        const data = {
            telephone: $('#profileTelephone').val(),
            poste: $('#profilePoste').val(),
            service: $('#profileService').val(),
            notify_whatsapp: $('#profileNotifyWhatsapp').is(':checked'),
        };
        const waKey = ($('#profileWhatsappApiKey').val() || '').trim();
        if (waKey) data.whatsapp_api_key = waKey;
        const { ok } = await apiFetch('/api/user/profile', { method: 'PUT', headers: authHeaders(true), body: JSON.stringify(data) });
        if (ok) {
            showToast('Profil enregistré');
            $('#profileWhatsappApiKey').val('');
            loadUserInfo();
        }
        else showToast('Erreur enregistrement', true);
    };

    window.openPasswordModal = function () {
        $('#profilePasswordNew, #profilePasswordConfirm').val('');
        new bootstrap.Modal(document.getElementById('passwordModal')).show();
    };

    window.savePassword = async function () {
        const pwd = $('#profilePasswordNew').val();
        const confirm = $('#profilePasswordConfirm').val();
        if (pwd.length < 6) { showToast('Minimum 6 caractères', true); return; }
        if (pwd !== confirm) { showToast('Les mots de passe ne correspondent pas', true); return; }
        const { ok } = await apiFetch('/api/user/profile', {
            method: 'PUT',
            headers: authHeaders(true),
            body: JSON.stringify({ password: pwd }),
        });
        if (ok) {
            showToast('Mot de passe mis à jour');
            bootstrap.Modal.getInstance(document.getElementById('passwordModal'))?.hide();
            $('#profilePasswordNew, #profilePasswordConfirm').val('');
        } else showToast('Erreur mot de passe', true);
    };

    window.uploadProfilePhoto = function () {
        const file = document.getElementById('profilePhotoInput').files[0];
        if (!file) return;
        const fd = new FormData();
        fd.append('photo', file);
        fetch(API + '/api/user/photo', { method: 'POST', headers: { Authorization: 'Bearer ' + token }, body: fd })
            .then(r => r.json())
            .then(d => { if (d.success) { showToast('Photo mise à jour'); loadUserInfo(); } else showToast('Erreur photo', true); });
    };

    function refreshVisibleTab() {
        if ($('#tabDashboard').is(':visible')) loadDashboard(true);
        else if ($('#tabDocuments').is(':visible')) loadDocuments(true);
        else if ($('#tabNotifications').is(':visible')) loadNotifications();
        else if ($('#tabFavoris').is(':visible')) loadFavoris();
        else if ($('#tabHistorique').is(':visible')) loadHistorique();
        loadNotifications();
    }

    // ========== NAV ==========
    $('#tabDashboard').show();
    $('.sidebar a').click(function (e) {
        e.preventDefault();
        $('.sidebar a').removeClass('active');
        $(this).addClass('active');
        const tab = $(this).data('tab');
        $('.tab-pane').hide();
        const map = {
            dashboard: () => { $('#tabDashboard').show(); loadDashboard(); },
            documents: () => { $('#tabDocuments').show(); loadCategories(); loadDocuments(); updateClipboardUI(); },
            upload: () => { $('#tabUpload').show(); loadCategories(); },
            recherche: () => { $('#tabRecherche').show(); loadCategoriesSearch(); },
            historique: () => { $('#tabHistorique').show(); loadHistorique(); },
            favoris: () => { $('#tabFavoris').show(); loadFavoris(); },
            notifications: () => { $('#tabNotifications').show(); loadNotifications(); },
            profil: () => { $('#tabProfil').show(); loadProfile(); },
        };
        if (map[tab]) map[tab]();
        if (window.innerWidth <= 992) $('#sidebar').removeClass('open');
    });

    $('#menuToggle').click(() => $('#sidebar').toggleClass('open'));
    $('#notifIcon').click(e => { e.stopPropagation(); $('#notifDropdown').toggle(); });
    $(document).click(() => $('#notifDropdown').hide());
    $(document).on('click', '#documentsPagination .page-link', function (e) {
        e.preventDefault();
        docPage = parseInt($(this).data('page'), 10);
        loadDocuments(true);
    });

    let docSearchTimer;
    $('#docSearch').on('input', function () {
        clearTimeout(docSearchTimer);
        docSearchTimer = setTimeout(() => { docPage = 1; loadDocuments(true); }, 450);
    });
    $('#docStatutFilter').on('change', function () { docPage = 1; loadDocuments(true); });
    $('#docCategorieFilter').on('change', function () {
        currentCategoryFilter = $(this).val();
        docPage = 1;
        loadCategoriesOnce().then(cats => renderCategorySidebar(cats));
        loadDocuments(true);
    });

    updateClipboardUI();

    // ========== INIT ==========
    async function warmOfflineCache() {
        const urls = [
            '/documents/stats',
            '/documents?page=1&limit=15',
            '/categories',
        ];
        await Promise.allSettled(urls.map((u) => apiFetch(u, { headers: authHeaders() })));
    }

    Promise.all([
        loadUserInfo(true),
        loadDashboard(),
        loadNotifications(),
    ]).catch(() => {});

    const deferCache = () => warmOfflineCache().catch(() => {});
    if (typeof requestIdleCallback === 'function') {
        requestIdleCallback(deferCache, { timeout: 4000 });
    } else {
        setTimeout(deferCache, 2000);
    }

    (function initUploadDropzone() {
        const dropzone = document.getElementById('uploadDropzone');
        const fileInput = document.getElementById('docFile');
        const fileNameEl = document.getElementById('uploadFileName');
        if (!dropzone || !fileInput) return;

        function showFileName(file) {
            if (fileNameEl) fileNameEl.textContent = file ? file.name : '';
        }

        fileInput.addEventListener('change', () => {
            showFileName(fileInput.files[0] || null);
        });

        ['dragenter', 'dragover'].forEach(evt => {
            dropzone.addEventListener(evt, (e) => {
                e.preventDefault();
                dropzone.classList.add('dragover');
            });
        });
        ['dragleave', 'drop'].forEach(evt => {
            dropzone.addEventListener(evt, (e) => {
                e.preventDefault();
                dropzone.classList.remove('dragover');
            });
        });
        dropzone.addEventListener('drop', (e) => {
            const files = e.dataTransfer && e.dataTransfer.files;
            if (files && files.length) {
                try {
                    const dt = new DataTransfer();
                    dt.items.add(files[0]);
                    fileInput.files = dt.files;
                } catch (err) {
                    /* fallback si DataTransfer indisponible */
                }
                showFileName(files[0]);
            }
        });
    })();

    const docParam = new URLSearchParams(window.location.search).get('doc');
    if (docParam) setTimeout(() => viewDocument(parseInt(docParam, 10)), 400);

    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js?v=4').then((reg) => {
            reg.update();
            if (reg.waiting) reg.waiting.postMessage({ type: 'SKIP_WAITING' });
        }).catch(() => {});
    }

    setInterval(loadNotifications, 60000);
})();
