"""
Servidor de verificación QR para Render.com
Lee datos desde Google Sheets
pip install flask gspread google-auth
"""
import os, json, base64
from flask import Flask, request, render_template_string, abort, redirect, url_for

SHEET_ID   = "1iWWsKn0Yas6uoBuhsIW-lBwUfodsoO0LDqqlyb1evNk"
HOJA       = "documentos_verificados"
BASE_URL   = "https://contabilapp-verificacion.onrender.com/verificar?codigo="
CRED_JSON  = os.environ.get("GOOGLE_CREDS_JSON", "")

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
header p{color:#6c7086;font-size:12px;margin-top:4px;}
.container{max-width:800px;margin:40px auto;padding:0 20px;}
.card{background:#1a1a2e;border-radius:14px;padding:32px;border:1px solid #313244;margin-bottom:20px;}
.card.ok{border-color:#a6e3a1;border-width:2px;}
.card.fail{border-color:#f38ba8;border-width:2px;}
input{width:100%;padding:12px;border-radius:8px;background:#252535;border:1px solid #45475a;
      color:#cdd6f4;font-size:15px;outline:none;margin-bottom:12px;}
button{background:#89b4fa;color:#1e1e2e;font-weight:700;border:none;border-radius:8px;
       padding:12px 28px;font-size:15px;cursor:pointer;}
button:hover{background:#b4befe;}
.badge-ok{background:#1a3a2a;color:#a6e3a1;padding:6px 16px;border-radius:20px;font-weight:bold;display:inline-block;margin-top:8px;}
.badge-no{background:#3a1a1a;color:#f38ba8;padding:6px 16px;border-radius:20px;font-weight:bold;display:inline-block;margin-top:8px;}
.row{display:flex;gap:8px;padding:10px 0;border-bottom:1px solid #313244;}
.row:last-child{border:none;}
.key{color:#89b4fa;font-weight:600;min-width:180px;font-size:13px;}
.val{color:#cdd6f4;word-break:break-all;font-size:14px;}
h2{color:#cdd6f4;font-size:18px;margin-bottom:8px;}
.icon{font-size:48px;margin-bottom:12px;display:block;}
a{color:#89b4fa;}
.hint{color:#6c7086;font-size:12px;margin-top:8px;}
</style></head>
<body>
<header>
  <h1>🔐 ContabilApp – Verificación de Documentos</h1>
  <p>Sistema de autenticidad de informes financieros</p>
</header>
<div class="container">
{% if doc %}
<div class="card {{ 'ok' if doc.ok else 'fail' }}">
  <span class="icon">{{ '✅' if doc.ok else '⚠️' }}</span>
  <h2>{{ 'Documento VÁLIDO y auténtico' if doc.ok else 'Documento no verificado' }}</h2>
  <span class="{{ 'badge-ok' if doc.ok else 'badge-no' }}">
    {{ '✔ VERIFICADO' if doc.ok else '⚠ PENDIENTE DE VERIFICACIÓN' }}
  </span>
  <div style="margin-top:24px;">
  {% for k,v in doc.fields.items() %}
  <div class="row"><span class="key">{{k}}</span><span class="val">{{v}}</span></div>
  {% endfor %}
  </div>
  <p style="margin-top:20px;"><a href="/">← Verificar otro documento</a></p>
</div>
{% elif codigo %}
<div class="card">
  <span class="icon">🔍</span>
  <h2 style="color:#f38ba8;">Documento no encontrado</h2>
  <p style="color:#a6adc8;">No se encontró ningún documento con el código:<br>
  <strong style="color:#89b4fa;">{{codigo}}</strong></p>
  <p style="margin-top:20px;"><a href="/">← Volver a buscar</a></p>
</div>
{% else %}
<div class="card">
  <h2 style="color:#89b4fa;margin-bottom:16px;">🔍 Verificar autenticidad de documento</h2>
  <p style="color:#a6adc8;margin-bottom:20px;font-size:14px;">
    Ingresa el código único del documento para verificar su autenticidad.
  </p>
  <form method="get" action="/verificar">
    <input name="codigo" placeholder="Ingresa el código del documento..." autofocus>
    <button type="submit">Verificar documento</button>
    <p class="hint">También puedes escanear el código QR del documento con tu celular</p>
  </form>
</div>
{% endif %}
</div></body></html>
"""

@app.route("/")
def index():
    from jinja2 import Template
    return Template(TMPL).render(doc=None, codigo=None)

@app.route("/verify/<codigo>")
def verify_old(codigo):
    """Ruta para QR viejos que usan /verify/CODIGO"""
    return redirect(url_for("verificar", codigo=codigo))

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
                    label = {
                        "codigo_unico":    "Código único",
                        "cliente_nombre":  "Cliente",
                        "cliente_nit":     "NIT / Identificación",
                        "tipo_documento":  "Tipo de documento",
                        "numero_documento":"Número de documento",
                        "fecha_emision":   "Fecha de emisión",
                        "verificacion":    "Estado de verificación",
                        "fecha_creacion":  "Fecha de registro",
                    }
                    fields = {}
                    for col, val in row.items():
                        if col in ("url_verificacion","qr_path","metadata","id"): continue
                        if val and str(val).strip():
                            lbl = label.get(col, col.replace("_"," ").title())
                            fields[lbl] = str(val)
                    doc = {"ok": is_ok, "fields": fields}
                    break
            if doc: break
    from jinja2 import Template
    return Template(TMPL).render(doc=doc, codigo=codigo)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5050)))


