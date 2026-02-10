import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
from utils.xml_parser import extrair_dados_nfse

# URL de conexão atualizada
DB_URL = "postgresql+psycopg2://lucasprado:HDGawOQc1792ECmNHGnaQKPi9hMJwD4S@dpg-d65gn7dum26s73birugg-a.virginia-postgres.render.com/db_controlefinanceiropradoconsulting"
engine = create_engine(DB_URL)

st.set_page_config(page_title="Lucas Prado - Gestão MEI", layout="wide")

st.sidebar.title("🛠️ Controle Financeiro")
menu = st.sidebar.selectbox("Ir para:", ["Dashboard", "Importar XML", "Histórico"])

# --- IMPORTAR XML ---
if menu == "Importar XML":
    st.header("📥 Importar Notas Fiscais")
    files = st.file_uploader("Arraste os XMLs", type="xml", accept_multiple_files=True)
    
    if files:
        novos = []
        with engine.connect() as conn:
            existentes = [r[0] for r in conn.execute(text("SELECT chave_nfse FROM lancamentos"))]

        for f in files:
            dados = extrair_dados_nfse(f.read())
            if dados['chave_nfse'] in existentes:
                st.warning(f"Nota já importada: {dados['chave_nfse']}")
            else:
                novos.append(dados)

        if novos:
            df_novos = pd.DataFrame(novos)
            st.dataframe(df_novos)
            if st.button("Salvar no Render"):
                df_novos.to_sql('lancamentos', engine, if_exists='append', index=False)
                st.success("Salvo com sucesso!")

# --- DASHBOARD ---
elif menu == "Dashboard":
    st.header("📊 Resumo de Faturamento")
    df = pd.read_sql("SELECT * FROM lancamentos", engine)

    if not df.empty:
        total = df['valor'].sum()
        limite = 81000
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Acumulado", f"R$ {total:,.2f}")
        c2.metric("Fôlego MEI", f"R$ {limite - total:,.2f}")
        c3.progress(min(total/limite, 1.0), text=f"{(total/limite)*100:.1f}% do teto")

        # Gráfico por Cliente
        df_cli = df.groupby('cliente')['valor'].sum().reset_index()
        fig_cli = px.pie(df_cli, values='valor', names='cliente', title="Faturamento por Cliente", hole=.4)
        st.plotly_chart(fig_cli, use_container_width=True)
    else:
        st.info("Nenhuma nota encontrada.")

# --- HISTÓRICO ---
elif menu == "Histórico":
    st.header("📜 Todas as Notas")
    df_h = pd.read_sql("SELECT data_registro, cliente, valor, descricao FROM lancamentos ORDER BY data_registro DESC", engine)
    st.table(df_h)