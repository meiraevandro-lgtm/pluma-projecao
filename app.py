import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import math

st.set_page_config(
    page_title="Projeção de Ovos — Grupo Pluma",
    page_icon="🐓",
    layout="wide",
)

# ── Curvas oficiais ──────────────────────────────────────────────────────────

CURVA_COBB = {
    23:(0.00,0.00,100.00),24:(0.00,0.00,99.75),25:(5.00,65.00,99.50),
    26:(23.00,80.00,99.20),27:(53.00,85.00,98.90),28:(74.00,90.00,98.60),
    29:(80.00,92.00,98.30),30:(83.00,93.00,98.00),31:(84.00,94.50,97.70),
    32:(83.00,95.50,97.40),33:(82.00,96.00,97.15),34:(81.00,96.80,96.90),
    35:(80.00,97.20,96.65),36:(79.00,97.50,96.40),37:(78.00,97.50,96.15),
    38:(77.00,97.50,95.90),39:(76.00,97.50,95.65),40:(75.00,97.50,95.40),
    41:(74.00,97.50,95.15),42:(73.00,97.50,94.90),43:(72.00,97.50,94.65),
    44:(71.00,97.50,94.40),45:(70.00,97.50,94.20),46:(69.00,97.50,94.00),
    47:(67.95,97.50,93.80),48:(66.90,97.50,93.60),49:(65.85,97.50,93.40),
    50:(64.80,97.50,93.20),51:(63.75,97.50,93.00),52:(62.70,97.50,92.80),
    53:(61.65,97.50,92.60),54:(60.60,97.50,92.40),55:(59.55,97.50,92.20),
    56:(58.50,97.50,92.00),57:(57.45,97.50,91.80),58:(56.40,97.50,91.60),
    59:(55.35,97.50,91.40),60:(54.30,97.50,91.20),61:(53.25,97.50,91.00),
    62:(52.20,97.50,90.80),63:(51.50,97.50,90.60),64:(50.10,97.50,90.40),
    65:(49.05,97.50,90.20),66:(48.00,97.50,90.00),
}

CURVA_ROSS = {
    23:(0.00,0.00,100.00),24:(0.00,0.00,99.75),25:(4.00,70.00,99.50),
    26:(25.00,85.00,99.20),27:(60.00,90.00,98.90),28:(80.00,93.00,98.60),
    29:(85.00,94.40,98.30),30:(87.00,95.40,98.00),31:(87.00,96.40,97.70),
    32:(86.50,96.90,97.40),33:(86.00,97.30,97.15),34:(85.50,97.60,96.90),
    35:(85.00,97.90,96.65),36:(84.00,98.00,96.40),37:(83.00,98.00,96.15),
    38:(82.00,98.00,95.90),39:(81.00,98.00,95.65),40:(80.00,98.00,95.40),
    41:(79.00,98.00,95.15),42:(78.00,98.00,94.90),43:(77.00,98.00,94.65),
    44:(76.00,98.00,94.40),45:(75.00,98.00,94.20),46:(74.00,98.00,94.00),
    47:(73.00,98.00,93.80),48:(72.00,98.00,93.60),49:(71.00,98.00,93.40),
    50:(70.00,98.00,93.20),51:(69.00,98.00,93.00),52:(68.00,98.00,92.80),
    53:(67.00,98.00,92.60),54:(66.00,98.00,92.40),55:(65.00,98.00,92.20),
    56:(64.00,98.00,92.00),57:(63.00,98.00,91.80),58:(62.00,98.00,91.60),
    59:(61.00,98.00,91.40),60:(60.00,98.00,91.20),61:(59.00,97.50,91.00),
    62:(58.00,97.50,90.80),63:(57.00,97.50,90.60),64:(56.00,97.50,90.40),
    65:(55.00,97.50,90.20),66:(54.00,97.50,90.00),
}

CORES_UNIDADE = {
    "Pluma PR+SC":"#1a6fbf","Pluma SP":"#e07b2a","Pluma CV":"#2eaa5f",
    "Pluma MI":"#9b59b6","Pluma DF":"#e74c3c","Pluma G3":"#16a085",
    "Plusval":"#f39c12","Cassilândia":"#8e44ad",
}

HOJE = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

# ── Mapeamento de colunas por aba (0-based) ──────────────────────────────────

CUTOFF_DATE = pd.Timestamp('2025-01-01')

