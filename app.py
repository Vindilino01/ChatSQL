"""Chat SQL - interface Streamlit.

Uma fonte de dados ativa por vez. O SQL gerado e sempre exibido antes da
execucao. O Motor Offline e o padrao; um Provedor de IA e opcional.
"""

from __future__ import annotations

import html
import os
import re
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from chat_sql.config import (
    DEFAULT_PROVIDER,
    DISPLAY_ROWS,
    OFFLINE_PROVIDER,
    PROVIDER_PRESETS,
    SAMPLE_ROWS_DEFAULT,
    SAMPLE_ROWS_MAX,
    SAMPLE_ROWS_MIN,
)
from chat_sql import store
from chat_sql.engine import InMemoryDatabase, QueryError
from chat_sql.nl.engine import suggest_questions
from chat_sql.offline import OfflineEngine
from chat_sql.pipeline import ChatSession
from chat_sql.prompt import build_fewshots
from chat_sql.provider import OpenAICompatibleProvider, ProviderError
from chat_sql.sample_data import generate_sample_data
from chat_sql.schema import Schema, SchemaError, parse_schema
from chat_sql.spreadsheet import read_tables, tables_to_data, tables_to_schema

load_dotenv()

SCHEMAS_DIR = Path(__file__).parent / "schemas"
EXAMPLE_SCHEMAS = ["e-commerce", "rh", "vendas"]
PRESET_LABELS = [OFFLINE_PROVIDER, *PROVIDER_PRESETS]

SOURCE_SPREADSHEET = "Planilhas (CSV/Excel)"
SOURCE_SCRIPT = "Script SQL (CREATE + INSERT)"
SOURCE_EXAMPLE = "Schema de exemplo"

MAX_TURNS = 20

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', system-ui, sans-serif; }

.stApp {
  background:
    radial-gradient(1100px 550px at 8% -8%, rgba(99,102,241,0.22), transparent 60%),
    radial-gradient(900px 500px at 100% 0%, rgba(14,165,233,0.14), transparent 55%),
    #0b0d14;
}

section[data-testid="stSidebar"] {
  background: rgba(15,18,30,0.92);
  border-right: 1px solid rgba(255,255,255,0.07);
}

