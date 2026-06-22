"""Test complet endpoints GED-PME avec tokens admin_pme + employe."""
import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:5000"
TIMEOUT = 30


def req(method, path, token=None, data=None):
    hdrs = {"Content-Type": "application/json"}
    if token:
        hdrs["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    request = urllib.request.Request(BASE + path, data=body, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                parsed = {"_raw": raw[:300], "_content_type": resp.headers.get("Content-Type")}
            return resp.status, parsed
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = {"_raw": raw[:300]}
        return e.code, parsed
    except Exception as e:
        return 0, {"error": str(e)}


def login(email, password):
    s, d = req("POST", "/login", data={"email": email, "password": password})
    if 200 <= s < 300 and d.get("success"):
        return d["token"], d["user"]
    return None, None


def test(label, method, path, token, data=None, expect_ok=True):
    s, b = req(method, path, token=token, data=data)
    ok = (200 <= s < 300) if expect_ok else not (200 <= s < 300)
    mark = "PASS" if ok else "FAIL"
    detail = b.get("message") or b.get("error") or ""
    if not detail and isinstance(b, dict) and b.get("success") is True:
        detail = "OK"
    if not ok:
        detail = detail or str(b)[:150]
    print(f"  [{mark}] {label}: {method} {path} -> {s} | {detail}")
    return s, b


def main():
    print("=" * 70)
    print("GED-PME — Test complet endpoints")
    print("=" * 70)

    accounts = [
        ("chef@pme.com", "admin123", "admin_pme"),
        ("jean@entreprise.com", "employe123", "employe"),
        ("super@admin.com", "admin123", "admin_global"),
    ]

    tokens = {}
    for email, pwd, expected_role in accounts:
        t, u = login(email, pwd)
        if t:
            tokens[expected_role] = t
            print(f"  Login OK: {email} -> {u['role']} (entreprise_id={u.get('entreprise_id')})")
        else:
            print(f"  Login FAIL: {email}")

    pme = tokens.get("admin_pme")
    emp = tokens.get("employe")
    glob = tokens.get("admin_global")

    if not pme:
        print("\nERREUR: pas de token admin_pme — tests PME ignorés")
    else:
        print("\n--- API Admin PME ---")
        test("stats", "GET", "/api/pme/stats", pme)
        s, docs = test("documents", "GET", "/api/pme/documents?page=1&limit=5", pme)
        test("employes", "GET", "/api/pme/employes", pme)
        test("validation", "GET", "/api/pme/validation", pme)
        test("corbeille", "GET", "/api/pme/corbeille", pme)
        s_exp, exp = test("export CSV", "GET", "/api/pme/documents/export", pme)
        if s_exp == 200:
            print(f"         Export: {len(str(exp))} bytes reçus" if isinstance(exp, dict) and exp.get("_raw") else "         Export: fichier CSV reçu")

        doc_id = None
        if docs.get("documents"):
            doc_id = docs["documents"][0]["id"]

        print("\n--- Validation document (admin PME) ---")
        if doc_id:
            test("valider", "PUT", f"/documents/{doc_id}/valider", pme, expect_ok=False)
            test("rejeter sans motif", "PUT", f"/documents/{doc_id}/rejeter", pme, {}, expect_ok=False)

        print("\n--- Création employé ---")
        import time
        email_test = f"test.auto.{int(time.time())}@ged.local"
        s_emp, emp_created = test("create employe", "POST", "/admin/employes", pme, {
            "nom": "Test Auto",
            "email": email_test,
            "password": "test123456",
            "telephone": "0600000000"
        })
        if s_emp == 201:
            test("list employes after create", "GET", "/api/pme/employes", pme)

        print("\n--- Catégories PME ---")
        s, cats = test("list categories", "GET", "/categories", pme)
        s, cat = test("create category", "POST", "/categories", pme, {
            "nom": f"Cat Test {int(time.time())}",
            "description": "Test auto"
        })
        cat_id = cat.get("category_id")
        if cat_id and doc_id:
            test("deplacer document", "PUT", f"/documents/{doc_id}/categorie", pme, {"categorie_id": cat_id})
        if cat_id:
            test("delete empty category", "DELETE", f"/categories/{cat_id}", pme)

        print("\n--- Backup ---")
        test("backup", "POST", "/api/pme/backup", pme, expect_ok=False)

    if emp:
        print("\n--- Endpoints Employé ---")
        s, edocs = test("mes documents", "GET", "/documents?limit=5", emp)
        test("stats", "GET", "/documents/stats", emp)
        test("historique", "GET", "/documents/historique", emp)
        test("pending", "GET", "/documents/pending", emp)
        test("corbeille", "GET", "/documents/corbeille", emp)
        emp_doc = edocs.get("documents", [{}])[0].get("id") if edocs.get("documents") else None
        if emp_doc:
            test("contenu", "GET", f"/documents/{emp_doc}/contenu", emp)
            test("versions", "GET", f"/documents/{emp_doc}/versions", emp)
            test("ocr", "POST", f"/documents/{emp_doc}/ocr", emp, expect_ok=False)

    if glob:
        print("\n--- Admin Global (échantillon) ---")
        test("global stats", "GET", "/api/admin-global/stats", glob, expect_ok=False)

    print("\n--- Routes communes ---")
    tok = pme or emp or glob
    if tok:
        test("profile", "GET", "/api/user/profile", tok)
        test("notifications", "GET", "/notifications/all", tok)
        test("workflow config", "GET", "/api/workflow/config", pme or tok, expect_ok=bool(pme))

    print("\n" + "=" * 70)
    print("Fin des tests")
    print("=" * 70)


if __name__ == "__main__":
    main()