# Estrutura padrão da maioria das unidades
COL_DEFAULT = dict(
    aloj=1, lote_recria=3, granja_recria=6,
    raca=11, transfer=13, lote_prod=14,
    qty=18, abate_dt=19, idade_inicio=22,
)

# Pluma DF: coluna extra no início + inicia produção na semana 25
COL_DF = dict(
    aloj=2, lote_recria=4, granja_recria=7,
    raca=12, transfer=14, lote_prod=15,
    qty=18, abate_dt=19, idade_inicio=25,
)

SHEET_COLS = {'Pluma DF': COL_DF}

UNIT_SHEETS = [
    'Pluma PR+SC', 'Pluma SP', 'Pluma CV', 'Pluma MI', 'Pluma DF',
    'PLuma G3', 'Plusval', 'Cassilândia',
]

def normalize_unit(sheet):
    return sheet.replace('PLuma', 'Pluma').strip()

def get_curva(raca):
    r = str(raca).upper()
    return CURVA_ROSS if ("ROSS" in r or "HUBB" in r) else CURVA_COBB

def get_linhagem(raca):
    r = str(raca).upper()
    if "ROSS" in r or "HUBB" in r:
        return "ROSS"
    return "COBB"

def fmt_n(v):
    try:
        return f"{int(v):,}".replace(",", ".")
    except:
        return str(v)

# ── Leitura do arquivo de alojamento ────────────────────────────────────────

def ler_alojamento(uploaded_file):
    """Lê o arquivo de alojamento completo e extrai lotes de todas as unidades."""
    xl = pd.ExcelFile(uploaded_file)
    todos_lotes = []

    for sheet in UNIT_SHEETS:
        # aceita variações de capitalização
        sheet_real = next((s for s in xl.sheet_names if s.strip().lower() == sheet.strip().lower()), None)
        if sheet_real is None:
            continue

        df = pd.read_excel(xl, sheet_name=sheet_real, header=None)
        unit = normalize_unit(sheet)
        C = SHEET_COLS.get(sheet_real, SHEET_COLS.get(sheet, COL_DEFAULT))

        for i, row in df.iterrows():
            if i == 0:
                continue
            try:
                # Data de alojamento — filtro base >= 01/01/2025
                aloj_val = row.iloc[C['aloj']]
                if not isinstance(aloj_val, (datetime, pd.Timestamp)):
                    continue
                aloj_dt = pd.Timestamp(aloj_val)
                if aloj_dt < CUTOFF_DATE:
                    continue

                lote_recria   = str(row.iloc[C['lote_recria']]).strip()
                granja_recria = str(row.iloc[C['granja_recria']]).strip()
                raca          = str(row.iloc[C['raca']]).strip()
                transfer_val  = row.iloc[C['transfer']]
                qty_val       = row.iloc[C['qty']]
                abate_val     = row.iloc[C['abate_dt']]
                lote_prod     = str(row.iloc[C['lote_prod']]).strip()
                idade_inicio  = C['idade_inicio']

                if pd.isna(transfer_val) or pd.isna(abate_val):
                    continue
                if pd.isna(qty_val) or float(qty_val) <= 0:
                    continue
                if not isinstance(transfer_val, (datetime, pd.Timestamp)):
                    continue
                if not isinstance(abate_val, (datetime, pd.Timestamp)):
                    continue
                if lote_prod in ('nan', 'NaN', ''):
                    continue

                transfer = pd.Timestamp(transfer_val)
                abate    = pd.Timestamp(abate_val)
                if abate <= transfer:
                    continue

                todos_lotes.append(dict(
                    unidade=unit,
                    lote=lote_prod,
                    lote_recria=lote_recria,
                    granja=granja_recria,
                    raca=raca,
                    linhagem=get_linhagem(raca),
                    aloj_dt=aloj_dt,
                    transfer=transfer,
                    abate=abate,
                    femeas=float(qty_val),
                    idade_inicio=idade_inicio,
                ))
            except Exception:
                continue

    return todos_lotes

# ── Cálculo de projeção ──────────────────────────────────────────────────────

