"""
Servidor de verificación QR para Render.com
Lee datos desde Google Sheets (accesible desde la nube)
pip install flask gspread google-auth
"""
import os, json, base64
from flask import Flask, request, render_template_string, abort

SHEET_ID   = "1iWWsKn0Yas6uoBuhsIW-lBwUfodsoO0LDqqlyb1evNk"
HOJA       = "documentos_verificados"
BASE_URL   = "https://unentailed-mckenzie-unermined.ngrok-free.dev/verificar?codigo="
CRED_JSON  = os.environ.get("GOOGLE_CREDS_JSON", "")  # variable de entorno en Render

app = Flask(__name__)
_cache = []

def get_data():
    global _cache
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        scopes = ["https://spreadsheets.google.com/feeds",
                  "https://www.googleapis.com/auth/drive"]
        info   = json.loads(CRED_JSON)
        creds  = Credentials.from_service_account_info(info, scopes=scopes)
        gc     = gspread.authorize(creds)
        ws     = gc.open_by_key(SHEET_ID).worksheet(HOJA)
        _cache = ws.get_all_records()
        return _cache
    except Exception as e:
        print(f"Error Sheets: {e}")
        return _cache

TMPL = """
<!DOCTYPE html><html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Verificación – ContabilApp</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;font-family:'Segoe UI',sans-serif;}
body{background:#0f0f1a;color:#cdd6f4;min-height:100vh;}
header{background:#1a1a2e;padding:20px 32px;border-bottom:1px solid #313244;}
header h1{color:#89b4fa;font-size:20px;}
.container{max-width:800px;margin:40px auto;padding:0 20px;}
.card{background:#1a1a2e;border-radius:14px;padding:32px;border:1px solid #313244;margin-bottom:20px;}
input{width:100%;padding:12px;border-radius:8px;background:#252535;border:1px solid #45475a;
       color:#cdd6f4;font-size:15px;outline:none;}
button{background:#89b4fa;color:#1e1e2e;font-weight:700;border:none;border-radius:8px;
        padding:12px 28px;font-size:15px;cursor:pointer;margin-top:12px;}
.ok{border-color:#a6e3a1;} .fail{border-color:#f38ba8;}
.badge-ok{background:#1a3a2a;color:#a6e3a1;padding:6px 16px;border-radius:20px;font-weight:bold;}
.badge-no{background:#3a1a1a;color:#f38ba8;padding:6px 16px;border-radius:20px;font-weight:bold;}
.row{display:flex;gap:8px;padding:10px 0;border-bottom:1px solid #313244;}
.row:last-child{border:none;}
.key{color:#89b4fa;font-weight:600;min-width:160px;font-size:13px;}
.val{color:#cdd6f4;word-break:break-all;}
.qr{display:block;max-width:220px;margin:16px auto;border-radius:10px;border:3px solid #89b4fa;}
</style></head>
<body>
<header><h1>🔐 ContabilApp – Verificación de Documentos</h1></header>
<div class="container">
{% if doc %}
<div class="card {'ok' if doc.ok else 'fail'}">
  <div style="display:flex;align-items:center;gap:16px;margin-bottom:20px;">
    <span style="font-size:48px">{'✅' if doc.ok else '⚠️'}</span>
    <div>
      <h2 style="color:{'#a6e3a1' if doc.ok else '#f38ba8'}">
        {'Documento VÁLIDO y auténtico' if doc.ok else 'Documento no verificado'}
      </h2>
      <span class="{'badge-ok' if doc.ok else 'badge-no'}">
        {'✔ VERIFICADO' if doc.ok else '⚠ PENDIENTE'}
      </span>
    </div>
  </div>
  {% for k,v in doc.fields.items() %}
  <div class="row"><span class="key">{k}</span><span class="val">{v}</span></div>
  {% endfor %}
  <p style="margin-top:20px;"><a href="/" style="color:#89b4fa">← Verificar otro</a></p>
</div>
{% elif codigo %}
<div class="card"><p style="color:#f38ba8;font-size:18px;text-align:center;">
  ❌ No se encontró el documento: <strong>{codigo}</strong></p>
  <p style="text-align:center;margin-top:16px;"><a href="/" style="color:#89b4fa">← Volver</a></p>
</div>
{% else %}
<div class="card">
  <h2 style="color:#89b4fa;margin-bottom:16px;">🔍 Verificar documento</h2>
  <form method="get" action="/verificar">
    <input name="codigo" placeholder="Ingresa el código del documento..." autofocus>
    <br><button type="submit">Verificar</button>
  </form>
</div>
{% endif %}
</div></body></html>
"""

@app.route("/")
def index():
    from jinja2 import Template
    return Template(TMPL).render(doc=None, codigo=None)

@app.route("/verificar")
def verificar():
    codigo = request.args.get("codigo","").strip()
    doc    = None
    if codigo:
        rows = get_data()
        for row in rows:
            for k, v in row.items():
                if str(v).strip() == codigo.strip() or codigo in str(v):
                    est   = row.get("verificacion", row.get("estado",""))
                    is_ok = str(est).strip() in ("1","True","true","verificado","válido","activo")
                    fields = {}
                    label = {"codigo_unico":"Código único","cliente_nombre":"Cliente",
                              "cliente_nit":"NIT","tipo_documento":"Tipo documento",
                              "fecha_emision":"Fecha emisión","verificacion":"Estado"}
                    for col, val in row.items():
                        if col == "url_verificacion": continue
                        lbl = label.get(col, col)
                        if val: fields[lbl] = str(val)
                    doc = {"ok": is_ok, "fields": fields}
                    break
            if doc: break
    from jinja2 import Template
    return Template(TMPL).render(doc=doc, codigo=codigo)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5050)))
