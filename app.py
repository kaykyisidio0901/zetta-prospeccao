import csv
import io
import json
import os
import re
import sys
import time
import zipfile
import urllib.request
import urllib.parse
from functools import wraps
from flask import (Flask, render_template, request, jsonify, send_file,
                   send_from_directory, session, redirect, url_for)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

try:
    from ia_motor import gerar_funil_vendas
except Exception:
    gerar_funil_vendas = None

try:
    from whatsapp import gerar_link_whatsapp
except Exception:
    gerar_link_whatsapp = None

try:
    from replicas import gerar_replica
except Exception:
    gerar_replica = None

try:
    from scraper import raspar_google_maps
    SCRAPER_OK = True
except Exception:
    SCRAPER_OK = False


def _lazy_gerar_pdf_contrato(**kwargs):
    from contrato import gerar_pdf_contrato
    return gerar_pdf_contrato(**kwargs)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"),
            static_folder=os.path.join(BASE_DIR, "uploads"))
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24).hex())

ARQUIVO_DADOS = os.path.join(BASE_DIR, "dados_funnels.json")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def _sb_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _sb_get(table, params=""):
    url = f"{SUPABASE_URL}/rest/v1/{table}?{params}"
    req = urllib.request.Request(url, headers=_sb_headers())
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def _sb_insert(table, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers=_sb_headers(), method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def _sb_update(table, data, params):
    url = f"{SUPABASE_URL}/rest/v1/{table}?{params}"
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers=_sb_headers(), method="PATCH")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def _init_db():
    pass


@app.before_request
def _ensure_db():
    pass


@app.errorhandler(500)
def handle_500(e):
    import traceback
    return f"<pre>Erro 500:\n{traceback.format_exc()}</pre>", 500


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def _iniciais(nome):
    partes = nome.strip().split()
    if not partes:
        return "??"
    if len(partes) == 1:
        return partes[0][:2].upper()
    return (partes[0][0] + partes[-1][0]).upper()


def _ler_dados():
    if not os.path.exists(ARQUIVO_DADOS):
        return {"leads": [], "base_mensagens": {"msg1": "", "msg2": "", "msg3": ""}}
    with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
        dados = json.load(f)
    for l in dados.get("leads", []):
        l.setdefault("iniciais", _iniciais(l.get("nome", "")))
        l.setdefault("segmento", "")
        l.setdefault("msg1", "")
        l.setdefault("msg2", "")
        l.setdefault("msg3", "")
        l.setdefault("link", "")
        l.setdefault("status", "abordar")
        l.setdefault("site", "")
        l.setdefault("tem_site", False)
        l.setdefault("url_site", "")
        l.setdefault("telefone", "")
        l.setdefault("telefone_limpo", l["telefone"])
    return dados


def _salvar_dados(dados):
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


CONQUISTAS_METAS = [
    {"id": 1, "title": "5 MIL", "target": 5000, "display": "5K", "subtitle": "DE VENDAS"},
    {"id": 2, "title": "10 MIL", "target": 10000, "display": "10K", "subtitle": "DE VENDAS"},
    {"id": 3, "title": "20 MIL", "target": 20000, "display": "20K", "subtitle": "DE VENDAS"},
    {"id": 4, "title": "30 MIL", "target": 30000, "display": "30K", "subtitle": "DE VENDAS"},
    {"id": 5, "title": "50 MIL", "target": 50000, "display": "50K", "subtitle": "DE VENDAS"},
    {"id": 6, "title": "100 MIL", "target": 100000, "display": "100K", "subtitle": "DE VENDAS"},
    {"id": 7, "title": "1 MILHÃO", "target": 1000000, "display": "1 MILHÃO", "subtitle": "DE VENDAS", "big": True},
]


def _verificar_e_salvar_conquistas(dados, faturamento):
    conquistas = dados.get("conquistas", [])
    ids_salvos = {c["id"] for c in conquistas}
    for meta in CONQUISTAS_METAS:
        if meta["target"] <= faturamento and meta["id"] not in ids_salvos:
            conquistas.append({
                "id": meta["id"],
                "title": meta["title"],
                "target": meta["target"],
                "display": meta["display"],
                "subtitle": meta["subtitle"],
                "desbloqueada_em": time.strftime("%Y-%m-%d %H:%M:%S"),
            })
    dados["conquistas"] = conquistas
    return conquistas


