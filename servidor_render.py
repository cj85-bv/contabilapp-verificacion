"""
Servidor de verificación QR para Render.com
Lee datos + imágenes QR base64 desde Google Sheets
pip install flask gspread google-auth
"""
import os, json
from flask import Flask, request, redirect, url_for
from jinja2 import Template

SHEET_ID  = "1iWWsKn0Yas6uoBuhsIW-lBwUfodsoO0LDqqlyb1evNk"
HOJA      = "documentos_verificados"
CRED_JSON = os.environ.get("GOOGLE_CREDS_JSON", "")

app = Flask(__name__)
_cache = []

def get_data():
    global _cache
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        scopes = ["https://spreadsheets.google.com/feeds",
                  "https://www.googleapis.com/auth/drive"]
        creds  = Credentials.from_service_account_info(json.loads(CRED_JSON), scopes=scopes)
        gc     = gspread.authorize(creds)
        ws     = gc.open_by_key(SHEET_ID).worksheet(HOJA)
        _cache = ws.get_all_records()
        return _cache
    except Exception as e:
        print(f"Error Sheets: {e}")
        return _cache

TMPL = """
<!DOCTYPE html><html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Verificación – ContabilApp</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;font-family:'Segoe UI',sans-serif;}
body{background:#0f0f1a;color:#cdd6f4;min-height:100vh;}
header{background:#1a1a2e;padding:18px 28px;border-bottom:2px solid #313244;
       display:flex;align-items:center;gap:14px;}
header h1{color:#89b4fa;font-size:18px;font-weight:700;}
header p{color:#6c7086;font-size:11px;margin-top:3px;}
.container{max-width:700px;margin:32px auto;padding:0 16px;}
.card{background:#1a1a2e;border-radius:16px;padding:28px;
      border:1px solid #313244;margin-bottom:20px;}
.card.ok{border-color:#a6e3a1;border-width:2px;
         box-shadow:0 0 24px rgba(166,227,161,0.12);}
.card.fail{border-color:#f38ba8;border-width:2px;}
.status-bar{display:flex;align-items:center;gap:16px;margin-bottom:24px;
            padding:16px;border-radius:10px;}
.status-bar.ok{background:rgba(166,227,161,0.08);}
.status-bar.fail{background:rgba(243,139,168,0.08);}
.icon{font-size:44px;line-height:1;}
.status-title{font-size:18px;font-weight:700;margin-bottom:4px;}
.ok .status-title{color:#a6e3a1;}
.fail .status-title{color:#f38ba8;}
.badge{display:inline-block;padding:5px 14px;border-radius:20px;
       font-size:12px;font-weight:700;letter-spacing:.5px;}
.badge-ok{background:#1a3a2a;color:#a6e3a1;border:1px solid #a6e3a1;}
.badge-fail{background:#3a1a1a;color:#f38ba8;border:1px solid #f38ba8;}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:8px;}
@media(max-width:560px){.grid{grid-template-columns:1fr;}}
.info-panel{}
.row{padding:9px 0;border-bottom:1px solid #252535;}
.row:last-child{border:none;}
.key{color:#89b4fa;font-size:11px;font-weight:600;text-transform:uppercase;
     letter-spacing:.5px;margin-bottom:2px;}
.val{color:#cdd6f4;font-size:14px;word-break:break-all;}
.qr-panel{text-align:center;display:flex;flex-direction:column;
          align-items:center;justify-content:center;gap:10px;}
.qr-img{width:180px;height:180px;border-radius:12px;
        border:3px solid #89b4fa;object-fit:contain;
        background:#fff;padding:6px;}
.qr-caption{color:#6c7086;font-size:11px;}
.no-qr{width:180px;height:180px;border-radius:12px;border:2px dashed #45475a;
        display:flex;align-items:center;justify-content:center;
        color:#45475a;font-size:12px;text-align:center;padding:16px;}
input{width:100%;padding:13px 16px;border-radius:10px;background:#252535;
      border:1px solid #45475a;color:#cdd6f4;font-size:15px;outline:none;
      margin-bottom:14px;transition:border .2s;}
input:focus{border-color:#89b4fa;}
button{background:#89b4fa;color:#1e1e2e;font-weight:700;border:none;
       border-radius:10px;padding:13px 32px;font-size:15px;cursor:pointer;
       width:100%;transition:background .2s;}
button:hover{background:#b4befe;}
.back{display:inline-block;margin-top:20px;color:#89b4fa;
      text-decoration:none;font-size:13px;}
.back:hover{color:#b4befe;}
.hint{color:#6c7086;font-size:12px;margin-top:10px;text-align:center;}
.not-found{text-align:center;padding:20px 0;}
.not-found .icon{font-size:56px;margin-bottom:16px;display:block;}
.sello{margin-top:20px;padding:12px 16px;border-radius:8px;
       background:#252535;font-size:12px;color:#6c7086;text-align:center;}
</style>
</head>
<body>
<header>
  <span style="font-size:30px">🔐</span>
  <div>
    <h1>ContabilApp – Verificación de Documentos</h1>
    <p>Sistema de autenticidad de informes financieros · CB & Consultor</p>
  </div>
</header>
<div class="container">

{% if doc %}
<div class="card {{ 'ok' if doc.ok else 'fail' }}">
  <div class="status-bar {{ 'ok' if doc.ok else 'fail' }}">
    <span class="icon">{{ '✅' if doc.ok else '⚠️' }}</span>
    <div>
      <div class="status-title">
        {{ 'Documento VÁLIDO y auténtico' if doc.ok else 'Documento no verificado' }}
      </div>
      <span class="{{ 'badge badge-ok' if doc.ok else 'badge badge-fail' }}">
        {{ '✔ VERIFICADO' if doc.ok else '⚠ PENDIENTE DE VERIFICACIÓN' }}
      </span>
    </div>
  </div>

  <div class="grid">
    <div class="info-panel">
      {% for k,v in doc.fields.items() %}
      <div class="row">
        <div class="key">{{k}}</div>
        <div class="val">{{v}}</div>
      </div>
      {% endfor %}
    </div>
    <div class="qr-panel">
      {% if doc.qr_b64 %}
        <img class="qr-img" src="data:image/png;base64,{{doc.qr_b64}}" alt="Código QR">
        <span class="qr-caption">📱 Código QR del documento</span>
      {% else %}
        <div class="no-qr">Sin imagen QR disponible</div>
      {% endif %}
    </div>
  </div>

  <div class="sello">
    🏢 CB & Consultor · Sistema de Verificación Documental ·
    Este documento fue generado y certificado digitalmente
  </div>
</div>
<a href="/" class="back">← Verificar otro documento</a>

{% elif codigo %}
<div class="card">
  <div class="not-found">
    <span class="icon">🔍</span>
    <p style="color:#f38ba8;font-size:17px;font-weight:600;margin-bottom:8px;">
      Documento no encontrado</p>
    <p style="color:#a6adc8;font-size:14px;">
      No se encontró ningún documento con el código:<br>
      <strong style="color:#89b4fa;">{{codigo}}</strong>
    </p>
  </div>
  <a href="/" class="back" style="display:block;text-align:center;">← Volver a buscar</a>
</div>

{% else %}
<div class="card">
  <h2 style="color:#89b4fa;margin-bottom:8px;font-size:17px;">
    🔍 Verificar autenticidad de documento
  </h2>
  <p style="color:#a6adc8;margin-bottom:20px;font-size:14px;line-height:1.6;">
    Ingresa el código único del documento o escanea el código QR
    con tu celular para verificar su autenticidad.
  </p>
  <form method="get" action="/verificar">
    <input name="codigo" placeholder="Código del documento (ej: CC6663...)" autofocus>
    <button type="submit">🔍 Verificar documento</button>
    <p class="hint">Escanea el código QR del documento para verificación automática</p>
  </form>
</div>
{% endif %}

</div>
</body></html>
"""

