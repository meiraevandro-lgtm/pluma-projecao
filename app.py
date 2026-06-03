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
    "Pluma PR+SC": "#1a6fbf","Pluma SP": "#e07b2a","Pluma CV": "#2eaa5f",
    "Pluma MI": "#9b59b6","Pluma DF": "#e74c3c","Pluma G3": "#16a085",
    "Argentina": "#2c3e50","Plusval": "#f39c12","Cassilândia": "#8e44ad",
    "PlumaGen": "#27ae60",
}
CORES_RGBA = {
    "Pluma PR+SC":"rgba(26,111,191,0.6)","Pluma SP":"rgba(224,123,42,0.6)",
    "Pluma CV":"rgba(46,170,95,0.6)","Pluma MI":"rgba(155,89,182,0.6)",
    "Pluma DF":"rgba(231,76,60,0.6)","Pluma G3":"rgba(22,160,133,0.6)",
    "Argentina":"rgba(44,62,80,0.6)","Plusval":"rgba(243,156,18,0.6)",
    "Cassilândia":"rgba(142,68,173,0.6)","PlumaGen":"rgba(39,174,96,0.6)",
}
RACAS_DISP = ["COBB", "ROSS", "HUBBARD"]

def get_curva(raca):
    r = str(raca).upper()
    return CURVA_ROSS if ("ROSS" in r or "HUBB" in r) else CURVA_COBB

HOJE = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

def parse_qtde(v):
    if v is None:
        return 0
    if isinstance(v, (int, float)):
        return 0 if math.isnan(v) else int(v)
    s = str(v).strip()
    if s in ("", "nan", "None", "NaT", "NaN"):
        return 0
    s = s.replace(".", "").replace(",", "").split()[0]
    try:
        return int(s)
    except:
        return 0

def parse_data(v):
    if isinstance(v, datetime):
        return v
    if isinstance(v, pd.Timestamp):
        return v.to_pydatetime()
    s = str(v).strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s[:10], fmt)
        except:
            pass
    return None

def extrair_lotes(df):
    """Lê o Excel de alojamento e devolve lista de dicts com campos básicos."""
    col_map = {
        "Dt. Aloj.":"dt_aloj","Dt. Alojamento":"dt_aloj",
        "Lote":"lote","Recria":"granja",
        "Núcleo":"nucleo","Nucleo":"nucleo",
        "Qtde.":"qtde","Qtde":"qtde",
        "Raca":"raca","Raça":"raca",
        "Reg.":"reg","Reg":"reg",
    }
    df = df.rename(columns={k:v for k,v in col_map.items() if k in df.columns})
    invalidos = {"#n/d","#n/a","solicitar lote","","nan","none","undefined"}
    mapa = {}
    for _, r in df.iterrows():
        lote = str(r.get("lote","")).strip()
        if not lote or lote.lower() in invalidos:
            continue
        qtde = parse_qtde(r.get("qtde", r.get("Qtde.",0)))
        if qtde <= 0:
            continue
        dt = parse_data(r.get("dt_aloj",""))
        if not dt:
            continue
        raca   = str(r.get("raca","COBB")).strip()
        granja = str(r.get("granja","")).strip()
        nucleo = str(r.get("nucleo","")).strip()
        key = lote + "||" + granja
        if key not in mapa:
            mapa[key] = {"lote":lote,"granja":granja,"nucleo":nucleo,
                         "raca":raca,"dt_aloj":dt,"femeas":0}
        mapa[key]["femeas"] += qtde
    return list(mapa.values())