def auto_detectar_coluna(colunas: list, palavras_chave: list) -> int:
    for i, col in enumerate(colunas):
        col_lower = col.lower().strip()
        for kw in palavras_chave:
            if kw in col_lower:
                return i
    return 0


def carregar_csv(arquivo):
    raw = arquivo.read()
    for enc in ("utf-8", "latin1", "cp1252"):
        try:
            text = raw.decode(enc)
            reader = csv.DictReader(io.StringIO(text))
            rows = list(reader)
            cols = reader.fieldnames or []
            return cols, rows
        except (UnicodeDecodeError, csv.Error):
            continue
    text = raw.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    return reader.fieldnames or [], list(reader)


def limpar_url(url: str) -> str:
    url = url.strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


# ─────────────────────────── AUTH ───────────────────────────


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    erro = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = None
        try:
            users = _sb_get("users", f"username=eq.{urllib.parse.quote(username)}&select=id,password")
            if users and len(users) > 0:
                user = users[0]
        except Exception as e:
            print(f"LOGIN ERROR: {e}", flush=True)
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = username
            return redirect(url_for("dashboard"))
        elif user:
            erro = "Senha inválida."
        else:
            erro = "Usuário não encontrado."
    return render_template("login.html", erro=erro)


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    erro = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or len(username) < 3:
            erro = "Usuário deve ter pelo menos 3 caracteres."
        elif not password or len(password) < 4:
            erro = "Senha deve ter pelo menos 4 caracteres."
        else:
            try:
                result = _sb_insert("users", {
                    "username": username,
                    "password": generate_password_hash(password, method='pbkdf2:sha256'),
                })
                user_id = result[0]["id"]
                _sb_insert("user_settings", {
                    "user_id": user_id,
                    "company_name": "",
                    "whatsapp_number": "",
                    "photo_path": "",
                })
                session["user_id"] = user_id
                session["username"] = username
                return redirect(url_for("dashboard"))
            except Exception:
                erro = "Usuário já existe."
    return render_template("register.html", erro=erro)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ─────────────────────────── SETTINGS ───────────────────────────


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    user_id = session["user_id"]
    try:
        rows = _sb_get("user_settings", f"user_id=eq.{user_id}&select=company_name,whatsapp_number,photo_path")
        s = rows[0] if rows else {}
    except Exception:
        s = {}

    erro = ""
    sucesso = ""
    if request.method == "POST":
        company_name = request.form.get("company_name", "").strip()
        whatsapp_number = re.sub(r"\D", "", request.form.get("whatsapp_number", ""))
        photo = request.files.get("photo")
        photo_path = s.get("photo_path", "")

        if photo and photo.filename:
            ext = secure_filename(photo.filename).rsplit(".", 1)[-1] if "." in photo.filename else "png"
            filename = f"user_{user_id}_photo.{ext}"
            dest = os.path.join(UPLOAD_FOLDER, filename)
            photo.save(dest)
            photo_path = f"/uploads/{filename}"

        _sb_update("user_settings", {
            "company_name": company_name,
            "whatsapp_number": whatsapp_number,
            "photo_path": photo_path,
        }, f"user_id=eq.{user_id}")

        s = {"company_name": company_name, "whatsapp_number": whatsapp_number, "photo_path": photo_path}
        sucesso = "Configurações salvas com sucesso."

    return render_template("settings.html", settings=s, erro=erro, sucesso=sucesso)


# ─────────────────────────── STRATEGY ───────────────────────────


