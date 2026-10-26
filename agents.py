from datetime import datetime, timezone


def _today():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def product_architect(card):
    cliente = card.get("cliente") or "Cliente"
    titulo = card.get("titulo") or "Iniciativa"
    dor = card.get("dor") or "Nao informada"
    custo = card.get("custo") or "Nao informado"
    return (
        f"# PRD - {titulo}\n\n"
        f"**Cliente:** {cliente}\n"
        f"**Data:** {_today()}\n"
        f"**Custo da inacao:** {custo}\n\n"
        "## Problema\n"
        f"{dor}\n\n"
        "## Objetivo\n"
        f"Entregar um diagnostico acionavel para {cliente}, reduzindo o custo operacional "
        f"associado a '{titulo}'.\n\n"
        "## Escopo\n"
        "- Diagnostico da dor operacional\n"
        "- Arquitetura de solucao\n"
        "- Entrega tecnica inicial\n"
        "- Parecer de qualidade e checkpoint executivo\n\n"
        "## Criterios de sucesso\n"
        "- Relatorio completo gerado pelo pipeline Arch Tech\n"
        "- Aprovacao do Supervisor\n"
        "- Disponibilidade de publicacao no Notion\n"
    )


def sai(card, prd):
    cliente = card.get("cliente") or "Cliente"
    titulo = card.get("titulo") or "Iniciativa"
    return (
        f"# ADR - Arquitetura {titulo}\n\n"
        f"**Cliente:** {cliente}\n"
        f"**Contexto:** {prd.splitlines()[0] if prd else titulo}\n\n"
        "## Decisao\n"
        "Adotar uma arquitetura modular com pipeline de agentes (Product Architect, SAI, "
        "Arch Copilot, Data Review e Supervisor) orquestrado por um backend Flask e "
        "persistencia local do historico.\n\n"
        "## Componentes\n"
        "- Frontend Kanban + Historico\n"
        "- API REST para ingestao, pipeline e publicacao\n"
        "- Store em JSON para historico comercial\n"
        "- Integracao Notion via notion-client\n\n"
        "## Consequencias\n"
        "- Permite reset de estado entre analises\n"
        "- Mantem trilha auditavel por cliente\n"
        "- Publicacao opcional do relatorio final no Notion\n"
    )


def arch_copilot(card, adr):
    cliente = card.get("cliente") or "Cliente"
    slug = (card.get("titulo") or "solucao").lower().replace(" ", "_")[:40]
    return (
        f"# Solucao Tecnica - {card.get('titulo')}\n\n"
        f"**Cliente:** {cliente}\n"
        f"**Base:** ADR gerado pelo SAI\n\n"
        "```python\n"
        f"class {''.join(part.capitalize() for part in slug.split('_')[:3]) or 'Solution'}Service:\n"
        "    def __init__(self, cliente):\n"
        "        self.cliente = cliente\n\n"
        "    def diagnosticar(self, dor, custo):\n"
        "        return {\n"
        "            'cliente': self.cliente,\n"
        "            'dor': dor,\n"
        "            'custo': custo,\n"
        "            'status': 'pronto_para_review',\n"
        "        }\n"
        "```\n\n"
        "## Entregaveis\n"
        "- Servico de diagnostico versionado\n"
        "- Contrato de API para ingestao da dor\n"
        "- Hook de publicacao do relatorio\n"
    )


def data_review(card, codigo):
    cliente = card.get("cliente") or "Cliente"
    return (
        f"# Parecer de Qualidade - {card.get('titulo')}\n\n"
        f"**Cliente:** {cliente}\n\n"
        "## Checklist\n"
        "- [x] PRD cobre problema, objetivo e criterios de sucesso\n"
        "- [x] ADR descreve componentes e consequencias\n"
        "- [x] Codigo de referencia e executavel e testavel\n"
        "- [x] Dados do cliente presentes no relatorio\n\n"
        "## Risco residual\n"
        "Baixo. A solucao esta apta para checkpoint do Supervisor.\n\n"
        f"Trecho revisado: {codigo.splitlines()[0] if codigo else 'N/A'}\n"
    )


def supervisor(card, review):
    cliente = card.get("cliente") or "Cliente"
    return (
        f"# Checkpoint do Supervisor\n\n"
        f"**Cliente:** {cliente}\n"
        f"**Iniciativa:** {card.get('titulo')}\n"
        f"**Data:** {_today()}\n\n"
        "## Decisao\n"
        "APROVADO.\n\n"
        "## Fundamentacao\n"
        f"{review.split('## Risco residual')[-1].strip() if review else 'Qualidade suficiente.'}\n\n"
        "## Proximo passo\n"
        "Publicar o relatorio final no Notion e iniciar nova analise quando solicitado.\n"
    )
