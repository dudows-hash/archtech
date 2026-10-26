import re
from datetime import datetime, timezone

from config import NOTION_API_KEY, NOTION_DATABASE_ID, NOTION_PAGE_ID

SECTION_MAP = [
    ("prd", "Resumo Executivo (PRD do Product Architect)"),
    ("adr", "Arquitetura (ADR do SAI)"),
    ("codigo", "Solucao Tecnica (Codigo do Arch Copilot)"),
    ("review", "Parecer de Qualidade (Data Review)"),
    ("checkpoint", "Checkpoint (Supervisor)"),
]

INLINE_PATTERN = re.compile(
    r"(`[^`]+`|\*\*[^*]+\*\*|__[^_]+__|\*[^*]+\*|_[^_]+_|\[[^\]]+\]\([^)]+\))"
)


class NotionConfigError(Exception):
    pass


class NotionPublishError(Exception):
    pass


def _normalize_id(value):
    raw = (value or "").strip().replace("-", "")
    if len(raw) == 32:
        return f"{raw[0:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:32]}"
    return (value or "").strip()


def _text_chunk(content, bold=False, italic=False, code=False, href=None):
    piece = content if content else " "
    annotation = {"bold": bold, "italic": italic, "code": code}
    payload = {"type": "text", "text": {"content": piece}, "annotations": annotation}
    if href:
        payload["text"]["link"] = {"url": href}
    return payload


def _rich_text_from_markdown(text):
    if text is None:
        return [_text_chunk(" ")]
    source = str(text)
    if not source.strip():
        return [_text_chunk(" ")]
    chunks = []
    cursor = 0
    for match in INLINE_PATTERN.finditer(source):
        start, end = match.span()
        if start > cursor:
            chunks.append(_text_chunk(source[cursor:start]))
        token = match.group(0)
        if token.startswith("`") and token.endswith("`"):
            chunks.append(_text_chunk(token[1:-1], code=True))
        elif token.startswith("**") and token.endswith("**"):
            chunks.append(_text_chunk(token[2:-2], bold=True))
        elif token.startswith("__") and token.endswith("__"):
            chunks.append(_text_chunk(token[2:-2], bold=True))
        elif token.startswith("*") and token.endswith("*"):
            chunks.append(_text_chunk(token[1:-1], italic=True))
        elif token.startswith("_") and token.endswith("_"):
            chunks.append(_text_chunk(token[1:-1], italic=True))
        elif token.startswith("[") and "](" in token:
            label, href = token[1:-1].split("](", 1)
            chunks.append(_text_chunk(label, href=href))
        else:
            chunks.append(_text_chunk(token))
        cursor = end
    if cursor < len(source):
        chunks.append(_text_chunk(source[cursor:]))
    merged = []
    for chunk in chunks:
        content = chunk["text"]["content"]
        if not content:
            continue
        for start in range(0, len(content), 1800):
            piece = dict(chunk)
            piece["text"] = dict(chunk["text"])
            piece["text"]["content"] = content[start : start + 1800]
            piece["annotations"] = dict(chunk["annotations"])
            merged.append(piece)
    return merged or [_text_chunk(" ")]


def _block(block_type, text, extra=None):
    payload = {
        "object": "block",
        "type": block_type,
        block_type: {"rich_text": _rich_text_from_markdown(text)},
    }
    if extra:
        payload[block_type].update(extra)
    return payload


def _heading(text, level=2):
    key = f"heading_{level}"
    return _block(key, text)


def _paragraph(text):
    return _block("paragraph", text)


def _bullet(text):
    return _block("bulleted_list_item", text)


def _numbered(text):
    return _block("numbered_list_item", text)


def _quote(text):
    return _block("quote", text)


def _code(text, language="plain text"):
    return {
        "object": "block",
        "type": "code",
        "code": {
            "rich_text": [_text_chunk(text or " ")],
            "language": language or "plain text",
        },
    }


def _to_code_language(fence):
    language = (fence or "").strip().lower()
    allowed = {
        "python",
        "javascript",
        "typescript",
        "json",
        "bash",
        "shell",
        "html",
        "css",
        "sql",
        "yaml",
        "plain text",
        "markdown",
    }
    if language in ("js",):
        return "javascript"
    if language in ("ts",):
        return "typescript"
    if language in ("sh", "zsh"):
        return "shell"
    if language in allowed:
        return language
    return "plain text"