def calcular_projecao(lotes):
    resumo_rows = []
    proj_rows   = []

    for l in lotes:
        curva        = get_curva(l['raca'])
        transfer     = l['transfer']
        abate        = l['abate']
        idade_inicio = l['idade_inicio']
        femeas       = l['femeas']

        semanas_lote = []
        for sem in range(idade_inicio, 67):
            if sem not in curva:
                continue
            weeks_from_transfer = sem - idade_inicio
            dt_sem = transfer + timedelta(weeks=weeks_from_transfer)
            if dt_sem > abate:
                break
            pos, apr, viab = curva[sem]
            aves  = femeas * (viab / 100)
            ovos  = aves * (pos / 100) * (apr / 100) * 7
            semanas_lote.append(dict(
                lote=l['lote'], lote_recria=l['lote_recria'],
                granja=l['granja'], raca=l['raca'], linhagem=l['linhagem'],
                femeas=femeas, dt_aloj=l['aloj_dt'], unidade=l['unidade'],
                semana=sem, dt_sem=dt_sem,
                ano=dt_sem.year, mes=dt_sem.month,
                pos=pos, ovos_incub=ovos,
            ))

        if not semanas_lote:
            continue

        proj_rows.extend(semanas_lote)

        sem_atual  = max(0, (HOJE - transfer.to_pydatetime()).days // 7) + idade_inicio
        pico       = max(semanas_lote, key=lambda x: x['pos'])
        total_ovos = sum(p['ovos_incub'] for p in semanas_lote)
        sems_pico  = max(0, pico['semana'] - sem_atual)
        alerta     = 0 <= sems_pico <= 4 and sem_atual < 66

        resumo_rows.append(dict(
            unidade=l['unidade'], lote=l['lote'], lote_recria=l['lote_recria'],
            granja=l['granja'], raca=l['raca'], linhagem=l['linhagem'],
            femeas=femeas, dt_aloj=l['aloj_dt'],
            sem_atual=sem_atual, pico_pct=pico['pos'],
            pico_sem=pico['semana'], pico_dt=pico['dt_sem'],
            total_ovos=total_ovos, sems_pico=sems_pico, alerta=alerta,
        ))

    return pd.DataFrame(resumo_rows), pd.DataFrame(proj_rows)

# ── Interface ────────────────────────────────────────────────────────────────

st.title("🐓 Projeção de Ovos — Grupo Pluma")
st.caption(f"Curvas oficiais COBB e ROSS · {HOJE.strftime('%d/%m/%Y')} · Alojamentos a partir de 01/01/2025")
st.markdown("---")

# ── Upload único ─────────────────────────────────────────────────────────────

with st.expander("📂 Carregar arquivo de alojamento", expanded=True):
    st.markdown("Faça upload do arquivo **Alojamento Atual Grupo Pluma.xlsx** — todas as unidades serão carregadas automaticamente.")
    arquivo = st.file_uploader(
        "Arquivo de alojamento", type=["xlsx", "xls"],
        label_visibility="collapsed", key="up_alojamento")

    if arquivo:
        with st.spinner("Lendo arquivo e processando todas as unidades..."):
            try:
                lotes = ler_alojamento(arquivo)
                if lotes:
                    df_res, df_proj = calcular_projecao(lotes)
                    st.session_state['df_res']  = df_res
                    st.session_state['df_proj'] = df_proj
                    unidades_ok = sorted(df_res['unidade'].unique())
                    st.success(f"✅ {len(lotes)} lotes carregados | {len(unidades_ok)} unidades: {', '.join(unidades_ok)}")
                else:
                    st.warning("Nenhum lote válido encontrado. Verifique se o arquivo está correto.")
            except Exception as e:
                st.error(f"Erro ao processar arquivo: {e}")

# ── Dashboard ────────────────────────────────────────────────────────────────

if 'df_res' not in st.session_state or st.session_state['df_res'].empty:
    st.info("Faça upload do arquivo de alojamento para ver o dashboard.")
    st.stop()

df_res_full  = st.session_state['df_res']
df_proj_full = st.session_state['df_proj']

st.markdown("---")

# Filtros
unidades_disp = ["Todas"] + sorted(df_res_full['unidade'].unique().tolist())
unidade_view  = st.radio("Visualizar", unidades_disp, horizontal=True)

if unidade_view == "Todas":
    df_res_v  = df_res_full.copy()
    df_proj_v = df_proj_full.copy()
else:
    df_res_v  = df_res_full[df_res_full['unidade'] == unidade_view].copy()
    df_proj_v = df_proj_full[df_proj_full['unidade'] == unidade_view].copy()

fc1, fc2, fc3 = st.columns(3)
granjas   = ["Todas"] + sorted(df_res_v['granja'].dropna().unique().tolist())
linhagens = ["Todas"] + sorted(df_res_v['linhagem'].dropna().unique().tolist())
anos      = ["Todos"] + sorted(df_proj_v['ano'].unique().tolist())

with fc1: fil_granja = st.selectbox("Granja de Recria", granjas)
with fc2: fil_lin    = st.selectbox("Linhagem", linhagens)
with fc3: fil_ano    = st.selectbox("Ano", anos)

res  = df_res_v.copy()
proj = df_proj_v.copy()

if fil_granja != "Todas": res = res[res['granja'] == fil_granja]; proj = proj[proj['granja'] == fil_granja]
if fil_lin    != "Todas": res = res[res['linhagem'] == fil_lin];  proj = proj[proj['linhagem'] == fil_lin]
if fil_ano    != "Todos": proj = proj[proj['ano'] == int(fil_ano)]

alertas = res[res['alerta']]

# KPIs
k1, k2, k3, k4 = st.columns(4)
k1.metric("Fêmeas no plantel",  fmt_n(res['femeas'].sum()))
k2.metric("Lotes processados",  len(res))
k3.metric("Ovos proj. (total)", f"{res['total_ovos'].sum()/1e6:.1f}M")
k4.metric("Alertas de pico",    len(alertas))

st.markdown("---")

# Curva consolidada
grp = proj.groupby(["ano","mes"])["ovos_incub"].sum().reset_index()
grp["periodo"] = pd.to_datetime(
    grp["ano"].astype(str) + "-" + grp["mes"].astype(str).str.zfill(2) + "-01")
grp = grp.sort_values("periodo")
hm  = pd.Timestamp(HOJE.year, HOJE.month, 1)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=grp[grp["periodo"] < hm]["periodo"],
    y=grp[grp["periodo"] < hm]["ovos_incub"].round(),
    mode="lines+markers", name="Realizado",
    line=dict(color="#185FA5", width=2.5), marker=dict(size=4)))