def calcular_projecao(lotes, unidade):
    """Recebe lista de dicts de lotes e gera DataFrames resumo + projeção."""
    proj = []
    for l in lotes:
        curva = get_curva(l["raca"])
        for sem in range(23, 67):
            if sem not in curva:
                continue
            pos, apr, viab = curva[sem]
            dt_sem = l["dt_aloj"] + timedelta(weeks=sem)
            aves   = l["femeas"] * (viab / 100)
            ovos_i = aves * (pos / 100) * 7 * (apr / 100)
            proj.append({
                "lote":l["lote"],"granja":l["granja"],"raca":l["raca"],
                "femeas":l["femeas"],"dt_aloj":l["dt_aloj"],"unidade":unidade,
                "semana":sem,"dt_sem":dt_sem,
                "ano":dt_sem.year,"mes":dt_sem.month,
                "pos":pos,"ovos_incub":ovos_i,
            })

    resumo = []
    for l in lotes:
        lp = [p for p in proj if p["lote"]==l["lote"] and p["granja"]==l["granja"]]
        if not lp:
            continue
        pico       = max(lp, key=lambda x: x["pos"])
        total_ovos = sum(p["ovos_incub"] for p in lp)
        sem_atual  = max(0, (HOJE - l["dt_aloj"]).days // 7)
        sems_pico  = max(0, pico["semana"] - sem_atual)
        resumo.append({**l, "unidade":unidade,
            "sem_atual":sem_atual,"pico_pct":pico["pos"],
            "pico_sem":pico["semana"],"pico_dt":pico["dt_sem"],
            "total_ovos":total_ovos,"sems_pico":sems_pico,
            "alerta": 0 <= sems_pico <= 4 and sem_atual < 66,
        })
    return pd.DataFrame(resumo), pd.DataFrame(proj)

def fmt_n(v):
    return f"{int(v):,}".replace(",",".")

# ── Interface ────────────────────────────────────────────────────────────────
st.title("🐓 Projeção de Ovos — Grupo Pluma")
st.caption(f"Curvas oficiais COBB e ROSS · {HOJE.strftime('%d/%m/%Y')}")
st.markdown("---")

UNIDADES = ["Pluma PR+SC","Pluma SP","Pluma CV","Pluma MI","Pluma DF",
            "Pluma G3","Argentina","Plusval","Cassilândia","PlumaGen"]

if "dados_unidades" not in st.session_state:
    st.session_state.dados_unidades = {}
if "lotes_editor" not in st.session_state:
    st.session_state.lotes_editor = {}   # unidade -> lista de dicts editáveis

# ── Upload ───────────────────────────────────────────────────────────────────
with st.expander("📂 Carregar / editar lotes por unidade", expanded=True):
    col_sel, col_up = st.columns([1, 2])
    with col_sel:
        unidade_sel = st.selectbox("Unidade", UNIDADES)
    with col_up:
        arquivo = st.file_uploader(
            f"Excel de {unidade_sel}", type=["xlsx","xls","csv"],
            label_visibility="collapsed", key=f"up_{unidade_sel}")

    if arquivo:
        try:
            if arquivo.name.endswith(".csv"):
                df_raw = pd.read_csv(arquivo, sep="\t", encoding="utf-8-sig")
            else:
                df_raw = pd.read_excel(arquivo)
            lotes_raw = extrair_lotes(df_raw)
            if lotes_raw:
                st.session_state.lotes_editor[unidade_sel] = lotes_raw
                st.success(f"✓ {len(lotes_raw)} lotes carregados de {unidade_sel} — revise e ajuste abaixo.")
            else:
                st.warning("Nenhum lote válido encontrado.")
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")

    # ── Tabela editável ──────────────────────────────────────────────────────
    if unidade_sel in st.session_state.lotes_editor:
        st.markdown(f"**✏️ Revise e ajuste os lotes de {unidade_sel} antes de projetar:**")
        lotes_orig = st.session_state.lotes_editor[unidade_sel]

        df_edit = pd.DataFrame([{
            "Lote":      l["lote"],
            "Granja":    l["granja"],
            "Dt. Aloj.": l["dt_aloj"].strftime("%d/%m/%Y") if isinstance(l["dt_aloj"], datetime) else str(l["dt_aloj"]),
            "Fêmeas":    l["femeas"],
            "Linhagem":  l["raca"],
        } for l in lotes_orig])

        df_editado = st.data_editor(
            df_edit,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            column_config={
                "Lote":      st.column_config.TextColumn("Lote"),
                "Granja":    st.column_config.TextColumn("Granja"),
                "Dt. Aloj.": st.column_config.TextColumn("Dt. Aloj.", help="Formato: DD/MM/AAAA"),
                "Fêmeas":    st.column_config.NumberColumn("Fêmeas", min_value=0, step=1, format="%d"),
                "Linhagem":  st.column_config.SelectboxColumn("Linhagem", options=RACAS_DISP),
            },
            key=f"editor_{unidade_sel}",
        )

        col_projetar, col_add, col_remove = st.columns([2, 1, 1])
        with col_projetar:
            if st.button(f"▶ Projetar {unidade_sel}", type="primary", use_container_width=True):
                lotes_finais = []
                erros = []
                for i, row in df_editado.iterrows():
                    lote  = str(row["Lote"]).strip()
                    granja= str(row["Granja"]).strip()
                    femeas= int(row["Fêmeas"]) if pd.notna(row["Fêmeas"]) else 0
                    raca  = str(row["Linhagem"]).strip()
                    dt    = parse_data(row["Dt. Aloj."])
                    if not lote or femeas <= 0:
                        continue
                    if not dt:
                        erros.append(f"Linha {i+1} ({lote}): data inválida '{row['Dt. Aloj.']}'")
                        continue
                    lotes_finais.append({"lote":lote,"granja":granja,"nucleo":"",
                                         "raca":raca,"dt_aloj":dt,"femeas":femeas})
                if erros:
                    for e in erros:
                        st.warning(e)
                if lotes_finais:
                    df_res, df_proj = calcular_projecao(lotes_finais, unidade_sel)
                    st.session_state.dados_unidades[unidade_sel] = {"res":df_res,"proj":df_proj}
                    st.success(f"✓ Projeção gerada — {len(lotes_finais)} lotes.")
                    st.rerun()
                else:
                    st.error("Nenhum lote válido para projetar.")

        with col_remove:
            if st.button(f"🗑 Remover {unidade_sel}", use_container_width=True):
                st.session_state.lotes_editor.pop(unidade_sel, None)
                st.session_state.dados_unidades.pop(unidade_sel, None)
                st.rerun()

    # Status geral
    if st.session_state.dados_unidades:
        carregadas = list(st.session_state.dados_unidades.keys())
        st.markdown("**Unidades projetadas:** " +
            " · ".join([f"🟢 {u}" for u in carregadas]))
        if st.button("🗑️ Limpar tudo"):
            st.session_state.dados_unidades = {}
            st.session_state.lotes_editor   = {}
            st.rerun()

# ── Dashboard ────────────────────────────────────────────────────────────────
if not st.session_state.dados_unidades:
    st.info("Carregue pelo menos uma unidade e clique em **▶ Projetar** para ver o dashboard.")
    st.stop()

st.markdown("---")

unidades_disp = ["Todas"] + list(st.session_state.dados_unidades.keys())
unidade_view  = st.radio("Visualizar", unidades_disp, horizontal=True)

if unidade_view == "Todas":
    df_res_all  = pd.concat([d["res"]  for d in st.session_state.dados_unidades.values()], ignore_index=True)
    df_proj_all = pd.concat([d["proj"] for d in st.session_state.dados_unidades.values()], ignore_index=True)
else:
    df_res_all  = st.session_state.dados_unidades[unidade_view]["res"]
    df_proj_all = st.session_state.dados_unidades[unidade_view]["proj"]

fc1, fc2, fc3 = st.columns(3)
granjas = ["Todas"] + sorted(df_res_all["granja"].dropna().unique().tolist())
racas   = ["Todas"] + sorted(df_res_all["raca"].dropna().unique().tolist())
anos    = ["Todos"] + sorted(df_proj_all["ano"].unique().tolist())
with fc1: fil_granja = st.selectbox("Granja", granjas)
with fc2: fil_raca   = st.selectbox("Linhagem", racas)
with fc3: fil_ano    = st.selectbox("Ano", anos)

res  = df_res_all.copy()
proj = df_proj_all.copy()
if fil_granja != "Todas": res = res[res["granja"]==fil_granja]; proj = proj[proj["granja"]==fil_granja]
if fil_raca   != "Todas": res = res[res["raca"]==fil_raca];     proj = proj[proj["raca"]==fil_raca]
if fil_ano    != "Todos": proj = proj[proj["ano"]==int(fil_ano)]

alertas = res[res["alerta"]]
k1,k2,k3,k4 = st.columns(4)
k1.metric("Fêmeas no plantel",  fmt_n(res["femeas"].sum()))
k2.metric("Lotes processados",  len(res))
k3.metric("Ovos proj. (total)", f"{res['total_ovos'].sum()/1e6:.1f}M")
k4.metric("Alertas de pico",    len(alertas))
st.markdown("---")

grp = proj.groupby(["ano","mes"])["ovos_incub"].sum().reset_index()
grp["periodo"] = pd.to_datetime(
    grp["ano"].astype(str)+"-"+grp["mes"].astype(str).str.zfill(2)+"-01")
grp = grp.sort_values("periodo")
hm  = pd.Timestamp(HOJE.year, HOJE.month, 1)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=grp[grp["periodo"]<hm]["periodo"],
    y=grp[grp["periodo"]<hm]["ovos_incub"].round(),
    mode="lines+markers", name="Realizado",
    line=dict(color="#185FA5",width=2.5), marker=dict(size=4)))