@app.route("/strategy", methods=["GET", "POST"])
@login_required
def strategy():
    dados = _ler_dados()
    board = dados.get("strategy", {"colunas": [
        {"titulo": "Ideias", "cartoes": []},
        {"titulo": "Em Andamento", "cartoes": []},
        {"titulo": "Concluído", "cartoes": []},
    ]})

    if request.method == "POST":
        action = request.form.get("action", "")
        if action == "add_card":
            col_idx = int(request.form.get("col_idx", 0))
            titulo = request.form.get("titulo", "").strip()
            desc = request.form.get("descricao", "").strip()
            if titulo and 0 <= col_idx < len(board["colunas"]):
                board["colunas"][col_idx]["cartoes"].append({
                    "id": int(time.time() * 1000) if 'time' in dir() else len([c for col in board["colunas"] for c in col["cartoes"]]),
                    "titulo": titulo,
                    "descricao": desc,
                })
                dados["strategy"] = board
                _salvar_dados(dados)

        elif action == "add_column":
            titulo = request.form.get("titulo_coluna", "").strip()
            if titulo:
                board["colunas"].append({"titulo": titulo, "cartoes": []})
                dados["strategy"] = board
                _salvar_dados(dados)

        return redirect(url_for("strategy"))

    return render_template("strategy.html", board=board)


@app.route("/strategy/mover", methods=["POST"])
@login_required
def strategy_mover():
    data = request.get_json(force=True)
    card_id = data.get("card_id")
    destino_col = data.get("destino_col")
    dados = _ler_dados()
    board = dados.get("strategy", {"colunas": []})
    card = None
    for col in board["colunas"]:
        for c in col["cartoes"]:
            if c["id"] == card_id:
                card = c
                col["cartoes"].remove(c)
                break
        if card:
            break
    if card and 0 <= destino_col < len(board["colunas"]):
        board["colunas"][destino_col]["cartoes"].append(card)
        dados["strategy"] = board
        _salvar_dados(dados)
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 400


@app.route("/strategy/deletar", methods=["POST"])
@login_required
def strategy_deletar():
    data = request.get_json(force=True)
    card_id = data.get("card_id")
    dados = _ler_dados()
    board = dados.get("strategy", {"colunas": []})
    for col in board["colunas"]:
        for c in col["cartoes"]:
            if c["id"] == card_id:
                col["cartoes"].remove(c)
                dados["strategy"] = board
                _salvar_dados(dados)
                return jsonify({"ok": True})
    return jsonify({"ok": False}), 400


# ─────────────────────────── LEAD ROUTES ───────────────────────────


@app.route("/")
@login_required
def home():
    return redirect(url_for("dashboard"))


