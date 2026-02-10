import xml.etree.ElementTree as ET

def extrair_dados_nfse(xml_content):
    ns = {'ns': 'http://www.sped.fazenda.gov.br/nfse'}
    root = ET.fromstring(xml_content)
    
    # Identificador Único da Nota
    inf_nfse = root.find('.//ns:infNFSe', ns)
    chave = inf_nfse.attrib['Id'] if inf_nfse is not None else None

    # Dados do Cliente (Tomador)
    toma = root.find('.//ns:toma', ns)
    cliente_nome = toma.find('ns:xNome', ns).text
    
    cnpj = toma.find('ns:CNPJ', ns)
    cpf = toma.find('ns:CPF', ns)
    documento = cnpj.text if cnpj is not None else (cpf.text if cpf is not None else "N/A")

    # Datas
    data_hora = root.find('.//ns:infDPS/ns:dhEmi', ns).text
    data_emi = data_hora[:10] 

    # Descrição e Valor (vServ)
    descricao = root.find('.//ns:serv/ns:cServ/ns:xDescServ', ns).text
    valor = float(root.find('.//ns:valores/ns:vServPrest/ns:vServ', ns).text)

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