fig.add_trace(go.Scatter(
    x=grp[grp["periodo"]>=hm]["periodo"],
    y=grp[grp["periodo"]>=hm]["ovos_incub"].round(),
    mode="lines+markers", name="Projetado",
    line=dict(color="#85B7EB",width=2,dash="dot"), marker=dict(size=4)))
fig.add_shape(type="line", x0=str(hm.date()), x1=str(hm.date()),
    y0=0, y1=1, yref="paper", line=dict(dash="dash",color="#aaa",width=1))
fig.add_annotation(x=str(hm.date()), y=1, yref="paper",
    text="hoje", showarrow=False, yanchor="bottom", font=dict(size=11,color="#888"))
fig.update_layout(
    title=f"Curva consolidada — {'Todas as unidades' if unidade_view=='Todas' else unidade_view}",
    height=350, margin=dict(l=60,r=20,t=60,b=40),
    plot_bgcolor="#fff", paper_bgcolor="#fff",
    legend=dict(orientation="h",y=1.1),
    yaxis=dict(tickformat=",.0f"))
st.plotly_chart(fig, use_container_width=True)

if unidade_view == "Todas":
    st.subheader("Por unidade")
    fig_u = go.Figure()
    for u, d in st.session_state.dados_unidades.items():
        sub = d["proj"].groupby(["ano","mes"])["ovos_incub"].sum().reset_index()
        sub["periodo"] = pd.to_datetime(
            sub["ano"].astype(str)+"-"+sub["mes"].astype(str).str.zfill(2)+"-01")
        sub = sub.sort_values("periodo")
        fig_u.add_trace(go.Scatter(
            x=sub["periodo"], y=sub["ovos_incub"].round(),
            mode="lines", name=u,
            line=dict(color=CORES_UNIDADE.get(u,"#888"), width=2)))
    fig_u.update_layout(
        height=320, margin=dict(l=60,r=20,t=20,b=40),
        plot_bgcolor="#fff", paper_bgcolor="#fff",
        legend=dict(orientation="h", y=1.15),
        yaxis=dict(tickformat=",.0f"))
    st.plotly_chart(fig_u, use_container_width=True)

