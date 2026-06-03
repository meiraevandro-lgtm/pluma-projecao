import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from io import StringIO

st.set_page_config(
    page_title="Projeção de Ovos — Pluma",
    page_icon="🐓",
    layout="wide",
)

# ─── Curvas oficiais ────────────────────────────────────────────────────────
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

def get_curva(raca):
    r = str(raca).upper()
    return CURVA_ROSS if ("ROSS" in r or "HUBB" in r) else CURVA_COBB

HOJE = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

# ─── Limpeza e processamento ────────────────────────────────────────────────
def parse_qtde(v):
    if v is None or str(v).strip() in ("", "nan", "None"): return 0
    return int(str(v).replace(".", "").replace(",", "").strip().split()[0]) if str(v).strip() else 0

def parse_data(v):
    if isinstance(v, datetime): return v
    if isinstance(v, pd.Timestamp): return v.to_pydatetime()
    s = str(v).strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
        try: return datetime.strptime(s[:10], fmt)
        except: pass
    return None

def processar(df):
    col_map = {
        "Dt. Aloj.":"dt_aloj","Dt. Alojamento":"dt_aloj","Data Alojamento":"dt_aloj",
        "Lote":"lote","Recria":"granja","Núcleo":"nucleo","Nucleo":"nucleo",
        "Qtde.":"qtde","Qtde":"qtde","Quantidade":"qtde",
        "Raca":"raca","Raça":"raca","Reg.":"reg","Reg":"reg",
    }
    df = df.rename(columns={k:v for k,v in col_map.items() if k in df.columns})

    invalidos = {"#n/d","#n/a","solicitar lote","","nan","none","undefined"}
    mapa = {}
    for _, r in df.iterrows():
        lote = str(r.get("lote","")).strip()
        if not lote or lote.lower() in invalidos: continue
        qtde_raw = r.get("qtde", r.get("Qtde.", 0))
        qtde = parse_qtde(qtde_raw)
        if qtde <= 0: continue
        dt = parse_data(r.get("dt_aloj",""))
        if not dt: continue
        raca = str(r.get("raca","COBB")).strip()
        granja = str(r.get("granja","")).strip()
        nucleo = str(r.get("nucleo","")).strip()
        key = lote + "||" + granja
        if key not in mapa:
            mapa[key] = {"lote":lote,"granja":granja,"nucleo":nucleo,
                         "raca":raca,"dt_aloj":dt,"femeas":0}
        mapa[key]["femeas"] += qtde

    lotes = list(mapa.values())
    proj = []
    for l in lotes:
        curva = get_curva(l["raca"])
        for sem in range(23, 67):
            if sem not in curva: continue
            pos, apr, viab = curva[sem]
            dt_sem = l["dt_aloj"] + timedelta(weeks=sem)
            aves = l["femeas"] * (viab/100)
            ovos_t = aves * (pos/100) * 7
            ovos_i = ovos_t * (apr/100)
            proj.append({
                "lote":l["lote"],"granja":l["granja"],"raca":l["raca"],
                "femeas":l["femeas"],"dt_aloj":l["dt_aloj"],
                "semana":sem,"dt_sem":dt_sem,
                "ano":dt_sem.year,"mes":dt_sem.month,
                "pos":pos,"ovos_incub":ovos_i,
            })

    df_proj = pd.DataFrame(proj)

    resumo = []
    for l in lotes:
        lp = [p for p in proj if p["lote"]==l["lote"] and p["granja"]==l["granja"]]
        if not lp: continue
        pico = max(lp, key=lambda x: x["pos"])
        total_ovos = sum(p["ovos_incub"] for p in lp)
        sem_atual = max(0, (HOJE - l["dt_aloj"]).days // 7)
        sems_pico = max(0, pico["semana"] - sem_atual)
        resumo.append({**l,
            "sem_atual": sem_atual,
            "pico_pct": pico["pos"],
            "pico_sem": pico["semana"],
            "pico_dt":  pico["dt_sem"],
            "total_ovos": total_ovos,
            "sems_pico": sems_pico,
            "alerta": 0 <= sems_pico <= 4 and sem_atual < 66,
        })

    return pd.DataFrame(resumo), df_proj

# ─── Interface ──────────────────────────────────────────────────────────────
st.title("🐓 Projeção de Ovos — Pluma Agroavícola")
st.caption(f"Curvas oficiais COBB e ROSS · Atualizado em {HOJE.strftime('%d/%m/%Y')}")

st.markdown("---")

col_up, col_txt = st.columns([1,1])
with col_up:
    st.subheader("Upload de Excel")
    arquivo = st.file_uploader("Selecione o arquivo exportado do Maxicon",
                               type=["xlsx","xls","csv"],
                               label_visibility="collapsed")
with col_txt:
    st.subheader("Ou cole os dados")
    texto = st.text_area("Cole aqui (com cabeçalho, separado por tabulação)",
                         height=120, label_visibility="collapsed",
                         placeholder="Reg.\tDt. Aloj.\tLote\tRecria\tNúcleo\tQtde.\tRaca\n...")

df_raw = None
if arquivo:
    try:
        if arquivo.name.endswith(".csv"):
            df_raw = pd.read_csv(arquivo, sep="\t", encoding="utf-8-sig")
        else:
            df_raw = pd.read_excel(arquivo)
        st.success(f"Arquivo lido: {len(df_raw)} linhas")
    except Exception as e:
        st.error(f"Erro ao ler arquivo: {e}")

elif texto.strip():
    try:
        sep = "\t" if "\t" in texto else ";"
        df_raw = pd.read_csv(StringIO(texto), sep=sep)
        st.success(f"Dados lidos: {len(df_raw)} linhas")
    except Exception as e:
        st.error(f"Erro ao ler dados: {e}")

if df_raw is not None:
    try:
        df_res, df_proj = processar(df_raw)
    except Exception as e:
        st.error(f"Erro no processamento: {e}")
        st.stop()

    if df_res.empty:
        st.warning("Nenhum lote válido encontrado. Verifique se as colunas Lote, Dt. Aloj., Qtde. e Raca estão presentes.")
        st.stop()

    st.markdown("---")

    # Filtros
    fc1, fc2, fc3 = st.columns(3)
    granjas = ["Todas"] + sorted(df_res["granja"].dropna().unique().tolist())
    racas   = ["Todas"] + sorted(df_res["raca"].dropna().unique().tolist())
    anos    = ["Todos"] + sorted(df_proj["ano"].unique().tolist())

    with fc1: fil_granja = st.selectbox("Granja", granjas)
    with fc2: fil_raca   = st.selectbox("Linhagem", racas)
    with fc3: fil_ano    = st.selectbox("Ano", anos)

    res = df_res.copy()
    proj = df_proj.copy()
    if fil_granja != "Todas": res = res[res["granja"]==fil_granja]; proj = proj[proj["granja"]==fil_granja]
    if fil_raca   != "Todas": res = res[res["raca"]==fil_raca];     proj = proj[proj["raca"]==fil_raca]
    if fil_ano    != "Todos": proj = proj[proj["ano"]==int(fil_ano)]

    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    alertas = res[res["alerta"]]
    k1.metric("Fêmeas no plantel",   f"{int(res['femeas'].sum()):,}".replace(",","."))
    k2.metric("Lotes processados",   len(res))
    k3.metric("Ovos proj. (total)",  f"{res['total_ovos'].sum()/1e6:.1f}M")
    k4.metric("Alertas de pico",     len(alertas), delta=None,
              help="Lotes com pico nas próximas 4 semanas")

    st.markdown("---")

    # Gráfico consolidado
    grp = proj.groupby(["ano","mes"])["ovos_incub"].sum().reset_index()
    grp["periodo"] = pd.to_datetime(
        grp["ano"].astype(str)+"-"+grp["mes"].astype(str).str.zfill(2)+"-01")
    grp = grp.sort_values("periodo")

    hm = pd.Timestamp(HOJE.year, HOJE.month, 1)
    passado  = grp[grp["periodo"] <  hm]
    futuro   = grp[grp["periodo"] >= hm]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=passado["periodo"], y=passado["ovos_incub"].round(),
        mode="lines+markers", name="Realizado",
        line=dict(color="#185FA5", width=2.5), marker=dict(size=4)))
    fig.add_trace(go.Scatter(x=futuro["periodo"], y=futuro["ovos_incub"].round(),
        mode="lines+markers", name="Projetado",
        line=dict(color="#85B7EB", width=2, dash="dot"), marker=dict(size=4)))
    fig.add_vline(x=str(hm.date()), line_dash="dash", line_color="#aaa",
                  annotation_text="hoje")
    fig.update_layout(
        title="Curva consolidada — ovos incubáveis por mês",
        xaxis_title="Mês", yaxis_title="Ovos incubáveis",
        legend=dict(orientation="h", y=1.1),
        height=350, margin=dict(l=60,r=20,t=60,b=40),
        plot_bgcolor="#fff", paper_bgcolor="#fff",
        yaxis=dict(tickformat=",.0f"),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Gráfico por linhagem + Top 10
    c_lin, c_top = st.columns(2)

    with c_lin:
        fig2 = go.Figure()
        cores = {"COBB":"#185FA5","ROSS":"#BA7517","HUBB":"#3B6D11"}
        for r in proj["raca"].unique():
            sub = proj[proj["raca"]==r].groupby(["ano","mes"])["ovos_incub"].sum().reset_index()
            sub["periodo"] = pd.to_datetime(
                sub["ano"].astype(str)+"-"+sub["mes"].astype(str).str.zfill(2)+"-01")
            sub = sub.sort_values("periodo")
            fig2.add_trace(go.Scatter(x=sub["periodo"], y=sub["ovos_incub"].round(),
                mode="lines", name=r,
                line=dict(color=cores.get(r,"#888"), width=2)))
        fig2.update_layout(title="Por linhagem", height=280,
            margin=dict(l=50,r=10,t=40,b=30),
            plot_bgcolor="#fff", paper_bgcolor="#fff",
            legend=dict(orientation="h", y=1.15),
            yaxis=dict(tickformat=",.0f"))
        st.plotly_chart(fig2, use_container_width=True)

    with c_top:
        top10 = res.nlargest(10,"total_ovos")[["lote","total_ovos","raca"]]
        fig3 = go.Figure(go.Bar(
            x=top10["total_ovos"].round(), y=top10["lote"],
            orientation="h",
            marker_color=[cores.get(r,"#888")+"99" for r in top10["raca"]],
            text=top10["total_ovos"].apply(lambda v: f"{v/1000:.0f}k"),
            textposition="outside",
        ))
        fig3.update_layout(title="Top 10 lotes por volume", height=280,
            margin=dict(l=80,r=60,t=40,b=30),
            plot_bgcolor="#fff", paper_bgcolor="#fff",
            yaxis=dict(autorange="reversed"),
            xaxis=dict(tickformat=",.0f"))
        st.plotly_chart(fig3, use_container_width=True)

    # Alertas
    st.markdown("---")
    st.subheader("⚠️ Alertas — pico nas próximas 4 semanas")
    if alertas.empty:
        st.success("Nenhum lote entrando em pico nas próximas 4 semanas.")
    else:
        df_alerta = alertas[["lote","granja","raca","femeas","sems_pico","pico_dt","pico_pct"]].copy()
        df_alerta["femeas"] = df_alerta["femeas"].apply(lambda v: f"{int(v):,}".replace(",","."))
        df_alerta["pico_dt"] = pd.to_datetime(df_alerta["pico_dt"]).dt.strftime("%d/%m/%Y")
        df_alerta["pico_pct"] = df_alerta["pico_pct"].apply(lambda v: f"{v:.1f}%")
        df_alerta["sems_pico"] = df_alerta["sems_pico"].apply(lambda v: f"{int(v)} sem.")
        df_alerta.columns = ["Lote","Granja","Linhagem","Fêmeas","Sem. p/ pico","Data pico","% pico"]
        st.dataframe(df_alerta, use_container_width=True, hide_index=True)

    # Tabela completa
    st.markdown("---")
    st.subheader("Todos os lotes")
    df_tab = res[["lote","granja","raca","dt_aloj","femeas",
                  "sem_atual","pico_sem","pico_dt","pico_pct","total_ovos"]].copy()
    df_tab["dt_aloj"] = pd.to_datetime(df_tab["dt_aloj"]).dt.strftime("%d/%m/%Y")
    df_tab["pico_dt"] = pd.to_datetime(df_tab["pico_dt"]).dt.strftime("%d/%m/%Y")
    df_tab["pico_pct"] = df_tab["pico_pct"].apply(lambda v: f"{v:.1f}%")
    df_tab["femeas"] = df_tab["femeas"].apply(lambda v: f"{int(v):,}".replace(",","."))
    df_tab["total_ovos"] = df_tab["total_ovos"].apply(lambda v: f"{v:,.0f}".replace(",","."))
    df_tab.columns = ["Lote","Granja","Linhagem","Dt. aloj.","Fêmeas",
                      "Sem. atual","Sem. pico","Data pico","% pico","Ovos proj."]
    st.dataframe(df_tab.sort_values("Sem. atual", ascending=False),
                 use_container_width=True, hide_index=True)

    st.caption("Pluma Agroavícola · Sistema de Projeção de Ovos · Curvas oficiais COBB e ROSS")

else:
    st.info("Faça upload do Excel ou cole os dados para começar.")
