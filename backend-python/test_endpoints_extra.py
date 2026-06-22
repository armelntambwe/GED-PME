"""Tests complementaires : OCR, validation, partage, notifications."""
import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:5000"
TIMEOUT = 90


def req(method, path, token=None, data=None):
    hdrs = {"Content-Type": "application/json"}
    if token:
        hdrs["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    request = urllib.request.Request(BASE + path, data=body, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            ct = resp.headers.get("Content-Type", "")
            if "json" in ct:
                parsed = json.loads(raw) if raw else {}
            else:
                parsed = {"_bytes": len(raw), "_content_type": ct}
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


def login(email, password):
    s, d = req("POST", "/login", data={"email": email, "password": password})
    return d.get("token") if s == 200 and d.get("success") else None


def test(label, method, path, token, data=None, expect_ok=True):
    s, b = req(method, path, token=token, data=data)
    ok = (200 <= s < 300) if expect_ok else not (200 <= s < 300)
    mark = "PASS" if ok else "FAIL"
    msg = b.get("message") or b.get("error") or ""
    if not msg and isinstance(b, dict) and b.get("success"):
        msg = "OK"
    if not msg and b.get("_bytes"):
        msg = f"{b['_bytes']} bytes ({b.get('_content_type')})"
    print(f"  [{mark}] {label}: {method} {path} -> {s} | {msg}")
    return s, b


def main():
    print("=== Tests complementaires ===")
    pme = login("chef@pme.com", "admin123")
    emp = login("jean@entreprise.com", "employe123")

    s, docs = req("GET", "/documents?limit=10", emp)
    emp_docs = docs.get("documents", [])
    print(f"  Employe: {len(emp_docs)} document(s)")
    emp_doc = emp_docs[0]["id"] if emp_docs else None

    if emp_doc:
        test("OCR employe", "POST", f"/documents/{emp_doc}/ocr", emp)
        s_dl, dl = test("download", "GET", f"/documents/{emp_doc}/download", emp)
        test("versions", "GET", f"/documents/{emp_doc}/versions", emp)
        test("soumettre", "PUT", f"/documents/{emp_doc}/soumettre", emp, expect_ok=False)
        test("valider (apres soumission)", "PUT", f"/documents/{emp_doc}/valider", pme, expect_ok=False)

    doc_for_share = emp_doc or 62
    test("partager document", "POST", "/api/categories/partager", pme, {
        "email": "jean@entreprise.com", "document_id": doc_for_share
    })
    test("partager categorie", "POST", "/api/categories/1/partager", pme, {
        "email": "jean@entreprise.com"
    })

    s, n = req("GET", "/notifications/all", emp)
    notifs = n.get("notifications", [])
    if notifs:
        test("marquer notification lue", "PUT", f"/notifications/{notifs[0]['id']}/lire", emp)

    test("logs entreprise", "GET", "/api/entreprise/logs", pme)
    test("mes-documents", "GET", "/mes-documents", emp)
    test("admin employes GET", "GET", "/admin/employes", pme)
    test("historique doc PME", "GET", f"/api/pme/document/{doc_for_share}/historique", pme)

    print("=== Fin tests complementaires ===")


if __name__ == "__main__":
    main()
