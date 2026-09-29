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

# Curvas ajustadas Girardi/Pluma — semanas 24–66 (postura%, aprov%, viab%)
CURVA_COBB = {
    24:(0.0,0.0,99.7),25:(4.91,65.0,99.4),26:(22.586,80.0,99.04),
    27:(52.046,85.0,98.68),28:(72.668,90.0,98.32),29:(78.56,92.0,97.96),
    30:(81.506,93.0,97.6),31:(82.488,94.5,97.24),32:(81.506,95.5,96.88),
    33:(80.524,96.0,96.58),34:(79.542,96.8,96.28),35:(78.56,97.2,95.98),
    36:(77.578,97.5,95.68),37:(76.596,97.5,95.38),38:(75.614,97.5,95.08),
    39:(74.632,97.5,94.78),40:(73.65,97.5,94.48),41:(72.668,97.5,94.18),
    42:(71.686,97.5,93.88),43:(70.704,97.5,93.58),44:(69.722,97.5,93.28),
    45:(68.74,97.5,93.04),46:(67.758,97.5,92.8),47:(66.7269,97.5,92.56),
    48:(65.6958,97.5,92.32),49:(64.6647,97.5,92.08),50:(63.6336,97.5,91.84),
    51:(62.6025,97.5,91.6),52:(61.5714,97.5,91.36),53:(60.5403,97.5,91.12),
    54:(59.5092,97.5,90.88),55:(58.4781,97.5,90.64),56:(57.447,97.5,90.4),
    57:(56.4159,97.5,90.16),58:(55.3848,97.5,89.92),59:(54.3537,97.5,89.68),
    60:(53.3226,97.5,89.44),61:(52.2915,97.5,89.2),62:(51.2604,97.5,88.96),
    63:(50.4973,97.5,88.72),64:(49.1982,97.5,88.48),65:(48.2644,97.5,88.24),
    66:(47.136,97.5,88.0),
}

CURVA_ROSS = {
    24:(0.0,0.0,99.75),25:(4.0003,70.0,99.5),26:(25.0016,85.0,99.2),
    27:(60.0039,90.0,98.9),28:(80.0052,93.0,98.6),29:(85.0055,94.4,98.3),
    30:(87.0056,95.4,98.0),31:(87.0056,96.4,97.7),32:(86.5056,96.9,97.4),
    33:(86.0056,97.3,97.15),34:(85.5055,97.6,96.9),35:(85.0055,97.9,96.65),
    36:(84.0054,98.0,96.4),37:(83.0054,98.0,96.15),38:(82.0053,98.0,95.9),
    39:(81.0052,98.0,95.65),40:(80.0052,98.0,95.4),41:(79.0051,98.0,95.15),
    42:(78.005,98.0,94.9),43:(77.005,98.0,94.65),44:(76.0049,98.0,94.4),
    45:(75.0048,98.0,94.2),46:(74.0048,98.0,94.0),47:(73.0047,98.0,93.8),
    48:(72.0047,98.0,93.6),49:(71.0046,98.0,93.4),50:(70.0045,98.0,93.2),
    51:(69.0045,98.0,93.0),52:(68.0044,98.0,92.8),53:(67.0043,98.0,92.6),
    54:(66.0043,98.0,92.4),55:(65.0042,98.0,92.2),56:(64.0041,98.0,92.0),
    57:(63.0041,98.0,91.8),58:(62.004,98.0,91.6),59:(61.0039,98.0,91.4),
    60:(60.0039,98.0,91.2),61:(59.0038,97.5,91.0),62:(58.0037,97.5,90.8),
    63:(57.0037,97.5,90.6),64:(56.0036,97.5,90.4),65:(55.0036,97.5,90.2),
    66:(54.0035,97.5,90.0),
}

CURVA_HUBBARD = CURVA_ROSS  # Hubbard Efficiency Plus = mesma curva Ross AP95

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
    raca=11, fem_mac=12, transfer=13, lote_prod=14,
    granja_prod=16,                          # granja de produção (fixa após semana 23)
    qty=18, qty_recria=8, abate_dt=19, idade_inicio=22,
)