@app.route("/leads", methods=["GET", "POST"])
@login_required
def index():
    leads = []
    colunas = []
    mapeamento = {}
    stats = {"total": 0, "com_telefone": 0, "segmentos": 0, "com_site": 0}
    erro = None

    dados_json = _ler_dados()
    leads_json = dados_json.get("leads", [])

    if request.method == "POST":
        csv_file = request.files.get("csv_file")
        if not csv_file or not csv_file.filename.endswith(".csv"):
            erro = "Envie um arquivo CSV válido."
        else:
            colunas, rows = carregar_csv(csv_file)

            chaves_nome = ["nome", "name", "empresa", "business", "razao", "titulo", "title"]
            chaves_tel = ["telefone", "phone", "whatsapp", "celular", "contato", "tel", "fone"]
            chaves_seg = ["categoria", "category", "segmento", "segment", "tipo", "type", "ramo", "area"]
            chaves_site = ["site", "website", "url", "web", "pagina", "pagina_web"]

            col_nome = request.form.get("col_nome") or colunas[auto_detectar_coluna(colunas, chaves_nome)]
            col_telefone = request.form.get("col_telefone") or colunas[auto_detectar_coluna(colunas, chaves_tel)]
            col_segmento = request.form.get("col_segmento") or colunas[auto_detectar_coluna(colunas, chaves_seg)]
            col_site = colunas[auto_detectar_coluna(colunas, chaves_site)]

            mapeamento = {
                "colunas": colunas,
                "col_nome": col_nome,
                "col_telefone": col_telefone,
                "col_segmento": col_segmento,
                "col_site": col_site,
            }

            tem_coluna_site = col_site in colunas

            for row in rows:
                nome = str(row.get(col_nome, "")).strip() or "Sem nome"
                telefone = str(row.get(col_telefone, "")).strip()
                segmento = str(row.get(col_segmento, "")).strip() if col_segmento else "geral"
                if not segmento or segmento.lower() in ("", "nan", "none"):
                    segmento = "geral"
                if re.search(r'https?://|www\.|google\.com/maps', segmento, re.IGNORECASE):
                    segmento = "geral"

                if not telefone or telefone.lower() in ("", "nan", "none"):
                    continue

                msg1, msg2, msg3 = gerar_funil_vendas(nome, segmento)
                link_whats = gerar_link_whatsapp(telefone, msg1)
                iniciais = "".join(w[0] for w in nome.split()[:2]).upper()

                url_site = ""
                tem_site = False
                if tem_coluna_site:
                    raw_site = row.get(col_site, "")
                    if raw_site and raw_site.lower() not in ("", "nan", "none"):
                        raw_url = str(raw_site).strip()
                        cleaned = limpar_url(raw_url)
                    if cleaned and re.match(r"https?://[^\s/$.?#].[^\s]*", cleaned, re.IGNORECASE):
                        url_site = cleaned
                        tem_site = True

                from whatsapp import limpar_numero, garantir_codigo_pais
                telefone_limpo = garantir_codigo_pais(limpar_numero(telefone))

                leads.append({
                    "nome": nome,
                    "telefone": telefone,
                    "telefone_limpo": telefone_limpo,
                    "segmento": segmento,
                    "msg1": msg1,
                    "msg2": msg2,
                    "msg3": msg3,
                    "link": link_whats,
                    "iniciais": iniciais,
                    "tem_site": tem_site,
                    "url_site": url_site,
                })

            for l in leads:
                l["status"] = "abordar"

            dados = _ler_dados()
            existentes = dados.get("leads", [])
            dados["leads"] = existentes + leads
            _salvar_dados(dados)

            stats = {
                "total": len(leads),
                "com_telefone": len(leads),
                "segmentos": len(set(l["segmento"] for l in leads)),
                "com_site": sum(1 for l in leads if l["tem_site"]),
            }

    if not leads:
        leads = leads_json

    if leads:
        stats = {
            "total": len(leads),
            "com_telefone": sum(1 for l in leads if l.get("telefone")),
            "segmentos": len(set(l["segmento"] for l in leads if l.get("segmento"))),
            "com_site": sum(1 for l in leads if l.get("tem_site")),
        }
        limite_exibicao = min(len(leads), 10)
    else:
        limite_exibicao = 0

    return render_template(
        "index.html",
        leads=leads,
        colunas=colunas,
        mapeamento=mapeamento,
        stats=stats,
        erro=erro,
        limite_exibicao=limite_exibicao,
        username=session.get("username", ""),
    )


@app.route("/gerar_replica", methods=["POST"])
@login_required
def gerar_replica_route():
    data = request.get_json(force=True)
    nicho = data.get("nicho", "")
    etapa = data.get("etapa", "abordagem")
    resposta = data.get("resposta", "")
    reply = gerar_replica(nicho, etapa, resposta)
    return jsonify({"reply": reply})


# ─────────────────────────── CONTRACTS ───────────────────────────


@app.route("/contratos", methods=["GET", "POST"])
@login_required
def contratos():
    pdf_data = None
    dados = {}

    if request.method == "POST":
        dados = {
            "cliente_nome": request.form.get("cliente_nome", "").strip(),
            "cliente_doc": re.sub(r"\D", "", request.form.get("cliente_doc", "")),
            "valor_projeto": float(request.form.get("valor_projeto", 0) or 0),
            "valor_entrada": float(request.form.get("valor_entrada", 0) or 0),
            "prazo_dias": int(request.form.get("prazo_dias", 30) or 30),
        }

        if not dados["cliente_nome"] or not dados["cliente_doc"]:
            dados["erro"] = "Preencha todos os campos obrigatórios."
        elif dados["valor_projeto"] <= 0:
            dados["erro"] = "O valor do projeto deve ser maior que zero."
        else:
            dados_json = _ler_dados()
            if "contratos" not in dados_json:
                dados_json["contratos"] = []
            dados_json["contratos"].append({
                "cliente": dados["cliente_nome"],
                "doc": dados["cliente_doc"],
                "valor_projeto": dados["valor_projeto"],
                "valor_entrada": dados["valor_entrada"],
                "prazo_dias": dados["prazo_dias"],
            })
            _salvar_dados(dados_json)

            pdf = _lazy_gerar_pdf_contrato(
                cliente_nome=dados["cliente_nome"],
                cliente_doc=dados["cliente_doc"],
                valor_projeto=dados["valor_projeto"],
                valor_entrada=dados["valor_entrada"],
                prazo_dias=dados["prazo_dias"],
            )
            nome_arquivo = f"contrato_{dados['cliente_nome'].replace(' ', '_').lower()}.pdf"
            return send_file(
                pdf,
                mimetype="application/pdf",
                as_attachment=True,
                download_name=nome_arquivo,
            )

    return render_template("contratos.html", dados=dados, pdf_data=pdf_data, username=session.get("username", ""))


