import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
from utils.xml_parser import extrair_dados_nfse

# 1. CONEXÃO (RENDER)
DB_URL = "postgresql+psycopg2://lucasprado:HDGawOQc1792ECmNHGnaQKPi9hMJwD4S@dpg-d65gn7dum26s73birugg-a.virginia-postgres.render.com/db_controlefinanceiropradoconsulting"
engine = create_engine(DB_URL)

st.set_page_config(page_title="Lucas Prado - Multi-CNPJ", layout="wide")

# 2. MENU LATERAL
st.sidebar.title("🛠️ Gestão de Empresas")
menu = st.sidebar.selectbox("Navegação", ["Dashboard", "Importar XML", "Histórico"])

# --- TELA: IMPORTAR XML ---
if menu == "Importar XML":
    st.header("📥 Importar Notas Fiscais")
    files = st.file_uploader("Selecione os XMLs", type="xml", accept_multiple_files=True)
    
    if files:
        novos = []
        with engine.connect() as conn:
            res = conn.execute(text("SELECT chave_nfse FROM lancamentos"))
            existentes = [r[0] for r in res]

        for f in files:
            dados = extrair_dados_nfse(f.read())
            if dados['chave_nfse'] in existentes:
                st.warning(f"Nota já existe: {dados['chave_nfse']}")
            else:
                novos.append(dados)

        if novos:
            df_novos = pd.DataFrame(novos)
            st.dataframe(df_novos[['cnpj_emissor', 'cliente', 'valor']])
            if st.button("Salvar no Banco de Dados"):
                df_novos.to_sql('lancamentos', engine, if_exists='append', index=False)
                st.success("Dados salvos!")

# --- TELA: DASHBOARD ---
elif menu == "Dashboard":
    st.header("📊 Análise por CNPJ")
    
    try:
        df = pd.read_sql("SELECT * FROM lancamentos", engine)
    except Exception:
        df = pd.DataFrame()

    if not df.empty:
        # Preparação de Dados
        df['data_registro'] = pd.to_datetime(df['data_registro'])
        df['ano'] = df['data_registro'].dt.year
        df['mes_ano'] = df['data_registro'].dt.strftime('%m/%Y')

        # --- FILTROS NA SIDEBAR ---
        st.sidebar.subheader("Filtros")
        
        # Filtro de CNPJ (Importante para não misturar os limites)
        meus_cnpjs = sorted(df['cnpj_emissor'].unique())
        cnpj_sel = st.sidebar.selectbox("Selecione sua Empresa", meus_cnpjs)
        
        # Filtro de Ano
        anos = sorted(df['ano'].unique(), reverse=True)
        ano_sel = st.sidebar.selectbox("Ano de Referência", anos)

        # Aplicar Filtros
        df_filtrado = df[(df['cnpj_emissor'] == cnpj_sel) & (df['ano'] == ano_sel)]

        # --- KPIs ---
        total_empresa = df_filtrado['valor'].sum()
        limite_mei = 81000
        
        st.subheader(f"Resumo: {cnpj_sel}")
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Total {ano_sel}", f"R$ {total_empresa:,.2f}")
        c2.metric("Saldo Limite MEI", f"R$ {max(0, limite_mei - total_empresa):,.2f}")
        
        perc = min(total_empresa/limite_mei, 1.0)
        c3.progress(perc, text=f"{perc*100:.1f}% do teto anual")

        # --- GRÁFICO MENSAL ---
        st.divider()
        df_mensal = df_filtrado.groupby(df_filtrado['data_registro'].dt.month).agg({
            'valor': 'sum', 'mes_ano': 'first'
        }).reset_index().sort_values('data_registro')

        fig = px.line(df_mensal, x='mes_ano', y='valor', markers=True, title="Evolução Mensal de Faturamento")
        fig.add_hline(y=6750, line_dash="dot", line_color="red", annotation_text="Média MEI")
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("Importe notas para visualizar o dashboard.")

# --- TELA: HISTÓRICO ---
elif menu == "Histórico":
    st.header("📜 Histórico Geral")
    df_h = pd.read_sql("SELECT cnpj_emissor, data_registro, cliente, valor FROM lancamentos ORDER BY data_registro DESC", engine)
    st.dataframe(df_h, use_container_width=True)