fig.add_trace(go.Scatter(
    x=grp[grp["periodo"] >= hm]["periodo"],
    y=grp[grp["periodo"] >= hm]["ovos_incub"].round(),
    mode="lines+markers", name="Projetado",
    line=dict(color="#85B7EB", width=2, dash="dot"), marker=dict(size=4)))
fig.add_shape(type="line", x0=str(hm.date()), x1=str(hm.date()),
              y0=0, y1=1, yref="paper",
              line=dict(dash="dash", color="#aaa", width=1))
fig.add_annotation(x=str(hm.date()), y=1, yref="paper",
                   text="hoje", showarrow=False, yanchor="bottom",
                   font=dict(size=11, color="#888"))
fig.update_layout(
    title=f"Curva consolidada — {'Todas as unidades' if unidade_view == 'Todas' else unidade_view}",
    height=350, margin=dict(l=60, r=20, t=60, b=40),
    plot_bgcolor="#fff", paper_bgcolor="#fff",
    legend=dict(orientation="h", y=1.1),
    yaxis=dict(tickformat=",.0f"))
st.plotly_chart(fig, use_container_width=True)

# Por unidade (somente no modo Todas)
if unidade_view == "Todas":
    st.subheader("Por unidade")
    fig_u = go.Figure()
    for u in sorted(df_proj_v['unidade'].unique()):
        sub = df_proj_v[df_proj_v['unidade'] == u].groupby(["ano","mes"])["ovos_incub"].sum().reset_index()
        sub["periodo"] = pd.to_datetime(
            sub["ano"].astype(str) + "-" + sub["mes"].astype(str).str.zfill(2) + "-01")
        sub = sub.sort_values("periodo")
        fig_u.add_trace(go.Scatter(
            x=sub["periodo"], y=sub["ovos_incub"].round(),
            mode="lines", name=u,
            line=dict(color=CORES_UNIDADE.get(u, "#888"), width=2)))
    fig_u.update_layout(
        height=320, margin=dict(l=60, r=20, t=20, b=40),
        plot_bgcolor="#fff", paper_bgcolor="#fff",
        legend=dict(orientation="h", y=1.15),
        yaxis=dict(tickformat=",.0f"))
    st.plotly_chart(fig_u, use_container_width=True)

