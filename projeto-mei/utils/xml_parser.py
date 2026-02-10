import xml.etree.ElementTree as ET

def extrair_dados_nfse(xml_content):
    ns = {'ns': 'http://www.sped.fazenda.gov.br/nfse'}
    try:
        root = ET.fromstring(xml_content if isinstance(xml_content, bytes) else xml_content.encode('utf-8'))
    except Exception as e:
        return {"erro": str(e)}

    # --- NOVIDADE: QUEM EMITIU A NOTA (SEU CNPJ) ---
    prestador = root.find('.//ns:prest', ns)
    meu_cnpj = prestador.find('ns:CNPJ', ns).text if prestador is not None else "00.000.000/0001-00"

    inf_nfse = root.find('.//ns:infNFSe', ns)
    chave = inf_nfse.attrib.get('Id', 'SEM-CHAVE') if inf_nfse is not None else 'SEM-CHAVE'

    # Tomador (Cliente)
    toma = root.find('.//ns:toma', ns)
    cliente_nome = toma.find('ns:xNome', ns).text if toma is not None and toma.find('ns:xNome', ns) is not None else "Consumidor"
    
    # Datas e Valores
    data_el = root.find('.//ns:infDPS/ns:dhEmi', ns)
    data_emi = data_el.text[:10] if data_el is not None else "2025-01-01"
    
    valor_el = root.find('.//ns:valores/ns:vServPrest/ns:vServ', ns)
    valor = float(valor_el.text) if valor_el is not None else 0.0

    return {
        "chave_nfse": chave,
        "cnpj_emissor": meu_cnpj, 
        "data_registro": data_emi,
        "cliente": cliente_nome,
        "valor": valor,
        "tipo": "Receita"
    }
