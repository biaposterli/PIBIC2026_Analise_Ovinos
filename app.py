import io
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, PageBreak
)

st.set_page_config(
    page_title="Análise Reprodutiva de Ovinos",
    page_icon="🐑",
    layout="wide",
)

COLUNAS_OBRIGATORIAS = [
    "Ordem",
    "Número de Identificação",
    "Diagnóstico de Gestação Inicial",
    "Protocolo de IATF_1",
    "Carneiro_IATF_1",
    "Diagnóstico de Gestação 1",
    "Protocolo de IATF_2",
    "Carneiro_IATF_2",
    "Diagnóstico de Gestação 2",
    "Protocolo de IATF_3",
    "Carneiro_IATF_3",
    "Diagnóstico de Gestação 3",
    "Diagnóstico de Gestação Final",
]

IATFS = [
    {"rodada": 1, "protocolo": "Protocolo de IATF_1", "carneiro": "Carneiro_IATF_1", "diagnostico": "Diagnóstico de Gestação 1"},
    {"rodada": 2, "protocolo": "Protocolo de IATF_2", "carneiro": "Carneiro_IATF_2", "diagnostico": "Diagnóstico de Gestação 2"},
    {"rodada": 3, "protocolo": "Protocolo de IATF_3", "carneiro": "Carneiro_IATF_3", "diagnostico": "Diagnóstico de Gestação 3"},
]

MODEL_PATH = Path(__file__).with_name("Modelo_Dados_Ovinos_IATF.xlsx")


def norm(x):
    return str(x).strip().casefold()


def validar_colunas(df):
    return [c for c in COLUNAS_OBRIGATORIAS if c not in df.columns]


def resumo_iatf(df):
    linhas = []
    for iatf in IATFS:
        protocolo = iatf["protocolo"]
        diag = iatf["diagnostico"]
        mask_protocolo = df[protocolo].notna() & df[protocolo].astype(str).str.strip().ne("")
        diag_norm = df[diag].map(norm)
        validos = mask_protocolo & diag_norm.isin(["prenhe", "vazia"])
        prenhes = (mask_protocolo & (diag_norm == "prenhe")).sum()
        vazias = (mask_protocolo & (diag_norm == "vazia")).sum()
        submetidos = mask_protocolo.sum()
        n_validos = validos.sum()
        taxa = prenhes / n_validos * 100 if n_validos else np.nan
        linhas.append({
            "IATF": f"IATF {iatf['rodada']}",
            "Animais submetidos": int(submetidos),
            "Diagnósticos válidos": int(n_validos),
            "Prenhes": int(prenhes),
            "Vazias": int(vazias),
            "Taxa de prenhez (%)": round(taxa, 2) if pd.notna(taxa) else np.nan,
        })
    return pd.DataFrame(linhas)


def diagnostico_tabela(df, coluna):
    s = df[coluna].copy()
    s = s.where(s.notna(), "Não informado")
    s = s.astype(str).str.strip()
    c = s.value_counts()
    out = pd.DataFrame({"Diagnóstico": c.index, "N": c.values})
    out["%"] = (out["N"] / len(df) * 100).round(2)
    return out


def carneiros(df):
    nomes = set()
    por_iatf = {}
    for iatf in IATFS:
        s = df[iatf["carneiro"]].dropna().astype(str).str.strip()
        s = s[s.ne("")]
        vals = sorted(s.unique().tolist())
        por_iatf[iatf["rodada"]] = vals
        nomes.update(vals)
    return sorted(nomes), por_iatf


def taxa_carneiro(df, iatf):
    p = iatf["protocolo"]
    c = iatf["carneiro"]
    d = iatf["diagnostico"]
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
    for iatf in IATFS:
        t = taxa_carneiro(df, iatf)
        if not t.empty:
            t["IATF"] = iatf["rodada"]
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
                "Nº de IATFs utilizadas": ("IATF", "nunique"),
            }
        )
    )
    out["Taxa de prenhez (%)"] = (out["Prenhes"] / out["Animais avaliados"] * 100).round(2)
    return out


def pie_figure(values, labels, title):
    fig, ax = plt.subplots(figsize=(5.8, 5.2))
    vals = [int(v) for v in values]
    if sum(vals) == 0:
        ax.text(0.5, 0.5, "Sem dados válidos", ha="center", va="center")
        ax.axis("off")
    else:
        ax.pie(vals, labels=labels, autopct="%1.1f%%", startangle=90,
               wedgeprops={"edgecolor": "white"})
        ax.set_title(title)
    fig.tight_layout()
    return fig