# Pluma DF: coluna extra no início + inicia produção na semana 25
# col 13 é data (Inic. 22 Sem.), não Fêmea-Macho — sem fem_mac
COL_DF = dict(
    aloj=2, lote_recria=4, granja_recria=7,
    raca=12, fem_mac=None, transfer=14, lote_prod=15,
    granja_prod=17,
    qty=18, qty_recria=9, abate_dt=19, idade_inicio=25,
)

# Cassilândia: sem coluna Núcleo — todas deslocadas -2 a partir da col 7
COL_CASSIL = dict(
    aloj=1, lote_recria=3, granja_recria=6,
    raca=10, fem_mac=11, transfer=12, lote_prod=13,
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
    if "HUBB" in r: return CURVA_HUBBARD
    if "ROSS" in r: return CURVA_ROSS
    return CURVA_COBB

def get_linhagem(raca, fem_mac=""):
    """Retorna nome comercial da linhagem usando coluna Fêmea-Macho quando disponível."""
    fm = str(fem_mac).upper().strip()
    r  = str(raca).upper().strip()
    # Hubbard — detecta pela raça ou pelo macho
    if "HUBB" in r or "EFFICIENCY PLUS" in fm:
        return "Hubbard EP"
    # Ross
    if "ROSS" in r or "AP95" in fm:
        if "APN" in fm:
            return "Ross APN"
        return "Ross AP95"
    if "APN" in fm:
        return "Ross APN"
    # Cobb — distingue 500 / 800 / CDP4 pela coluna fem_mac
    if "COBB" in r or "JBS" in r:
        if "800" in fm:
            return "Cobb 800"
        if "CDP4" in fm:
            return "Cobb CDP4"
        return "Cobb 500"
    # fallback
    return str(raca).strip().title()

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
                fem_mac       = str(row.iloc[C['fem_mac']]).strip() if C.get('fem_mac') is not None else ""
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
                    fem_mac=fem_mac,
                    linhagem=get_linhagem(raca, fem_mac),
                    aloj_dt=aloj_dt,
                    transfer=transfer,
                    abate=abate,
                    femeas=float(qty_val),
                    idade_inicio=idade_inicio,
                ))
            except Exception:
                continue

    # ── Deduplicação: remove lotes duplicados por transferência entre unidades ──
    # Um lote pode aparecer na aba de origem E na aba de destino.
    # Chave de unicidade: granja_prod + qty + abate + transfer (mesma produção)
    vistos = set()
    lotes_dedup = []
    for l in todos_lotes:
        chave = (
            l['granja_prod'].strip().lower(),
            round(l['femeas']),
            l['abate'].date(),
            l['transfer'].date(),
        )
        if chave not in vistos:
            vistos.add(chave)
            lotes_dedup.append(l)

    removidos = len(todos_lotes) - len(lotes_dedup)
    if removidos > 0:
        print(f"[INFO] {removidos} lotes duplicados removidos (transferências entre unidades)")

    return lotes_dedup

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
            raca=l['raca'], fem_mac=l['fem_mac'], linhagem=l['linhagem'],
            femeas=femeas, dt_aloj=l['aloj_dt'], transfer=l['transfer'],
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

# ── Carregamento automático + opção de atualizar ─────────────────────────────

DATA_FILE = "data/alojamento.xlsx"

_CACHE_VER = "v4"  # incrementar para forçar recarga do cache

@st.cache_data(show_spinner=False)
def carregar_dados_automatico(_ver=_CACHE_VER):
    """Lê o arquivo commitado no repositório."""
    import os
    if not os.path.exists(DATA_FILE):
        return None, None, None
    lotes = ler_alojamento(DATA_FILE)
    if not lotes:
        return None, None, None
    df_res, df_proj = calcular_projecao(lotes)
    return lotes, df_res, df_proj

# Carrega automaticamente se ainda não estiver na sessão
if 'df_res' not in st.session_state or st.session_state['df_res'] is None:
    with st.spinner("Carregando dados... aguarde."):
        lotes_auto, df_res_auto, df_proj_auto = carregar_dados_automatico()
        if df_res_auto is not None:
            st.session_state['df_res']  = df_res_auto
            st.session_state['df_proj'] = df_proj_auto