c_lin, c_top = st.columns(2)
cores_raca      = {"COBB":"#185FA5","ROSS":"#BA7517","HUBB":"#3B6D11"}
cores_raca_rgba = {"COBB":"rgba(24,95,165,0.6)","ROSS":"rgba(186,117,23,0.6)","HUBB":"rgba(59,109,17,0.6)"}

with c_lin:
    fig2 = go.Figure()
    for r in proj["raca"].unique():
        sub = proj[proj["raca"]==r].groupby(["ano","mes"])["ovos_incub"].sum().reset_index()
        sub["periodo"] = pd.to_datetime(
            sub["ano"].astype(str)+"-"+sub["mes"].astype(str).str.zfill(2)+"-01")
        sub = sub.sort_values("periodo")
        fig2.add_trace(go.Scatter(
            x=sub["periodo"], y=sub["ovos_incub"].round(),
            mode="lines", name=r,
            line=dict(color=cores_raca.get(r,"#888"),width=2)))
    fig2.update_layout(
        title="Por linhagem", height=280,
        margin=dict(l=50,r=10,t=40,b=30),
        plot_bgcolor="#fff", paper_bgcolor="#fff",
        legend=dict(orientation="h",y=1.15),
        yaxis=dict(tickformat=",.0f"))
    st.plotly_chart(fig2, use_container_width=True)

