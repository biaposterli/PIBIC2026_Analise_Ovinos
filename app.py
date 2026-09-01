import io
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from reportlab.lib import colors as rl_colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, PageBreak, HRFlowable
)

# ══════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO DA PÁGINA
# ══════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Análise Reprodutiva de Ovinos",
    page_icon="🐑",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paleta de cores institucional ───────────────────────────────────────
# Identidade "pastagem tecnológica": verde-esmeralda profundo como cor de
# marca, dourado de etiqueta de identificação animal como acento — uma
# leitura mais saturada e contemporânea do tema agropecuário, evitando o
# par clichê creme + terracota comum em interfaces geradas por IA.
COR_PRIMARIA      = "#0E4335"   # verde-esmeralda profundo (identidade/marca)
COR_PRIMARIA_ESCURA = "#082A21" # verde quase-preto (gradientes, hover)
COR_PRIMARIA_CLARA= "#2F9370"   # verde esmeralda vivo (dados positivos)
COR_SECUNDARIA    = "#E4F1EA"   # verde menta claríssimo (chips/fundos suaves)
COR_DESTAQUE      = "#D19A34"   # dourado de etiqueta (acento)
COR_ALERTA        = "#C24A32"   # terracota vivo (vazias/alertas)
COR_NEUTRA_1      = "#5B6B64"   # cinza-ardósia esverdeado (texto secundário)
COR_NEUTRA_2      = "#E1E6E1"   # cinza-pedra claro (linhas/bordas)
COR_FUNDO         = "#F4F6F4"   # fundo geral (pedra clara)
COR_CARD          = "#FFFFFF"
COR_TEXTO         = "#101915"   # tinta quase preta

PALETA_CATEGORICA = [COR_PRIMARIA_CLARA, COR_ALERTA, COR_DESTAQUE, COR_NEUTRA_1, COR_SECUNDARIA, COR_NEUTRA_2]

MAPA_CORES_FIXAS = {
    "prenhe": COR_PRIMARIA_CLARA,
    "vazia": COR_ALERTA,
    "não informado": COR_NEUTRA_2,
    "nao informado": COR_NEUTRA_2,
}



def cores_para_labels(labels):
    """Atribui cores consistentes: prenhe/vazia sempre nas mesmas cores; o resto segue a paleta."""
    usados = []
    livres = [c for c in PALETA_CATEGORICA]
    saida = []
    for lb in labels:
        chave = str(lb).strip().casefold()
        if chave in MAPA_CORES_FIXAS:
            saida.append(MAPA_CORES_FIXAS[chave])
        else:
            cor = livres[len(usados) % len(livres)]
            usados.append(cor)
            saida.append(cor)
    return saida


def estilo_matplotlib():
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": COR_NEUTRA_2,
        "axes.labelcolor": COR_NEUTRA_1,
        "axes.titleweight": "bold",
        "axes.titlesize": 12.5,
        "axes.titlecolor": COR_TEXTO,
        "axes.titlepad": 14,
        "axes.linewidth": 0.9,
        "text.color": COR_TEXTO,
        "xtick.color": COR_NEUTRA_1,
        "ytick.color": COR_NEUTRA_1,
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "grid.color": COR_NEUTRA_2,
        "grid.linewidth": 0.9,
        "font.family": "sans-serif",
        "font.sans-serif": ["Manrope", "IBM Plex Sans", "DejaVu Sans", "Arial"],
    })


estilo_matplotlib()