def fig_to_png(fig):
    b = io.BytesIO()
    fig.savefig(b, format="png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    b.seek(0)
    return b


def tabela_pdf(df, max_rows=40):
    if df is None or df.empty:
        return Table([["Sem dados"]])
    x = df.head(max_rows).copy()
    data = [list(x.columns)] + x.fillna("").astype(str).values.tolist()
    t = Table(data, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAD3")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
    ]))
    return t


def gerar_pdf(df, dados):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=1.4*cm, leftMargin=1.4*cm,
                            topMargin=1.3*cm, bottomMargin=1.3*cm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleCenter", parent=styles["Title"], alignment=TA_CENTER))
    story = []

    story.append(Paragraph("Análise da Eficiência Reprodutiva de Ovinos", styles["TitleCenter"]))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        f"Total de animais analisados: {len(df):,}<br/>"
        f"Carneiros distintos identificados: {len(dados['carneiros'])}<br/>"
        f"Taxa de prenhez final: {dados['taxa_final']:.2f}%",
        styles["BodyText"]
    ))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("1. Resultados por IATF", styles["Heading2"]))
    story.append(tabela_pdf(dados["tabela_iatf"]))
    story.append(Spacer(1, 0.3*cm))

    for iatf in IATFS:
        fig = pie_figure(
            [dados["tabela_iatf"].loc[iatf["rodada"]-1, "Prenhes"],
             dados["tabela_iatf"].loc[iatf["rodada"]-1, "Vazias"]],
            ["Prenhe", "Vazia"],
            f"Prenhe x Vazia — IATF {iatf['rodada']}"
        )
        story.append(RLImage(fig_to_png(fig), width=10.5*cm, height=9.4*cm))

    story.append(PageBreak())
    story.append(Paragraph("2. Diagnóstico de gestação final", styles["Heading2"]))
    story.append(tabela_pdf(dados["resumo_final"]))
    fig = pie_figure(
        dados["resumo_final"]["N"].tolist(),
        dados["resumo_final"]["Resultado"].tolist(),
        "Diagnóstico de gestação final"
    )
    story.append(RLImage(fig_to_png(fig), width=11*cm, height=10*cm))

    story.append(PageBreak())
    story.append(Paragraph("3. Desempenho dos carneiros", styles["Heading2"]))
    story.append(tabela_pdf(dados["carneiros_consolidado"]))
    if not dados["carneiros_consolidado"].empty:
        for _, row in dados["carneiros_consolidado"].iterrows():
            fig = pie_figure(
                [row["Prenhes"], row["Vazias"]],
                ["Prenhe", "Vazia"],
                f"Carneiro {row['Carneiro']}"
            )
            story.append(RLImage(fig_to_png(fig), width=9*cm, height=8*cm))
    story.append(PageBreak())

    story.append(Paragraph("4. Animais que permaneceram vazios ao final", styles["Heading2"]))
    story.append(Paragraph(
        f"Total de animais vazios: {len(dados['vazios']):,}.",
        styles["BodyText"]
    ))
    story.append(Spacer(1, 0.2*cm))
    story.append(tabela_pdf(dados["vazios_resumida"], max_rows=100))

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()


st.markdown("# 🐑 Análise Reprodutiva de Ovinos")
st.markdown("Envie a planilha preenchida e receba automaticamente as análises, gráficos e relatório final.")

