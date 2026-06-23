/**
 * GED-PME — Aperçu multi-formats (PDF, images, texte, vidéo, DOCX…)
 */
(function (global) {
    'use strict';

    const PREVIEW_IMAGE_EXT = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg', 'ico', 'tif', 'tiff'];
    const PREVIEW_TEXT_EXT = ['txt', 'md', 'csv', 'json', 'xml', 'html', 'htm', 'css', 'js', 'py', 'sql', 'log', 'yaml', 'yml', 'ini', 'cfg', 'rtf'];
    const PREVIEW_VIDEO_EXT = ['mp4', 'webm', 'ogg', 'mov', 'avi'];
    const PREVIEW_AUDIO_EXT = ['mp3', 'wav', 'ogg', 'aac', 'm4a', 'flac'];

    const MIME_BY_EXT = {
        pdf: 'application/pdf',
        doc: 'application/msword',
        docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        xls: 'application/vnd.ms-excel',
        xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        ppt: 'application/vnd.ms-powerpoint',
        pptx: 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        txt: 'text/plain',
        md: 'text/markdown',
        csv: 'text/csv',
        json: 'application/json',
        xml: 'application/xml',
        html: 'text/html',
        htm: 'text/html',
        jpg: 'image/jpeg',
        jpeg: 'image/jpeg',
        png: 'image/png',
        gif: 'image/gif',
        webp: 'image/webp',
        mp4: 'video/mp4',
        mp3: 'audio/mpeg',
        wav: 'audio/wav',
        zip: 'application/zip',
    };

    let _token = '';
    let _apiBase = '';

    function init(config) {
        _token = config.token || '';
        _apiBase = (config.apiBase || global.location.origin).replace(/\/$/, '');
    }

    function authHeaders() {
        return { Authorization: 'Bearer ' + _token };
    }

    function fileExtension(filename) {
        return (filename || '').split('.').pop().toLowerCase();
    }

    function inferMime(filename, mime) {
        const ext = fileExtension(filename);
        if (mime && !['application/octet-stream', 'binary/octet-stream', ''].includes(mime)) return mime;
        return MIME_BY_EXT[ext] || mime || 'application/octet-stream';
    }

    function formatSize(bytes) {
        if (!bytes) return '-';
        if (bytes < 1024) return bytes + ' o';
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' Ko';
        return (bytes / 1048576).toFixed(1) + ' Mo';
    }

    function getFileIcon(ext) {
        const m = {
            pdf: 'fa-file-pdf text-danger',
            doc: 'fa-file-word text-primary',
            docx: 'fa-file-word text-primary',
            xls: 'fa-file-excel text-success',
            xlsx: 'fa-file-excel text-success',
            ppt: 'fa-file-powerpoint text-warning',
            pptx: 'fa-file-powerpoint text-warning',
            jpg: 'fa-file-image text-info',
            jpeg: 'fa-file-image text-info',
            png: 'fa-file-image text-info',
            gif: 'fa-file-image text-info',
            mp4: 'fa-file-video text-purple',
            mp3: 'fa-file-audio text-secondary',
            zip: 'fa-file-archive text-muted',
        };
        return m[ext] || 'fa-file-alt text-muted';
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str).replace(/[&<>"]/g, function (m) {
            if (m === '&') return '&amp;';
            if (m === '<') return '&lt;';
            if (m === '>') return '&gt;';
            if (m === '"') return '&quot;';
            return m;
        });
    }

    async function fetchBlob(docId, hintFilename) {
        const tryFetch = async (kind) => {
            const res = await fetch(`${_apiBase}/documents/${docId}/${kind}`, { headers: authHeaders() });
            if (!res.ok) return null;
            const ct = (res.headers.get('Content-Type') || '').toLowerCase();
            if (ct.includes('application/json')) return null;
            const blob = await res.blob();
            if (!blob || blob.size === 0) return null;
            let filename = hintFilename || 'document';
            const disp = res.headers.get('Content-Disposition');
            if (disp) {
                const m = disp.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                if (m) filename = decodeURIComponent(m[1].replace(/['"]/g, ''));
            }
            const mime = inferMime(filename, res.headers.get('Content-Type') || blob.type);
            return { blob, filename, mime };
        };

        const fromPreview = await tryFetch('preview');
        if (fromPreview) return fromPreview;
        const fromDownload = await tryFetch('download');
        if (fromDownload) return fromDownload;
        throw new Error('Fichier inaccessible');
    }

    async function buildPreview(blob, mime, filename, doc, onDownload) {
        const ext = fileExtension(filename);
        const blobUrl = URL.createObjectURL(blob);
        const resolvedMime = inferMime(filename, mime);
        const downloadFn = onDownload || '';

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
        if (ext === 'docx' && global.mammoth) {
            try {
                const arrayBuffer = await blob.arrayBuffer();
                const result = await global.mammoth.convertToHtml({ arrayBuffer });
                return `<div class="docx-preview border rounded p-3 bg-white" style="max-height:480px;overflow:auto;">${result.value || '<p class="text-muted">Document vide</p>'}</div>`;
            } catch (e) { /* fallthrough */ }
        }
        if ((ext === 'xlsx' || ext === 'xls') && global.XLSX) {
            try {
                const arrayBuffer = await blob.arrayBuffer();
                const wb = global.XLSX.read(arrayBuffer, { type: 'array' });
                const sheetName = wb.SheetNames[0];
                if (sheetName) {
                    const html = global.XLSX.utils.sheet_to_html(wb.Sheets[sheetName], { id: 'ged-xlsx-preview' });
                    return `<div class="xlsx-preview border rounded p-2 bg-white" style="max-height:480px;overflow:auto;">${html}</div>`;
                }
            } catch (e) { /* fallthrough */ }
        }
        if (ext === 'csv') {
            try {
                const text = await blob.text();
                const rows = text.split(/\r?\n/).filter(Boolean).slice(0, 200);
                const table = rows.map(row => {
                    const cells = row.split(/[,;|\t]/).map(c => `<td>${escapeHtml(c.trim())}</td>`).join('');
                    return `<tr>${cells}</tr>`;
                }).join('');
                return `<div class="border rounded bg-white" style="max-height:480px;overflow:auto;"><table class="table table-sm table-bordered mb-0">${table}</table></div>`;
            } catch (e) { /* fallthrough */ }
        }
        if (ext === 'svg' || ext === 'htm' || ext === 'html') {
            return `<iframe src="${blobUrl}" class="w-100 border rounded" style="height:480px"></iframe>`;
        }

        const icon = getFileIcon(ext);
        let ocrBlock = '';
        if (doc && doc.contenu_ocr) {
            ocrBlock = `<hr><p class="small fw-semibold text-start"><i class="fas fa-font me-1"></i>Texte extrait (OCR)</p><pre class="ocr-text text-start small mb-0" style="max-height:200px;overflow:auto;">${escapeHtml(String(doc.contenu_ocr).substring(0, 5000))}</pre>`;
        }
        const dlBtn = downloadFn
            ? `<button type="button" class="btn btn-sm btn-primary" onclick="${downloadFn}"><i class="fas fa-download me-1"></i>Télécharger pour ouvrir</button>`
            : '';

        return `<div class="text-center py-4 border rounded bg-light">
            <i class="fas ${icon} fa-4x mb-3"></i>
            <p class="fw-semibold mb-1">${escapeHtml(filename)}</p>
            <p class="text-muted small">${escapeHtml(resolvedMime || ext.toUpperCase())} · ${formatSize(blob.size)}</p>
            <p class="small text-muted">Aperçu non disponible pour ce format (${escapeHtml(ext.toUpperCase() || 'inconnu')}). Téléchargez le fichier pour l'ouvrir.</p>
            ${dlBtn}
            ${ocrBlock}
        </div>`;
    }

    global.GedDocPreview = {
        init,
        fetchBlob,
        buildPreview,
        formatSize,
        fileExtension,
        inferMime,
        getFileIcon,
        escapeHtml,
    };
})(typeof window !== 'undefined' ? window : globalThis);