# Por linhagem + Top 10
c_lin, c_top = st.columns(2)
cores_lin = {"COBB": "#185FA5", "ROSS": "#BA7517"}
cores_lin_rgba = {"COBB": "rgba(24,95,165,0.6)", "ROSS": "rgba(186,117,23,0.6)"}

with c_lin:
    fig2 = go.Figure()
    for lin in proj['linhagem'].unique():
        sub = proj[proj['linhagem'] == lin].groupby(["ano","mes"])["ovos_incub"].sum().reset_index()
        sub["periodo"] = pd.to_datetime(
            sub["ano"].astype(str) + "-" + sub["mes"].astype(str).str.zfill(2) + "-01")
        sub = sub.sort_values("periodo")
        fig2.add_trace(go.Scatter(
            x=sub["periodo"], y=sub["ovos_incub"].round(),
            mode="lines", name=lin,
            line=dict(color=cores_lin.get(lin, "#888"), width=2)))
    fig2.update_layout(
        title="Por linhagem", height=280,
        margin=dict(l=50, r=10, t=40, b=30),
        plot_bgcolor="#fff", paper_bgcolor="#fff",
        legend=dict(orientation="h", y=1.15),
        yaxis=dict(tickformat=",.0f"))
    st.plotly_chart(fig2, use_container_width=True)

with c_top:
    top10 = res.nlargest(10, "total_ovos")[["lote","total_ovos","linhagem","unidade"]]
    fig3  = go.Figure(go.Bar(
        x=top10["total_ovos"].round(), y=top10["lote"],
        orientation="h",
        marker_color=[cores_lin_rgba.get(r, "rgba(128,128,128,0.6)") for r in top10["linhagem"]],
    ))
    fig3.update_layout(
        title="Top 10 lotes por volume", height=280,
        margin=dict(l=80, r=40, t=40, b=30),
        plot_bgcolor="#fff", paper_bgcolor="#fff",
        yaxis=dict(autorange="reversed"),
        xaxis=dict(tickformat=",.0f"))
    st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")

# Alertas
st.subheader("⚠️ Alertas — pico nas próximas 4 semanas")
if alertas.empty:
    st.success("Nenhum lote entrando em pico nas próximas 4 semanas.")
else:
    df_al = alertas[["unidade","lote","lote_recria","granja","linhagem","femeas","sems_pico","pico_dt","pico_pct"]].copy()
    df_al["femeas"]   = df_al["femeas"].apply(fmt_n)
    df_al["pico_dt"]  = pd.to_datetime(df_al["pico_dt"]).dt.strftime("%d/%m/%Y")
    df_al["pico_pct"] = df_al["pico_pct"].apply(lambda v: f"{v:.1f}%")
    df_al["sems_pico"]= df_al["sems_pico"].apply(lambda v: f"{int(v)} sem.")
    df_al.columns = ["Unidade","Lote Prod.","Lote Recria","Granja Recria","Linhagem","Fêmeas","Sem. p/ pico","Data pico","% pico"]
    st.dataframe(df_al, use_container_width=True, hide_index=True)

st.markdown("---")

# Tabela completa de lotes
st.subheader("Todos os lotes")
df_tab = res[["unidade","lote","lote_recria","granja","linhagem","dt_aloj",
              "femeas","sem_atual","pico_sem","pico_dt","pico_pct","total_ovos"]].copy()
df_tab["dt_aloj"]    = pd.to_datetime(df_tab["dt_aloj"]).dt.strftime("%d/%m/%Y")
df_tab["pico_dt"]    = pd.to_datetime(df_tab["pico_dt"]).dt.strftime("%d/%m/%Y")
df_tab["pico_pct"]   = df_tab["pico_pct"].apply(lambda v: f"{v:.1f}%")
df_tab["femeas"]     = df_tab["femeas"].apply(fmt_n)
df_tab["total_ovos"] = df_tab["total_ovos"].apply(lambda v: f"{v:,.0f}".replace(",","."))
df_tab.columns = ["Unidade","Lote Prod.","Lote Recria","Granja Recria","Linhagem",
                  "Dt. Aloj.","Fêmeas","Sem. atual","Sem. pico","Data pico","% pico","Ovos proj."]
st.dataframe(df_tab.sort_values("Sem. atual", ascending=False),
             use_container_width=True, hide_index=True)

st.caption("Grupo Pluma · Sistema de Projeção de Ovos · Curvas oficiais COBB e ROSS")
