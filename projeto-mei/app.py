# --- TELA: DASHBOARD ---
elif menu == "Dashboard":
    st.header("📊 Análise de Faturamento")
    
    # Busca todos os dados para alimentar o filtro de ano
    df = pd.read_sql("SELECT * FROM lancamentos WHERE tipo = 'Receita'", engine)
    
    if not df.empty:
        # Criar coluna de Ano e Mês para facilitar filtros
        df['data_registro'] = pd.to_datetime(df['data_registro'])
        df['ano'] = df['data_registro'].dt.year
        df['mes_ano'] = df['data_registro'].dt.strftime('%m/%Y')
        df['mes_nome'] = df['data_registro'].dt.strftime('%b') # Jan, Fev...

        # --- FILTRO DE ANO NA SIDEBAR ---
        anos_disponiveis = sorted(df['ano'].unique(), reverse=True)
        ano_selecionado = st.sidebar.selectbox("Selecione o Ano", anos_disponiveis)

        # Filtrar o DataFrame com base na escolha
        df_filtrado = df[df['ano'] == ano_selecionado]

        # --- KPIs DO ANO SELECIONADO ---
        total_ano = df_filtrado['valor'].sum()
        limite_mei = 81000
        
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Faturamento em {ano_selecionado}", f"R$ {total_ano:,.2f}")
        c2.metric("Saldo Restante (MEI)", f"R$ {max(0, limite_mei - total_ano):,.2f}")
        c3.progress(min(total_ano/limite_mei, 1.0), text=f"{(total_ano/limite_mei)*100:.1f}% do limite anual")

        st.divider()

        # --- GRÁFICO 1: EVOLUÇÃO MÊS A MÊS ---
        st.subheader(f"📈 Evolução Mensal - {ano_selecionado}")
        
        # Agrupar por mês e garantir a ordem cronológica
        df_mensal = df_filtrado.groupby(df_filtrado['data_registro'].dt.month).agg({
            'valor': 'sum',
            'mes_ano': 'first'
        }).reset_index()
        
        fig_evolucao = px.line(df_mensal, x='mes_ano', y='valor', 
                               title="Faturamento Mensal",
                               markers=True,
                               text=df_mensal['valor'].apply(lambda x: f"R$ {x:,.2f}"))
        
        # Linha da média do MEI (R$ 6.750)
        fig_evolucao.add_hline(y=6750, line_dash="dot", line_color="red", 
                               annotation_text="Média Limite MEI (R$ 6.750)")
        
        st.plotly_chart(fig_evolucao, use_container_width=True)

        # --- GRÁFICO 2: FATURAMENTO POR CLIENTE ---
        st.subheader("🎯 Concentração por Cliente")
        df_cli = df_filtrado.groupby('cliente')['valor'].sum().reset_index().sort_values('valor', ascending=False)
        fig_pizza = px.pie(df_cli, values='valor', names='cliente', 
                           hole=.4, title=f"Faturamento por Cliente em {ano_selecionado}")
        st.plotly_chart(fig_pizza, use_container_width=True)

    else:
        st.info("Nenhum dado cadastrado ainda. Vá em 'Importar XML' para começar.")
