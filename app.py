import io
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
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
COR_PRIMARIA      = "#20463B"   # verde profundo (marca)
COR_PRIMARIA_CLARA= "#3D7A5F"   # verde médio
COR_SECUNDARIA    = "#8FB996"   # verde suave
COR_DESTAQUE      = "#C99A4A"   # dourado/terracota (acento)
COR_ALERTA        = "#B7472A"   # terracota escuro (vazias)
COR_NEUTRA_1      = "#5B6B63"   # cinza esverdeado
COR_NEUTRA_2      = "#A9B4AD"   # cinza claro
COR_FUNDO         = "#F5F7F3"   # fundo geral
COR_CARD          = "#FFFFFF"
COR_TEXTO         = "#1F2A24"

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
        "axes.labelcolor": COR_TEXTO,
        "axes.titleweight": "bold",
        "axes.titlesize": 12,
        "axes.titlecolor": COR_PRIMARIA,
        "text.color": COR_TEXTO,
        "xtick.color": COR_TEXTO,
        "ytick.color": COR_TEXTO,
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "grid.color": "#E4E8E2",
        "grid.linewidth": 0.8,
        "font.family": "sans-serif",
    })


estilo_matplotlib()

# ══════════════════════════════════════════════════════════════════════════
# CSS CUSTOMIZADO — visual profissional
# ══════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<style>
    .stApp {{
        background-color: {COR_FUNDO};
    }}
    .block-container {{
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }}

    /* ── Cabeçalho ── */
    .app-header {{
        background: linear-gradient(135deg, {COR_PRIMARIA} 0%, {COR_PRIMARIA_CLARA} 100%);
        padding: 2rem 2.2rem;
        border-radius: 14px;
        margin-bottom: 1.6rem;
        box-shadow: 0 4px 18px rgba(32, 70, 59, 0.25);
    }}
    .app-header h1 {{
        color: #FFFFFF;
        font-size: 1.9rem;
        font-weight: 700;
        margin: 0 0 0.35rem 0;
    }}
    .app-header p {{
        color: #E4EFE7;
        font-size: 1rem;
        margin: 0;
    }}

    /* ── Cartões de seção ── */
    .section-card {{
        background: {COR_CARD};
        border-radius: 12px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 1.2rem;
        border: 1px solid #E7EBE4;
        box-shadow: 0 1px 4px rgba(0,0,0,0.03);
    }}

    h2, h3 {{
        color: {COR_PRIMARIA} !important;
        font-weight: 700 !important;
    }}
    h3 {{
        font-size: 1.15rem !important;
        border-left: 5px solid {COR_DESTAQUE};
        padding-left: 0.6rem;
        margin-top: 0.4rem !important;
    }}

    /* ── Métricas (KPIs) ── */
    div[data-testid="stMetric"] {{
        background: {COR_CARD};
        border: 1px solid #E7EBE4;
        border-top: 4px solid {COR_PRIMARIA_CLARA};
        border-radius: 12px;
        padding: 0.9rem 1rem 0.7rem 1rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }}
    div[data-testid="stMetricLabel"] {{
        color: {COR_NEUTRA_1};
        font-weight: 600;
    }}
    div[data-testid="stMetricValue"] {{
        color: {COR_PRIMARIA};
    }}

    /* ── Botões ── */
    .stButton>button, .stDownloadButton>button {{
        background-color: {COR_PRIMARIA};
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.55rem 1rem;
        transition: background-color 0.15s ease-in-out;
    }}
    .stButton>button:hover, .stDownloadButton>button:hover {{
        background-color: {COR_PRIMARIA_CLARA};
        color: white;
    }}

    /* ── Abas ── */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 4px;
        border-bottom: 2px solid #E7EBE4;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: transparent;
        border-radius: 8px 8px 0 0;
        padding: 0.55rem 1.1rem;
        color: {COR_NEUTRA_1};
        font-weight: 600;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {COR_CARD};
        color: {COR_PRIMARIA} !important;
        border: 1px solid #E7EBE4;
        border-bottom: 2px solid {COR_CARD};
    }}

    /* ── Expanders ── */
    .streamlit-expanderHeader {{
        background-color: #F0F3EE;
        border-radius: 8px;
        font-weight: 600;
        color: {COR_PRIMARIA};
    }}

    /* ── Dataframes ── */
    div[data-testid="stDataFrame"] {{
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #E7EBE4;
    }}

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {{
        background-color: #FFFFFF;
        border-right: 1px solid #E7EBE4;
    }}
    section[data-testid="stSidebar"] h2 {{
        font-size: 1.05rem !important;
    }}

    /* Alertas */
    div[data-testid="stAlert"] {{
        border-radius: 10px;
    }}

    footer {{visibility: hidden;}}
    #MainMenu {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)

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