# Painel de atualização (colapsado por padrão)
with st.expander("🔄 Atualizar arquivo de alojamento", expanded=False):
    st.markdown("Faça upload de uma versão mais recente do arquivo para atualizar a projeção.")
    arquivo = st.file_uploader(
        "Novo arquivo de alojamento", type=["xlsx", "xls"],
        label_visibility="collapsed", key="up_alojamento")

    if arquivo:
        with st.spinner("Processando novo arquivo..."):
            try:
                lotes = ler_alojamento(arquivo)
                if lotes:
                    df_res, df_proj = calcular_projecao(lotes)
                    st.session_state['df_res']  = df_res
                    st.session_state['df_proj'] = df_proj
                    st.cache_data.clear()
                    unidades_ok = sorted(df_res['unidade'].unique())
                    st.success(f"✅ {len(lotes)} lotes carregados | {len(unidades_ok)} unidades: {', '.join(unidades_ok)}")
                else:
                    st.warning("Nenhum lote válido encontrado.")
            except Exception as e:
                st.error(f"Erro: {e}")

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
CORES_LIN = {
    "Cobb 500":   "#185FA5",
    "Cobb 800":   "#2471a3",
    "Cobb CDP4":  "#5dade2",
    "Ross AP95":  "#BA7517",
    "Ross APN":   "#d4ac0d",
    "Hubbard EP": "#2eaa5f",
}

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
    for lin in ["Cobb 500", "Cobb 800", "Cobb CDP4", "Ross AP95", "Ross APN", "Hubbard EP"]:
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
col_aloj_tit, col_aloj_per, col_aloj_btn = st.columns([3, 1.5, 1.5])
with col_aloj_tit:
    st.markdown("#### 🐣 Alojamentos — Fêmeas alojadas")
with col_aloj_per:
    periodo_aloj = st.radio("", ["Semanal", "Mensal"],
                            horizontal=True, key="periodo_aloj",
                            label_visibility="collapsed")
with col_aloj_btn:
    modo_aloj = st.radio("", ["Total", "Por Unidade"],
                         horizontal=True, key="modo_aloj",
                         label_visibility="collapsed")

def week_start_from_dt(dt):
    if isinstance(dt, pd.Timestamp):
        dt = dt.to_pydatetime()
    days = (dt.weekday() - 3) % 7
    return (dt - timedelta(days=days)).date()

aloj_data = df_res_full[df_res_full['unidade'].isin(unidades_sel)].copy()
if fil_anos_aloj:
    aloj_data = aloj_data[aloj_data['dt_aloj'].apply(lambda d: d.year).isin(fil_anos_aloj)]

if periodo_aloj == "Semanal":
    aloj_data['periodo'] = pd.to_datetime(aloj_data['dt_aloj'].apply(week_start_from_dt))
    x_fmt = "%d/%m/%Y"
    dtick = "M1"
else:
    aloj_data['periodo'] = pd.to_datetime(
        aloj_data['dt_aloj'].dt.to_period('M').dt.to_timestamp())
    x_fmt = "%b/%Y"
    dtick = "M1"

grp_aloj = aloj_data.groupby(['periodo','unidade'])['femeas'].sum().unstack(fill_value=0)
tot_aloj = grp_aloj.sum(axis=1)

fig_aloj = go.Figure()

if modo_aloj == "Total":
    fig_aloj.add_trace(go.Bar(
        x=tot_aloj.index, y=tot_aloj.values,
        name="Total", marker_color="#1F3864",
        hovertemplate="%{x|" + x_fmt + "}<br><b>%{y:,.0f} fêmeas</b><extra></extra>",
    ))
else:
    for u in sorted(aloj_data['unidade'].unique()):
        if u not in grp_aloj.columns: continue
        fig_aloj.add_trace(go.Bar(
            x=grp_aloj.index, y=grp_aloj[u],
            name=u, marker_color=CORES_UNIDADE.get(u, '#888'),
            hovertemplate=f"{u}<br>%{{x|{x_fmt}}}<br><b>%{{y:,.0f}} fêmeas</b><extra></extra>",
        ))

fig_aloj.update_layout(
    barmode='stack',
    height=340, margin=dict(l=60, r=20, t=10, b=40),
    plot_bgcolor="#fff", paper_bgcolor="#fff",
    legend=dict(orientation="h", y=1.08),
    xaxis=dict(tickformat=x_fmt, dtick=dtick),
    yaxis=dict(tickformat=",.0f", title="Fêmeas alojadas"),
)
st.plotly_chart(fig_aloj, use_container_width=True)

