import streamlit as st
import pandas as pd
import io
import re


def tratar_planilha(file, incoterm_valor):
    # Carrega a planilha de origem ignorando o header original (linha 1)
    df_origem = pd.read_excel(file, header=0)

    # Criando o DataFrame final com a estrutura exata solicitada (Case Sensitive)
    colunas_finais = [
        'PARTNUMBER', 'QUANTIDADE', 'UNIDADE', 'PRECOTOTAL', 'PESOTOTAL',
        'INCOTERMS', 'MOEDA', 'FATURA', 'OUTRAS REFERENCIAS', 'nrlote', 'expedicao'
    ]
    df_final = pd.DataFrame(columns=colunas_finais)

    def col_idx(letra):
        return ord(letra.upper()) - ord('A')

    # A: PARTNUMBER ➔ Origem A
    df_final['PARTNUMBER'] = df_origem.iloc[:, col_idx('A')]

    # B: QUANTIDADE ➔ Origem F
    df_final['QUANTIDADE'] = df_origem.iloc[:, col_idx('F')]

    # C: UNIDADE ➔ Lógica Tênis/Sapato/Mocassim
    def verificar_unidade(valor):
        valor_str = str(valor).upper()
        palavras_pares = ["TENIS", "TÊNIS", "SAPATO", "MOCASSIM"]
        if any(p in valor_str for p in palavras_pares):
            return "PARES"
        return "PECA"

    df_final['UNIDADE'] = df_origem.iloc[:, col_idx('J')].apply(verificar_unidade)

    # D: PRECOTOTAL ➔ K * F
    df_final['PRECOTOTAL'] = pd.to_numeric(df_origem.iloc[:, col_idx('K')], errors='coerce') * pd.to_numeric(
        df_origem.iloc[:, col_idx('F')], errors='coerce')

    # E: PESOTOTAL ➔ G * F
    df_final['PESOTOTAL'] = pd.to_numeric(df_origem.iloc[:, col_idx('G')], errors='coerce') * pd.to_numeric(
        df_origem.iloc[:, col_idx('F')], errors='coerce')

    # F: INCOTERMS ➔ Valor da interface
    df_final['INCOTERMS'] = incoterm_valor

    # G: MOEDA ➔ Sempre '790'
    df_final['MOEDA'] = '790'

    # H: FATURA ➔ Origem Q
    df_final['FATURA'] = df_origem.iloc[:, col_idx('Q')]

    # I: OUTRAS REFERENCIAS ➔ Origem Y (Tratado como Texto Puro para evitar o E+12)
    def limpar_referencia(valor):
        if pd.isna(valor): return ""
        val_str = str(valor).strip()
        if val_str.endswith('.0'): val_str = val_str[:-2]
        return val_str

    df_final['OUTRAS REFERENCIAS'] = df_origem.iloc[:, col_idx('Y')].apply(limpar_referencia)

    # --- OPÇÃO B: REGRINHA DAS COLUNAS J E K COM REGEX (À prova de falhas de digitação) ---
    def extrair_dados_regex(valor):
        val_str = str(valor).strip()

        # Procura por dois blocos de texto separados por qualquer tipo de barra (\ ou /)
        # permitindo variações com ou sem espaços.
        match = re.search(r"([^\/\\]+)\s*[\/\\]+\s*([^\/\\]+)", val_str)

        if match:
            # Pega o primeiro bloco, limpa espaços e captura os 6 primeiros caracteres
            parte_1 = match.group(1).strip()
            exp = parte_1[:6]

            # Pega o segundo bloco, limpa espaços e captura os 3 últimos caracteres
            parte_2 = match.group(2).strip()
            lote = parte_2[-3:]

            return lote, exp

        # Caso a célula não tenha o padrão esperado (ex: sem barras), tenta um split simples por segurança
        try:
            for sep in ["\\", "/"]:
                if sep in val_str:
                    partes = val_str.split(sep)
                    return partes[1].strip()[-3:], partes[0].strip()[:6]
        except:
            pass

        return "", ""

    # Aplicando a Opção B na coluna X da planilha de origem
    dados_extraidos = df_origem.iloc[:, col_idx('X')].apply(extrair_dados_regex)
    df_final['nrlote'] = [d[0] for d in dados_extraidos]
    df_final['expedicao'] = [d[1] for d in dados_extraidos]

    return df_final


# --- CONFIGURAÇÃO DA INTERFACE WEB (STREAMLIT) ---
st.set_page_config(page_title="Tratador de Planilhas", layout="centered")
st.title("Tratamento de Arquivos Excel")
st.markdown("Insira os dados abaixo para gerar a nova planilha tratada.")

incoterm_input = st.text_input("Informe o INCOTERMS:", placeholder="Ex: FOB, CIF, EXW...")
uploaded_file = st.file_uploader("Selecione o arquivo Excel de origem (.xlsx)", type=["xlsx"])

if uploaded_file and incoterm_input:
    if st.button("Processar Planilha", use_container_width=True):
        try:
            with st.spinner("Processando dados com a lógica de Regex..."):
                resultado = tratar_planilha(uploaded_file, incoterm_input)
                output = io.BytesIO()

                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    resultado.to_excel(writer, index=False, sheet_name='Planilha Tratada')
                    workbook = writer.book
                    worksheet = writer.sheets['Planilha Tratada']

                    # Força a formatação de texto puro do Excel nas colunas I, J e K (índices 8, 9, 10)
                    # Isso garante que lotes numéricos ou referências longas não quebrem visualmente
                    fmt_txt = workbook.add_format({'num_format': '@'})
                    worksheet.set_column(8, 10, None, fmt_txt)

                st.success("Planilha processada com sucesso!")
                st.download_button(
                    label="📥 Clique aqui para baixar a Planilha Tratada",
                    data=output.getvalue(),
                    file_name="planilha_tratada.xlsx",
                    use_container_width=True
                )
        except Exception as e:
            st.error(f"Erro ao processar: {e}")

elif uploaded_file and not incoterm_input:
    st.warning("⚠️ Por favor, digite o INCOTERMS no campo de texto para liberar o processamento.")