def barras_agrupadas_carneiros_monta():
    """Gera o gráfico de uso de cada carneiro por monta."""
    categorias = ["Apolo", "Greek", "Zeus"]
    monta1 = [1000, 1000, 1000]
    monta2 = [750, 500, 750]
    monta3 = [333, 333, 333]

    x = np.arange(len(categorias))
    width = 0.25

    fig, ax = plt.subplots(figsize=(9, 5))

    ax.bar(x - width, monta1, width, label="Monta 1", color="#1f77b4", edgecolor="none", zorder=3)
    ax.bar(x, monta2, width, label="Monta 2", color="#2ca02c", edgecolor="none", zorder=3)
    ax.bar(x + width, monta3, width, label="Monta 3", color="#d62728", edgecolor="none", zorder=3)

    ax.set_title("Uso de cada carneiro por monta")
    ax.set_ylabel("Nº de montas")
    ax.set_xticks(x)
    ax.set_xticklabels(categorias)
    ax.set_ylim(0, 1000)
    ax.set_yticks(np.arange(0, 1001, 200))
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
    styles.add(ParagraphStyle(name="TitleCenter", parent=styles["Title"], alignment=TA_CENTER,
                               textColor=rl_colors.HexColor(COR_PRIMARIA), fontSize=22))
    styles.add(ParagraphStyle(name="Subtitulo", parent=styles["BodyText"], alignment=TA_CENTER,
                               textColor=rl_colors.HexColor(COR_NEUTRA_1), fontSize=11))
    styles.add(ParagraphStyle(name="SecaoTitulo", parent=styles["Heading2"],
                               textColor=rl_colors.HexColor(COR_PRIMARIA), fontSize=14,
                               spaceBefore=6, spaceAfter=4))
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

    for estacao in ESTACOES:
        fig = pie_figure(
            [dados["tabela_estacoes"].loc[estacao["rodada"]-1, "Prenhes"],
             dados["tabela_estacoes"].loc[estacao["rodada"]-1, "Vazias"]],
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
<div class="app-header">
    <h1>🐑 Análise Reprodutiva de Ovinos</h1>
    <p>Envie a planilha preenchida e receba automaticamente indicadores, gráficos e o relatório final em PDF.</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# BARRA LATERAL — ENTRADA DE DADOS
# ══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 📁 Dados de Entrada")
    st.markdown("**Passo 1 —** baixe o modelo (se ainda não tiver).")
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

    st.markdown("**Passo 2 —** envie a planilha preenchida.")
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
# KPIs
# ══════════════════════════════════════════════════════════════════════════
m1, m2, m3, m4 = st.columns(4)
m1.metric("🐑 Animais", f"{len(df):,}")
m2.metric("🐏 Carneiros", f"{len(todos_carneiros):,}")
m3.metric("📈 Prenhez final", f"{taxa_final:.2f}%")
m4.metric("⚠️ Vazias finais", f"{n_vazias_final:,}")

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# ABAS DE CONTEÚDO
# ══════════════════════════════════════════════════════════════════════════
tab_geral, tab_diag, tab_carneiros, tab_vazios, tab_export = st.tabs(
    ["📊 Visão Geral", "🩺 Diagnósticos", "🐏 Carneiros", "⚠️ Animais Vazios", "📥 Exportar"]
)

with tab_geral:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### Taxa de prenhez por Estação de Monta")
    st.dataframe(t_estacoes, use_container_width=True, hide_index=True)
    fig = barras_taxa_estacao(t_estacoes)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### Prenhe × Vazia por Estação de Monta")
    cols = st.columns(3)
    for idx, estacao in enumerate(ESTACOES):
        row = t_estacoes.iloc[idx]
        fig = pie_figure([row["Prenhes"], row["Vazias"]], ["Prenhe", "Vazia"], f"Estação de Monta {estacao['rodada']}")
        cols[idx].pyplot(fig, use_container_width=True)
        plt.close(fig)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### Diagnóstico de gestação final")
    st.dataframe(resumo_final, use_container_width=True, hide_index=True)
    fig = pie_figure(resumo_final["N"], resumo_final["Resultado"], "Diagnóstico de gestação final")
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)
    st.markdown('</div>', unsafe_allow_html=True)

with tab_diag:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### Diagnósticos de gestação por etapa")
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
    st.markdown('</div>', unsafe_allow_html=True)

with tab_carneiros:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### Taxa de prenhez por carneiro")
    if carneiros_cons.empty:
        st.info("Nenhum carneiro com diagnóstico válido foi encontrado.")
    else:
        st.dataframe(carneiros_cons, use_container_width=True, hide_index=True)
        fig = barh_taxa_carneiro(carneiros_cons)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### Uso de cada carneiro por monta")
    fig_uso = barras_agrupadas_carneiros_monta()
    st.pyplot(fig_uso, use_container_width=True)
    plt.close(fig_uso)
    st.markdown('</div>', unsafe_allow_html=True)

with tab_vazios:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(f"### ⚠️ {len(vazios):,} animais permaneceram vazios ao final")
    st.dataframe(vazios, use_container_width=True, hide_index=True)
    st.markdown("#### Lista simplificada")
    st.dataframe(vazios_resumida, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tab_export:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### Exportar resultados")
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
        with st.spinner("Gerando relatório em PDF..."):
            pdf_bytes = gerar_pdf(df, dados)
        st.download_button(
            "📄 Baixar relatório final em PDF",
            data=pdf_bytes,
            file_name="Relatorio_Analise_Reprodutiva_Ovinos.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown(
    f"<p style='text-align:center; color:{COR_NEUTRA_1}; font-size:0.85rem; margin-top:2rem;'>"
    "Sistema de Análise Reprodutiva de Ovinos — processamento baseado na estrutura da planilha-modelo."
    "</p>",
    unsafe_allow_html=True,
)