c1, c2 = st.columns(2)
with c1:
    if MODEL_PATH.exists():
        st.download_button(
            "📥 Baixar modelo da planilha",
            data=MODEL_PATH.read_bytes(),
            file_name="Modelo_Dados_Ovinos_IATF.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
with c2:
    uploaded = st.file_uploader(
        "📤 Envie a planilha preenchida",
        type=["xlsx", "xls"],
        help="Use o modelo disponibilizado acima e mantenha os nomes das colunas.",
    )

if uploaded is None:
    st.info("Baixe o modelo, preencha os dados e envie a planilha para iniciar a análise.")
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

# Cálculos
t_iatf = resumo_iatf(df)
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

todos_carneiros, carneiros_por_iatf = carneiros(df)
carneiros_cons = consolidado_carneiros(df)

vazios = df.loc[dg_final == "vazia"].copy()
cols_resumidas = [c for c in ["Ordem", "Número de Identificação", "Diagnóstico de Gestação Final"] if c in vazios.columns]
vazios_resumida = vazios[cols_resumidas].reset_index(drop=True)

dados = {
    "tabela_iatf": t_iatf,
    "resumo_final": resumo_final,
    "carneiros": todos_carneiros,
    "carneiros_consolidado": carneiros_cons,
    "vazios": vazios,
    "vazios_resumida": vazios_resumida,
    "taxa_final": taxa_final,
}

st.success(f"✅ Planilha analisada: {len(df):,} animais.")

# Dashboard
st.markdown("## 📊 Dashboard")
m1, m2, m3, m4 = st.columns(4)
m1.metric("🐑 Animais", f"{len(df):,}")
m2.metric("🐏 Carneiros", f"{len(todos_carneiros):,}")
m3.metric("📈 Prenhez final", f"{taxa_final:.2f}%")
m4.metric("⚠️ Vazias finais", f"{n_vazias_final:,}")

st.markdown("### 📈 Taxa de prenhez por IATF")
st.dataframe(t_iatf, use_container_width=True, hide_index=True)

fig, ax = plt.subplots(figsize=(9, 4.5))
ax.bar(t_iatf["IATF"], t_iatf["Taxa de prenhez (%)"])
ax.set_ylim(0, 100)
ax.set_ylabel("Taxa de prenhez (%)")
ax.set_title("Taxa de prenhez por IATF")
for i, v in enumerate(t_iatf["Taxa de prenhez (%)"]):
    if pd.notna(v):
        ax.text(i, v + 1, f"{v:.1f}%", ha="center")
fig.tight_layout()
st.pyplot(fig, use_container_width=True)
plt.close(fig)

st.markdown("### 🥧 Prenhe × Vazia por IATF")
cols = st.columns(3)
for idx, iatf in enumerate(IATFS):
    row = t_iatf.iloc[idx]
    fig = pie_figure([row["Prenhes"], row["Vazias"]], ["Prenhe", "Vazia"], f"IATF {iatf['rodada']}")
    cols[idx].pyplot(fig, use_container_width=True)
    plt.close(fig)

st.markdown("### 🩺 Diagnóstico de gestação")
for coluna in ["Diagnóstico de Gestação Inicial", "Diagnóstico de Gestação 1",
               "Diagnóstico de Gestação 2", "Diagnóstico de Gestação 3",
               "Diagnóstico de Gestação Final"]:
    with st.expander(coluna):
        tab = diagnostico_tabela(df, coluna)
        st.dataframe(tab, use_container_width=True, hide_index=True)
        fig = pie_figure(tab["N"], tab["Diagnóstico"], coluna)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

st.markdown("### 🐏 Taxa de prenhez por carneiro")
if carneiros_cons.empty:
    st.info("Nenhum carneiro com diagnóstico válido foi encontrado.")
else:
    st.dataframe(carneiros_cons, use_container_width=True, hide_index=True)
    fig, ax = plt.subplots(figsize=(9, max(4.5, len(carneiros_cons) * 0.55)))
    p = carneiros_cons.sort_values("Taxa de prenhez (%)")
    ax.barh(p["Carneiro"], p["Taxa de prenhez (%)"])
    ax.set_xlim(0, 100)
    ax.set_xlabel("Taxa de prenhez (%)")
    ax.set_title("Taxa de prenhez consolidada por carneiro")
    for y, v in enumerate(p["Taxa de prenhez (%)"]):
        ax.text(v + 1, y, f"{v:.1f}%", va="center")
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

st.markdown("### 🧪 Prenhez por protocolo/IATF")
st.dataframe(t_iatf, use_container_width=True, hide_index=True)

st.markdown("### 🥧 Diagnóstico final")
st.dataframe(resumo_final, use_container_width=True, hide_index=True)
fig = pie_figure(resumo_final["N"], resumo_final["Resultado"], "Diagnóstico de gestação final")
st.pyplot(fig, use_container_width=True)
plt.close(fig)

st.markdown("### ⚠️ Animais que permaneceram vazios ao final")
st.write(f"**{len(vazios):,} animais** permaneceram vazios ao final.")
st.dataframe(vazios, use_container_width=True, hide_index=True)

st.markdown("#### Lista simplificada")
st.dataframe(vazios_resumida, use_container_width=True, hide_index=True)

# Downloads
st.markdown("## 📥 Downloads")
excel_buffer = io.BytesIO()
with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
    t_iatf.to_excel(writer, sheet_name="Resumo IATF", index=False)
    resumo_final.to_excel(writer, sheet_name="Diagnostico Final", index=False)
    carneiros_cons.to_excel(writer, sheet_name="Carneiros", index=False)
    vazios.to_excel(writer, sheet_name="Animais Vazios", index=False)
excel_buffer.seek(0)

st.download_button(
    "📊 Baixar resultados em Excel",
    data=excel_buffer.getvalue(),
    file_name="Resultados_Analise_Reprodutiva_Ovinos.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
)

pdf_bytes = gerar_pdf(df, dados)
st.download_button(
    "📄 Baixar relatório final em PDF",
    data=pdf_bytes,
    file_name="Relatorio_Analise_Reprodutiva_Ovinos.pdf",
    mime="application/pdf",
    use_container_width=True,
)

st.caption("Sistema de análise reprodutiva de ovinos — processamento baseado na estrutura da planilha-modelo.")
