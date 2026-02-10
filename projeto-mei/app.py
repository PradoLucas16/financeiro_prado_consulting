import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
from utils.xml_parser import extrair_dados_nfse

# 1. CONEXÃO COM O BANCO (RENDER)
DB_URL = "postgresql+psycopg2://lucasprado:HDGawOQc1792ECmNHGnaQKPi9hMJwD4S@dpg-d65gn7dum26s73birugg-a.virginia-postgres.render.com/db_controlefinanceiropradoconsulting"
engine = create_engine(DB_URL)

st.set_page_config(page_title="Lucas Prado - Gestão MEI", layout="wide")

# 2. MENU LATERAL
st.sidebar.title("🛠️ Controle Financeiro")
menu = st.sidebar.selectbox("Ir para:", ["Dashboard", "Importar XML", "Histórico"])

# --- TELA: IMPORTAR XML ---
if menu == "Importar XML":
    st.header("📥 Importar Notas Fiscais")
    files = st.file_uploader("Arraste os XMLs", type="xml", accept_multiple_files=True)
    
    if files:
        novos = []
        with engine.connect() as conn:
            # Busca notas que já estão no banco para não duplicar
            res = conn.execute(text("SELECT chave_nfse FROM lancamentos"))
            existentes = [r[0] for r in res]

        for f in files:
            dados = extrair_dados_nfse(f.read())
            if dados['chave_nfse'] in existentes:
                st.warning(f"Nota já importada: {dados['chave_nfse']}")
            else:
                novos.append(dados)

        if novos:
            df_novos = pd.DataFrame(novos)
            st.write("### Notas Detectadas:")
            st.dataframe(df_novos[['data_registro', 'cliente', 'valor']])
            if st.button("Confirmar e Salvar no Banco"):
                df_novos.to_sql('lancamentos', engine, if_exists='append', index=False)
                st.success("Salvo com sucesso!")
                st.balloons()

# --- TELA: DASHBOARD (COM FILTRO DE ANO) ---
elif menu == "Dashboard":
    st.header("📊 Análise de Faturamento")
    
    try:
        df = pd.read_sql("SELECT * FROM lancamentos WHERE tipo = 'Receita'", engine)
    except Exception:
        df = pd.DataFrame()

    if not df.empty:
        # Tratamento de Datas
        df['data_registro'] = pd.to_datetime(df['data_registro'])
        df['ano'] = df['data_registro'].dt.year
        df['mes_ano'] = df['data_registro'].dt.strftime('%m/%Y')

        # Filtro de Ano na Sidebar
        anos_disponiveis = sorted(df['ano'].unique(), reverse=True)
        ano_selecionado = st.sidebar.selectbox("Selecione o Ano", anos_disponiveis)
        df_filtrado = df[df['ano'] == ano_selecionado]

        # KPIs
        total_ano = df_filtrado['valor'].sum()
        limite_mei = 81000
        
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Total em {ano_selecionado}", f"R$ {total_ano:,.2f}")
        c2.metric("Saldo p/ Limite", f"R$ {max(0, limite_mei - total_ano):,.2f}")
        c3.progress(min(total_ano/limite_mei, 1.0), text=f"{(total_ano/limite_mei)*100:.1f}% do teto")

        st.divider()

        # Gráfico Mensal
        st.subheader(f"📈 Evolução Mensal - {ano_selecionado}")
        df_mensal = df_filtrado.groupby(df_filtrado['data_registro'].dt.month).agg({'valor': 'sum', 'mes_ano': 'first'}).reset_index()
        fig_evolucao = px.line(df_mensal, x='mes_ano', y='valor', markers=True, text_auto='.2s')
        fig_evolucao.add_hline(y=6750, line_dash="dot", line_color="red", annotation_text="Média MEI")
        st.plotly_chart(fig_evolucao, use_container_width=True)

        # Gráfico Cliente
        st.subheader("🎯 Faturamento por Cliente")
        df_cli = df_filtrado.groupby('cliente')['valor'].sum().reset_index()
        fig_pizza = px.pie(df_cli, values='valor', names='cliente', hole=.4)
        st.plotly_chart(fig_pizza, use_container_width=True)
    else:
        st.info("Ainda não há dados. Importe seus XMLs primeiro.")

# --- TELA: HISTÓRICO ---
elif menu == "Histórico":
    st.header("📜 Histórico Detalhado")
    df_h = pd.read_sql("SELECT data_registro, cliente, valor, descricao FROM lancamentos ORDER BY data_registro DESC", engine)
    st.dataframe(df_h, use_container_width=True)