@app.route("/contratos/massa", methods=["POST"])
@login_required
def contratos_massa():
    data = request.get_json(force=True)
    raw = data.get("valor_projeto", 0)
    if isinstance(raw, str):
        valor_projeto = float(raw.replace(".", "").replace(",", "."))
    else:
        valor_projeto = float(raw or 0)
    valor_entrada = float(data.get("valor_entrada", 0) or 0)
    prazo_dias = int(data.get("prazo_dias", 30) or 30)

    if valor_projeto <= 0:
        return jsonify({"ok": False, "erro": "Valor do projeto deve ser maior que zero."}), 400

    dados_json = _ler_dados()
    leads_fechados = [l for l in dados_json.get("leads", []) if l.get("status") == "fechado"]

    if not leads_fechados:
        return jsonify({"ok": False, "erro": "Nenhum lead na coluna Contrato Fechado."}), 400

    if "contratos" not in dados_json:
        dados_json["contratos"] = []

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for lead in leads_fechados:
            nome = lead.get("nome", "Cliente")
            doc_placeholder = "00000000000"
            pdf = _lazy_gerar_pdf_contrato(
                cliente_nome=nome,
                cliente_doc=doc_placeholder,
                valor_projeto=valor_projeto,
                valor_entrada=valor_entrada,
                prazo_dias=prazo_dias,
            )
            dados_json["contratos"].append({
                "cliente": nome,
                "doc": doc_placeholder,
                "valor_projeto": valor_projeto,
                "valor_entrada": valor_entrada,
                "prazo_dias": prazo_dias,
            })
            nome_arquivo = f"contrato_{nome.replace(' ', '_').lower()}.pdf"
            zf.writestr(nome_arquivo, pdf.getvalue())

    _salvar_dados(dados_json)

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name="contratos_massa.zip",
    )


@app.route("/gerar_contrato_lead", methods=["POST"])
@login_required
def gerar_contrato_lead():
    data = request.get_json(force=True)
    cliente_nome = data.get("cliente_nome", "").strip()
    cliente_doc = re.sub(r"\D", "", data.get("cliente_doc", ""))
    raw = data.get("valor_projeto", 0)
    if isinstance(raw, str):
        valor_projeto = float(raw.replace(".", "").replace(",", "."))
    else:
        valor_projeto = float(raw or 0)
    tipo_contrato = data.get("tipo_contrato", "Site")

    if not cliente_nome or not cliente_doc:
        return jsonify({"ok": False, "erro": "Nome e CPF/CNPJ são obrigatórios."}), 400
    if valor_projeto <= 0:
        return jsonify({"ok": False, "erro": "Valor deve ser maior que zero."}), 400

    valor_entrada = round(valor_projeto * 0.5, 2)
    prazo_dias = 30

    dados_json = _ler_dados()
    if "contratos" not in dados_json:
        dados_json["contratos"] = []
    dados_json["contratos"].append({
        "cliente": cliente_nome,
        "doc": cliente_doc,
        "valor_projeto": valor_projeto,
        "valor_entrada": valor_entrada,
        "prazo_dias": prazo_dias,
        "tipo": tipo_contrato,
    })
    _salvar_dados(dados_json)

    pdf = _lazy_gerar_pdf_contrato(
        cliente_nome=cliente_nome,
        cliente_doc=cliente_doc,
        valor_projeto=valor_projeto,
        valor_entrada=valor_entrada,
        prazo_dias=prazo_dias,
    )
    nome_arquivo = f"contrato_{cliente_nome.replace(' ', '_').lower()}_{tipo_contrato.replace(' ', '_').lower()}.pdf"
    return send_file(
        pdf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=nome_arquivo,
    )