st.markdown("---")

# ── Tabela de lotes por unidade ──────────────────────────────────────────────
st.markdown("#### 📋 Lotes por Unidade")

# Todos os lotes ativos: em produção, recria ou futuros (dentro do ciclo)
HOJE_PY = HOJE

df_tab = res[res['sem_atual'] <= 68].copy()

def _fase(row):
    aloj_py = row['dt_aloj'].to_pydatetime().replace(tzinfo=None)
    if aloj_py > HOJE_PY:        return "🔜 Recria Futura"
    if row['sem_atual'] < 23:    return "🐣 Recria"
    return "🥚 Produção"

df_tab['_fase'] = df_tab.apply(_fase, axis=1)

# Filtros
tf1, tf2, tf3 = st.columns(3)
with tf1:
    fase_fil2 = st.selectbox("Fase", ["Todas", "🥚 Produção", "🐣 Recria", "🔜 Recria Futura"], key="fase_fil2")
with tf2:
    unit_fil2 = st.selectbox("Unidade", ["Todas"] + sorted(df_tab['unidade'].unique()), key="unit_fil2")
with tf3:
    lin_fil2  = st.selectbox("Linhagem", ["Todas"] + sorted(df_tab['linhagem'].unique()), key="lin_fil2")

if fase_fil2 != "Todas": df_tab = df_tab[df_tab['_fase'] == fase_fil2]
if unit_fil2 != "Todas": df_tab = df_tab[df_tab['unidade'] == unit_fil2]
if lin_fil2  != "Todas": df_tab = df_tab[df_tab['linhagem'] == lin_fil2]

# Contadores
n_prod2   = (df_tab['_fase'] == "🥚 Produção").sum()
n_rec2    = (df_tab['_fase'] == "🐣 Recria").sum()
n_fut2    = (df_tab['_fase'] == "🔜 Recria Futura").sum()
m1, m2, m3 = st.columns(3)
m1.metric("🥚 Em Produção",   n_prod2)
m2.metric("🐣 Em Recria",     n_rec2)
m3.metric("🔜 Recria Futura", n_fut2)

# Ordenação: fase → unidade → dt_aloj
fase_ord2 = {"🥚 Produção": 0, "🐣 Recria": 1, "🔜 Recria Futura": 2}
df_tab['_ford'] = df_tab['_fase'].map(fase_ord2)
df_tab = df_tab.sort_values(['_ford', 'unidade', 'dt_aloj']).reset_index(drop=True)

# Monta exibição com as 6 colunas marcadas na imagem
df_exib = pd.DataFrame({
    "Fase":            df_tab['_fase'].values,
    "Unidade":         df_tab['unidade'].values,
    "Dt. Aloj.":       pd.to_datetime(df_tab['dt_aloj']).dt.strftime("%d/%m/%Y").values,
    "Dt. Inic. Prod.": pd.to_datetime(df_tab['transfer']).dt.strftime("%d/%m/%Y").values,
    "Lote":            df_tab['lote_recria'].values,
    "Recria":          df_tab['granja_recria'].values,
    "Qtde. Fêmeas":    df_tab['femeas'].apply(fmt_n).values,
    "Fêmea - Macho":   df_tab['fem_mac'].values,
})

st.dataframe(
    df_exib,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Fase":            st.column_config.TextColumn("Fase",            width="medium"),
        "Unidade":         st.column_config.TextColumn("Unidade",         width="medium"),
        "Dt. Aloj.":       st.column_config.TextColumn("Dt. Aloj.",       width="small"),
        "Dt. Inic. Prod.": st.column_config.TextColumn("Dt. Inic. Prod.", width="small"),
        "Lote":            st.column_config.TextColumn("Lote",            width="small"),
        "Recria":          st.column_config.TextColumn("Recria",          width="large"),
        "Qtde. Fêmeas":    st.column_config.TextColumn("Qtde.",           width="small"),
        "Fêmea - Macho":   st.column_config.TextColumn("Fêmea - Macho",  width="medium"),
    },
)

st.caption("Grupo Pluma · Sistema de Projeção de Ovos · Curvas oficiais COBB e ROSS")
