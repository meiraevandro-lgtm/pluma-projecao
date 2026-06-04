import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import math

st.set_page_config(
    page_title="Projeção de Ovos — Grupo Pluma",
    page_icon="logo.png",
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

# Unidades que ainda NÃO lançaram alojamento de 2027 — excluir ano 2027
SEM_ALOJ_2027 = {'Pluma DF'}

# Estrutura padrão da maioria das unidades
COL_DEFAULT = dict(
    aloj=1, lote_recria=3, granja_recria=6,
    raca=11, transfer=13, lote_prod=14,
    granja_prod=16,                          # granja de produção (fixa após semana 23)
    qty=18, qty_recria=8, abate_dt=19, idade_inicio=22,
)

# Pluma DF: coluna extra no início + inicia produção na semana 25
COL_DF = dict(
    aloj=2, lote_recria=4, granja_recria=7,
    raca=12, transfer=14, lote_prod=15,
    granja_prod=17,
    qty=18, qty_recria=9, abate_dt=19, idade_inicio=25,
)

# Cassilândia: sem coluna Núcleo — todas deslocadas -2 a partir da col 7
COL_CASSIL = dict(
    aloj=1, lote_recria=3, granja_recria=6,
    raca=10, transfer=12, lote_prod=13,
    granja_prod=15,
    qty=16, qty_recria=7, abate_dt=17, idade_inicio=22,
)

SHEET_COLS = {'Pluma DF': COL_DF, 'Cassilândia': COL_CASSIL}

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
    if "HUBB" in r:
        return "HUBBARD"
    if "ROSS" in r:
        return "ROSS"
    return "COBB"

def week_start_pluma(dt):
    """Semana Pluma: começa na quinta-feira, termina na quarta-feira."""
    if isinstance(dt, pd.Timestamp):
        dt = dt.to_pydatetime()
    days_since_thu = (dt.weekday() - 3) % 7
    return (dt - timedelta(days=days_since_thu)).date()

def week_label(dt):
    """Rótulo da semana: 'Qui DD/MM - Qua DD/MM/YYYY'"""
    ini = week_start_pluma(dt)
    fim = ini + timedelta(days=6)
    return f"{ini.strftime('%d/%m')} – {fim.strftime('%d/%m/%Y')}"

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
                # unidades sem alojamento 2027 lançado → ignora registros de 2027
                if aloj_dt.year >= 2027 and normalize_unit(sheet) in SEM_ALOJ_2027:
                    continue

                lote_recria   = str(row.iloc[C['lote_recria']]).strip()
                granja_recria = str(row.iloc[C['granja_recria']]).strip()
                granja_prod   = str(row.iloc[C['granja_prod']]).strip()
                raca          = str(row.iloc[C['raca']]).strip()
                transfer_val  = row.iloc[C['transfer']]
                qty_val       = row.iloc[C['qty']]
                # fallback: usa qty de recria quando qty produção está vazia
                if pd.isna(qty_val) or float(qty_val) <= 0:
                    qty_val = row.iloc[C['qty_recria']]
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
                # lote produção ainda não atribuído → usa lote recria ou gera chave pela data
                if lote_prod in ('nan', 'NaN', ''):
                    if lote_recria not in ('nan', 'NaN', ''):
                        lote_prod = f"REC-{lote_recria}"
                    else:
                        # lotes futuros sem numeração: identifica por unidade + data aloj + qty
                        lote_prod = f"{unit}-{aloj_dt.strftime('%d%m%y')}-{int(float(qty_val))}"
                if not lote_prod:
                    continue

                transfer = pd.Timestamp(transfer_val)
                abate    = pd.Timestamp(abate_val)
                if abate <= transfer:
                    continue

                if granja_prod in ('nan', 'NaN', ''):
                    granja_prod = granja_recria

                todos_lotes.append(dict(
                    unidade=unit,
                    lote=lote_prod,
                    lote_recria=lote_recria,
                    granja_recria=granja_recria,
                    granja_prod=granja_prod,
                    granja=granja_recria,           # chave principal = recria
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
            # 95% viabilidade recria (5% mortalidade antes da produção)
            aves  = femeas * 0.95 * (viab / 100)
            ovos  = aves * (pos / 100) * (apr / 100) * 7
            sem_pluma = week_start_pluma(dt_sem)
            # até sem 23 usa granja recria; após usa granja produção (fixa)
            granja_sem = l['granja_recria'] if sem <= 23 else l['granja_prod']
            semanas_lote.append(dict(
                lote=l['lote'], lote_recria=l['lote_recria'],
                granja=granja_sem,
                granja_recria=l['granja_recria'],
                granja_prod=l['granja_prod'],
                raca=l['raca'], linhagem=l['linhagem'],
                femeas=femeas, dt_aloj=l['aloj_dt'], unidade=l['unidade'],
                semana=sem, dt_sem=dt_sem,
                sem_pluma=sem_pluma,
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
            granja=l['granja_recria'],
            granja_recria=l['granja_recria'],
            granja_prod=l['granja_prod'],
            raca=l['raca'], linhagem=l['linhagem'],
            femeas=femeas, dt_aloj=l['aloj_dt'],
            sem_atual=sem_atual, pico_pct=pico['pos'],
            pico_sem=pico['semana'], pico_dt=pico['dt_sem'],
            total_ovos=total_ovos, sems_pico=sems_pico, alerta=alerta,
        ))

    return pd.DataFrame(resumo_rows), pd.DataFrame(proj_rows)

# ── Interface ────────────────────────────────────────────────────────────────

col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.image("logo.png", width=110)
with col_title:
    st.markdown("## Projeção de Ovos — Grupo Pluma")
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

# ── Seleção de unidades (multiselect estilizado) ─────────────────────────────
todas_unidades = sorted(df_res_full['unidade'].unique().tolist())

unidades_sel = st.multiselect(
    "**Unidades visualizadas:**",
    options=todas_unidades,
    default=todas_unidades,
    placeholder="Selecione as unidades...",
)

if not unidades_sel:
    st.warning("Selecione pelo menos uma unidade.")
    st.stop()

df_res_v  = df_res_full[df_res_full['unidade'].isin(unidades_sel)].copy()
df_proj_v = df_proj_full[df_proj_full['unidade'].isin(unidades_sel)].copy()

# ── Filtros adicionais ───────────────────────────────────────────────────────
fc1, fc2, fc3, fc4 = st.columns(4)

granjas     = ["Todas"] + sorted(df_res_v['granja'].dropna().unique().tolist())
linhagens   = ["Todas"] + sorted(df_res_v['linhagem'].dropna().unique().tolist())
anos_proj   = ["Todos"] + sorted(df_proj_v['ano'].unique().tolist())
anos_aloj   = sorted(df_res_v['dt_aloj'].dropna().apply(lambda d: d.year).unique().tolist())

with fc1: fil_granja   = st.selectbox("Granja de Recria", granjas)
with fc2: fil_lin      = st.selectbox("Linhagem", linhagens)
with fc3: fil_ano_proj = st.selectbox("Ano projeção", anos_proj)
with fc4:
    fil_anos_aloj = st.multiselect(
        "Ano alojamento", anos_aloj,
        default=anos_aloj,          # todos os anos selecionados por padrão
        help="Filtra lotes pelo ano em que foram alojados na recria")

res  = df_res_v.copy()
proj = df_proj_v.copy()

if fil_granja   != "Todas":  res = res[res['granja'] == fil_granja];      proj = proj[proj['granja'] == fil_granja]
if fil_lin      != "Todas":  res = res[res['linhagem'] == fil_lin];       proj = proj[proj['linhagem'] == fil_lin]
if fil_ano_proj != "Todos":  proj = proj[proj['ano'] == int(fil_ano_proj)]
if fil_anos_aloj:
    res  = res[res['dt_aloj'].apply(lambda d: d.year).isin(fil_anos_aloj)]
    proj = proj[proj['dt_aloj'].apply(lambda d: d.year).isin(fil_anos_aloj)]

alertas = res[res['alerta']]

# Indicadores de plantel por fase
def semanas_desde_aloj(dt):
    try:
        return (HOJE - dt.to_pydatetime().replace(tzinfo=None)).days // 7
    except:
        return 0

res['semanas_aloj'] = res['dt_aloj'].apply(semanas_desde_aloj)
# somente lotes já alojados (dt_aloj <= hoje) e dentro do ciclo (≤ 68 sem)
ja_alojados = res[res['dt_aloj'].apply(lambda d: d.to_pydatetime().replace(tzinfo=None)) <= HOJE]
aves_recria   = int(ja_alojados[(ja_alojados['semanas_aloj'] < 23)]['femeas'].sum())
aves_producao = int(ja_alojados[(ja_alojados['sem_atual'] >= 23) & (ja_alojados['sem_atual'] <= 68)]['femeas'].sum())

# ── KPIs linha 1 ────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Fêmeas no plantel",           fmt_n(res['femeas'].sum()))
k2.metric("Lotes processados",           len(res))
k3.metric("Ovos proj. (total)",          f"{res['total_ovos'].sum()/1e6:.1f}M")
k4.metric("Alertas de pico",             len(alertas))

# ── KPIs linha 2 ────────────────────────────────────────────────────────────
k5, k6, _, _ = st.columns(4)
k5.metric("🐣 Aves em Recria (< 23 sem)",     fmt_n(aves_recria))
k6.metric("🥚 Aves em Produção (23–68 sem)",   fmt_n(aves_producao))

st.markdown("---")

# ── Cards por unidade ────────────────────────────────────────────────────────
st.markdown("#### Projeção por Unidade")
unidades_card = sorted(res['unidade'].unique())
n_cols = min(len(unidades_card), 4)
rows_cards = [unidades_card[i:i+n_cols] for i in range(0, len(unidades_card), n_cols)]

for row_u in rows_cards:
    cols_u = st.columns(len(row_u))
    for col, u in zip(cols_u, row_u):
        r_u    = res[res['unidade'] == u]
        cor    = CORES_UNIDADE.get(u, '#555555')
        ovos   = r_u['total_ovos'].sum()
        lotes  = len(r_u)
        # fêmeas e lotes por fase (já alojados, dentro do ciclo)
        r_u2 = r_u.copy()
        r_u2['aloj_dt_py'] = r_u2['dt_aloj'].apply(lambda d: d.to_pydatetime().replace(tzinfo=None))
        r_u2['sem_aloj']   = r_u2['aloj_dt_py'].apply(lambda d: (HOJE - d).days // 7)
        ja_aloj_u  = r_u2[r_u2['aloj_dt_py'] <= HOJE]
        mask_rec   = ja_aloj_u['sem_aloj'] < 23
        mask_prod  = (ja_aloj_u['sem_atual'] >= 23) & (ja_aloj_u['sem_atual'] <= 68)
        fem_prod   = int(ja_aloj_u[mask_prod]['femeas'].sum())
        lotes_rec  = int(mask_rec.sum())
        lotes_prod = int(mask_prod.sum())
        # breakdown somente 2026 e 2027
        p_u = df_proj_full[df_proj_full['unidade'] == u]
        if fil_anos_aloj:
            p_u = p_u[p_u['dt_aloj'].apply(lambda d: d.year).isin(fil_anos_aloj)]
        por_ano = p_u[p_u['ano'].isin([2026, 2027])].groupby('ano')['ovos_incub'].sum()
        anos_html = "".join([
            f'<span style="margin-right:10px"><b>{a}:</b> {v/1e6:.0f}M</span>'
            for a, v in por_ano.items()
        ])
        col.markdown(
            f"""<div style="border-left:5px solid {cor};padding:10px 14px;
                border-radius:6px;background:#f8f9fa;margin-bottom:8px">
                <div style="font-weight:700;color:{cor};font-size:15px">{u}</div>
                <div style="font-size:24px;font-weight:800;color:#1a1a1a">{ovos/1e6:.1f}M</div>
                <div style="font-size:11px;color:#888;margin-bottom:4px">total de ovos projetados</div>
                <div style="font-size:12px;color:#333;font-weight:600">{anos_html}</div>
                <hr style="margin:6px 0;border-color:#ddd">
                <div style="font-size:12px;color:#444">
                    🥚 {fmt_n(fem_prod)} fêmeas em produção
                </div>
                <div style="font-size:12px;color:#444;margin-top:3px">
                    🐣 {lotes_rec} lotes em recria &nbsp;|&nbsp; 🥚 {lotes_prod} lotes em produção
                </div>
            </div>""",
            unsafe_allow_html=True)

st.markdown("---")

# ── Curva semanal consolidada ────────────────────────────────────────────────
st.markdown("#### 📅 Projeção Semanal — Semana Pluma (Qui → Qua)")
grp_sem = (
    proj.groupby("sem_pluma")["ovos_incub"].sum()
    .reset_index().sort_values("sem_pluma")
)
grp_sem["sem_pluma"] = pd.to_datetime(grp_sem["sem_pluma"])
hoje_thu = pd.Timestamp(week_start_pluma(HOJE))

fig_sem = go.Figure()
fig_sem.add_trace(go.Bar(
    x=grp_sem[grp_sem["sem_pluma"] < hoje_thu]["sem_pluma"],
    y=grp_sem[grp_sem["sem_pluma"] < hoje_thu]["ovos_incub"].round(),
    name="Realizado", marker_color="#1F3864"))
fig_sem.add_trace(go.Bar(
    x=grp_sem[grp_sem["sem_pluma"] >= hoje_thu]["sem_pluma"],
    y=grp_sem[grp_sem["sem_pluma"] >= hoje_thu]["ovos_incub"].round(),
    name="Projetado", marker_color="#85B7EB"))
fig_sem.add_shape(type="line",
    x0=str(hoje_thu.date()), x1=str(hoje_thu.date()),
    y0=0, y1=1, yref="paper",
    line=dict(dash="dash", color="#aaa", width=1))
fig_sem.add_annotation(x=str(hoje_thu.date()), y=1, yref="paper",
    text="hoje", showarrow=False, yanchor="bottom",
    font=dict(size=11, color="#888"))
fig_sem.update_layout(
    height=340, margin=dict(l=60, r=20, t=20, b=40),
    plot_bgcolor="#fff", paper_bgcolor="#fff",
    barmode="stack",
    legend=dict(orientation="h", y=1.08),
    xaxis=dict(tickformat="%d/%m/%Y", dtick="M1"),
    yaxis=dict(tickformat=",.0f"))
st.plotly_chart(fig_sem, use_container_width=True)

# ── Barras mensais: Total ou Por Linhagem ────────────────────────────────────
CORES_LIN = {"COBB": "#185FA5", "ROSS": "#BA7517", "HUBBARD": "#2eaa5f"}

col_tit, col_btn = st.columns([3, 2])
with col_tit:
    st.markdown("#### 📊 Projeção Mensal")
with col_btn:
    modo_mensal = st.radio("", ["Total", "Por Linhagem"],
                           horizontal=True, key="modo_mensal",
                           label_visibility="collapsed")

# pivot mensal por linhagem
grp_lin = (
    proj.groupby(["ano", "mes", "linhagem"])["ovos_incub"].sum()
    .reset_index()
)
grp_lin["periodo"] = pd.to_datetime(
    grp_lin["ano"].astype(str) + "-" + grp_lin["mes"].astype(str).str.zfill(2) + "-01")
grp_lin = grp_lin.sort_values("periodo")

total_periodo = grp_lin.groupby("periodo")["ovos_incub"].sum().rename("total")
grp_lin = grp_lin.join(total_periodo, on="periodo")
grp_lin["pct"] = (grp_lin["ovos_incub"] / grp_lin["total"] * 100).round(1)

fig_lin = go.Figure()
hm_mes = pd.Timestamp(HOJE.year, HOJE.month, 1)

if modo_mensal == "Total":
    grp_tot = grp_lin.groupby("periodo")["ovos_incub"].sum().reset_index()
    fig_lin.add_trace(go.Bar(
        x=grp_tot[grp_tot["periodo"] < hm_mes]["periodo"],
        y=grp_tot[grp_tot["periodo"] < hm_mes]["ovos_incub"].round(),
        name="Realizado", marker_color="#1F3864"))
    fig_lin.add_trace(go.Bar(
        x=grp_tot[grp_tot["periodo"] >= hm_mes]["periodo"],
        y=grp_tot[grp_tot["periodo"] >= hm_mes]["ovos_incub"].round(),
        name="Projetado", marker_color="#85B7EB"))
else:
    for lin in ["COBB", "ROSS", "HUBBARD"]:
        sub = grp_lin[grp_lin["linhagem"] == lin]
        if sub.empty:
            continue
        fig_lin.add_trace(go.Bar(
            x=sub["periodo"],
            y=sub["ovos_incub"].round(),
            name=lin,
            marker_color=CORES_LIN.get(lin, "#888"),
            customdata=sub[["pct"]],
            hovertemplate="%{x|%b/%Y}<br>%{y:,.0f} ovos<br><b>%{customdata[0]:.1f}%</b> do total<extra></extra>",
        ))

fig_lin.add_shape(type="line",
    x0=str(hm_mes.date()), x1=str(hm_mes.date()),
    y0=0, y1=1, yref="paper",
    line=dict(dash="dash", color="#aaa", width=1))
fig_lin.add_annotation(x=str(hm_mes.date()), y=1, yref="paper",
    text="hoje", showarrow=False, yanchor="bottom",
    font=dict(size=11, color="#888"))
fig_lin.update_layout(
    barmode="stack",
    height=340, margin=dict(l=60, r=20, t=10, b=40),
    plot_bgcolor="#fff", paper_bgcolor="#fff",
    legend=dict(orientation="h", y=1.08),
    xaxis=dict(tickformat="%b/%Y", dtick="M3"),
    yaxis=dict(tickformat=",.0f"))
st.plotly_chart(fig_lin, use_container_width=True)

st.markdown("---")

# ── Gráfico de alojamento semanal ────────────────────────────────────────────
st.markdown("#### 🐣 Alojamentos Semanais — Fêmeas alojadas por semana Pluma")

def week_start_from_dt(dt):
    if isinstance(dt, pd.Timestamp):
        dt = dt.to_pydatetime()
    days = (dt.weekday() - 3) % 7
    return (dt - timedelta(days=days)).date()

# Usar df_res_full para montar o gráfico de alojamento
aloj_data = df_res_full[df_res_full['unidade'].isin(unidades_sel)].copy()
if fil_anos_aloj:
    aloj_data = aloj_data[aloj_data['dt_aloj'].apply(lambda d: d.year).isin(fil_anos_aloj)]

aloj_data['sem_aloj'] = aloj_data['dt_aloj'].apply(week_start_from_dt)
aloj_data['sem_aloj'] = pd.to_datetime(aloj_data['sem_aloj'])

grp_aloj = aloj_data.groupby(['sem_aloj','unidade'])['femeas'].sum().unstack(fill_value=0)
grp_aloj_total = grp_aloj.sum(axis=1).reset_index()
grp_aloj_total.columns = ['semana','femeas']

fig_aloj = go.Figure()
for u in sorted(aloj_data['unidade'].unique()):
    if u not in grp_aloj.columns: continue
    fig_aloj.add_trace(go.Bar(
        x=grp_aloj.index,
        y=grp_aloj[u],
        name=u,
        marker_color=CORES_UNIDADE.get(u, '#888'),
    ))

fig_aloj.update_layout(
    barmode='stack',
    height=320, margin=dict(l=60, r=20, t=20, b=40),
    plot_bgcolor="#fff", paper_bgcolor="#fff",
    legend=dict(orientation="h", y=1.1),
    xaxis=dict(tickformat="%d/%m/%Y", dtick="M1"),
    yaxis=dict(tickformat=",.0f", title="Fêmeas alojadas"),
)
st.plotly_chart(fig_aloj, use_container_width=True)

st.markdown("---")

# Tabela completa de lotes — limitado a sem_atual <= 68
st.subheader("Todos os lotes")
df_tab = res[res["sem_atual"] <= 68][["unidade","lote","lote_recria","granja_recria","granja_prod","linhagem","dt_aloj",
              "femeas","sem_atual","pico_sem","pico_dt","pico_pct","total_ovos"]].copy()
df_tab["dt_aloj"]    = pd.to_datetime(df_tab["dt_aloj"]).dt.strftime("%d/%m/%Y")
df_tab["pico_dt"]    = pd.to_datetime(df_tab["pico_dt"]).dt.strftime("%d/%m/%Y")
df_tab["pico_pct"]   = df_tab["pico_pct"].apply(lambda v: f"{v:.1f}%")
df_tab["femeas"]     = df_tab["femeas"].apply(fmt_n)
df_tab["total_ovos"] = df_tab["total_ovos"].apply(lambda v: f"{v:,.0f}".replace(",","."))
df_tab.columns = ["Unidade","Lote Prod.","Lote Recria","Granja Recria","Granja Produção",
                  "Linhagem","Dt. Aloj.","Fêmeas","Sem. atual","Sem. pico","Data pico","% pico","Ovos proj."]
st.dataframe(df_tab.sort_values("Sem. atual", ascending=False),
             use_container_width=True, hide_index=True)

st.caption("Grupo Pluma · Sistema de Projeção de Ovos · Curvas oficiais COBB e ROSS")