@app.route("/analytics", methods=["GET"])
@login_required
def analytics():
    dados_json = _ler_dados()
    contratos = dados_json.get("contratos", [])

    total_contratos = len(contratos)
    faturamento_bruto = sum(c["valor_projeto"] for c in contratos)
    caixa_atual = sum(c["valor_entrada"] for c in contratos)

    custo_operacional = faturamento_bruto * 0.05
    lucro_liquido = faturamento_bruto - custo_operacional
    ticket_medio = faturamento_bruto / total_contratos if total_contratos else 0

    return render_template(
        "analytics.html",
        total_contratos=total_contratos,
        faturamento_bruto=faturamento_bruto,
        caixa_atual=caixa_atual,
        lucro_liquido=lucro_liquido,
        ticket_medio=ticket_medio,
        custo_operacional=custo_operacional,
        dados_json=dados_json,
        username=session.get("username", ""),
    )


@app.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    dados = _ler_dados()
    leads = dados.get("leads", [])
    contratos = dados.get("contratos", [])

    total = len(leads)
    com_site = sum(1 for l in leads if l.get("tem_site"))
    sem_site = total - com_site
    abordagens = sum(1 for l in leads if l.get("status") != "abordar")
    fechados = sum(1 for l in leads if l.get("status") == "fechado")
    pct_site = round(com_site / total * 100) if total else 0
    pct_sem_site = 100 - pct_site
    faturamento = sum(c.get("valor_projeto", 0) for c in contratos)

    conquistas = _verificar_e_salvar_conquistas(dados, faturamento)
    _salvar_dados(dados)

    return render_template(
        "dashboard.html",
        total=total,
        com_site=com_site,
        sem_site=sem_site,
        abordagens=abordagens,
        fechados=fechados,
        pct_site=pct_site,
        pct_sem_site=pct_sem_site,
        faturamento=faturamento,
        conquistas_json=json.dumps(conquistas, ensure_ascii=False),
        username=session.get("username", ""),
    )


@app.route("/api/faturamento")
@login_required
def api_faturamento():
    dados = _ler_dados()
    contratos = dados.get("contratos", [])
    total = sum(c.get("valor_projeto", 0) for c in contratos)
    conquistas = _verificar_e_salvar_conquistas(dados, total)
    _salvar_dados(dados)
    return jsonify({"faturamento": total, "conquistas": conquistas})


@app.route("/automations", methods=["GET"])
@login_required
def automations():
    dados = _ler_dados()
    regras = dados.get("regras", {
        "filtro_premium": False,
        "alerta_followup": False,
        "contrato_automatico": False,
    })
    return render_template("automations.html", regras=regras, username=session.get("username", ""))


@app.route("/automations/salvar", methods=["POST"])
@login_required
def automations_salvar():
    data = request.get_json(force=True)
    dados = _ler_dados()
    dados["regras"] = {
        "filtro_premium": data.get("filtro_premium", False),
        "alerta_followup": data.get("alerta_followup", False),
        "contrato_automatico": data.get("contrato_automatico", False),
    }
    _salvar_dados(dados)
    return jsonify({"ok": True})


@app.route("/funnels", methods=["GET"])
@login_required
def funnels():
    dados = _ler_dados()
    leads = dados.get("leads", [])
    base_msg = dados.get("base_mensagens", {"msg1": "", "msg2": "", "msg3": ""})

    colunas = ["abordar", "conversa", "proposta", "reuniao", "fechado"]
    rotulos = {
        "abordar": "A Abordar",
        "conversa": "Em Conversa",
        "proposta": "Proposta Enviada",
        "reuniao": "Reunião / Fechamento",
        "fechado": "Contrato Fechado",
    }

    pipeline = {c: [l for l in leads if l.get("status") == c] for c in colunas}
    return render_template(
        "funnels.html",
        pipeline=pipeline,
        rotulos=rotulos,
        colunas=colunas,
        base_msg=base_msg,
        username=session.get("username", ""),
    )


