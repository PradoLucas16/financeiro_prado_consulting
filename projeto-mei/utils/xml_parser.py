import xml.etree.ElementTree as ET

def extrair_dados_nfse(xml_content):
    ns = {'ns': 'http://www.sped.fazenda.gov.br/nfse'}
    
    try:
        # Tenta ler o conteúdo (suporta bytes ou string)
        root = ET.fromstring(xml_content if isinstance(xml_content, bytes) else xml_content.encode('utf-8'))
    except Exception as e:
        return {"erro": f"Falha na leitura do XML: {str(e)}"}

    # --- IDENTIFICADOR ÚNICO ---
    inf_nfse = root.find('.//ns:infNFSe', ns)
    chave = inf_nfse.attrib.get('Id', 'SEM-CHAVE') if inf_nfse is not None else 'SEM-CHAVE'

    # --- DADOS DO TOMADOR (CLIENTE) - COM BLINDAGEM ---
    toma = root.find('.//ns:toma', ns)
    if toma is not None:
        nome_el = toma.find('ns:xNome', ns)
        cliente_nome = nome_el.text if nome_el is not None else "Consumidor Não Identificado"
        
        cnpj_el = toma.find('ns:CNPJ', ns)
        cpf_el = toma.find('ns:CPF', ns)
        documento = cnpj_el.text if cnpj_el is not None else (cpf_el.text if cpf_el is not None else "000.000.000-00")
    else:
        # Se a tag <toma> sequer existir no XML
        cliente_nome = "Consumidor Não Identificado"
        documento = "000.000.000-00"

    # --- DATA DE EMISSÃO ---
    data_el = root.find('.//ns:infDPS/ns:dhEmi', ns)
    data_emi = data_el.text[:10] if data_el is not None else "2000-01-01"

    # --- DESCRIÇÃO DO SERVIÇO ---
    desc_el = root.find('.//ns:serv/ns:cServ/ns:xDescServ', ns)
    descricao = desc_el.text if desc_el is not None else "Serviço Prestado (Descrição Ausente)"

    # --- VALOR DO SERVIÇO ---
    valor_el = root.find('.//ns:valores/ns:vServPrest/ns:vServ', ns)
    valor = float(valor_el.text) if valor_el is not None else 0.0

    return {
        "chave_nfse": chave,
        "data_registro": data_emi,
        "cliente": cliente_nome,
        "documento_cliente": documento,
        "valor": valor,
        "descricao": descricao,
        "tipo": "Receita",
        "categoria": "Serviço"
    }