with c_top:
    top10 = res.nlargest(10,"total_ovos")[["lote","total_ovos","raca","unidade"]]
    fig3 = go.Figure(go.Bar(
        x=top10["total_ovos"].round(), y=top10["lote"],
        orientation="h",
        marker_color=[cores_raca_rgba.get(r,"rgba(128,128,128,0.6)") for r in top10["raca"]],
    ))
    fig3.update_layout(
        title="Top 10 lotes por volume", height=280,
        margin=dict(l=80,r=40,t=40,b=30),
        plot_bgcolor="#fff", paper_bgcolor="#fff",
        yaxis=dict(autorange="reversed"),
        xaxis=dict(tickformat=",.0f"))
    st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")
st.subheader("⚠️ Alertas — pico nas próximas 4 semanas")
if alertas.empty:
    st.success("Nenhum lote entrando em pico nas próximas 4 semanas.")
else:
    cols = ["unidade","lote","granja","raca","femeas","sems_pico","pico_dt","pico_pct"]
    df_al = alertas[cols].copy()
    df_al["femeas"]    = df_al["femeas"].apply(fmt_n)
    df_al["pico_dt"]   = pd.to_datetime(df_al["pico_dt"]).dt.strftime("%d/%m/%Y")
    df_al["pico_pct"]  = df_al["pico_pct"].apply(lambda v: f"{v:.1f}%")
    df_al["sems_pico"] = df_al["sems_pico"].apply(lambda v: f"{int(v)} sem.")
    df_al.columns = ["Unidade","Lote","Granja","Linhagem","Fêmeas","Sem. p/ pico","Data pico","% pico"]
    st.dataframe(df_al, use_container_width=True, hide_index=True)

st.markdown("---")
st.subheader("Todos os lotes")
df_tab = res[["unidade","lote","granja","raca","dt_aloj","femeas",
              "sem_atual","pico_sem","pico_dt","pico_pct","total_ovos"]].copy()
df_tab["dt_aloj"]    = pd.to_datetime(df_tab["dt_aloj"]).dt.strftime("%d/%m/%Y")
df_tab["pico_dt"]    = pd.to_datetime(df_tab["pico_dt"]).dt.strftime("%d/%m/%Y")
df_tab["pico_pct"]   = df_tab["pico_pct"].apply(lambda v: f"{v:.1f}%")
df_tab["femeas"]     = df_tab["femeas"].apply(fmt_n)
df_tab["total_ovos"] = df_tab["total_ovos"].apply(lambda v: f"{v:,.0f}".replace(",","."))
df_tab.columns = ["Unidade","Lote","Granja","Linhagem","Dt. aloj.","Fêmeas",
                  "Sem. atual","Sem. pico","Data pico","% pico","Ovos proj."]
st.dataframe(df_tab.sort_values("Sem. atual", ascending=False),
             use_container_width=True, hide_index=True)

st.caption("Grupo Pluma · Sistema de Projeção de Ovos · Curvas oficiais COBB e ROSS")
