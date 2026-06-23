// File d'attente hors-ligne GED-PME
class OfflineQueue {
    constructor() {
        this.dbReady = new Promise((resolve, reject) => {
            const request = indexedDB.open('GED-PME-Offline', 2);
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                if (!db.objectStoreNames.contains('actions')) {
                    db.createObjectStore('actions', { keyPath: 'id', autoIncrement: true });
                }
            };
            request.onsuccess = (event) => {
                this.db = event.target.result;
                resolve(this.db);
            };
            request.onerror = (event) => reject(event.target.error);
        });
    }

    _txDone(tx) {
        return new Promise((resolve, reject) => {
            tx.oncomplete = () => resolve();
            tx.onerror = () => reject(tx.error);
            tx.onabort = () => reject(tx.error);
        });
    }

    async _store(mode = 'readwrite') {
        await this.dbReady;
        return this.db.transaction(['actions'], mode).objectStore('actions');
    }

    async detectConflict(action, response, result) {
        if (response.status === 409) return true;
        const msg = String(result.message || result.error || '').toLowerCase();
        if (msg.includes('conflit')) return true;
        if (result.version && action.data.version && result.version > action.data.version) return true;
        return false;
    }

    _extractError(result, response) {
        return result.message || result.error || `Erreur HTTP ${response.status}`;
    }

    _isAlreadyDone(action, result) {
        const msg = String(result.message || result.error || '').toLowerCase();
        if (action.action === 'SOUMISSION' && msg.includes("statut 'soumis'")) return true;
        if (action.action === 'REPRENDRE_BROUILLON' && msg.includes("statut 'brouillon'")) return true;
        if (action.action === 'CREATE_CATEGORY' && msg.includes('existe déjà')) return true;
        return false;
    }

    async addAction(action, data) {
        const db = await this.dbReady;
        const tx = db.transaction(['actions'], 'readwrite');
        const store = tx.objectStore('actions');
        const id = await new Promise((resolve, reject) => {
            const req = store.add({
                action,
                data: data || {},
                timestamp: new Date().toISOString(),
                status: 'pending',
            });
            req.onsuccess = () => resolve(req.result);
            req.onerror = () => reject(req.error);
        });
        await this._txDone(tx);
        return id;
    }

    async getPendingActions() {
        await this.dbReady;
        return new Promise((resolve, reject) => {
            const req = this.db.transaction(['actions'], 'readonly').objectStore('actions').getAll();
            req.onsuccess = () => resolve((req.result || []).filter((i) => i.status === 'pending'));
            req.onerror = () => reject(req.error);
        });
    }

    async getPendingCount() {
        const actions = await this.getPendingActions();
        return actions.length;
    }

    async markAsSynced(actionId) {
        const db = await this.dbReady;
        const tx = db.transaction(['actions'], 'readwrite');
        const store = tx.objectStore('actions');
        const row = await new Promise((res, rej) => {
            const r = store.get(actionId);
            r.onsuccess = () => res(r.result);
            r.onerror = () => rej(r.error);
        });
        if (!row) return;
        row.status = 'synced';
        store.put(row);
        await this._txDone(tx);
        if (row.data && row.data.fileId && window.gedOfflineStore) {
            await window.gedOfflineStore.deleteFile(row.data.fileId);
        }
    }

    async replayAction(action) {
        const token = localStorage.getItem('token');
        if (!token) return { success: false, error: 'Session expirée — reconnectez-vous' };

        const base = window.location.origin;
        let url = '';
        let options = { headers: { Authorization: 'Bearer ' + token } };

        switch (action.action) {
            case 'UPLOAD': {
                url = `${base}/documents/upload`;
                const formData = new FormData();
                formData.append('titre', action.data.titre || 'Document hors-ligne');
                formData.append('description', action.data.description || '');
                const catId = action.data.categorie_id;
                if (catId && String(catId).trim() && String(catId) !== '0') {
                    formData.append('categorie_id', catId);
                }

                let fileBlob;
                let fileName = action.data.fichier || 'document_hors_ligne.bin';

                if (action.data.fileId && window.gedOfflineStore) {
                    const stored = await window.gedOfflineStore.getFile(action.data.fileId);
                    if (stored && stored.buffer) {
                        fileBlob = new Blob([stored.buffer], { type: stored.type || 'application/octet-stream' });
                        fileName = stored.name || fileName;
                    }
                }
                if (!fileBlob) {
                    return { success: false, error: 'Fichier introuvable en cache local — ré-uploadez le document' };
                }
                formData.append('file', fileBlob, fileName);
                options = { method: 'POST', headers: { Authorization: 'Bearer ' + token }, body: formData };
                break;
            }
            case 'CREATE_CATEGORY':
                url = `${base}/categories`;
                options.method = 'POST';
                options.headers['Content-Type'] = 'application/json';
                options.body = JSON.stringify({
                    nom: action.data.nom,
                    description: action.data.description || '',
                });
                break;
            case 'DELETE': {
                const docId = action.data.id || action.data.doc_id;
                url = `${base}/documents/${docId}/supprimer`;
                options.method = 'DELETE';
                break;
            }
            case 'SOUMISSION':
                url = `${base}/documents/${action.data.doc_id}/soumettre`;
                options.method = 'PUT';
                options.headers['Content-Type'] = 'application/json';
                break;
            case 'REPRENDRE_BROUILLON':
                url = `${base}/documents/${action.data.doc_id}/reprendre-brouillon`;
                options.method = 'PUT';
                options.headers['Content-Type'] = 'application/json';
                break;
            case 'VALIDATION':
                url = `${base}/documents/${action.data.doc_id}/valider`;
                options.method = 'PUT';
                options.headers['Content-Type'] = 'application/json';
                options.body = JSON.stringify({ commentaire: action.data.commentaire || '' });
                break;
            case 'REJET':
                url = `${base}/documents/${action.data.doc_id}/rejeter`;
                options.method = 'PUT';
                options.headers['Content-Type'] = 'application/json';
                options.body = JSON.stringify({ commentaire: action.data.commentaire || '' });
                break;
            default:
                return { success: false, error: 'Type action inconnu: ' + action.action };
        }

        try {
            const response = await fetch(url, options);
            let result = {};
            try { result = await response.json(); } catch (e) { result = {}; }

            if (response.status === 401) {
                return { success: false, auth: true, error: 'Session expirée — reconnectez-vous puis resynchronisez' };
            }

            if (await this.detectConflict(action, response, result)) {
                return { success: false, conflict: true, error: this._extractError(result, response), data: result };
            }

            if (response.ok) return { success: true, data: result };

            if (this._isAlreadyDone(action, result)) {
                return { success: true, data: result, skipped: true };
            }

            return { success: false, error: this._extractError(result, response) };
        } catch (error) {
            return { success: false, error: error.message || 'Erreur réseau' };
        }
    }

    async syncAll() {
        const actions = await this.getPendingActions();
        if (!actions.length) return [];

        const results = [];
        for (const action of actions) {
            try {
                const result = await this.replayAction(action);
                if (result.success) {
                    await this.markAsSynced(action.id);
                    results.push({ id: action.id, success: true, action: action.action, skipped: !!result.skipped });
                } else if (result.conflict) {
                    results.push({ id: action.id, success: false, conflict: true, action: action.action, error: result.error });
                } else {
                    results.push({ id: action.id, success: false, action: action.action, error: result.error, auth: !!result.auth });
                }
            } catch (error) {
                results.push({ id: action.id, success: false, action: action.action, error: error.message });
            }
        }
        return results;
    }
}

window.offlineQueue = new OfflineQueue();

window.getPendingActionsCount = async function () {
    return window.offlineQueue ? window.offlineQueue.getPendingCount() : 0;
};

window.updateSyncBadge = async function () {
    const count = await window.getPendingActionsCount();
    const badge = document.getElementById('syncBadge');
    if (badge) {
        badge.style.display = count > 0 ? 'inline-block' : 'none';
        badge.textContent = count;
    }
};
