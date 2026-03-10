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

    // ===== NOUVELLES MÉTHODES =====

    // Synchroniser toutes les actions en attente
    async syncAll() {
        const actions = await this.getPendingActions();
        
        if (actions.length === 0) {
            console.log('✅ Rien à synchroniser');
            return [];
        }
        
        console.log(`🔄 Synchronisation de ${actions.length} action(s)...`);
        
        const results = [];
        
        for (const action of actions) {
            try {
                // Rejouer l'action sur le serveur
                const result = await this.replayAction(action);
                
                if (result.success) {
                    await this.markAsSynced(action.id);
                    results.push({ id: action.id, success: true });
                    console.log(`✅ Action ${action.id} synchronisée`);
                } else {
                    results.push({ id: action.id, success: false, error: result.error });
                    console.error(`❌ Action ${action.id} échouée:`, result.error);
                }
            } catch (error) {
                results.push({ id: action.id, success: false, error: error.message });
                console.error(`❌ Erreur action ${action.id}:`, error);
            }
        }
        
        return results;
    }

    // Rejouer une action spécifique
    async replayAction(action) {
        console.log(`🔄 Rejouer ${action.action}:`, action.data);
        
        // Simulation de succès (à remplacer par vraie API plus tard)
        return { success: true };
    }

    // Obtenir le nombre d'actions en attente
    async getPendingCount() {
        const actions = await this.getPendingActions();
        return actions.length;
    }
}

// Instance globale
const offlineQueue = new OfflineQueue();