def markdown_to_notion_blocks(markdown):
    blocks = []
    if not markdown:
        return [_paragraph("Conteudo nao disponivel.")]
    lines = str(markdown).replace("\r\n", "\n").split("\n")
    in_code = False
    code_lang = "plain text"
    code_lines = []
    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_code:
                blocks.append(_code("\n".join(code_lines), code_lang))
                in_code = False
                code_lines = []
                code_lang = "plain text"
            else:
                in_code = True
                code_lang = _to_code_language(stripped[3:])
            continue
        if in_code:
            code_lines.append(raw)
            continue
        if not stripped:
            continue
        if stripped.startswith("### "):
            blocks.append(_heading(stripped[4:], 3))
            continue
        if stripped.startswith("## "):
            blocks.append(_heading(stripped[3:], 2))
            continue
        if stripped.startswith("# "):
            blocks.append(_heading(stripped[2:], 2))
            continue
        if re.match(r"^[-*+]\s+", stripped):
            blocks.append(_bullet(re.sub(r"^[-*+]\s+", "", stripped)))
            continue
        if re.match(r"^\d+\.\s+", stripped):
            blocks.append(_numbered(re.sub(r"^\d+\.\s+", "", stripped)))
            continue
        if stripped.startswith("> "):
            blocks.append(_quote(stripped[2:]))
            continue
        if stripped in ("---", "***"):
            blocks.append({"object": "block", "type": "divider", "divider": {}})
            continue
        if re.match(r"^- \[[ xX]\]\s+", stripped):
            checked = stripped[3].lower() == "x"
            text = re.sub(r"^- \[[ xX]\]\s+", "", stripped)
            blocks.append(
                {
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": _rich_text_from_markdown(text),
                        "checked": checked,
                    },
                }
            )
            continue
        blocks.append(_paragraph(stripped))
    if in_code:
        blocks.append(_code("\n".join(code_lines), code_lang))
    return blocks or [_paragraph("Conteudo nao disponivel.")]


def _resolve_title_property(client, db_id):
    retrieve = getattr(getattr(client, "databases", None), "retrieve", None)
    if not retrieve:
        return "title"
    try:
        database = retrieve(database_id=db_id)
        properties = database.get("properties") or {}
        for name, prop in properties.items():
            if (prop or {}).get("type") == "title":
                return name
    except Exception:
        return "title"
    return "title"


def _page_title(card):
    cliente = card.get("cliente") or "Cliente"
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"[Diagnostico] - {cliente} - {date_str}"


def _blocks_from_card(card):
    artifacts = card.get("artifacts") or {}
    blocks = [
        _paragraph(f"**Cliente:** {card.get('cliente') or '-'}"),
        _paragraph(f"**Titulo:** {card.get('titulo') or '-'}"),
        _paragraph(f"**Custo da inacao:** {card.get('custo') or '-'}"),
        _paragraph(f"**Dor:** {card.get('dor') or '-'}"),
    ]
    for key, heading in SECTION_MAP:
        blocks.append(_heading(heading, 2))
        content = artifacts.get(key) or "Conteudo nao disponivel."
        blocks.extend(markdown_to_notion_blocks(content))
    return blocks[:90]


def _parent_and_properties(client, db_id, page_id, title):
    if db_id:
        normalized_db = _normalize_id(db_id)
        title_property = _resolve_title_property(client, normalized_db)
        return {"database_id": normalized_db}, {
            title_property: {
                "title": [{"type": "text", "text": {"content": title}}],
            }
        }
    normalized_page = _normalize_id(page_id)
    return {"page_id": normalized_page}, {
        "title": {
            "title": [{"type": "text", "text": {"content": title}}],
        }
    }


def publicar_no_notion(
    dados_do_card,
    client=None,
    api_key=None,
    database_id=None,
    page_id=None,
):
    key = api_key if api_key is not None else NOTION_API_KEY
    db_id = database_id if database_id is not None else NOTION_DATABASE_ID
    parent_page = page_id if page_id is not None else NOTION_PAGE_ID

    if not key or not str(key).strip():
        raise NotionConfigError("NOTION_API_KEY ausente ou invalida.")
    if (not db_id or not str(db_id).strip()) and (not parent_page or not str(parent_page).strip()):
        raise NotionConfigError(
            "Informe NOTION_DATABASE_ID ou NOTION_PAGE_ID no arquivo .env."
        )

    if client is None:
        try:
            from notion_client import Client
        except ImportError as exc:
            raise NotionPublishError("Biblioteca notion-client nao instalada.") from exc
        client = Client(auth=key)

    title = _page_title(dados_do_card)
    parent, properties = _parent_and_properties(client, db_id, parent_page, title)
    try:
        page = client.pages.create(
            parent=parent,
            properties=properties,
            children=_blocks_from_card(dados_do_card),
        )
    except Exception as exc:
        message = str(exc)
        lowered = message.lower()
        if "unauthorized" in lowered or "invalid" in lowered or "401" in lowered:
            raise NotionPublishError(
                "Falha ao publicar no Notion: chave de API incorreta."
            ) from exc
        if "database" in lowered or "404" in lowered or "could not find" in lowered:
            target = "NOTION_DATABASE_ID" if db_id else "NOTION_PAGE_ID"
            raise NotionPublishError(
                f"Falha ao publicar no Notion: {target} incorreto."
            ) from exc
        raise NotionPublishError(f"Falha ao publicar no Notion: {message}") from exc

    url = page.get("url") if isinstance(page, dict) else None
    created_id = page.get("id") if isinstance(page, dict) else None
    if not url:
        raise NotionPublishError("Notion nao retornou a URL da pagina criada.")
    return {"id": created_id, "url": url, "title": title}
