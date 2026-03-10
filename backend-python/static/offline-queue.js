// ============================================
// static/offline-queue.js - File d'attente hors-ligne
// ============================================

class OfflineQueue {
    constructor() {
        this.queueName = 'ged-pme-offline-queue';
        this.initDB();
    }

    // Initialiser IndexedDB
    initDB() {
        const request = indexedDB.open('GED-PME-Offline', 1);

        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains('actions')) {
                db.createObjectStore('actions', { keyPath: 'id', autoIncrement: true });
            }
        };

        request.onsuccess = (event) => {
            this.db = event.target.result;
            console.log('✅ IndexedDB prête');
        };

        request.onerror = (event) => {
            console.error('❌ Erreur IndexedDB:', event.target.error);
        };
    }

    // Ajouter une action à la file d'attente
    async addAction(action, data) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['actions'], 'readwrite');
            const store = transaction.objectStore('actions');

            const actionItem = {
                action: action,
                data: data,
                timestamp: new Date().toISOString(),
                status: 'pending'
            };

            const request = store.add(actionItem);

            request.onsuccess = () => {
                console.log('✅ Action mise en attente:', action);
                resolve(request.result);
            };

            request.onerror = () => {
                console.error('❌ Erreur ajout action:', request.error);
                reject(request.error);
            };
        });
    }

    // Récupérer toutes les actions en attente
    async getPendingActions() {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['actions'], 'readonly');
            const store = transaction.objectStore('actions');
            const request = store.getAll();

            request.onsuccess = () => {
                resolve(request.result.filter(item => item.status === 'pending'));
            };

            request.onerror = () => {
                reject(request.error);
            };
        });
    }

    // Marquer une action comme synchronisée
    async markAsSynced(actionId) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['actions'], 'readwrite');
            const store = transaction.objectStore('actions');
            
            const getRequest = store.get(actionId);

            getRequest.onsuccess = () => {
                const action = getRequest.result;
                action.status = 'synced';
                
                const putRequest = store.put(action);
                putRequest.onsuccess = () => resolve();
                putRequest.onerror = () => reject(putRequest.error);
            };

            getRequest.onerror = () => reject(getRequest.error);
        });
    }

    // Nettoyer les anciennes actions
    async cleanOldActions(days = 7) {
        const cutoff = new Date();
        cutoff.setDate(cutoff.getDate() - days);

        const actions = await this.getPendingActions();
        const toDelete = actions.filter(a => new Date(a.timestamp) < cutoff);

        const transaction = this.db.transaction(['actions'], 'readwrite');
        const store = transaction.objectStore('actions');

        toDelete.forEach(action => {
            store.delete(action.id);
        });
    }
}

// Instance globale
const offlineQueue = new OfflineQueue();