# ══════════════════════════════════════════════════════════════════════════
# CSS CUSTOMIZADO — identidade "caderno de campo"
# ══════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,600;1,6..72,500;1,6..72,600&family=Manrope:wght@500;600;700;800&family=IBM+Plex+Mono:wght@500;600&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Manrope', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    .stApp {{
        background:
            radial-gradient(1100px 420px at 12% -8%, {COR_SECUNDARIA}55, transparent 60%),
            {COR_FUNDO};
    }}
    .block-container {{
        padding-top: 1.6rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }}

    /* ── Masthead — hero em cartão com gradiente, assinatura visual do app ── */
    .masthead {{
        position: relative;
        overflow: hidden;
        padding: 2.1rem 2.4rem;
        margin-bottom: 1.9rem;
        border-radius: 18px;
        background: linear-gradient(135deg, {COR_PRIMARIA_ESCURA} 0%, {COR_PRIMARIA} 62%, {COR_PRIMARIA_CLARA} 130%);
        box-shadow: 0 14px 34px -14px {COR_PRIMARIA_ESCURA}99;
    }}
    .masthead::after {{
        content: "";
        position: absolute;
        inset: 0;
        background: radial-gradient(420px 240px at 96% 8%, {COR_DESTAQUE}3d, transparent 70%);
        pointer-events: none;
    }}
    .masthead .eyebrow {{
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        font-family: 'Manrope', sans-serif;
        font-weight: 700;
        font-size: 0.74rem;
        letter-spacing: 0.09em;
        text-transform: uppercase;
        color: {COR_DESTAQUE};
        background: #ffffff14;
        border: 1px solid #ffffff26;
        padding: 0.3rem 0.75rem;
        border-radius: 999px;
        margin-bottom: 0.9rem;
    }}
    .masthead h1 {{
        font-family: 'Newsreader', serif !important;
        font-weight: 600 !important;
        font-style: italic;
        color: #FFFFFF !important;
        font-size: 2.35rem;
        line-height: 1.15;
        margin: 0 0 0.55rem 0;
        position: relative;
    }}
    .masthead p {{
        color: #E7EFEA;
        font-size: 1.01rem;
        max-width: 42rem;
        margin: 0;
        position: relative;
        line-height: 1.5;
    }}

    /* ── Grade de indicadores ── */
    .kpi-grid {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.9rem;
        margin-bottom: 2rem;
    }}
    @media (max-width: 900px) {{
        .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }}
    }}
    .kpi-card {{
        position: relative;
        background: {COR_CARD};
        border: 1px solid {COR_NEUTRA_2};
        border-radius: 14px;
        padding: 1.1rem 1.25rem 1rem;
        box-shadow: 0 1px 2px #10191508, 0 10px 24px -18px #10191530;
        transition: transform 0.16s ease, box-shadow 0.16s ease;
    }}
    .kpi-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 10px 22px -12px #10191533;
    }}
    .kpi-card::before {{
        content: "";
        position: absolute;
        left: 0; top: 0.9rem; bottom: 0.9rem;
        width: 3px;
        border-radius: 0 3px 3px 0;
        background: {COR_PRIMARIA_CLARA};
    }}
    .kpi-card.kpi-alert::before {{ background: {COR_ALERTA}; }}
    .kpi-top {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.55rem;
    }}
    .kpi-icon {{
        font-size: 1.05rem;
        width: 2rem;
        height: 2rem;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        background: {COR_SECUNDARIA};
    }}
    .kpi-card.kpi-alert .kpi-icon {{ background: {COR_ALERTA}1f; }}
    .kpi-label {{
        display: block;
        font-size: 0.8rem;
        font-weight: 600;
        color: {COR_NEUTRA_1};
    }}
    .kpi-value {{
        display: block;
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 600;
        font-size: 1.95rem;
        letter-spacing: -0.01em;
        color: {COR_PRIMARIA};
    }}
    .kpi-card.kpi-alert .kpi-value {{ color: {COR_ALERTA}; }}

    /* ── Seções: cartão elevado com cabeçalho com ícone ──
       (o wrapper real é um st.container(key=...), que o Streamlit marca
       com uma classe "st-key-sec-*" no bloco vertical interno) */
    div[class*="st-key-sec-"] {{
        background: {COR_CARD};
        border: 1px solid {COR_NEUTRA_2};
        border-radius: 16px;
        padding: 1.5rem 1.6rem 1.6rem;
        margin-bottom: 1.4rem;
        box-shadow: 0 1px 2px #10191508, 0 14px 30px -22px #10191530;
    }}
    .section-header {{
        display: flex;
        align-items: center;
        gap: 0.65rem;
        margin-bottom: 1rem;
    }}
    .section-header .icon-badge {{
        display: flex;
        align-items: center;
        justify-content: center;
        width: 2.2rem;
        height: 2.2rem;
        border-radius: 9px;
        background: {COR_SECUNDARIA};
        font-size: 1.08rem;
        flex-shrink: 0;
    }}
    .section-header h3 {{
        margin: 0 !important;
    }}
    .section-header .section-sub {{
        display: block;
        font-size: 0.84rem;
        font-weight: 500;
        color: {COR_NEUTRA_1};
        margin-top: 0.1rem;
    }}

    h1, h2, h3, h4 {{
        font-family: 'Manrope', sans-serif;
        color: {COR_TEXTO} !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em;
    }}
    h3 {{
        font-size: 1.15rem !important;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }}

    /* ── Botões ── */
    .stButton>button, .stDownloadButton>button {{
        background: linear-gradient(135deg, {COR_PRIMARIA} 0%, {COR_PRIMARIA_ESCURA} 100%);
        color: white;
        border: none;
        border-radius: 9px;
        font-weight: 600;
        padding: 0.6rem 1.15rem;
        box-shadow: 0 6px 16px -8px {COR_PRIMARIA}80;
        transition: transform 0.12s ease, box-shadow 0.12s ease, background 0.15s ease-in-out;
    }}
    .stButton>button:hover, .stDownloadButton>button:hover {{
        background: linear-gradient(135deg, {COR_PRIMARIA_CLARA} 0%, {COR_PRIMARIA} 100%);
        color: white;
        transform: translateY(-1px);
        box-shadow: 0 10px 20px -8px {COR_PRIMARIA}90;
    }}
    .stButton>button:active, .stDownloadButton>button:active {{
        transform: translateY(0);
    }}
    .stButton>button:focus-visible, .stDownloadButton>button:focus-visible {{
        outline: 2px solid {COR_DESTAQUE};
        outline-offset: 2px;
    }}

    /* ── Abas — estilo segmentado/pílula ── */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.3rem;
        border-bottom: none;
        background: {COR_CARD};
        border: 1px solid {COR_NEUTRA_2};
        border-radius: 12px;
        padding: 0.3rem;
        margin-bottom: 0.4rem;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: transparent;
        padding: 0.5rem 1rem;
        color: {COR_NEUTRA_1};
        font-weight: 600;
        border-radius: 9px;
        transition: background-color 0.15s ease, color 0.15s ease;
    }}
    .stTabs [data-baseweb="tab"]:hover {{
        background-color: {COR_SECUNDARIA};
        color: {COR_PRIMARIA};
    }}
    .stTabs [aria-selected="true"] {{
        color: #FFFFFF !important;
        background: {COR_PRIMARIA};
        font-weight: 700;
    }}
    .stTabs [aria-selected="true"]:hover {{
        color: #FFFFFF !important;
        background: {COR_PRIMARIA};
    }}
    .stTabs [data-baseweb="tab-highlight"] {{ display: none; }}
    .stTabs [data-baseweb="tab-panel"] {{
        padding-top: 1rem;
    }}

    /* ── Expanders ── */
    .streamlit-expanderHeader {{
        background-color: {COR_FUNDO};
        border: 1px solid {COR_NEUTRA_2};
        border-radius: 10px !important;
        font-weight: 600;
        color: {COR_TEXTO};
    }}
    .streamlit-expanderContent {{
        border: 1px solid {COR_NEUTRA_2};
        border-top: none;
        border-radius: 0 0 10px 10px;
    }}

    /* ── Dataframes ── */
    div[data-testid="stDataFrame"] {{
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid {COR_NEUTRA_2};
    }}

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {{
        background-color: #FFFFFF;
        border-right: 1px solid {COR_NEUTRA_2};
    }}
    section[data-testid="stSidebar"] .block-container {{
        padding-top: 1.6rem;
    }}
    section[data-testid="stSidebar"] h2 {{
        font-family: 'Manrope', sans-serif;
        font-size: 1.02rem !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: {COR_PRIMARIA} !important;
    }}
    .sidebar-step {{
        display: flex;
        gap: 0.6rem;
        align-items: flex-start;
        margin: 0.9rem 0 0.5rem;
    }}
    .sidebar-step .step-num {{
        flex-shrink: 0;
        width: 1.5rem;
        height: 1.5rem;
        border-radius: 999px;
        background: {COR_PRIMARIA};
        color: #fff;
        font-size: 0.76rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    .sidebar-step .step-text {{
        font-size: 0.88rem;
        color: {COR_TEXTO};
        font-weight: 600;
        line-height: 1.4;
        padding-top: 0.1rem;
    }}
    [data-testid="stFileUploaderDropzone"] {{
        border-radius: 10px !important;
        border: 1.5px dashed {COR_NEUTRA_2} !important;
        background: {COR_FUNDO} !important;
    }}

    /* Alertas */
    div[data-testid="stAlert"] {{
        border-radius: 10px;
        border: 1px solid {COR_NEUTRA_2};
    }}

    /* Foco visível para navegação por teclado */
    a:focus-visible, button:focus-visible, [tabindex]:focus-visible {{
        outline: 2px solid {COR_DESTAQUE};
        outline-offset: 2px;
    }}

    .app-footer {{
        text-align: center;
        color: {COR_NEUTRA_1};
        font-size: 0.85rem;
        margin-top: 2.2rem;
        padding-top: 1.2rem;
        border-top: 1px solid {COR_NEUTRA_2};
    }}

    footer {{visibility: hidden;}}
    #MainMenu {{visibility: hidden;}}
    header[data-testid="stHeader"] {{visibility: hidden; height: 0;}}
</style>
""", unsafe_allow_html=True)


_contador_secoes = 0


@contextmanager
def section_card():
    """Envolve um bloco de conteúdo em um cartão de seção estilizado.

    Usa `st.container(key=...)` (em vez de abrir/fechar uma <div> via dois
    `st.markdown` separados) porque o Streamlit renderiza cada chamada de
    `st.markdown` como um nó isolado no DOM — a tag HTML não chega a
    "envolver" de fato os widgets nativos (tabelas, gráficos) inseridos
    entre elas. O container real recebe a classe `st-key-sec-N`, usada
    pelo CSS para aplicar o visual de cartão.
    """
    global _contador_secoes
    _contador_secoes += 1
    with st.container(key=f"sec-{_contador_secoes}"):
        yield


def titulo_secao(icone, titulo, subtitulo=None):
    """Renderiza o cabeçalho padrão de uma seção: badge de ícone + título
    (+ subtítulo opcional), no lugar de um `st.markdown('### ...')` isolado."""
    sub_html = f'<span class="section-sub">{subtitulo}</span>' if subtitulo else ""
    st.markdown(
        f'<div class="section-header">'
        f'<span class="icon-badge">{icone}</span>'
        f'<div><h3>{titulo}</h3>{sub_html}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

COLUNAS_OBRIGATORIAS = [
    "Ordem",
    "Número de Identificação",
    "Diagnóstico de Gestação Inicial",
    "Estação de monta 1",
    "Carneiro_monta_1",
    "Diagnóstico de Gestação 1",
    "Estação de monta 2",
    "Carneiro_monta_2",
    "Diagnóstico de Gestação 2",
    "Estação de monta 3",
    "Carneiro_monta_3",
    "Diagnóstico de Gestação 3",
    "Diagnóstico de Gestação Final",
]

ESTACOES = [
    {"rodada": 1, "estacao": "Estação de monta 1", "carneiro": "Carneiro_monta_1", "diagnostico": "Diagnóstico de Gestação 1"},
    {"rodada": 2, "estacao": "Estação de monta 2", "carneiro": "Carneiro_monta_2", "diagnostico": "Diagnóstico de Gestação 2"},
    {"rodada": 3, "estacao": "Estação de monta 3", "carneiro": "Carneiro_monta_3", "diagnostico": "Diagnóstico de Gestação 3"},
]

MODEL_PATH = Path(__file__).with_name("Modelo_Dados_Ovinos_IATF.xlsx")


# ══════════════════════════════════════════════════════════════════════════
# FUNÇÕES DE CÁLCULO
# ══════════════════════════════════════════════════════════════════════════
def norm(x):
    return str(x).strip().casefold()


def validar_colunas(df):
    return [c for c in COLUNAS_OBRIGATORIAS if c not in df.columns]


@st.cache_data(show_spinner=False)
def resumo_estacoes(df):
    linhas = []
    for estacao in ESTACOES:
        estacao_col = estacao["estacao"]
        diag = estacao["diagnostico"]
        mask_estacao = df[estacao_col].notna() & df[estacao_col].astype(str).str.strip().ne("")
        diag_norm = df[diag].map(norm)
        validos = mask_estacao & diag_norm.isin(["prenhe", "vazia"])
        prenhes = (mask_estacao & (diag_norm == "prenhe")).sum()
        vazias = (mask_estacao & (diag_norm == "vazia")).sum()
        submetidos = mask_estacao.sum()
        n_validos = validos.sum()
        taxa = prenhes / n_validos * 100 if n_validos else np.nan
        linhas.append({
            "Estação de Monta": f"Estação de Monta {estacao['rodada']}",
            "Animais submetidos": int(submetidos),
            "Diagnósticos válidos": int(n_validos),
            "Prenhes": int(prenhes),
            "Vazias": int(vazias),
            "Taxa de prenhez (%)": round(taxa, 2) if pd.notna(taxa) else np.nan,
        })
    return pd.DataFrame(linhas)


def diagnostico_tabela(df, coluna, protocolo_col=None):
    if protocolo_col and protocolo_col in df.columns:
        mask = df[protocolo_col].notna() & df[protocolo_col].astype(str).str.strip().ne("")
        s = df.loc[mask, coluna].copy()
    else:
        s = df[coluna].copy()

    s = s.where(s.notna(), "Não informado")
    s = s.astype(str).str.strip()
    c = s.value_counts()

    total_validos = len(s) if len(s) > 0 else 1
    out = pd.DataFrame({"Diagnóstico": c.index, "N": c.values})
    out["%"] = (out["N"] / total_validos * 100).round(2)
    return out


@st.cache_data(show_spinner=False)
def carneiros(df):
    nomes = set()
    por_estacao = {}
    for estacao in ESTACOES:
        s = df[estacao["carneiro"]].dropna().astype(str).str.strip()
        s = s[s.ne("")]
        vals = sorted(s.unique().tolist())
        por_estacao[estacao["rodada"]] = vals
        nomes.update(vals)
    return sorted(nomes), por_estacao


def taxa_carneiro(df, estacao):
    p = estacao["estacao"]
    c = estacao["carneiro"]
    d = estacao["diagnostico"]
    mask = (
        df[p].notna() &
        df[p].astype(str).str.strip().ne("") &
        df[c].notna() &
        df[c].astype(str).str.strip().ne("") &
        df[d].map(norm).isin(["prenhe", "vazia"])
    )
    tmp = df.loc[mask, [c, d]].copy()
    tmp[c] = tmp[c].astype(str).str.strip()
    tmp[d] = tmp[d].map(norm)
    rows = []
    for nome, g in tmp.groupby(c, sort=True):
        n = len(g)
        pr = (g[d] == "prenhe").sum()
        va = (g[d] == "vazia").sum()
        rows.append({
            "Carneiro": nome,
            "Animais avaliados": n,
            "Prenhes": int(pr),
            "Vazias": int(va),
            "Taxa de prenhez (%)": round(pr / n * 100, 2) if n else np.nan,
        })
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def consolidado_carneiros(df):
    partes = []
    for estacao in ESTACOES:
        t = taxa_carneiro(df, estacao)
        if not t.empty:
            t["Estação de Monta"] = estacao["rodada"]
            partes.append(t)
    if not partes:
        return pd.DataFrame()
    x = pd.concat(partes, ignore_index=True)
    out = (
        x.groupby("Carneiro", as_index=False)
        .agg(
            **{
                "Animais avaliados": ("Animais avaliados", "sum"),
                "Prenhes": ("Prenhes", "sum"),
                "Vazias": ("Vazias", "sum"),
                "Nº de Estações de Monta utilizadas": ("Estação de Monta", "nunique"),
            }
        )
    )
    out["Taxa de prenhez (%)"] = (out["Prenhes"] / out["Animais avaliados"] * 100).round(2)
    return out


# ══════════════════════════════════════════════════════════════════════════
# GRÁFICOS
# ══════════════════════════════════════════════════════════════════════════
def pie_figure(values, labels, title):
    fig, ax = plt.subplots(figsize=(5.4, 4.9))
    vals = [int(v) for v in values]
    if sum(vals) == 0:
        ax.text(0.5, 0.5, "Sem dados válidos", ha="center", va="center", color=COR_NEUTRA_1)
        ax.axis("off")
    else:
        cores = cores_para_labels(labels)
        wedges, texts, autotexts = ax.pie(
            vals, labels=labels, autopct="%1.1f%%", startangle=90,
            colors=cores,
            wedgeprops={"edgecolor": "white", "linewidth": 1.5},
            textprops={"color": COR_TEXTO, "fontsize": 9.5},
        )
        for at in autotexts:
            at.set_color("white")
            at.set_fontweight("bold")
        ax.set_title(title, pad=12)
    fig.tight_layout()
    return fig


def barras_taxa_estacao(t_estacoes):
    fig, ax = plt.subplots(figsize=(9, 4.3))
    x = t_estacoes["Estação de Monta"]
    y = t_estacoes["Taxa de prenhez (%)"]
    ax.bar(x, y, color=COR_PRIMARIA_CLARA, edgecolor=COR_PRIMARIA, linewidth=0.8, width=0.55, zorder=3)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Taxa de prenhez (%)")
    ax.set_title("Taxa de prenhez por Estação de Monta")
    ax.grid(axis="y", zorder=0)
    for i, v in enumerate(y):
        if pd.notna(v):
            ax.text(i, v + 2, f"{v:.1f}%", ha="center", fontweight="bold", color=COR_PRIMARIA)
    fig.tight_layout()
    return fig


def barh_taxa_carneiro(carneiros_cons):
    fig, ax = plt.subplots(figsize=(9, max(4.2, len(carneiros_cons) * 0.5)))
    p = carneiros_cons.sort_values("Taxa de prenhez (%)")
    ax.barh(p["Carneiro"], p["Taxa de prenhez (%)"], color=COR_PRIMARIA_CLARA,
            edgecolor=COR_PRIMARIA, linewidth=0.8, zorder=3)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Taxa de prenhez (%)")
    ax.set_title("Taxa de prenhez consolidada por carneiro")
    ax.grid(axis="x", zorder=0)
    for y, v in enumerate(p["Taxa de prenhez (%)"]):
        ax.text(v + 1.5, y, f"{v:.1f}%", va="center", fontweight="bold", color=COR_PRIMARIA)
    fig.tight_layout()
    return fig


@st.cache_data(show_spinner=False)
def contagem_uso_carneiros(df):
    """Conta quantas fêmeas cada carneiro cobriu em cada estação de monta.

    Retorna a lista de nomes de carneiros (ordenada) e um dicionário
    {rodada: pandas.Series(nome_do_carneiro -> contagem)}.
    """
    contagens = {}
    nomes = set()
    for estacao in ESTACOES:
        s = df[estacao["carneiro"]].dropna().astype(str).str.strip()
        s = s[s.ne("")]
        contagens[estacao["rodada"]] = s.value_counts()
        nomes.update(s.unique().tolist())
    return sorted(nomes), contagens


def barras_agrupadas_carneiros_monta(nomes, contagens):
    """Gera o gráfico de uso de cada carneiro por monta, a partir dos dados
    reais enviados na planilha (nomes/contagens vindos de `contagem_uso_carneiros`)."""
    if not nomes:
        fig, ax = plt.subplots(figsize=(9, 3))
        ax.text(0.5, 0.5, "Sem dados de carneiros para exibir", ha="center", va="center", color=COR_NEUTRA_1)
        ax.axis("off")
        return fig

    x = np.arange(len(nomes))
    n_estacoes = len(ESTACOES)
    width = 0.8 / n_estacoes
    cores_monta = [COR_PRIMARIA, COR_PRIMARIA_CLARA, COR_DESTAQUE]

    fig, ax = plt.subplots(figsize=(max(9, len(nomes) * 1.1), 5))

    valor_max = 1
    for i, estacao in enumerate(ESTACOES):
        rodada = estacao["rodada"]
        serie = contagens.get(rodada, pd.Series(dtype=int))
        valores = [int(serie.get(nome, 0)) for nome in nomes]
        valor_max = max(valor_max, max(valores, default=0))
        offset = (i - (n_estacoes - 1) / 2) * width
        cor = cores_monta[i % len(cores_monta)]
        ax.bar(x + offset, valores, width, label=f"Monta {rodada}", color=cor, edgecolor="none", zorder=3)

    ax.set_title("Uso de cada carneiro por monta")
    ax.set_ylabel("Nº de fêmeas cobertas")
    ax.set_xticks(x)
    ax.set_xticklabels(nomes, rotation=30, ha="right")
    ax.set_ylim(0, valor_max * 1.2)
    ax.legend(loc="upper right")
    ax.grid(axis="y", zorder=0)

    fig.tight_layout()
    return fig


def fig_to_png(fig):
    b = io.BytesIO()
    fig.savefig(b, format="png", dpi=170, bbox_inches="tight")
    plt.close(fig)
    b.seek(0)
    return b


# ══════════════════════════════════════════════════════════════════════════
# GERAÇÃO DO PDF
# ══════════════════════════════════════════════════════════════════════════
def tabela_pdf(df, max_rows=40):
    if df is None or df.empty:
        return Table([["Sem dados"]])
    x = df.head(max_rows).copy()
    data = [list(x.columns)] + x.fillna("").astype(str).values.tolist()
    t = Table(data, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), rl_colors.HexColor(COR_PRIMARIA)),
        ("TEXTCOLOR", (0, 0), (-1, 0), rl_colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [rl_colors.white, rl_colors.HexColor("#F0F3EE")]),
        ("GRID", (0, 0), (-1, -1), 0.4, rl_colors.HexColor("#D3DAD0")),
        ("FONTSIZE", (0, 0), (-1, -1), 7.3),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def cabecalho_secao(numero, titulo, styles):
    partes = [
        Paragraph(f'<font color="{COR_DESTAQUE}">{numero}.</font>  {titulo}', styles["SecaoTitulo"]),
        HRFlowable(width="100%", thickness=1.2, color=rl_colors.HexColor(COR_DESTAQUE), spaceAfter=10),
    ]
    return partes


def gerar_pdf(df, dados):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=1.6*cm, leftMargin=1.6*cm,
                             topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    # Times (fonte base do PDF, sem necessidade de embutir arquivos) para os
    # títulos — a mesma dupla serifada/sem serifa usada na tela do app.
    styles.add(ParagraphStyle(name="TitleCenter", parent=styles["Title"], alignment=TA_CENTER,
                               textColor=rl_colors.HexColor(COR_PRIMARIA), fontSize=23,
                               fontName="Times-BoldItalic", leading=27))
    styles.add(ParagraphStyle(name="Subtitulo", parent=styles["BodyText"], alignment=TA_CENTER,
                               textColor=rl_colors.HexColor(COR_NEUTRA_1), fontSize=11))
    styles.add(ParagraphStyle(name="SecaoTitulo", parent=styles["Heading2"],
                               textColor=rl_colors.HexColor(COR_TEXTO), fontSize=14,
                               fontName="Times-Bold", spaceBefore=6, spaceAfter=4))
    styles.add(ParagraphStyle(name="CorpoTexto", parent=styles["BodyText"],
                               textColor=rl_colors.HexColor(COR_TEXTO), fontSize=10, leading=15))
    styles.add(ParagraphStyle(name="Rodape", parent=styles["BodyText"], alignment=TA_LEFT,
                               textColor=rl_colors.HexColor(COR_NEUTRA_1), fontSize=8))


    story = []

    # ── Capa ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 3.5*cm))
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("Relatório de Análise da<br/>Eficiência Reprodutiva de Ovinos", styles["TitleCenter"]))
    story.append(Spacer(1, 0.3*cm))
    story.append(Spacer(1, 1.2*cm))
    story.append(HRFlowable(width="60%", thickness=1.2, color=rl_colors.HexColor(COR_DESTAQUE), hAlign="CENTER"))
    story.append(Spacer(1, 1.2*cm))

    resumo_tbl = Table([
        ["Total de animais analisados", f"{len(df):,}".replace(",", ".")],
        ["Carneiros distintos identificados", f"{len(dados['carneiros'])}"],
        ["Taxa de prenhez final", f"{dados['taxa_final']:.2f}%"],
    ], colWidths=[9*cm, 5*cm])
    resumo_tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (-1, -1), rl_colors.HexColor(COR_TEXTO)),
        ("TEXTCOLOR", (1, 0), (1, -1), rl_colors.HexColor(COR_PRIMARIA)),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, rl_colors.HexColor("#D3DAD0")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(resumo_tbl)
    story.append(PageBreak())

    # ── 1. Estações de monta ────────────────────────────────────────
    story += cabecalho_secao(1, "Resultados por Estação de Monta", styles)
    story.append(tabela_pdf(dados["tabela_estacoes"]))
    story.append(Spacer(1, 0.4*cm))

    # `zip` casa cada linha de `tabela_estacoes` com a estação correspondente
    # em ESTACOES — mais claro e seguro do que indexar por `rodada - 1`.
    for estacao, row in zip(ESTACOES, dados["tabela_estacoes"].to_dict("records")):
        fig = pie_figure(
            [row["Prenhes"], row["Vazias"]],
            ["Prenhe", "Vazia"],
            f"Prenhe x Vazia — Estação de Monta {estacao['rodada']}"
        )
        story.append(RLImage(fig_to_png(fig), width=10*cm, height=9*cm))

    story.append(PageBreak())

    # ── 2. Diagnóstico final ────────────────────────────────────────
    story += cabecalho_secao(2, "Diagnóstico de Gestação Final", styles)
    story.append(tabela_pdf(dados["resumo_final"]))
    fig = pie_figure(
        dados["resumo_final"]["N"].tolist(),
        dados["resumo_final"]["Resultado"].tolist(),
        "Diagnóstico de gestação final"
    )
    story.append(RLImage(fig_to_png(fig), width=10.5*cm, height=9.5*cm))
    story.append(PageBreak())

    # ── 3. Carneiros ─────────────────────────────────────────────────
    story += cabecalho_secao(3, "Desempenho dos Carneiros", styles)
    story.append(tabela_pdf(dados["carneiros_consolidado"]))
    if not dados["carneiros_consolidado"].empty:
        story.append(Spacer(1, 0.3*cm))
        for _, row in dados["carneiros_consolidado"].iterrows():
            fig = pie_figure(
                [row["Prenhes"], row["Vazias"]],
                ["Prenhe", "Vazia"],
                f"Carneiro {row['Carneiro']}"
            )
            story.append(RLImage(fig_to_png(fig), width=8.5*cm, height=7.6*cm))
    story.append(PageBreak())

    # ── 4. Vazios ────────────────────────────────────────────────────
    story += cabecalho_secao(4, "Animais que Permaneceram Vazios ao Final", styles)
    story.append(Paragraph(
        f"Total de animais vazios: <b>{len(dados['vazios']):,}</b>.".replace(",", "."),
        styles["CorpoTexto"]
    ))
    story.append(Spacer(1, 0.25*cm))
    story.append(tabela_pdf(dados["vazios_resumida"], max_rows=100))

    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=0.6, color=rl_colors.HexColor("#D3DAD0")))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "Relatório gerado automaticamente pelo Sistema de Análise Reprodutiva de Ovinos.",
        styles["Rodape"]
    ))

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════════════════
# INTERFACE — CABEÇALHO
# ══════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="masthead">
    <span class="eyebrow"> &nbsp; Painel de Desempenho Reprodutivo</span>
    <h1>Análise Reprodutiva de Ovinos</h1>
    <p>Envie a planilha preenchida para obter indicadores, gráficos e o relatório final em PDF.</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# BARRA LATERAL — ENTRADA DE DADOS
# ══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 📁 Dados de Entrada")

    st.markdown(
        '<div class="sidebar-step"><span class="step-num">1</span>'
        '<span class="step-text">Baixe o modelo (se ainda não tiver)</span></div>',
        unsafe_allow_html=True,
    )
    if MODEL_PATH.exists():
        st.download_button(
            "📥 Baixar modelo da planilha",
            data=MODEL_PATH.read_bytes(),
            file_name="Modelo_Dados_Ovinos_IATF.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    else:
        st.info("Modelo não encontrado no servidor.")

    st.markdown(
        '<div class="sidebar-step"><span class="step-num">2</span>'
        '<span class="step-text">Envie a planilha preenchida</span></div>',
        unsafe_allow_html=True,
    )
    uploaded = st.file_uploader(
        "Planilha preenchida",
        type=["xlsx", "xls"],
        help="Use o modelo disponibilizado acima e mantenha os nomes das colunas.",
        label_visibility="collapsed",
    )

    with st.expander("ℹ️ Colunas obrigatórias"):
        for c in COLUNAS_OBRIGATORIAS:
            st.markdown(f"- `{c}`")

if uploaded is None:
    st.info("⬅️ Baixe o modelo, preencha os dados e envie a planilha pela barra lateral para iniciar a análise.")
    st.stop()

try:
    df = pd.read_excel(uploaded)
except Exception as e:
    st.error(f"❌ Não foi possível ler a planilha: {e}")
    st.stop()

faltantes = validar_colunas(df)
if faltantes:
    st.error("❌ A planilha não possui todas as colunas obrigatórias.")
    st.warning("Corrija exatamente as seguintes colunas:")
    for c in faltantes:
        st.write(f"- `{c}`")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════
# CÁLCULOS
# ══════════════════════════════════════════════════════════════════════════
t_estacoes = resumo_estacoes(df)
dg_final = df["Diagnóstico de Gestação Final"].map(norm)
n_prenhes_final = int((dg_final == "prenhe").sum())
n_vazias_final = int((dg_final == "vazia").sum())
n_validos_final = int(dg_final.isin(["prenhe", "vazia"]).sum())
taxa_final = n_prenhes_final / n_validos_final * 100 if n_validos_final else 0.0

resumo_final = pd.DataFrame({
    "Resultado": ["Prenhe", "Vazia", "Não informado/Outro"],
    "N": [
        n_prenhes_final,
        n_vazias_final,
        int((~dg_final.isin(["prenhe", "vazia"])).sum()),
    ],
})
resumo_final["% do total"] = (resumo_final["N"] / len(df) * 100).round(2)

todos_carneiros, carneiros_por_estacao = carneiros(df)
carneiros_cons = consolidado_carneiros(df)

vazios = df.loc[dg_final == "vazia"].copy()
cols_resumidas = [c for c in ["Ordem", "Número de Identificação", "Diagnóstico de Gestação Final"] if c in vazios.columns]
vazios_resumida = vazios[cols_resumidas].reset_index(drop=True)

dados = {
    "tabela_estacoes": t_estacoes,
    "resumo_final": resumo_final,
    "carneiros": todos_carneiros,
    "carneiros_consolidado": carneiros_cons,
    "vazios": vazios,
    "vazios_resumida": vazios_resumida,
    "taxa_final": taxa_final,
}

st.success(f"✅ Planilha analisada com sucesso: **{len(df):,}** animais processados.")

# ══════════════════════════════════════════════════════════════════════════
# KPIs — tira de indicadores no lugar de cartões repetidos
# ══════════════════════════════════════════════════════════════════════════
def _fmt_int(n):
    return f"{n:,}".replace(",", ".")


kpis = [
    ("🐑", "Animais analisados", _fmt_int(len(df)), False),
    ("🏷️", "Carneiros distintos", _fmt_int(len(todos_carneiros)), False),
    ("📈", "Prenhez final", f"{taxa_final:.1f}%", False),
    ("⚠️", "Vazias ao final", _fmt_int(n_vazias_final), n_vazias_final > 0),
]
kpi_html = '<div class="kpi-grid">' + "".join(
    f'<div class="kpi-card{" kpi-alert" if alerta else ""}">'
    f'<div class="kpi-top"><span class="kpi-icon">{icone}</span></div>'
    f'<span class="kpi-label">{label}</span>'
    f'<span class="kpi-value">{valor}</span>'
    f'</div>'
    for icone, label, valor, alerta in kpis
) + '</div>'
st.markdown(kpi_html, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# ABAS DE CONTEÚDO
# ══════════════════════════════════════════════════════════════════════════
tab_geral, tab_diag, tab_carneiros, tab_vazios, tab_export = st.tabs(
    ["📊 Visão Geral", "🩺 Diagnósticos", "🐏 Carneiros", "⚠️ Animais Vazios", "📥 Exportar"]
)

with tab_geral:
    with section_card():
        titulo_secao("📈", "Taxa de prenhez por Estação de Monta")
        st.dataframe(t_estacoes, use_container_width=True, hide_index=True)
        fig = barras_taxa_estacao(t_estacoes)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    with section_card():
        titulo_secao("🥧", "Prenhe × Vazia por Estação de Monta")
        cols = st.columns(3)
        for idx, estacao in enumerate(ESTACOES):
            row = t_estacoes.iloc[idx]
            fig = pie_figure([row["Prenhes"], row["Vazias"]], ["Prenhe", "Vazia"], f"Estação de Monta {estacao['rodada']}")
            cols[idx].pyplot(fig, use_container_width=True)
            plt.close(fig)

    with section_card():
        titulo_secao("🩺", "Diagnóstico de gestação final")
        st.dataframe(resumo_final, use_container_width=True, hide_index=True)
        fig = pie_figure(resumo_final["N"], resumo_final["Resultado"], "Diagnóstico de gestação final")
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

with tab_diag:
    with section_card():
        titulo_secao("🩺", "Diagnósticos de gestação por etapa")
        mapeamento_protocolos = {
            "Diagnóstico de Gestação Inicial": None,
            "Diagnóstico de Gestação 1": "Estação de monta 1",
            "Diagnóstico de Gestação 2": "Estação de monta 2",
            "Diagnóstico de Gestação 3": "Estação de monta 3",
            "Diagnóstico de Gestação Final": None,
        }
        for coluna, prot_col in mapeamento_protocolos.items():
            with st.expander(coluna):
                tab_dados = diagnostico_tabela(df, coluna, protocolo_col=prot_col)
                c1, c2 = st.columns([1, 1])
                c1.dataframe(tab_dados, use_container_width=True, hide_index=True)
                fig = pie_figure(tab_dados["N"], tab_dados["Diagnóstico"], coluna)
                c2.pyplot(fig, use_container_width=True)
                plt.close(fig)

with tab_carneiros:
    with section_card():
        titulo_secao("🐏", "Taxa de prenhez por carneiro")
        if carneiros_cons.empty:
            st.info("Nenhum carneiro com diagnóstico válido foi encontrado.")
        else:
            st.dataframe(carneiros_cons, use_container_width=True, hide_index=True)
            fig = barh_taxa_carneiro(carneiros_cons)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

    with section_card():
        titulo_secao("📊", "Uso de cada carneiro por monta")
        nomes_carneiros, contagens_carneiros = contagem_uso_carneiros(df)
        fig_uso = barras_agrupadas_carneiros_monta(nomes_carneiros, contagens_carneiros)
        st.pyplot(fig_uso, use_container_width=True)
        plt.close(fig_uso)

with tab_vazios:
    with section_card():
        titulo_secao("⚠️", f"{len(vazios):,} animais permaneceram vazios ao final".replace(",", "."))
        st.dataframe(vazios, use_container_width=True, hide_index=True)
        st.markdown("#### Lista simplificada")
        st.dataframe(vazios_resumida, use_container_width=True, hide_index=True)

with tab_export:
    with section_card():
        titulo_secao("📥", "Exportar resultados")
        st.write("Baixe os resultados consolidados em Excel ou o relatório completo em PDF.")

        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            t_estacoes.to_excel(writer, sheet_name="Resumo Estações", index=False)
            resumo_final.to_excel(writer, sheet_name="Diagnostico Final", index=False)
            carneiros_cons.to_excel(writer, sheet_name="Carneiros", index=False)
            vazios.to_excel(writer, sheet_name="Animais Vazios", index=False)
        excel_buffer.seek(0)

        ce1, ce2 = st.columns(2)
        with ce1:
            st.download_button(
                "📊 Baixar resultados em Excel",
                data=excel_buffer.getvalue(),
                file_name="Resultados_Analise_Reprodutiva_Ovinos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with ce2:
            try:
                with st.spinner("Gerando relatório em PDF..."):
                    pdf_bytes = gerar_pdf(df, dados)
                st.download_button(
                    "📄 Baixar relatório final em PDF",
                    data=pdf_bytes,
                    file_name="Relatorio_Analise_Reprodutiva_Ovinos.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"❌ Não foi possível gerar o relatório em PDF: {e}")

st.markdown(
    '<p class="app-footer">🐑 Sistema de Análise Reprodutiva de Ovinos — '
    'processamento baseado na estrutura da planilha-modelo.</p>',
    unsafe_allow_html=True,
)
