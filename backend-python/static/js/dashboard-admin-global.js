const token = localStorage.getItem('token');
if (!token) window.location.href = '/login';
GedDocPreview.init({ token, apiBase: window.location.origin });

let entreprisesData = [], usersData = [], documentsData = [], logsData = [], pendingDocs = [], activityData = [];
let evolutionChart, topChart, storageChart;
let currentPageEntreprises = 1, currentPageUsers = 1, currentPageDocuments = 1, currentPageLogs = 1;
let docsTotalPages = 1, docsServerPage = 1;
const itemsPerPage = 10, itemsPerPageLogs = 20, docsPerPage = 25;
let filteredEntreprises = [], filteredUsers = [];
let currentUserId = null;
let docSearchTimer = null;

// Bootstrap 5 jQuery modal compat
(function() {
    if (!window.bootstrap || !window.jQuery) return;
    $.fn.modal = function(action) {
        return this.each(function() {
            const el = this;
            const inst = bootstrap.Modal.getOrCreateInstance(el);
            if (action === 'show') inst.show();
            else if (action === 'hide') inst.hide();
        });
    };
})();

function showToast(msg, isError) {
    const t = $('#toastMessage');
    t.text(msg).css('background', isError ? '#ef4444' : '#10b981').fadeIn(200);
    setTimeout(() => t.fadeOut(300), 3000);
}
Ged2FA.init({ getToken: () => token, showToast, onProfileRefresh: ensureAdminGlobalAccess });
function escapeHtml(s) {
    if (!s) return '';
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function authHeaders(json) {
    const h = { 'Authorization': 'Bearer ' + token };
    if (json) h['Content-Type'] = 'application/json';
    return h;
}
function redirectByRole(role) {
    if (role === 'admin_pme') window.location.href = '/dashboard-pme';
    else if (role === 'employe') window.location.href = '/dashboard-employee';
    else if (role === 'admin_global') window.location.href = '/dashboard-admin-global';
    else window.location.href = '/login';
}
function showModal(id) { bootstrap.Modal.getOrCreateInstance(document.getElementById(id)).show(); }
function hideModal(id) { const m = bootstrap.Modal.getInstance(document.getElementById(id)); if (m) m.hide(); }

async function ensureAdminGlobalAccess() {
    try {
        const stored = JSON.parse(localStorage.getItem('user') || 'null');
        if (stored && stored.role && stored.role !== 'admin_global') { redirectByRole(stored.role); return false; }
    } catch (e) {}
    try {
        const res = await fetch('/api/user/profile', { headers: authHeaders() });
        const data = await res.json();
        if (!res.ok || !data.success || data.role !== 'admin_global') {
            if (data.role) redirectByRole(data.role); else { localStorage.clear(); window.location.href = '/login'; }
            return false;
        }
        currentUserId = data.id;
        $('#userName').text(data.nom || 'Admin Global');
        $('#userAvatar').text((data.nom || 'A').charAt(0).toUpperCase());
        $('#profileNom').val(data.nom || '');
        $('#profileEmail').val(data.email || '');
        $('#profileTelephone').val(data.telephone || '');
        $('#profileNotifyWhatsapp').prop('checked', !!data.notify_whatsapp);
        if (window.Ged2FA) Ged2FA.updateUI(data);
        return true;
    } catch (e) { window.location.href = '/login'; return false; }
}

function updateStatus() {
    const s = $('#connectionStatus');
    if (navigator.onLine) s.removeClass('status-offline').addClass('status-online').html('<span class="dot"></span> Connecté');
    else s.removeClass('status-online').addClass('status-offline').html('<span class="dot"></span> Hors ligne');
}
window.addEventListener('online', updateStatus);
window.addEventListener('offline', updateStatus);
updateStatus();

$('#menuToggle').on('click', () => $('#sidebar').toggleClass('open'));
$('#notifIcon').on('click', function(e) { e.stopPropagation(); $('#notifDropdown').toggle(); });
$(document).on('click', () => $('#notifDropdown').hide());

const NOTIF_TAB_MAP = {
    ENTREPRISE: 'entreprises', USER: 'users', DOCUMENT: 'documents',
    VALIDATION: 'validation', SYSTEM: 'settings', LOG: 'logs',
};

async function chargerNotifications() {
    if (!navigator.onLine) return;
    try {
        const res = await fetch('/notifications/all', { headers: authHeaders() });
        const data = await res.json();
        const notifs = data.notifications || [];
        const nonLues = notifs.filter(n => !n.lue).length;
        $('#notifBadge').text(nonLues).css('display', nonLues > 0 ? 'inline-block' : 'none');
        let html = '<div class="notif-dropdown-header"><span>Notifications</span>' + (nonLues ? `<span class="badge bg-danger rounded-pill">${nonLues}</span>` : '') + '</div>';
        if (!notifs.length) html += '<div class="text-center py-4 text-muted small">Aucune notification</div>';
        else notifs.slice(0, 10).forEach(n => {
            const tab = NOTIF_TAB_MAP[(n.type || '').split('_')[0]] || 'dashboard';
            html += `<div class="notif-item ${!n.lue ? 'unread' : ''}" onclick="openNotif(${n.id}, '${tab}')">${escapeHtml(n.message || '')}<small class="d-block text-muted mt-1">${(n.date_creation || '').slice(0,16).replace('T',' ')}</small></div>`;
        });
        $('#notifDropdown').html(html);
    } catch (e) { console.error(e); }
}
async function openNotif(id, tab) {
    await fetch(`/notifications/${id}/lire`, { method: 'PUT', headers: authHeaders() });
    chargerNotifications();
    showTab(tab);
}
async function marquerLu(id) { await openNotif(id, 'dashboard'); }

function showTab(tab) {
    $('.tab-pane').hide();
    const paneId = 'tab' + tab.charAt(0).toUpperCase() + tab.slice(1);
    $('#' + paneId).show();
    $('.sidebar a').removeClass('active');
    $(`.sidebar a[data-tab="${tab}"]`).addClass('active');
    if (window.innerWidth <= 992) $('#sidebar').removeClass('open');
    const url = new URL(window.location);
    url.searchParams.set('tab', tab);
    history.replaceState(null, '', url);
    if (tab === 'dashboard') loadDashboard();
    else if (tab === 'entreprises') loadEntreprises();
    else if (tab === 'users') loadUsers();
    else if (tab === 'documents') loadDocuments();
    else if (tab === 'validation') loadValidation();
    else if (tab === 'activity') loadActivity();
    else if (tab === 'logs') loadLogs();
    else if (tab === 'storage') loadStorage();
    else if (tab === 'settings') loadSettings();
}
$('.sidebar a').on('click', function(e) { e.preventDefault(); showTab($(this).data('tab')); });

function renderPagination(containerId, current, total, fnName) {
    if (total <= 1) { $(containerId).empty(); return; }
    let html = '<nav><ul class="pagination pagination-sm justify-content-center">';
    html += `<li class="page-item ${current===1?'disabled':''}"><a class="page-link" href="#" onclick="${fnName}(${current-1});return false;">Préc.</a></li>`;
    const start = Math.max(1, current - 2), end = Math.min(total, start + 4);
    for (let i = start; i <= end; i++) html += `<li class="page-item ${current===i?'active':''}"><a class="page-link" href="#" onclick="${fnName}(${i});return false;">${i}</a></li>`;
    html += `<li class="page-item ${current===total?'disabled':''}"><a class="page-link" href="#" onclick="${fnName}(${current+1});return false;">Suiv.</a></li></ul></nav>`;
    $(containerId).html(html);
}

function populateEntrepriseSelects() {
    const opts = entreprisesData.map(e => `<option value="${e.id}">${escapeHtml(e.nom)}</option>`).join('');
    ['#filterUserEntreprise', '#filterDocEntreprise', '#filterActivityEntreprise', '#userEntrepriseSelect'].forEach(sel => {
        const cur = $(sel).val();
        const isUserModal = sel === '#userEntrepriseSelect';
        $(sel).html((isUserModal ? '' : '<option value="">Toutes entreprises</option>') + opts);
        if (cur) $(sel).val(cur);
    });
}

async function loadDashboard(silent) {
    if (!navigator.onLine) return;
    try {
        const [statsRes, evoRes, entRes] = await Promise.all([
            fetch('/api/admin-global/stats', { headers: authHeaders() }),
            fetch('/api/admin-global/stats/evolution', { headers: authHeaders() }),
            fetch('/api/admin-global/entreprises', { headers: authHeaders() }),
        ]);
        const statsData = await statsRes.json();
        const s = statsData.stats || {};
        $('#statEntreprises').text(s.total_entreprises || 0);
        $('#statDocuments').text(s.total_documents || 0);
        $('#statUsers').text(s.total_users || 0);
        $('#statUsersActifs').text(s.active_users || 0);

        const evoJson = await evoRes.json();
        const labels = (evoJson.labels || []).map(d => new Date(d).toLocaleDateString('fr-FR', { day:'2-digit', month:'2-digit' }));
        const evoValues = evoJson.data || [];
        if (silent && evolutionChart) {
            evolutionChart.data.labels = labels;
            evolutionChart.data.datasets[0].data = evoValues;
            evolutionChart.update('none');
        } else {
            if (evolutionChart) evolutionChart.destroy();
            evolutionChart = new Chart(document.getElementById('evolutionChart'), {
                type: 'line',
                data: { labels, datasets: [{ label: 'Documents', data: evoValues, borderColor: '#0ea5e9', backgroundColor: 'rgba(14,165,233,0.1)', tension: 0.3, fill: true }] },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
            });
        }

        const entJson = await entRes.json();
        entreprisesData = entJson.entreprises || [];
        populateEntrepriseSelects();
        const top5 = [...entreprisesData].sort((a,b) => (b.nb_documents||0) - (a.nb_documents||0)).slice(0, 5);
        if (silent && topChart) {
            topChart.data.labels = top5.map(e => (e.nom || '').substring(0, 12));
            topChart.data.datasets[0].data = top5.map(e => e.nb_documents || 0);
            topChart.update('none');
        } else {
            if (topChart) topChart.destroy();
            topChart = new Chart(document.getElementById('topChart'), {
                type: 'bar',
                data: { labels: top5.map(e => (e.nom || '').substring(0, 12)), datasets: [{ data: top5.map(e => e.nb_documents || 0), backgroundColor: '#0ea5e9', borderRadius: 8 }] },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
            });
        }
        await loadLastLogs();
    } catch (e) { console.error(e); showToast('Erreur dashboard', true); }
}

async function loadLastLogs() {
    try {
        const res = await fetch('/api/admin-global/all-logs', { headers: authHeaders() });
        const data = await res.json();
        const tbody = $('#lastLogsBody');
        if (!data.logs || !data.logs.length) { tbody.html('<tr><td colspan="3" class="text-center text-muted py-3">Aucune activité</td></tr>'); return; }
        tbody.html(data.logs.slice(0, 10).map(log =>
            `<tr><td>${(log.date_action||'').slice(0,16).replace('T',' ')}</td><td><span class="badge bg-secondary">${escapeHtml(log.action||'-')}</span></td><td>${escapeHtml(log.utilisateur_nom||'-')}</td></tr>`
        ).join(''));
    } catch (e) { console.error(e); }
}

async function loadEntreprises() {
    try {
        const res = await fetch('/api/admin-global/entreprises', { headers: authHeaders() });
        const data = await res.json();
        entreprisesData = data.entreprises || [];
        filteredEntreprises = [...entreprisesData];
        populateEntrepriseSelects();
        currentPageEntreprises = 1;
        renderEntreprisesPage();
    } catch (e) { showToast('Erreur entreprises', true); }
}

function renderEntreprisesPage() {
    const tbody = $('#entreprisesTable tbody');
    if (!filteredEntreprises.length) { tbody.html('<tr><td colspan="8" class="text-center text-muted py-4">Aucune entreprise</td></tr>'); $('#paginationEntreprises').empty(); return; }
    const start = (currentPageEntreprises - 1) * itemsPerPage;
    const page = filteredEntreprises.slice(start, start + itemsPerPage);
    tbody.html(page.map(ent => {
        const actif = (ent.statut || 'actif') === 'actif';
        const logo = ent.logo_url ? `<img src="${escapeHtml(ent.logo_url)}" class="company-logo-sm me-2" alt="">` : '';
        return `<tr>
            <td>${ent.id}</td>
            <td>${logo}<strong>${escapeHtml(ent.nom)}</strong><br><small class="text-muted">${escapeHtml(ent.secteur_activite||'')}</small></td>
            <td><small>${escapeHtml(ent.nif||'-')}<br>${escapeHtml(ent.rccm||'-')}</small></td>
            <td>${escapeHtml(ent.email||'-')}</td>
            <td>${ent.nb_employes||0}</td>
            <td>${ent.nb_documents||0}</td>
            <td><span class="${actif?'badge-active':'badge-inactive'}">${actif?'Actif':'Suspendu'}</span></td>
            <td class="text-end"><div class="doc-actions-cell">
                <button type="button" class="btn-action-icon" onclick="openCompanyDetail(${ent.id})" title="Fiche"><i class="fas fa-eye"></i></button>
                <button type="button" class="btn-action-icon" onclick="openEditCompany(${ent.id})" title="Modifier"><i class="fas fa-edit"></i></button>
                <button type="button" class="btn-action-icon" onclick="toggleStatus(${ent.id})" title="Activer/Suspendre"><i class="fas fa-toggle-on"></i></button>
                <button type="button" class="btn-action-icon text-danger" onclick="deleteEntreprise(${ent.id}, false)" title="Suspendre"><i class="fas fa-ban"></i></button>
            </div></td></tr>`;
    }).join(''));
    renderPagination('#paginationEntreprises', currentPageEntreprises, Math.ceil(filteredEntreprises.length / itemsPerPage), 'changePageEntreprises');
}
function changePageEntreprises(p) { currentPageEntreprises = Math.max(1, p); renderEntreprisesPage(); }
function filterEntreprises() {
    const q = $('#searchEntreprise').val().toLowerCase();
    filteredEntreprises = entreprisesData.filter(e => (e.nom||'').toLowerCase().includes(q) || (e.email||'').toLowerCase().includes(q) || (e.nif||'').toLowerCase().includes(q));
    currentPageEntreprises = 1; renderEntreprisesPage();
}

function showAddEntrepriseModal() {
    $('#companyModalTitle').text('Nouvelle PME + Admin');
    $('#companyEditId').val('');
    $('#compNom,#compNif,#compRccm,#compAdresse,#compTel,#compEmail,#adminNom,#adminEmail,#adminTel,#adminPassword').val('');
    $('#compSecteur').val('');
    $('#compLogo').val('');
    $('#compTabAdminLi').show();
    $('#companySaveBtn').text('Créer').off('click').on('click', saveCompany);
    showModal('companyModal');
}

function openEditCompany(id) {
    const ent = entreprisesData.find(e => e.id === id);
    if (!ent) return;
    $('#companyModalTitle').text('Modifier entreprise');
    $('#companyEditId').val(id);
    $('#compNom').val(ent.nom); $('#compNif').val(ent.nif); $('#compRccm').val(ent.rccm);
    $('#compAdresse').val(ent.adresse); $('#compTel').val(ent.telephone); $('#compEmail').val(ent.email);
    $('#compSecteur').val(ent.secteur_activite || '');
    $('#compTabAdminLi').hide();
    $('#companySaveBtn').text('Enregistrer').off('click').on('click', saveCompany);
    showModal('companyModal');
}

async function saveCompany() {
    const id = $('#companyEditId').val();
    if (id) {
        const data = {
            nom: $('#compNom').val(), nif: $('#compNif').val(), rccm: $('#compRccm').val(),
            adresse: $('#compAdresse').val(), telephone: $('#compTel').val(), email: $('#compEmail').val(),
            secteur_activite: $('#compSecteur').val(),
        };
        if (!data.nom) { showToast('Nom requis', true); return; }
        const res = await fetch(`/api/admin-global/entreprises/${id}`, { method: 'PUT', headers: authHeaders(true), body: JSON.stringify(data) });
        const result = await res.json();
        if (res.ok) { showToast('Entreprise modifiée'); hideModal('companyModal'); loadEntreprises(); }
        else showToast(result.message || 'Erreur', true);
        return;
    }
    const fd = new FormData();
    const entreprise = {
        nom: $('#compNom').val(), nif: $('#compNif').val(), rccm: $('#compRccm').val(),
        adresse: $('#compAdresse').val(), telephone: $('#compTel').val(), email: $('#compEmail').val(),
        secteur_activite: $('#compSecteur').val(),
    };
    const administrateur = {
        nom: $('#adminNom').val(), email: $('#adminEmail').val(),
        telephone: $('#adminTel').val(), password: $('#adminPassword').val(),
    };
    if (!entreprise.nom || !administrateur.nom || !administrateur.email || !administrateur.password) {
        showToast('Nom entreprise, admin (nom, email, MDP) requis', true); return;
    }
    fd.append('entreprise', JSON.stringify(entreprise));
    fd.append('administrateur', JSON.stringify(administrateur));
    const logo = document.getElementById('compLogo').files[0];
    if (logo) fd.append('logo', logo);
    const res = await fetch('/api/admin-global/entreprises', { method: 'POST', headers: { 'Authorization': 'Bearer ' + token }, body: fd });
    const result = await res.json();
    if (res.ok) { showToast('PME et admin créés'); hideModal('companyModal'); loadEntreprises(); loadDashboard(true); chargerNotifications(); }
    else showToast(result.message || 'Erreur', true);
}

async function openCompanyDetail(id) {
    showModal('companyDetailModal');
    $('#companyDetailBody').html('<div class="text-center py-4"><div class="spinner-border text-primary"></div></div>');
    try {
        const [detailRes, wfRes] = await Promise.all([
            fetch(`/api/admin-global/entreprises/${id}`, { headers: authHeaders() }),
            fetch(`/api/admin-global/entreprises/${id}/workflow`, { headers: authHeaders() }),
        ]);
        const detail = await detailRes.json();
        const wf = await wfRes.json();
        if (!detail.success) { $('#companyDetailBody').html('<p class="text-danger">Introuvable</p>'); return; }
        const e = detail.entreprise;
        const st = e.stats || {};
        $('#companyDetailTitle').text(e.nom || 'Fiche entreprise');
        let wfHtml = (wf.etapes || []).length
            ? wf.etapes.map((step, i) => `<div class="workflow-row"><span class="badge bg-primary">${i+1}</span><strong>${escapeHtml(step.nom_etape||step.nom||'')}</strong><span class="text-muted small">${escapeHtml(step.role_requis||step.role||'')} — ${step.delai_heures||48}h</span></div>`).join('')
            : '<p class="text-muted small">Aucune étape configurée.</p>';
        $('#companyDetailBody').html(`
            <div class="detail-grid mb-3">
                <div class="detail-item"><div class="lbl">NIF</div><div class="val">${escapeHtml(e.nif||'-')}</div></div>
                <div class="detail-item"><div class="lbl">RCCM</div><div class="val">${escapeHtml(e.rccm||'-')}</div></div>
                <div class="detail-item"><div class="lbl">Secteur</div><div class="val">${escapeHtml(e.secteur_activite||'-')}</div></div>
                <div class="detail-item"><div class="lbl">Statut</div><div class="val">${escapeHtml(e.statut||'-')}</div></div>
                <div class="detail-item"><div class="lbl">Documents</div><div class="val">${st.total_documents||0}</div></div>
                <div class="detail-item"><div class="lbl">En attente</div><div class="val">${st.en_attente||0}</div></div>
            </div>
            <p class="small text-muted">${escapeHtml(e.adresse||'')} — ${escapeHtml(e.telephone||'')} — ${escapeHtml(e.email||'')}</p>
            <div class="row g-3">
                <div class="col-md-6"><h6>Employés (${(e.employes||[]).length})</h6>
                    <div class="table-doc-wrap" style="max-height:200px;overflow:auto"><table class="table-custom table-sm"><tbody>
                    ${(e.employes||[]).slice(0,20).map(u=>`<tr><td>${escapeHtml(u.nom)}</td><td><span class="${roleBadge(u.role)}">${u.role}</span></td></tr>`).join('')||'<tr><td class="text-muted">Aucun</td></tr>'}
                    </tbody></table></div></div>
                <div class="col-md-6"><h6>Documents récents</h6>
                    <div class="table-doc-wrap" style="max-height:200px;overflow:auto"><table class="table-custom table-sm"><tbody>
                    ${(e.documents_recents||[]).map(d=>`<tr><td>${escapeHtml(d.titre)}</td><td>${escapeHtml(d.statut)}</td></tr>`).join('')||'<tr><td class="text-muted">Aucun</td></tr>'}
                    </tbody></table></div></div>
            </div>
            <hr><h6><i class="fas fa-project-diagram me-1"></i>Workflow</h6>${wfHtml}
            <div class="mt-3"><button class="btn btn-sm btn-outline-danger" onclick="deleteEntreprise(${id}, true)"><i class="fas fa-trash me-1"></i>Suppression définitive</button></div>`);
    } catch (err) { $('#companyDetailBody').html('<p class="text-danger">Erreur chargement</p>'); }
}

async function toggleStatus(id) {
    await fetch(`/api/admin-global/entreprises/${id}/toggle`, { method: 'PUT', headers: authHeaders() });
    showToast('Statut modifié'); loadEntreprises(); chargerNotifications();
}
async function deleteEntreprise(id, hard) {
    const msg = hard ? 'SUPPRIMER DÉFINITIVEMENT cette entreprise et toutes ses données ?' : 'Suspendre cette entreprise ?';
    if (!confirm(msg)) return;
    const url = hard ? `/api/admin-global/entreprises/${id}/delete?hard=1` : `/api/admin-global/entreprises/${id}/delete`;
    const res = await fetch(url, { method: 'DELETE', headers: authHeaders() });
    const data = await res.json();
    if (res.ok) { showToast(data.message || 'OK'); hideModal('companyDetailModal'); loadEntreprises(); loadDashboard(true); }
    else showToast(data.message || 'Erreur', true);
}

function roleBadge(role) {
    if (role === 'admin_global') return 'badge-admin';
    if (role === 'admin_pme') return 'badge-pme';
    return 'badge-employe';
}

async function loadUsers() {
    try {
        const role = $('#filterUserRole').val();
        const entreprise_id = $('#filterUserEntreprise').val();
        const actif = $('#filterUserActif').val();
        const search = $('#searchUser').val();
        let url = `/api/admin-global/all-users?limit=500&page=1`;
        if (role) url += `&role=${encodeURIComponent(role)}`;
        if (entreprise_id) url += `&entreprise_id=${entreprise_id}`;
        if (actif !== '') url += `&actif=${actif}`;
        if (search) url += `&search=${encodeURIComponent(search)}`;
        const res = await fetch(url, { headers: authHeaders() });
        const data = await res.json();
        usersData = data.users || [];
        filteredUsers = [...usersData];
        currentPageUsers = 1;
        renderUsersPage();
    } catch (e) { showToast('Erreur utilisateurs', true); }
}
function applyUserFilters() { loadUsers(); }

function renderUsersPage() {
    const tbody = $('#usersTable tbody');
    if (!filteredUsers.length) { tbody.html('<tr><td colspan="7" class="text-center text-muted py-4">Aucun utilisateur</td></tr>'); return; }
    const start = (currentPageUsers - 1) * itemsPerPage;
    const page = filteredUsers.slice(start, start + itemsPerPage);
    tbody.html(page.map(u => `<tr><td>${u.id}</td><td class="fw-semibold">${escapeHtml(u.nom)}</td><td>${escapeHtml(u.email)}</td>
        <td><span class="${roleBadge(u.role)}">${escapeHtml(u.role)}</span></td>
        <td>${escapeHtml(u.entreprise_nom||'-')}</td>
        <td><span class="${u.actif?'badge-active':'badge-inactive'}">${u.actif?'Actif':'Inactif'}</span></td>
        <td class="text-end"><div class="doc-actions-cell">
            <button type="button" class="btn-action-icon" onclick="openEditUser(${u.id})" title="Modifier"><i class="fas fa-edit"></i></button>
            <button type="button" class="btn-action-icon" onclick="toggleUserStatus(${u.id})" title="Toggle"><i class="fas fa-toggle-on"></i></button>
            <button type="button" class="btn-action-icon" onclick="openResetPassword(${u.id})" title="MDP"><i class="fas fa-key"></i></button>
            ${u.id !== currentUserId ? `<button type="button" class="btn-action-icon text-danger" onclick="deleteUser(${u.id})" title="Supprimer"><i class="fas fa-trash"></i></button>` : ''}
        </div></td></tr>`).join(''));
    renderPagination('#paginationUsers', currentPageUsers, Math.ceil(filteredUsers.length / itemsPerPage), 'changePageUsers');
}
function changePageUsers(p) { currentPageUsers = Math.max(1, p); renderUsersPage(); }

function resetUserRoleSelect(mode, currentRole) {
    const sel = $('#userRoleSelect');
    if (mode === 'create') {
        sel.html('<option value="employe">Employé</option><option value="admin_pme">Admin PME</option>');
        sel.val('employe');
    } else {
        sel.html('<option value="employe">Employé</option><option value="admin_pme">Admin PME</option><option value="admin_global">Admin global</option>');
        sel.val(currentRole || 'employe');
        if (currentRole === 'admin_global') sel.prop('disabled', true);
        else sel.prop('disabled', false);
    }
}

function showCreateUserModal() {
    $('#userModalTitle').text('Créer utilisateur');
    $('#userEditId').val('');
    $('#userNom,#userEmail,#userPassword,#userTel').val('');
    $('#userEmail').prop('readonly', false);
    resetUserRoleSelect('create');
    $('#userPasswordRow').show();
    populateEntrepriseSelects();
    toggleUserEntrepriseField();
    showModal('userModal');
}
function openEditUser(id) {
    const u = usersData.find(x => x.id === id);
    if (!u) return;
    $('#userModalTitle').text('Modifier utilisateur');
    $('#userEditId').val(id);
    $('#userNom').val(u.nom); $('#userEmail').val(u.email).prop('readonly', true);
    $('#userTel').val(u.telephone||'');
    resetUserRoleSelect('edit', u.role);
    $('#userEntrepriseSelect').val(u.entreprise_id||'');
    $('#userPasswordRow').hide();
    toggleUserEntrepriseField();
    showModal('userModal');
}
function toggleUserEntrepriseField() {
    const role = $('#userRoleSelect').val();
    $('#userEntrepriseRow').toggle(role !== 'admin_global');
}
async function saveUser() {
    const id = $('#userEditId').val();
    if (id) {
        const data = { nom: $('#userNom').val(), telephone: $('#userTel').val(), role: $('#userRoleSelect').val(), entreprise_id: parseInt($('#userEntrepriseSelect').val()) || null };
        const res = await fetch(`/api/admin-global/users/${id}`, { method: 'PUT', headers: authHeaders(true), body: JSON.stringify(data) });
        const result = await res.json();
        if (res.ok) { showToast('Utilisateur mis à jour'); hideModal('userModal'); $('#userEmail').prop('readonly', false); loadUsers(); }
        else showToast(result.message || 'Erreur', true);
        return;
    }
    const data = {
        nom: $('#userNom').val(), email: $('#userEmail').val(), password: $('#userPassword').val(),
        telephone: $('#userTel').val(), role: $('#userRoleSelect').val(),
        entreprise_id: parseInt($('#userEntrepriseSelect').val()) || null,
    };
    const res = await fetch('/api/admin-global/users', { method: 'POST', headers: authHeaders(true), body: JSON.stringify(data) });
    const result = await res.json();
    if (res.ok) { showToast('Utilisateur créé'); hideModal('userModal'); loadUsers(); }
    else showToast(result.message || 'Erreur', true);
}
async function toggleUserStatus(userId) {
    if (!confirm('Changer le statut ?')) return;
    const res = await fetch(`/api/admin-global/users/${userId}/toggle`, { method: 'PUT', headers: authHeaders() });
    const data = await res.json();
    if (res.ok) { showToast(data.message || 'OK'); loadUsers(); } else showToast(data.message || 'Erreur', true);
}
async function deleteUser(userId) {
    if (!confirm('Supprimer cet utilisateur ?')) return;
    const res = await fetch(`/api/admin-global/users/${userId}`, { method: 'DELETE', headers: authHeaders() });
    const data = await res.json();
    if (res.ok) { showToast('Supprimé'); loadUsers(); } else showToast(data.message || 'Erreur', true);
}
function openResetPassword(userId) { $('#resetPwdUserId').val(userId); $('#resetPwdInput').val(''); showModal('resetPwdModal'); }
async function confirmerResetPassword() {
    const userId = $('#resetPwdUserId').val();
    const pwd = ($('#resetPwdInput').val() || '').trim();
    if (!pwd || pwd.length < 6) { showToast('Mot de passe min. 6 caractères', true); return; }
    const res = await fetch(`/api/admin-global/users/${userId}/reset-password`, { method: 'PUT', headers: authHeaders(true), body: JSON.stringify({ password: pwd }) });
    const data = await res.json();
    if (res.ok) { showToast('Mot de passe réinitialisé'); hideModal('resetPwdModal'); } else showToast(data.message || 'Erreur', true);
}

function debounceLoadDocuments() {
    clearTimeout(docSearchTimer);
    docSearchTimer = setTimeout(() => { docsServerPage = 1; loadDocuments(); }, 350);
}
async function loadDocuments(page) {
    if (page) docsServerPage = page;
    try {
        let url = `/api/admin-global/all-documents?page=${docsServerPage}&limit=${docsPerPage}`;
        const search = $('#searchDoc').val();
        const statut = $('#filterDocStatut').val();
        const entreprise_id = $('#filterDocEntreprise').val();
        const extension = $('#filterDocFormat').val();
        if (search) url += `&search=${encodeURIComponent(search)}`;
        if (statut) url += `&statut=${encodeURIComponent(statut)}`;
        if (entreprise_id) url += `&entreprise_id=${entreprise_id}`;
        if (extension) url += `&extension=${encodeURIComponent(extension)}`;
        const res = await fetch(url, { headers: authHeaders() });
        const data = await res.json();
        documentsData = data.documents || [];
        docsTotalPages = data.total_pages || 1;
        $('#documentsTotalInfo').text(data.total != null ? `${data.total} document(s) trouvé(s)` : '');
        renderDocumentsPage();
    } catch (e) { showToast('Erreur documents', true); }
}
function docFormatLabel(doc) {
    const name = doc.fichier_nom || doc.titre || '';
    const ext = GedDocPreview.fileExtension(name);
    return ext ? ext.toUpperCase() : (doc.type_mime || '-').split('/').pop();
}
function renderDocumentsPage() {
    const tbody = $('#documentsTable tbody');
    if (!documentsData.length) {
        tbody.html('<tr><td colspan="7" class="text-center text-muted py-4">Aucun document</td></tr>');
        $('#paginationDocuments').empty();
        return;
    }
    tbody.html(documentsData.map(doc => {
        const ext = GedDocPreview.fileExtension(doc.fichier_nom || '');
        const icon = GedDocPreview.getFileIcon(ext);
        return `<tr>
        <td><i class="fas ${icon} me-1"></i><span class="fw-semibold">${escapeHtml(doc.titre)}</span>
            ${doc.fichier_nom ? `<br><small class="text-muted">${escapeHtml(doc.fichier_nom)}</small>` : ''}</td>
        <td><span class="badge bg-light text-dark border">${escapeHtml(docFormatLabel(doc))}</span></td>
        <td>${escapeHtml(doc.auteur_nom||'-')}</td>
        <td>${escapeHtml(doc.entreprise_nom||'-')}</td><td>${(doc.date_creation||'').slice(0,10)}</td>
        <td>${escapeHtml(doc.statut||'-')}</td>
        <td class="text-end"><div class="doc-actions-cell">
            <button type="button" class="btn-action-icon" onclick="viewDocument(${doc.id})" title="Aperçu"><i class="fas fa-eye"></i></button>
            <button type="button" class="btn-action-icon" onclick="downloadDoc(${doc.id})" title="Télécharger"><i class="fas fa-download"></i></button>
        </div></td></tr>`;
    }).join(''));
    renderPagination('#paginationDocuments', docsServerPage, docsTotalPages, 'loadDocuments');
}

async function loadValidation() {
    try {
        const res = await fetch('/api/admin-global/documents/pending', { headers: authHeaders() });
        const data = await res.json();
        pendingDocs = data.documents || [];
        const tbody = $('#validationTable tbody');
        if (!pendingDocs.length) { tbody.html('<tr><td colspan="5" class="text-center text-muted py-4">Aucun document en attente</td></tr>'); return; }
        tbody.html(pendingDocs.map(doc => `<tr>
            <td>${escapeHtml(doc.titre)}</td><td>${escapeHtml(doc.auteur_nom||'-')}</td>
            <td>${escapeHtml(doc.entreprise_nom||'-')}</td><td>${(doc.date_creation||'').slice(0,10)}</td>
            <td class="text-end"><div class="doc-actions-cell">
                <button class="btn-action-icon" onclick="viewDocument(${doc.id})" title="Aperçu"><i class="fas fa-eye"></i></button>
            </div></td></tr>`).join(''));
    } catch (e) { showToast('Erreur validation', true); }
}

async function viewDocument(docId) {
    showModal('viewDocumentModal');
    $('#viewDocBody').html('<div class="text-center py-4"><div class="spinner-border"></div><p class="mt-2 text-muted small">Chargement de l\'aperçu…</p></div>');
    $('#viewDocFooter').empty();
    try {
        const res = await fetch(`/documents/${docId}/contenu`, { headers: authHeaders() });
        const data = await res.json();
        const doc = data.document;
        if (!data.success || !doc) { $('#viewDocBody').html('<p class="text-danger">Document introuvable</p>'); return; }
        $('#viewDocTitle').text(doc.titre || 'Document');
        const fname = doc.fichier_nom || '';
        let previewHtml = '<div class="alert alert-warning mb-0">Aucun fichier associé.</div>';
        if (fname) {
            try {
                const { blob, mime, filename } = await GedDocPreview.fetchBlob(docId, fname);
                previewHtml = await GedDocPreview.buildPreview(blob, mime, filename || fname, doc, `downloadDoc(${docId})`);
            } catch (e) {
                if (doc.contenu_ocr) {
                    previewHtml = `<div class="border rounded p-3 bg-light"><p class="small fw-semibold mb-2"><i class="fas fa-font me-1"></i>Texte extrait (OCR)</p><pre class="ocr-text mb-0 small" style="max-height:420px;overflow:auto;white-space:pre-wrap;">${escapeHtml(String(doc.contenu_ocr).substring(0, 8000))}</pre></div>`;
                } else {
                    previewHtml = `<div class="alert alert-warning mb-0">Impossible de charger le fichier.<br><button type="button" class="btn btn-sm btn-primary mt-2" onclick="downloadDoc(${docId})"><i class="fas fa-download me-1"></i>Télécharger</button></div>`;
                }
            }
        }
        const ext = GedDocPreview.fileExtension(fname);
        $('#viewDocBody').html(`<div class="row g-3"><div class="col-lg-8">${previewHtml}</div><div class="col-lg-4">
            <div class="card border-0 bg-light"><div class="card-body small">
            <h6 class="fw-bold"><i class="fas fa-info-circle me-1 text-primary"></i>Métadonnées</h6>
            <p class="mb-1"><strong>Format :</strong> ${escapeHtml(ext ? ext.toUpperCase() : (doc.type_mime || '-'))}</p>
            <p class="mb-1"><strong>Fichier :</strong> ${escapeHtml(fname || '-')}</p>
            <p class="mb-1"><strong>Statut :</strong> ${escapeHtml(doc.statut)}</p>
            <p class="mb-1"><strong>Auteur :</strong> ${escapeHtml(doc.auteur_nom||'-')}</p>
            <p class="mb-1"><strong>Entreprise :</strong> ${escapeHtml(doc.entreprise_nom||'-')}</p>
            <p class="mb-0"><strong>Taille :</strong> ${GedDocPreview.formatSize(doc.fichier_taille)}</p>
            </div></div></div></div>`);
        $('#viewDocFooter').html(`<button class="btn btn-primary" onclick="downloadDoc(${docId})"><i class="fas fa-download me-1"></i>Télécharger</button>
                <button class="btn btn-secondary" data-bs-dismiss="modal">Fermer</button>`);
    } catch (e) { $('#viewDocBody').html('<p class="text-danger">Erreur chargement</p>'); }
}
async function downloadDoc(docId) {
    try {
        const res = await fetch(`/documents/${docId}/download`, { headers: authHeaders() });
        if (!res.ok) { showToast('Téléchargement impossible', true); return; }
        const blob = await res.blob();
        const cd = res.headers.get('Content-Disposition') || '';
        const match = cd.match(/filename[^;=\n]*=(['"]?)([^'"\n]*)\1/);
        const filename = match ? decodeURIComponent(match[2]) : 'document';
        const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = filename; a.click();
    } catch (e) { showToast('Erreur téléchargement', true); }
}
async function loadActivity() {
    try {
        let url = '/api/admin-global/activity?limit=200';
        const eid = $('#filterActivityEntreprise').val();
        if (eid) url += `&entreprise_id=${eid}`;
        const res = await fetch(url, { headers: authHeaders() });
        const data = await res.json();
        activityData = data.activity || [];
        const tbody = $('#activityTable tbody');
        if (!activityData.length) { tbody.html('<tr><td colspan="6" class="text-muted text-center py-4">Aucune donnée</td></tr>'); return; }
        tbody.html(activityData.map(a => `<tr>
            <td>${escapeHtml(a.nom)}<br><small class="text-muted">${escapeHtml(a.email)}</small></td>
            <td><span class="${roleBadge(a.role)}">${a.role}</span></td>
            <td>${escapeHtml(a.entreprise_nom||'-')}</td>
            <td>${a.nb_documents||0}</td><td>${a.nb_actions||0}</td>
            <td>${(a.derniere_connexion||'-').slice(0,16).replace('T',' ')}</td></tr>`).join(''));
    } catch (e) { showToast('Erreur activité', true); }
}
function exportActivityCSV() {
    if (!activityData.length) { showToast('Aucune donnée à exporter', true); return; }
    const headers = ['Nom', 'Email', 'Role', 'Entreprise', 'Documents', 'Actions', 'Derniere_connexion'];
    const rows = activityData.map(a => [
        a.nom || '', a.email || '', a.role || '', a.entreprise_nom || '',
        a.nb_documents || 0, a.nb_actions || 0, (a.derniere_connexion || '').slice(0, 19),
    ]);
    const csv = [headers, ...rows].map(r => r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n');
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `activite_ged_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    showToast('Export CSV téléchargé');
}

async function loadLogs() {
    try {
        const res = await fetch('/api/admin-global/all-logs', { headers: authHeaders() });
        const data = await res.json();
        logsData = data.logs || [];
        currentPageLogs = 1;
        renderLogsPage();
    } catch (e) { showToast('Erreur logs', true); }
}
function renderLogsPage() {
    const tbody = $('#logsTable tbody');
    if (!logsData.length) { tbody.html('<tr><td colspan="4" class="text-center text-muted py-4">Aucun log</td></tr>'); return; }
    const start = (currentPageLogs - 1) * itemsPerPageLogs;
    tbody.html(logsData.slice(start, start + itemsPerPageLogs).map(log =>
        `<tr><td>${(log.date_action||'').slice(0,16).replace('T',' ')}</td><td><span class="badge bg-secondary">${escapeHtml(log.action)}</span></td><td>${escapeHtml(log.utilisateur_nom||'-')}</td><td>${escapeHtml(log.description||'-')}</td></tr>`
    ).join(''));
    renderPagination('#paginationLogs', currentPageLogs, Math.ceil(logsData.length / itemsPerPageLogs), 'changePageLogs');
}
function changePageLogs(p) { currentPageLogs = Math.max(1, p); renderLogsPage(); }
async function filterLogs() {
    let url = '/api/admin-global/logs/filter?';
    const d1 = $('#logDateDebut').val(), d2 = $('#logDateFin').val(), act = $('#logAction').val();
    if (d1) url += `date_debut=${d1}&`; if (d2) url += `date_fin=${d2}&`; if (act) url += `action=${act}&`;
    const res = await fetch(url, { headers: authHeaders() });
    const data = await res.json();
    logsData = data.logs || []; currentPageLogs = 1; renderLogsPage();
}
function resetLogsFilter() { $('#logDateDebut,#logDateFin').val(''); $('#logAction').val(''); loadLogs(); }
async function exportLogs() {
    const res = await fetch('/api/admin-global/logs/export', { headers: authHeaders() });
    const blob = await res.blob();
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'logs_export.csv'; a.click();
    showToast('Export téléchargé');
}
async function exportEntreprisesCSV() {
    const res = await fetch('/api/admin-global/entreprises/export', { headers: authHeaders() });
    if (!res.ok) { showToast('Erreur export', true); return; }
    const blob = await res.blob(); const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'entreprises.csv'; a.click();
}
async function exportUsersCSV() {
    const res = await fetch('/api/admin-global/users/export', { headers: authHeaders() });
    if (!res.ok) { showToast('Erreur export', true); return; }
    const blob = await res.blob(); const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'utilisateurs.csv'; a.click();
}

async function loadStorage() {
    try {
        const [storRes, bakRes] = await Promise.all([
            fetch('/api/admin-global/storage', { headers: authHeaders() }),
            fetch('/api/admin-global/backups', { headers: authHeaders() }),
        ]);
        const data = await storRes.json();
        const bak = await bakRes.json();
        if (data.success) {
            const s = data.storage;
            $('#storageInfo').html(`
                <div class="row g-3 mb-4">
                    <div class="col-md-3"><div class="stat-card-pro"><div class="stat-body"><div class="number">${s.used_gb||0} GB</div><div class="label">Utilisé</div></div></div></div>
                    <div class="col-md-3"><div class="stat-card-pro"><div class="stat-body"><div class="number">${s.free_gb||0} GB</div><div class="label">Libre</div></div></div></div>
                    <div class="col-md-3"><div class="stat-card-pro"><div class="stat-body"><div class="number">${s.uploads_mb||0} MB</div><div class="label">Uploads</div></div></div></div>
                    <div class="col-md-3"><div class="stat-card-pro"><div class="stat-body"><div class="number">${s.percent||0}%</div><div class="label">Occupation</div></div></div></div>
                </div>
                <div style="max-width:320px;margin:0 auto;height:220px;"><canvas id="storageChart"></canvas></div>`);
            if (storageChart) storageChart.destroy();
            storageChart = new Chart(document.getElementById('storageChart'), {
                type: 'doughnut',
                data: { labels: ['Utilisé', 'Libre'], datasets: [{ data: [s.used_gb||0, s.free_gb||0], backgroundColor: ['#0ea5e9','#e2e8f0'] }] },
                options: { responsive: true, maintainAspectRatio: false }
            });
        }
        const backups = bak.backups || [];
        $('#backupsTable tbody').html(backups.length ? backups.map(b => `<tr>
            <td>${escapeHtml(b.filename)}</td><td>${b.size_mb} MB</td><td>${(b.date||'').slice(0,16).replace('T',' ')}</td>
            <td class="text-end"><a class="btn btn-sm btn-outline-primary" href="/api/admin-global/backups/${encodeURIComponent(b.filename)}" download onclick="event.preventDefault(); downloadBackup('${escapeHtml(b.filename).replace(/'/g,"\\'")}')"><i class="fas fa-download"></i></a></td>
        </tr>`).join('') : '<tr><td colspan="4" class="text-center text-muted py-3">Aucune sauvegarde</td></tr>');
    } catch (e) { showToast('Erreur stockage', true); }
}
async function downloadBackup(filename) {
    const res = await fetch(`/api/admin-global/backups/${encodeURIComponent(filename)}`, { headers: authHeaders() });
    const blob = await res.blob();
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = filename; a.click();
}
async function manualBackup() {
    if (!confirm('Lancer une sauvegarde MySQL ?')) return;
    const res = await fetch('/api/admin-global/backup', { method: 'POST', headers: authHeaders() });
    const data = await res.json();
    showToast(data.success ? (data.message || 'Sauvegarde OK') : (data.message || 'Erreur'), !data.success);
    if (data.success) loadStorage();
    chargerNotifications();
}

async function loadSettings() {
    try {
        const res = await fetch('/api/admin-global/settings', { headers: authHeaders() });
        const data = await res.json();
        if (!data.success) return;
        const s = data.settings || {}, h = data.health || {};
        $('#maintenanceToggle').prop('checked', !!s.maintenance_mode);
        $('#maintenanceMessage').val(s.maintenance_message || '');
        $('#healthInfo').html(`
            <p><i class="fas fa-database me-1"></i> Base de données: <strong class="${h.database_ok?'text-success':'text-danger'}">${h.database_ok?'OK':'Erreur'}</strong> — ${escapeHtml(h.database_message||'')}</p>
            <p><i class="fas fa-file me-1"></i> Documents: ${h.total_documents||0} (${h.documents_ocr||0} avec OCR)</p>
            <p><i class="fas fa-hdd me-1"></i> Fichiers uploads: ${h.upload_files||0} (${h.upload_size_mb||0} MB)</p>
            <p><i class="fas fa-tag me-1"></i> Version: ${escapeHtml(s.version||'-')}</p>`);
        $('#platformConfigInfo').html(`
            <p>WhatsApp: <strong>${s.whatsapp_enabled?'Activé':'Désactivé'}</strong> — Provider: ${escapeHtml(s.whatsapp_provider)} — Configuré: ${s.whatsapp_configured?'Oui':'Non'}</p>
            <p>Email: ${s.mail_enabled?'Activé':'Désactivé'} — ${escapeHtml(s.mail_server||'-')}:${s.mail_port||''} — ${escapeHtml(s.mail_from||'')}</p>
            <p>URL: ${escapeHtml(s.app_base_url||'-')} — Préfixe tel: ${escapeHtml(s.phone_prefix||'-')} — Upload max: ${s.max_upload_mb||16} MB</p>`);
    } catch (e) { showToast('Erreur paramètres', true); }
}
async function saveMaintenance() {
    const res = await fetch('/api/admin-global/settings/maintenance', {
        method: 'PUT', headers: authHeaders(true),
        body: JSON.stringify({ maintenance_mode: $('#maintenanceToggle').is(':checked'), maintenance_message: $('#maintenanceMessage').val() }),
    });
    const data = await res.json();
    showToast(data.success ? 'Maintenance enregistrée' : (data.message || 'Erreur'), !data.success);
}
async function testWhatsapp() {
    const res = await fetch('/api/user/whatsapp/test', { method: 'POST', headers: authHeaders() });
    const data = await res.json();
    showToast(data.message || (data.success ? 'Test envoyé' : 'Échec'), !data.success);
}

function openProfileModal() { showModal('profileModal'); }
function openPasswordModal() { $('#newPasswordInput').val(''); showModal('passwordModal'); }
async function saveProfile() {
    const res = await fetch('/api/user/profile', {
        method: 'PUT', headers: authHeaders(true),
        body: JSON.stringify({ nom: $('#profileNom').val(), telephone: $('#profileTelephone').val(), notify_whatsapp: $('#profileNotifyWhatsapp').is(':checked') }),
    });
    const data = await res.json();
    if (res.ok) { showToast('Profil mis à jour'); hideModal('profileModal'); ensureAdminGlobalAccess(); }
    else showToast(data.message || 'Erreur', true);
}
async function savePassword() {
    const pwd = $('#newPasswordInput').val();
    if (!pwd || pwd.length < 6) { showToast('Min. 6 caractères', true); return; }
    const res = await fetch('/api/user/profile', { method: 'PUT', headers: authHeaders(true), body: JSON.stringify({ password: pwd }) });
    const data = await res.json();
    if (res.ok) { showToast('Mot de passe mis à jour'); hideModal('passwordModal'); }
    else showToast(data.message || 'Erreur', true);
}

function logout() { localStorage.clear(); window.location.href = '/login'; }

ensureAdminGlobalAccess().then(ok => {
    if (!ok) return;
    const params = new URLSearchParams(window.location.search);
    const tab = params.get('tab') || 'dashboard';
    showTab(tab);
    chargerNotifications();
    setInterval(() => { chargerNotifications(); if ($('#tabDashboard').is(':visible')) loadDashboard(true); }, 30000);
});
