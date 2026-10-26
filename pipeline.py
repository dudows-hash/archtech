import threading
import time

import agents
import store
from config import PIPELINE_STEP_DELAY
from notion_integration import NotionConfigError, NotionPublishError, publicar_no_notion

STEPS = [
    ("product_architect", "prd", agents.product_architect, None),
    ("sai", "adr", agents.sai, "prd"),
    ("arch_copilot", "codigo", agents.arch_copilot, "adr"),
    ("data_review", "review", agents.data_review, "codigo"),
    ("supervisor", "checkpoint", agents.supervisor, "review"),
]

_running = set()
_lock = threading.Lock()


def _delay():
    if PIPELINE_STEP_DELAY and PIPELINE_STEP_DELAY > 0:
        time.sleep(PIPELINE_STEP_DELAY)


def run_pipeline(card_id, auto_publish=True):
    with _lock:
        if card_id in _running:
            return
        _running.add(card_id)
    try:
        card = store.get_card(card_id)
        if not card:
            return
        artifacts = dict(card.get("artifacts") or {})
        previous = None
        for column, artifact_key, producer, depends_on in STEPS:
            card = store.get_card(card_id)
            if not card:
                return
            arg = artifacts.get(depends_on) if depends_on else None
            content = producer(card) if depends_on is None else producer(card, arg)
            artifacts[artifact_key] = content
            previous = store.move_card(card_id, column, artifacts={artifact_key: content})
            _delay()

        notion_url = None
        notion_error = None
        if auto_publish:
            try:
                result = publicar_no_notion(previous or store.get_card(card_id))
                notion_url = result.get("url")
            except (NotionConfigError, NotionPublishError) as exc:
                notion_error = str(exc)
            except Exception as exc:
                notion_error = f"Falha inesperada na publicacao Notion: {exc}"

        store.complete_card(
            card_id,
            artifacts,
            notion_url=notion_url,
            notion_error=notion_error,
        )
    finally:
        with _lock:
            _running.discard(card_id)


def start_pipeline(card_id, auto_publish=True):
    thread = threading.Thread(
        target=run_pipeline,
        args=(card_id, auto_publish),
        daemon=True,
    )
    thread.start()
    return thread
