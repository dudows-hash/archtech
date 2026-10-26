# Arch Tech Framework

Produto comercial de diagnostico de arquitetura com pipeline de agentes, Kanban, historico e publicacao no Notion.

## Execucao

```bash
pip install --break-system-packages -r requirements.txt
python app.py
```

A aplicacao sobe em `http://localhost:8000`.

## Configuracao Notion

Copie `.env.example` para `.env` e preencha:

```
NOTION_API_KEY=your-notion-api-key-here
NOTION_DATABASE_ID=your-notion-database-id-here
NOTION_PAGE_ID=your-notion-page-id-here
```

Use `NOTION_DATABASE_ID` para publicar em um banco, ou `NOTION_PAGE_ID` para criar a pagina filha de uma pagina existente. Sem as credenciais, o pipeline ainda conclui a analise e o botao **Publicar Relatorio no Notion** mostra o erro de configuracao.

## Testes

```bash
pytest -q
```
