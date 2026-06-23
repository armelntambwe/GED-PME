import os


def save_company_logo(entreprise_id, file):
    if not file or not file.filename:
        return None
    upload_dir = os.path.join('static', 'uploads', 'logos')
    os.makedirs(upload_dir, exist_ok=True)
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ('.jpg', '.jpeg', '.png', '.webp', '.gif'):
        ext = '.jpg'
    filename = f"entreprise_{entreprise_id}{ext}"
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    return f'/static/uploads/logos/{filename}'
