/**
 * GED-PME - Cache IndexedDB pour mode hors-ligne
 * Stocke réponses API et fichiers en attente d'upload
 */
class GedOfflineStore {
    constructor() {
        this.dbPromise = new Promise((resolve, reject) => {
            const req = indexedDB.open('GED-PME-Store', 1);
            req.onupgradeneeded = (e) => {
                const db = e.target.result;
                if (!db.objectStoreNames.contains('apiCache')) {
                    db.createObjectStore('apiCache', { keyPath: 'url' });
                }
                if (!db.objectStoreNames.contains('files')) {
                    db.createObjectStore('files', { keyPath: 'id' });
                }
                if (!db.objectStoreNames.contains('docBlobs')) {
                    db.createObjectStore('docBlobs', { keyPath: 'docId' });
                }
            };
            req.onsuccess = (e) => resolve(e.target.result);
            req.onerror = () => reject(req.error);
        });
    }

    async cacheApi(url, data) {
        try {
            const db = await this.dbPromise;
            const tx = db.transaction('apiCache', 'readwrite');
            tx.objectStore('apiCache').put({ url, data, cachedAt: Date.now() });
        } catch (e) {
            console.warn('Cache API:', e);
        }
    }

    async getApi(url) {
        try {
            const db = await this.dbPromise;
            const tx = db.transaction('apiCache', 'readonly');
            const row = await new Promise((res, rej) => {
                const r = tx.objectStore('apiCache').get(url);
                r.onsuccess = () => res(r.result);
                r.onerror = () => rej(r.error);
            });
            return row ? row.data : null;
        } catch (e) {
            return null;
        }
    }

    _txDone(tx) {
        return new Promise((resolve, reject) => {
            tx.oncomplete = () => resolve();
            tx.onerror = () => reject(tx.error);
            tx.onabort = () => reject(tx.error);
        });
    }

    async saveFile(id, file) {
        const buffer = await file.arrayBuffer();
        const db = await this.dbPromise;
        const tx = db.transaction('files', 'readwrite');
        tx.objectStore('files').put({
            id,
            name: file.name,
            type: file.type || 'application/octet-stream',
            buffer,
            savedAt: Date.now(),
        });
        await this._txDone(tx);
        return id;
    }

    async getFile(id) {
        const db = await this.dbPromise;
        return new Promise((resolve, reject) => {
            const r = db.transaction('files', 'readonly').objectStore('files').get(id);
            r.onsuccess = () => resolve(r.result || null);
            r.onerror = () => reject(r.error);
        });
    }

    async deleteFile(id) {
        const db = await this.dbPromise;
        const tx = db.transaction('files', 'readwrite');
        tx.objectStore('files').delete(id);
        await this._txDone(tx);
    }

    async saveDocBlob(docId, blob, filename, mime) {
        const buffer = await blob.arrayBuffer();
        const db = await this.dbPromise;
        const tx = db.transaction('docBlobs', 'readwrite');
        tx.objectStore('docBlobs').put({ docId: String(docId), buffer, filename, mime, cachedAt: Date.now() });
    }

    async getDocBlob(docId) {
        const db = await this.dbPromise;
        const row = await new Promise((res, rej) => {
            const r = db.transaction('docBlobs', 'readonly').objectStore('docBlobs').get(String(docId));
            r.onsuccess = () => res(r.result);
            r.onerror = () => rej(r.error);
        });
        if (!row) return null;
        return {
            blob: new Blob([row.buffer], { type: row.mime }),
            filename: row.filename,
            mime: row.mime,
        };
    }
}

window.gedOfflineStore = new GedOfflineStore();