@app.route("/funnels/mover", methods=["POST"])
@login_required
def funnels_mover():
    data = request.get_json(force=True)
    indice = data.get("indice")
    direcao = data.get("direcao", 1)
    colunas = ["abordar", "conversa", "proposta", "reuniao", "fechado"]

    dados = _ler_dados()
    leads = dados.get("leads", [])
    if 0 <= indice < len(leads):
        atual = leads[indice].get("status", "abordar")
        if atual in colunas:
            nova_pos = colunas.index(atual) + direcao
            if 0 <= nova_pos < len(colunas):
                leads[indice]["status"] = colunas[nova_pos]
                _salvar_dados(dados)
                return jsonify({"ok": True, "novo_status": colunas[nova_pos]})
    return jsonify({"ok": False}), 400


@app.route("/funnels/salvar_base", methods=["POST"])
@login_required
def funnels_salvar_base():
    data = request.get_json(force=True)
    dados = _ler_dados()
    dados["base_mensagens"] = {
        "msg1": data.get("msg1", ""),
        "msg2": data.get("msg2", ""),
        "msg3": data.get("msg3", ""),
    }
    _salvar_dados(dados)
    return jsonify({"ok": True})


@app.route("/limpar_leads", methods=["POST"])
@login_required
def limpar_leads():
    dados = _ler_dados()
    leads = dados.get("leads", [])
    dados["leads"] = [l for l in leads if l.get("status") not in ("abordar", "")]
    _salvar_dados(dados)
    return jsonify({"ok": True})


@app.route("/scraper", methods=["GET", "POST"])
@login_required
def scraper():
    leads_encontrados = []
    erro = None
    url = ""

    if request.method == "POST":
        if not SCRAPER_OK:
            erro = "Scraper indisponível no servidor. Use a importação de CSV."
        else:
            url = request.form.get("url_maps", "").strip()
            if not url:
                erro = "Cole um link do Google Maps."
            elif "google.com/maps" not in url and "maps.google" not in url:
                erro = "O link precisa ser uma busca do Google Maps."
            else:
                try:
                    leads_encontrados = raspar_google_maps(url, max_resultados=10)

                    if leads_encontrados:
                        dados = _ler_dados()
                        novos = []
                        for l in leads_encontrados:
                            nome = l["nome"]
                            segmento = "geral"
                            telefone = l["telefone"]

                            msg1, msg2, msg3 = gerar_funil_vendas(nome, segmento)

                            from whatsapp import limpar_numero, garantir_codigo_pais
                            telefone_limpo = garantir_codigo_pais(limpar_numero(telefone)) if telefone else ""
                            link_whats = gerar_link_whatsapp(telefone, msg1) if telefone else ""
                            iniciais = "".join(w[0] for w in nome.split()[:2]).upper()

                            url_site = l.get("site", "")
                            tem_site = bool(url_site)

                            novos.append({
                                "nome": nome,
                                "telefone": telefone,
                                "telefone_limpo": telefone_limpo,
                                "segmento": segmento,
                                "msg1": msg1,
                                "msg2": msg2,
                                "msg3": msg3,
                                "link": link_whats,
                                "iniciais": iniciais,
                                "tem_site": tem_site,
                                "url_site": url_site,
                                "status": "abordar",
                            })

                        dados["leads"] = novos + dados.get("leads", [])
                        _salvar_dados(dados)
                except Exception as e:
                    erro = f"Erro ao raspar: {str(e)}"

    return render_template(
        "scraper.html",
        url=url,
        leads=leads_encontrados,
        erro=erro,
        username=session.get("username", ""),
    )


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route("/plaque-component")
@login_required
def plaque_component():
    return send_from_directory(
        os.path.join(BASE_DIR, "templates"),
        "plaque_component.html",
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