.chs-brand { font-size: 24px; font-weight: 800; letter-spacing: -0.02em;
  background: linear-gradient(120deg,#a5b4fc,#6366f1 40%,#22d3ee);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.chs-brand-sub { color: #8b93a7; font-size: 12.5px; margin-top: 2px; }

.chs-title { font-size: 34px; font-weight: 800; letter-spacing: -0.03em; margin-bottom: 0;
  background: linear-gradient(120deg,#e6e8ef,#a5b4fc 55%,#22d3ee);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.chs-sub { color: #8b93a7; font-size: 14px; margin-top: 4px; margin-bottom: 18px; }

.chs-card { background: rgba(255,255,255,0.035); border: 1px solid rgba(255,255,255,0.09);
  border-radius: 16px; padding: 14px 16px; margin-bottom: 12px; }
.chs-label { color: #8b93a7; font-size: 11px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.08em; margin-bottom: 6px; }
.chs-value { color: #e6e8ef; font-size: 15px; font-weight: 600; }

.chs-badge { display: inline-block; padding: 3px 11px; border-radius: 999px; font-size: 12px;
  font-weight: 600; background: rgba(99,102,241,0.18); color: #a5b4fc;
  border: 1px solid rgba(99,102,241,0.38); }
.chs-chip { display: flex; justify-content: space-between; align-items: center; gap: 8px;
  background: rgba(255,255,255,0.035); border: 1px solid rgba(255,255,255,0.07);
  border-radius: 10px; padding: 7px 11px; margin-bottom: 6px; font-size: 13px; color: #cfd4e2; }
.chs-chip span { color: #8b93a7; font-variant-numeric: tabular-nums; }

.chs-source-line { display: flex; align-items: center; gap: 8px; color: #8b93a7;
  font-size: 13px; margin-bottom: 10px; }

.chs-user { background: linear-gradient(135deg,#6366f1,#4f46e5); color: #fff;
  padding: 12px 16px; border-radius: 16px 16px 4px 16px; margin: 10px 0 8px auto;
  max-width: 78%; width: fit-content; font-weight: 500; box-shadow: 0 8px 24px rgba(79,70,229,0.28); }

.chs-answer { color: #8b93a7; font-size: 12px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.08em; margin: 6px 0; }

div[data-testid="stMetric"] { background: rgba(255,255,255,0.035);
  border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 10px 14px; }
div[data-testid="stMetricValue"] { font-size: 22px; }

.stButton > button { border-radius: 10px; font-weight: 600; }
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg,#6366f1,#4f46e5); border: none; }
.stButton > button[kind="primary"]:hover { filter: brightness(1.1); }

div[data-testid="stCodeBlock"] { border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); }
div[data-testid="stCodeBlock"] code, .stCode code { font-family: 'JetBrains Mono', monospace !important; }

.stTabs [data-baseweb="tab-list"] { gap: 6px; }
.stTabs [data-baseweb="tab"] { border-radius: 10px; padding: 6px 14px; }
.stTabs [aria-selected="true"] { background: rgba(99,102,241,0.16); }
</style>
"""


def _default_api_key() -> str:
    value = os.getenv("CHATSQL_API_KEY", "")
    if value:
        return value
    try:
        return st.secrets.get("CHATSQL_API_KEY", "")
    except Exception:
        return ""


def _init_state() -> None:
    if "api_key" not in st.session_state:
        st.session_state.api_key = _default_api_key()
    defaults = {
        "provider_name": DEFAULT_PROVIDER,
        "base_url": "",
        "model": "",
        "sample_rows": SAMPLE_ROWS_DEFAULT,
        "schema": None,
        "data": None,
        "database": None,
        "fewshots": [],
        "provider": None,
        "chat": None,
        "source_label": None,
        "source_id": None,
        "turns": [],
        "recent": [],
        "pending_question": None,
        "example_preset": "e-commerce",
        "source_mode": SOURCE_SPREADSHEET,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _build_provider():
    if st.session_state.provider_name == OFFLINE_PROVIDER:
        return OfflineEngine()
    preset = PROVIDER_PRESETS[st.session_state.provider_name]
    api_key = st.session_state.api_key
    if preset.requires_key and not api_key:
        return None
    return OpenAICompatibleProvider(
        api_key=api_key,
        base_url=st.session_state.base_url or preset.base_url,
        model=st.session_state.model or preset.default_model,
    )


def _fewshots_for(schema: Schema, provider) -> list[tuple[str, str]]:
    if provider is None or getattr(provider, "offline", False):
        return build_fewshots(schema, None)
    return build_fewshots(schema, provider)


def _flash(kind: str, message: str) -> None:
    st.session_state.flash = {"kind": kind, "message": message}


@st.cache_data(show_spinner=False)
def _build_payload(source_id: str) -> dict | None:
    """Monta schema e dados a partir da fonte salva em disco. Fica em cache
    (sobrevive a reloads); o banco em memoria e recriado por sessao."""
    meta = store.read_source(source_id)
    if meta is None:
        return None
    kind = meta.get("kind")
    label = meta.get("label")
    if kind == "spreadsheet":
        tables = read_tables(meta["files_payload"])
        schema = tables_to_schema(tables)
        data = tables_to_data(tables, schema)
        label = label or "Planilhas: " + ", ".join(table.name for table in tables)
    else:
        text = meta.get("text", "")
        schema = parse_schema(text)
        rows = int(meta.get("rows") or SAMPLE_ROWS_DEFAULT)
        if kind == "example":
            data = generate_sample_data(schema, rows)
            label = label or f"Exemplo: {meta.get('name') or 'schema'}"
        else:
            has_inserts = re.search(r"\binsert\s+into\b", text, re.IGNORECASE) is not None
            data = None if has_inserts else generate_sample_data(schema, rows)
            suffix = "seus dados" if has_inserts else "exemplo"
            label = label or f"Script SQL ({len(schema.table_names())} tabelas · {suffix})"
    return {"kind": kind, "label": label, "schema": schema, "data": data}


def _activate_source(source_id: str, announce: bool = True) -> bool:
    try:
        payload = _build_payload(source_id)
    except Exception as exc:
        st.error(f"Nao consegui ler os dados: {exc}")
        return False
    if payload is None:
        if announce:
            st.warning("A fonte salva nao foi encontrada. Carregue os dados novamente.")
        return False

    schema = payload["schema"]
    data = payload["data"]
    try:
        database = InMemoryDatabase(schema, data)
    except QueryError as exc:
        st.error(f"Falha ao preparar o banco: {exc}")
        return False

    provider = _build_provider()
    st.session_state.schema = schema
    st.session_state.data = data
    st.session_state.database = database
    st.session_state.provider = provider
    st.session_state.fewshots = _fewshots_for(schema, provider)
    st.session_state.chat = (
        ChatSession(provider, schema, database, st.session_state.fewshots)
        if provider is not None
        else None
    )
    st.session_state.source_label = payload["label"]
    st.session_state.source_id = source_id
    st.session_state.turns = store.read_turns(source_id)
    st.session_state.recent = store.read_recent(source_id)
    st.session_state.pending_question = None
    st.query_params["src"] = source_id
    return True


def _serialize_turns(turns: list[dict]) -> list[dict]:
    serializable: list[dict] = []
    for turn in turns:
        if not (turn.get("executed") or turn.get("error")):
            continue
        item = {
            "question": turn.get("question"),
            "sql": turn.get("sql"),
            "error": turn.get("error"),
            "executed": bool(turn.get("executed")),
            "explanation": turn.get("explanation", ""),
        }
        if turn.get("executed"):
            item.update(
                {
                    "columns": turn.get("columns", []),
                    "rows": [list(row) for row in turn.get("rows", [])],
                    "elapsed": turn.get("elapsed", 0.0),
                    "truncated": turn.get("truncated", False),
                }
            )
        serializable.append(item)
    return serializable


def _persist_turns() -> None:
    source_id = st.session_state.source_id
    if source_id:
        store.save_turns(source_id, _serialize_turns(st.session_state.turns))


def _remember_question(question: str) -> None:
    recent = [item for item in st.session_state.recent if item != question]
    recent.insert(0, question)
    st.session_state.recent = recent[:8]
    if st.session_state.source_id:
        store.save_recent(st.session_state.source_id, st.session_state.recent)


def _row_counts(schema: Schema, database, data) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table in schema.tables.values():
        if data is not None:
            rows = data.rows.get(table.name)
            counts[table.name] = len(rows) if rows is not None else 0
        elif database is not None:
            try:
                counts[table.name] = int(database.execute(f'SELECT COUNT(*) FROM "{table.name}";').rows[0][0])
            except Exception:
                counts[table.name] = 0
    return counts


# ---------------------------------------------------------------------------
# Fontes de dados
# ---------------------------------------------------------------------------


def _load_spreadsheets(uploaded) -> None:
    if not uploaded:
        st.warning("Envie ao menos um arquivo.")
        return
    files = [(item.name, item.getvalue()) for item in uploaded]
    try:
        source_id = store.save_uploaded(files)
    except Exception as exc:
        st.error(f"Nao consegui salvar as planilhas: {exc}")
        return
    if _activate_source(source_id):
        _flash("success", f"Fonte ativa: planilhas ({len(files)} arquivo(s)).")
        st.rerun()


def _load_script() -> None:
    text = st.session_state.get("script_text", "")
    try:
        schema = parse_schema(text)
    except SchemaError as exc:
        st.error(f"Script invalido: {exc}")
        return
    has_inserts = re.search(r"\binsert\s+into\b", text, re.IGNORECASE) is not None
    suffix = "seus dados" if has_inserts else "exemplo"
    label = f"Script SQL ({len(schema.table_names())} tabelas · {suffix})"
    source_id = store.save_text(
        text, "script", rows=int(st.session_state.sample_rows), label=label
    )
    if _activate_source(source_id):
        _flash("success", f"Fonte ativa: {label}.")
        st.rerun()


def _load_example() -> None:
    name = st.session_state.example_preset
    path = SCHEMAS_DIR / f"{name}.sql"
    if not path.exists():
        st.error(f"Schema de exemplo nao encontrado: {name}")
        return
    text = path.read_text(encoding="utf-8")
    source_id = store.save_text(
        text, "example", rows=int(st.session_state.sample_rows), name=name, label=f"Exemplo: {name}"
    )
    if _activate_source(source_id):
        _flash("success", f"Fonte ativa: exemplo {name}.")
        st.rerun()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------


def _render_sidebar() -> None:
    st.sidebar.markdown('<div class="chs-brand">Chat SQL</div>', unsafe_allow_html=True)
    st.sidebar.markdown(
        '<div class="chs-brand-sub">Perguntas em linguagem natural viram SQL somente leitura.</div>',
        unsafe_allow_html=True,
    )
    st.sidebar.write("")

    label = st.session_state.source_label
    st.sidebar.markdown(
        f'<div class="chs-card"><div class="chs-label">Fonte ativa</div>'
        f'<div class="chs-value">{html.escape(label) if label else "Nenhuma"}</div></div>',
        unsafe_allow_html=True,
    )

    schema = st.session_state.schema
    if schema is not None:
        counts = _row_counts(schema, st.session_state.database, st.session_state.data)
        st.sidebar.markdown('<div class="chs-label">Tabelas</div>', unsafe_allow_html=True)
        for name, count in counts.items():
            st.sidebar.markdown(
                f'<div class="chs-chip">{html.escape(name)} <span>{count}</span></div>',
                unsafe_allow_html=True,
            )

    st.sidebar.write("")
    st.sidebar.markdown(
        f'<div class="chs-chip">Provedor <span>{html.escape(st.session_state.provider_name)}</span></div>',
        unsafe_allow_html=True,
    )
    if st.session_state.schema is not None and st.sidebar.button("Trocar fonte", width="stretch"):
        st.session_state.schema = None
        st.session_state.data = None
        st.session_state.database = None
        st.session_state.chat = None
        st.session_state.source_label = None
        st.session_state.source_id = None
        st.session_state.turns = []
        if "src" in st.query_params:
            del st.query_params["src"]
        st.rerun()
    if st.session_state.turns and st.sidebar.button("Nova conversa", width="stretch"):
        st.session_state.turns = []
        _persist_turns()
        st.rerun()


# ---------------------------------------------------------------------------
# Aba Dados
# ---------------------------------------------------------------------------


def _render_data_tab() -> None:
    st.markdown("### Fonte de dados")
    st.caption("Uma fonte ativa por vez. Carregar uma nova substitui a atual.")
    mode = st.radio(
        "Como fornecer os dados?",
        [SOURCE_SPREADSHEET, SOURCE_SCRIPT, SOURCE_EXAMPLE],
        key="source_mode",
        horizontal=True,
    )

    if mode == SOURCE_SPREADSHEET:
        uploaded = st.file_uploader(
            "Arquivos (uma tabela por aba/arquivo)",
            type=["csv", "xlsx", "xls"],
            accept_multiple_files=True,
            key="data_files",
        )
        if st.button("Carregar planilhas", key="load_data", type="primary"):
            _load_spreadsheets(uploaded)
    elif mode == SOURCE_SCRIPT:
        st.text_area(
            "Script SQL",
            key="script_text",
            height=220,
            placeholder="CREATE TABLE clientes (id INTEGER PRIMARY KEY, nome TEXT);\n"
            "INSERT INTO clientes (id, nome) VALUES (1, 'Ana');",
        )
        st.caption("Sem INSERT, os Dados de Exemplo sao gerados automaticamente.")
        if st.button("Carregar script", key="load_script", type="primary"):
            _load_script()
    else:
        left, right = st.columns([2, 1])
        with left:
            st.selectbox("Schema de exemplo", EXAMPLE_SCHEMAS, key="example_preset")
        with right:
            st.slider("Linhas por tabela", SAMPLE_ROWS_MIN, SAMPLE_ROWS_MAX, key="sample_rows")
        if st.button("Carregar exemplo", key="load_example", type="primary"):
            _load_example()

    _render_source_preview()


def _render_source_preview() -> None:
    schema = st.session_state.schema
    if schema is None:
        return
    database = st.session_state.database
    counts = _row_counts(schema, database, st.session_state.data)
    st.divider()
    st.markdown("**Previa dos dados**")
    for table in schema.tables.values():
        if database is None:
            continue
        try:
            result = database.execute(f'SELECT * FROM "{table.name}" LIMIT 10;')
            frame = pd.DataFrame(result.rows, columns=result.columns)
        except Exception:
            continue
        title = f"{table.name} — {counts.get(table.name, 0)} linhas · {len(table.columns)} colunas"
        with st.expander(title, expanded=True):
            st.dataframe(frame, width="stretch", hide_index=True)
            st.caption("Mostrando as primeiras 10 linhas. Clique no cabecalho para ordenar.")


# ---------------------------------------------------------------------------
# Aba Configuracoes
# ---------------------------------------------------------------------------


def _render_config_tab() -> None:
    st.markdown("### Provedor")
    st.selectbox("Preset", PRESET_LABELS, key="provider_name")
    if st.session_state.provider_name == OFFLINE_PROVIDER:
        st.info(
            "Modo offline: as Consultas sao geradas por regras, sem enviar nada a servicos "
            "externos. Nenhuma chave de API e necessaria."
        )
    else:
        preset = PROVIDER_PRESETS[st.session_state.provider_name]
        st.text_input("Base URL", key="base_url", placeholder=preset.base_url)
        st.text_input("Modelo", key="model", placeholder=preset.default_model)
        st.text_input(
            "Chave de API",
            key="api_key",
            type="password",
            help="Fica apenas nesta sessao. Nunca e salva nem registrada.",
        )
        if st.button("Testar conexao", key="test_connection"):
            provider = _build_provider()
            if provider is None:
                st.warning("Informe a chave de API.")
            else:
                try:
                    provider.test_connection()
                    st.success("Conexao bem-sucedida.")
                except ProviderError as exc:
                    st.error(str(exc))
    st.divider()
    _render_storage_tab()


def _render_storage_tab() -> None:
    st.markdown("### Fontes salvas")
    st.caption(
        "As fontes ficam em disco e sobrevivem a reloads da pagina. "
        "A fonte ativa e lembrada na URL."
    )
    sources = store.list_sources()
    if not sources:
        st.caption("Nenhuma fonte salva ainda.")
    for item in sources:
        columns = st.columns([4, 1])
        active = item["source_id"] == st.session_state.source_id
        columns[0].markdown(
            f"{'**●** ' if active else ''}{item['label']}  \n`{item['source_id']}`"
        )
        if columns[1].button("Abrir", key=f"open_{item['source_id']}"):
            if _activate_source(item["source_id"]):
                st.rerun()
    st.divider()
    if st.button("Limpar fontes salvas", key="clear_sources"):
        store.clear_all()
        st.cache_data.clear()
        st.session_state.schema = None
        st.session_state.data = None
        st.session_state.database = None
        st.session_state.chat = None
        st.session_state.source_label = None
        st.session_state.source_id = None
        st.session_state.turns = []
        if "src" in st.query_params:
            del st.query_params["src"]
        _flash("success", "Fontes salvas removidas.")
        st.rerun()


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------


def _ensure_chat() -> ChatSession | None:
    chat = st.session_state.chat
    if chat is not None:
        return chat
    schema = st.session_state.schema
    database = st.session_state.database
    if schema is None or database is None:
        return None
    provider = _build_provider()
    if provider is None:
        return None
    fewshots = st.session_state.fewshots or _fewshots_for(schema, provider)
    chat = ChatSession(provider, schema, database, fewshots)
    st.session_state.provider = provider
    st.session_state.fewshots = fewshots
    st.session_state.chat = chat
    return chat


def _ask(question: str) -> None:
    chat = _ensure_chat()
    if chat is None:
        st.session_state.turns.append({"question": question, "error": "Configure o Provedor."})
        return
    try:
        with st.spinner("Gerando Consulta..."):
            proposal = chat.start_question(question)
    except ProviderError as exc:
        st.session_state.turns.append({"question": question, "error": str(exc)})
        return
    except Exception as exc:  # nunca deixa o app quebrar
        st.session_state.turns.append({"question": question, "error": f"Erro inesperado: {exc}"})
        return
    diagnostics = getattr(chat, "last_result", None)
    st.session_state.turns.append(
        {
            "question": question,
            "proposal": proposal,
            "sql": proposal.sql if proposal is not None else None,
            "error": chat.last_error if proposal is None else None,
            "diagnostics": diagnostics,
            "explanation": getattr(diagnostics, "explanation", ""),
            "executed": False,
        }
    )
    st.session_state.turns = st.session_state.turns[-MAX_TURNS:]
    _remember_question(question)
    _persist_turns()


def _render_suggestions(schema: Schema) -> None:
    suggestions = suggest_questions(schema)
    if not suggestions:
        return
    st.caption("Sugestoes — clique para perguntar:")
    for start in range(0, len(suggestions), 3):
        row = suggestions[start : start + 3]
        columns = st.columns(3)
        for offset, suggestion in enumerate(row):
            if columns[offset].button(
                suggestion, key=f"suggestion_{start + offset}", width="stretch"
            ):
                st.session_state.pending_question = suggestion


def _render_recent() -> None:
    recent = st.session_state.recent
    if not recent:
        return
    st.caption("Recentes:")
    for start in range(0, len(recent), 3):
        row = recent[start : start + 3]
        columns = st.columns(3)
        for offset, question in enumerate(row):
            if columns[offset].button(question, key=f"recent_{start + offset}", width="stretch"):
                st.session_state.pending_question = question


def _render_result(turn: dict, index: int) -> None:
    frame = pd.DataFrame(turn["rows"], columns=turn["columns"])
    if frame.empty:
        st.info("A Consulta rodou sem erros, mas nao retornou nenhuma linha.")
        return
    metrics = st.columns(3)
    metrics[0].metric("Linhas", len(frame))
    metrics[1].metric("Colunas", len(frame.columns))
    metrics[2].metric("Tempo", f"{turn['elapsed']:.0f} ms")
    st.dataframe(frame, width="stretch", hide_index=True)

    numeric = (
        len(frame.columns) == 2
        and len(frame) > 1
        and pd.api.types.is_numeric_dtype(frame[frame.columns[1]])
    )
    if numeric:
        chart = st.selectbox(
            "Grafico", ["Barra", "Linha", "Area", "Nenhum"], key=f"chart_{index}"
        )
        if chart == "Barra":
            st.bar_chart(frame, x=frame.columns[0], y=frame.columns[1], height=280)
        elif chart == "Linha":
            st.line_chart(frame, x=frame.columns[0], y=frame.columns[1], height=280)
        elif chart == "Area":
            st.area_chart(frame, x=frame.columns[0], y=frame.columns[1], height=280)

    if turn.get("truncated"):
        st.warning(f"Resultado limitado as primeiras {DISPLAY_ROWS} linhas.")
    downloads = st.columns(2)
    downloads[0].download_button(
        "Baixar CSV",
        frame.to_csv(index=False).encode("utf-8"),
        file_name="resultado.csv",
        mime="text/csv",
        key=f"download_{index}",
        width="stretch",
    )
    if turn.get("sql"):
        downloads[1].download_button(
            "Baixar SQL",
            turn["sql"],
            file_name="consulta.sql",
            mime="text/plain",
            key=f"sql_download_{index}",
            width="stretch",
        )


def _render_turn(turn: dict, index: int, is_last: bool) -> None:
    st.markdown(
        f'<div class="chs-user">{html.escape(turn["question"])}</div>', unsafe_allow_html=True
    )
    if turn.get("error"):
        st.error(f"Nao consegui gerar uma Consulta valida: {turn['error']}")
        diagnostics = turn.get("diagnostics")
        ambiguous = getattr(diagnostics, "ambiguous", None)
        if ambiguous:
            st.caption("Escolha a tabela:")
            columns = st.columns(len(ambiguous))
            for position, table in enumerate(ambiguous):
                if columns[position].button(table, key=f"disamb_{index}_{position}"):
                    st.session_state.pending_question = f"{turn['question']} [{table}]"
                    st.rerun()
        suggestions = getattr(diagnostics, "suggestions", None)
        if suggestions:
            st.caption("Tente algo como: " + " | ".join(suggestions))
        return

    st.markdown('<div class="chs-answer">Consulta SQL</div>', unsafe_allow_html=True)
    st.code(turn["sql"], language="sql")
    if turn.get("explanation"):
        st.caption(f"→ {turn['explanation']}")
    diagnostics = turn.get("diagnostics")
    understood = getattr(diagnostics, "understood", None)
    if understood:
        with st.expander("Detalhes tecnicos", expanded=False):
            for key, value in understood.items():
                st.write(f"**{key}:** {value}")

    if turn.get("executed"):
        _render_result(turn, index)
        return
    if is_last:
        actions = st.columns([1, 1, 3])
        if actions[0].button("Executar", type="primary", key=f"execute_{index}"):
            chat = st.session_state.chat
            outcome = chat.run(turn["proposal"])
            if outcome.status == "ok":
                turn.update(
                    {
                        "executed": True,
                        "columns": outcome.result.columns,
                        "rows": outcome.result.rows,
                        "elapsed": outcome.result.elapsed_ms,
                        "truncated": outcome.result.truncated,
                    }
                )
                _persist_turns()
                st.rerun()
            elif outcome.status == "corrected":
                turn["proposal"] = outcome.proposal
                turn["sql"] = outcome.proposal.sql
                st.warning("A execucao falhou e a Consulta foi corrigida. Revise e execute novamente.")
                st.rerun()
            else:
                turn["error"] = outcome.error
                _persist_turns()
                st.rerun()
        actions[1].download_button(
            "Baixar SQL",
            turn["sql"],
            file_name="consulta.sql",
            mime="text/plain",
            key=f"sql_{index}",
        )
    else:
        st.caption("Execute a ultima pergunta antes desta.")


def _empty_state() -> None:
    st.markdown(
        '<div class="chs-card"><div class="chs-label">Comece aqui</div>'
        '<div class="chs-value">Nenhuma fonte de dados carregada</div>'
        '<div class="chs-sub" style="margin-top:6px">Va para a aba <b>Dados</b>, escolha '
        '<b>Fonte de dados</b> e carregue planilhas, um script SQL ou um schema de exemplo.</div></div>',
        unsafe_allow_html=True,
    )


def _render_chat_tab() -> None:
    schema = st.session_state.schema
    if schema is None:
        _empty_state()
        return

    st.markdown('<div class="chs-source-line">Fonte ativa '
                f'<span class="chs-badge">{html.escape(st.session_state.source_label or "—")}</span></div>',
                unsafe_allow_html=True)
    _render_recent()
    _render_suggestions(schema)

    with st.form("pergunta_form", clear_on_submit=False):
        question = st.text_input(
            "Pergunta",
            key="question_input",
            placeholder="ex.: os 10 maiores clientes por faturamento no mes passado",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Perguntar", type="primary", width="stretch")

    if submitted and question.strip():
        st.session_state.pending_question = question.strip()
    if st.session_state.pending_question:
        _ask(st.session_state.pending_question)
        st.session_state.pending_question = None
        st.rerun()

    turns = st.session_state.turns
    for index, turn in enumerate(turns):
        _render_turn(turn, index, is_last=(index == len(turns) - 1))


def main() -> None:
    st.set_page_config(page_title="Chat SQL", page_icon="🗄️", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    _init_state()
    if st.session_state.schema is None:
        saved_source = st.query_params.get("src")
        if saved_source:
            _activate_source(saved_source, announce=False)
    flash = st.session_state.pop("flash", None)
    if flash:
        getattr(st, flash["kind"])(flash["message"])
    _render_sidebar()

    st.markdown('<div class="chs-title">Chat SQL</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="chs-sub">Pergunte em portugues e receba SQL somente leitura, validado '
        'pela Trava e executado em memoria.</div>',
        unsafe_allow_html=True,
    )

    chat_tab, data_tab, config_tab = st.tabs(["Chat", "Dados", "Configuracoes"])
    with chat_tab:
        _render_chat_tab()
    with data_tab:
        _render_data_tab()
    with config_tab:
        _render_config_tab()


if __name__ == "__main__":
    main()
