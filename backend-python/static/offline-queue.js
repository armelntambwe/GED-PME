// ============================================
// static/offline-queue.js - File d'attente hors-ligne
// GED-PME - Gestion des actions en mode déconnecté
// Version avec API réelle et synchronisation
// ============================================

class OfflineQueue {
    constructor() {
        this.queueName = 'ged-pme-offline-queue';
        this.initDB();
    }
    // ============================================
// DÉTECTER UN CONFLIT
// ============================================
async detectConflict(action, response, result) {
    // Conflit basé sur le code HTTP
    if (response.status === 409) {
        console.warn('⚠️ Conflit détecté (HTTP 409)');
        return true;
    }
    
    // Conflit basé sur le message
    if (result.message && result.message.includes('conflit')) {
        console.warn('⚠️ Conflit détecté (message)');
        return true;
    }
    
    // Conflit basé sur la version (si le serveur renvoie une version)
    if (result.version && action.data.version && result.version > action.data.version) {
        console.warn('⚠️ Conflit détecté (version plus récente)');
        return true;
    }
    
    return false;
}

    // ============================================
    // INITIALISATION INDEXEDDB
    // ============================================
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

    // ============================================
    // AJOUTER UNE ACTION À LA FILE D'ATTENTE
    // ============================================
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

    // ============================================
    // RÉCUPÉRER TOUTES LES ACTIONS EN ATTENTE
    // ============================================
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

    // ============================================
    // COMPTER LES ACTIONS EN ATTENTE
    // ============================================
    async getPendingCount() {
        const actions = await this.getPendingActions();
        return actions.length;
    }

    // ============================================
    // MARQUER UNE ACTION COMME SYNCHRONISÉE
    // ============================================
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

    // ============================================
    // NETTOYER LES ANCIENNES ACTIONS
    // ============================================
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

    // ============================================
    // REJOUER UNE ACTION SPÉCIFIQUE (VERSION API RÉELLE)
    // ============================================
    async replayAction(action) {
        console.log(`🔄 Exécution réelle: ${action.action}`, action.data);
        
        // Récupérer le token JWT depuis le localStorage
        // Récupérer le token (avec le bon nom)
const token = localStorage.getItem('token');
console.log('🔑 Token utilisé:', token ? token.substring(0, 20) + '...' : 'Aucun');

if (!token) {
    console.error('❌ Token manquant - Veuillez vous reconnecter');
    return { success: false, error: 'Token manquant' };
}
        
        let url = '';
        let options = {};
        
        // Configuration selon le type d'action
        switch(action.action) {
            case 'UPLOAD':
                url = 'http://localhost:5000/documents/upload';
                const formData = new FormData();
                formData.append('titre', action.data.titre || 'Document hors-ligne');
                formData.append('description', action.data.description || '');
                
                // Simuler un fichier (pour test)
                const blob = new Blob(['Contenu test créé en mode hors-ligne'], { type: 'text/plain' });
                formData.append('file', blob, action.data.fichier || 'document_hors_ligne.txt');
                
                options = {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    },
                    body: formData
                };
                break;
                
            case 'DELETE':
                url = `http://localhost:5000/documents/${action.data.id}`;
                options = {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                };
                break;
                
            case 'SOUMISSION':
                url = `http://localhost:5000/documents/${action.data.doc_id}/soumettre`;
                options = {
                    method: 'PUT',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                };
                break;
                
            case 'VALIDATION':
                url = `http://localhost:5000/documents/${action.data.doc_id}/valider-etape`;
                options = {
                    method: 'PUT',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ commentaire: action.data.commentaire || 'Validé hors-ligne' })
                };
                break;
                
            case 'REJET':
                url = `http://localhost:5000/documents/${action.data.doc_id}/rejeter`;
                options = {
                    method: 'PUT',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ 
                        commentaire: action.data.commentaire || 'Rejeté hors-ligne' 
                    })
                };
                break;
                
            default:
                console.error(`❌ Type d'action inconnu: ${action.action}`);
                return { success: false, error: 'Type action inconnu' };
        }
        
        try {
    console.log(`📤 Envoi à ${url}`, options);
    const response = await fetch(url, options);
    const result = await response.json();
    
    // Détection des conflits
    const hasConflict = await this.detectConflict(action, response, result);
    
    if (hasConflict) {
        console.warn('⚠️ Conflit détecté, action mise en attente');
        return { 
            success: false, 
            conflict: true, 
            error: 'Conflit détecté',
            data: result 
        };
    }
    
    if (response.ok) {
        console.log(`✅ Action ${action.action} réussie:`, result);
        return { success: true, data: result };
    } else {
        console.error(`❌ Action ${action.action} échouée:`, result);
        return { success: false, error: result.message || 'Erreur inconnue' };
    }

        } catch (error) {
            console.error(`❌ Erreur réseau:`, error);
            return { success: false, error: error.message };
        }
    }

   // ============================================
// SYNCHRONISER TOUTES LES ACTIONS
// ============================================
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
            const result = await this.replayAction(action);
            
            if (result.success) {
                await this.markAsSynced(action.id);
                results.push({ 
                    id: action.id, 
                    success: true, 
                    action: action.action 
                });
                console.log(`✅ Action ${action.id} (${action.action}) synchronisée`);
                this.showNotification(`✅ ${action.action} synchronisé`, 'success');
            } 
            // 👇 NOUVEAU : GESTION DES CONFLITS
            else if (result.conflict) {
                // Conflit détecté - on garde l'action dans la file
                results.push({ 
                    id: action.id, 
                    success: false, 
                    conflict: true,
                    action: action.action, 
                    error: result.error,
                    data: result.data 
                });
                console.warn(`⚠️ Action ${action.id} (${action.action}) en conflit - sera retentée plus tard`);
                this.showNotification(`⚠️ ${action.action} en conflit`, 'warning');
            }
            // 👇 GESTION DES ERREURS NORMALES
            else {
                results.push({ 
                    id: action.id, 
                    success: false, 
                    action: action.action, 
                    error: result.error 
                });
                console.error(`❌ Action ${action.id} échouée:`, result.error);
                this.showNotification(`❌ ${action.action} échoué: ${result.error}`, 'error');
            }
        } catch (error) {
            results.push({ 
                id: action.id, 
                success: false, 
                action: action.action, 
                error: error.message 
            });
            console.error(`❌ Erreur action ${action.id}:`, error);
            this.showNotification(`❌ Erreur: ${error.message}`, 'error');
        }
    }
    
    return results;
}

    // ============================================
    // AFFICHER UNE NOTIFICATION
    // ============================================
    showNotification(message, type = 'info') {
        if (typeof window.showNotification === 'function') {
            window.showNotification(message, type);
        } else {
            console.log(`[${type}] ${message}`);
        }
    }
}

// ============================================
// INSTANCE GLOBALE UNIQUE
// ============================================
const offlineQueue = new OfflineQueue();

// Exposer globalement pour le navigateur
window.offlineQueue = offlineQueue;

console.log('✅ File d\'attente hors-ligne initialisée avec API réelle');