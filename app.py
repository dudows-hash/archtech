from flask import Flask, jsonify, render_template, request

import store
from config import HOST, PORT, SECRET_KEY
from notion_integration import NotionConfigError, NotionPublishError, publicar_no_notion
from pipeline import start_pipeline

app = Flask(__name__)
app.secret_key = SECRET_KEY


def _error(message, status=400):
    return jsonify({"ok": False, "error": message}), status


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/landing")
def landing():
    return render_template("landing.html")


@app.get("/api/board")
def api_board():
    return jsonify({"ok": True, **store.snapshot()})


@app.get("/api/history")
def api_history():
    return jsonify({"ok": True, "history": store.list_history()})


@app.get("/api/cards/<card_id>")
def api_card(card_id):
    card = store.get_card(card_id)
    if not card:
        return _error("Card nao encontrado.", 404)
    return jsonify({"ok": True, "card": card})


@app.post("/api/analises")
def api_create_analise():
    payload = request.get_json(silent=True) or {}
    titulo = (payload.get("titulo") or "").strip()
    dor = (payload.get("dor") or "").strip()
    cliente = (payload.get("cliente") or "").strip()
    custo = payload.get("custo")
    if not titulo:
        return _error("Informe o titulo da analise.")
    if not dor:
        return _error("Informe a dor operacional.")
    if not cliente:
        return _error("Informe o nome do cliente.")
    if custo in (None, ""):
        return _error("Informe o custo da inacao.")
    card = store.create_card(titulo=titulo, dor=dor, custo=custo, cliente=cliente)
    start_pipeline(card["id"], auto_publish=True)
    return jsonify({"ok": True, "card": card, **store.snapshot()}), 201


@app.post("/api/reset")
def api_reset():
    return jsonify({"ok": True, **store.reset_board()})


@app.post("/api/cards/<card_id>/notion")
def api_publish_notion(card_id):
    card = store.get_card(card_id)
    if not card:
        return _error("Card nao encontrado.", 404)
    try:
        result = publicar_no_notion(card)
    except NotionConfigError as exc:
        store.update_card_notion(card_id, error=str(exc))
        return _error(str(exc), 400)
    except NotionPublishError as exc:
        store.update_card_notion(card_id, error=str(exc))
        return _error(str(exc), 502)
    except Exception as exc:
        message = f"Falha inesperada na publicacao Notion: {exc}"
        store.update_card_notion(card_id, error=message)
        return _error(message, 502)

    updated = store.update_card_notion(card_id, url=result["url"], error=None)
    return jsonify({"ok": True, "url": result["url"], "title": result["title"], "card": updated})


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=False, threaded=True)