@app.route("/")
def index():
    return Template(TMPL).render(doc=None, codigo=None)

@app.route("/verify/<codigo>")
def verify_old(codigo):
    return redirect(url_for("verificar", codigo=codigo))

@app.route("/verificar")
def verificar():
    codigo = request.args.get("codigo", "").strip()
    doc = None
    if codigo:
        rows = get_data()
        for row in rows:
            encontrado = any(codigo in str(v) or str(v).strip() == codigo
                           for v in row.values())
            if encontrado:
                # Estado — estado_texto siempre es VERIFICADO si viene del configurador
                estado = row.get("estado_texto", row.get("verificacion",
                         row.get("estado", "")))
                is_ok = str(estado).strip() in (
                    "1","True","true","verificado","válido","activo",
                    "VERIFICADO","Verificado","si","Sí","yes")

                # Imagen QR base64
                qr_b64 = row.get("qr_base64", "")
                if not qr_b64 or len(str(qr_b64)) < 50:
                    qr_b64 = None

                # Campos a mostrar
                ocultar = {"qr_base64","url_verificacion","estado_texto",
                           "qr_path","qr_ruta","metadata","id"}
                label = {
                    "codigo_unico":     "Código único",
                    "cliente_nombre":   "Cliente",
                    "cliente_nit":      "NIT / Identificación",
                    "tipo_documento":   "Tipo de documento",
                    "numero_documento": "Número de documento",
                    "fecha_emision":    "Fecha de emisión",
                    "verificacion":     "Estado",
                    "fecha_creacion":   "Fecha de registro",
                }
                fields = {}
                for col, val in row.items():
                    if col in ocultar: continue
                    if val and str(val).strip() and str(val) != "0":
                        lbl = label.get(col, col.replace("_"," ").title())
                        fields[lbl] = str(val)

                doc = {"ok": is_ok, "fields": fields, "qr_b64": qr_b64}
                break

    return Template(TMPL).render(doc=doc, codigo=codigo)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5050)))

