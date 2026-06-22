"""Test systématique des endpoints GED-PME."""
import json
import sys
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:5000"

CREDENTIALS = [
    ("chef@pme.com", "admin123"),
    ("admin@ged-pme.com", "admin123"),
    ("jean@entreprise.com", "employe123"),
    ("jean@entreprise.com", "admin123"),
    ("super@admin.com", "admin123"),
]


def req(method, path, token=None, data=None, headers=None):
    url = BASE + path
    hdrs = {"Content-Type": "application/json"}
    if token:
        hdrs["Authorization"] = f"Bearer {token}"
    if headers:
        hdrs.update(headers)
    body = json.dumps(data).encode() if data is not None else None
    request = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(request, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                parsed = {"_raw": raw[:200]}
            return resp.status, parsed
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = {"_raw": raw[:200]}
        return e.code, parsed
    except Exception as e:
        return 0, {"error": str(e)}


def ok(status):
    return 200 <= status < 300


def login():
    for email, password in CREDENTIALS:
        status, data = req("POST", "/login", data={"email": email, "password": password})
        if ok(status) and data.get("success"):
            print(f"  Login OK: {email} ({data['user']['role']})")
            return data["token"], data["user"]
    return None, None


def test(name, method, path, token, data=None, expect_ok=True):
    status, body = req(method, path, token=token, data=data)
    success = ok(status) if expect_ok else (not ok(status))
    mark = "PASS" if success else "FAIL"
    msg = body.get("message") or body.get("error") or ""
    if not success and isinstance(body, dict):
        msg = msg or str(body)[:120]
    print(f"  [{mark}] {method} {path} -> {status} {msg}")
    return status, body


def main():
    print("=" * 60)
    print("GED-PME — Test des endpoints")
    print("=" * 60)

    # Pages statiques
    print("\n--- Pages HTML ---")
    for path in ["/", "/login", "/dashboard-pme", "/dashboard-employee"]:
        status, _ = req("GET", path)
        print(f"  [{'PASS' if status == 200 else 'FAIL'}] GET {path} -> {status}")

    print("\n--- Authentification ---")
    token, user = login()
    if not token:
        print("  [FAIL] Impossible de se connecter — arrêt des tests authentifiés")
        sys.exit(1)

    role = user["role"]
    pme_token = token
    emp_token = None

    # Second login employé si admin connecté
    if role != "employe":
        for email, password in CREDENTIALS:
            if email == "jean@entreprise.com":
                s, d = req("POST", "/login", data={"email": email, "password": password})
                if ok(s) and d.get("success"):
                    emp_token = d["token"]
                    break
    else:
        emp_token = token

    if role == "admin_pme":
        pme_token = token
    elif role != "admin_pme":
        for email, password in CREDENTIALS:
            s, d = req("POST", "/login", data={"email": "chef@pme.com", "password": password})
            if ok(s) and d.get("success") and d["user"]["role"] == "admin_pme":
                pme_token = d["token"]
                break

    print("\n--- API Admin PME ---")
    test("stats", "GET", "/api/pme/stats", pme_token)
    test("documents", "GET", "/api/pme/documents?page=1&limit=5", pme_token)
    test("employes", "GET", "/api/pme/employes", pme_token)
    test("validation", "GET", "/api/pme/validation", pme_token)
    test("corbeille", "GET", "/api/pme/corbeille", pme_token)
    test("export", "GET", "/api/pme/documents/export", pme_token)

    print("\n--- Catégories ---")
    s, cats = test("list", "GET", "/categories", pme_token)
    cat_id = None
    if ok(s) and cats.get("categories"):
        cat_id = cats["categories"][0]["id"]

    s, created = test("create", "POST", "/categories", pme_token, {
        "nom": "Test Auto API",
        "description": "Créée par test_endpoints.py"
    })
    new_cat_id = created.get("category_id")
    if new_cat_id:
        test("update", "PUT", f"/categories/{new_cat_id}", pme_token, {
            "nom": "Test Auto API Modifiée",
            "description": "Mise à jour OK"
        })

    print("\n--- Documents (app.py) ---")
    s, docs = test("list", "GET", "/documents?limit=5", pme_token)
    doc_id = None
    if ok(s) and docs.get("documents"):
        doc_id = docs["documents"][0]["id"]
        test("by_id", "GET", f"/documents/{doc_id}", pme_token)
        test("contenu", "GET", f"/documents/{doc_id}/contenu", pme_token)
        if cat_id:
            test("by_categorie", "GET", f"/documents/categorie/{cat_id}", pme_token)
        test("versions", "GET", f"/documents/{doc_id}/versions", pme_token)
        test("historique", "GET", "/documents/historique", pme_token)
        test("stats", "GET", "/documents/stats", pme_token)
        test("ocr", "POST", f"/documents/{doc_id}/ocr", pme_token, expect_ok=False)

    print("\n--- Profil / Entreprise ---")
    test("profile", "GET", "/api/user/profile", pme_token)
    test("entreprise", "GET", "/api/entreprise/info", pme_token)

    print("\n--- Notifications ---")
    test("notifs", "GET", "/notifications/all", pme_token)
    test("count", "GET", "/notifications/count", pme_token)

    print("\n--- Employé (si token disponible) ---")
    if emp_token:
        test("docs emp", "GET", "/documents?limit=3", emp_token)
        test("stats emp", "GET", "/documents/stats", emp_token)
        test("historique emp", "GET", "/documents/historique", emp_token)
        if doc_id:
            test("ocr emp", "POST", f"/documents/{doc_id}/ocr", emp_token, expect_ok=False)
    else:
        print("  [SKIP] Token employé non disponible")

    print("\n--- Backup (peut échouer sans mysqldump) ---")
    test("backup", "POST", "/api/pme/backup", pme_token, expect_ok=False)

    # Cleanup test category
    if new_cat_id:
        test("delete cat", "DELETE", f"/categories/{new_cat_id}", pme_token)

    print("\n" + "=" * 60)
    print("Tests terminés")
    print("=" * 60)


if __name__ == "__main__":
    main()
