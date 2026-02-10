"""
NOTA DE PORTFÓLIO:
Este código é uma versão sanitizada de uma ferramenta desenvolvida para uso corporativo real.
Dados sensíveis, nomes de clientes e regras específicas de negócio foram substituídos por lógica genérica de mercado para fins de demonstração e ética profissional.
"""

import requests
import json
import csv
import os
import sys

# --- 1. CONFIGURAÇÕES ---
ARQUIVO_ENTRADA = 'transacoes_financeiras.csv' 
ARQUIVO_SAIDA = 'classificacao_final.csv'
# Modelo sugerido: qwen2.5-coder:7b ou llama3 (leves e excelentes em lógica)
MODELO_OLLAMA = "qwen2.5-coder:7b" 
URL_OLLAMA = "http://localhost:11434/api/generate"

# --- 2. INTEELIGÊNCIA DO NEGÓCIO (PROMPT ENGINEERING) ---

# Regras genéricas de controladoria para guiar a IA
REGRAS_NEGOCIO = """
1. GASTOS COM PESSOAL (Salários, Férias, 13º, Benefícios):
   - Se Centro de Custo for ADM/RH/FINANCEIRO/DIRETORIA -> Classificar como: Despesas Administrativas.
   - Se Centro de Custo for FÁBRICA/PRODUÇÃO/OPERAÇÃO -> Classificar como: Custo do Produto Vendido (CPV).
   - Se Centro de Custo for COMERCIAL/VENDAS/LOJAS -> Classificar como: Despesas Comerciais.

2. INFRAESTRUTURA (Aluguel, Energia, Água, Manutenção):
   - Se for na FÁBRICA -> Custos Indiretos de Fabricação.
   - Se for no ESCRITÓRIO -> Despesas Administrativas.
   - Se for na LOJA -> Despesas Comerciais.

3. LOGÍSTICA & FRETES:
   - Combustível, Pedágio, Manutenção de Veículos -> Despesas de Entrega/Logística.
   - Frete sobre Vendas -> Despesas de Entrega/Logística.
   - Frete sobre Compras (Matéria Prima) -> Custo do Estoque (Matéria-Prima).

4. IMPOSTOS:
   - ICMS, PIS, COFINS, ISS -> Deduções da Receita.
   - IPTU, IPVA, Taxas diversas -> Despesas Tributárias.

5. MARKETING:
   - Google Ads, Facebook, Brindes, Eventos -> Despesas de Marketing.
"""

# Lista fechada de categorias para evitar que a IA invente nomes
CATEGORIAS_VALIDAS = """
- Custo do Produto Vendido (CPV)
- Custos Indiretos de Fabricação
- Custo com Matéria-Prima
- Despesas Administrativas
- Despesas Comerciais
- Despesas de Marketing
- Despesas de Entrega/Logística
- Despesas Financeiras (Juros/Multas)
- Despesas Tributárias
- Deduções da Receita
- Investimentos (CAPEX)
- Distribuição de Lucros/Sócios
"""

# --- 3. FUNÇÕES ---

def classificar_transacao(conta, centro):
    """
    Envia a transação para o LLM local (Ollama) e retorna a classificação.
    """
    prompt = f"""
    Aja como um Controller Financeiro Sênior e classifique a despesa abaixo.
    
    REGRA DE OURO: O CENTRO DE CUSTO define a finalidade (Operacional vs Adm vs Comercial).
    
    --- REGRAS DE REFERÊNCIA ---
    {REGRAS_NEGOCIO}
    
    --- CATEGORIAS PERMITIDAS (USE APENAS ESTAS) ---
    {CATEGORIAS_VALIDAS}
    
    --- EXEMPLOS DE RACIOCÍNIO (Few-Shot Prompting) ---
    Entrada: Conta="SALARIOS", Centro="RH" -> Saída: Despesas Administrativas
    Entrada: Conta="SALARIOS", Centro="LINHA DE PRODUCAO" -> Saída: Custo do Produto Vendido (CPV)
    Entrada: Conta="ENERGIA ELETRICA", Centro="FABRICA" -> Saída: Custos Indiretos de Fabricação
    
    --- NOVA TRANSAÇÃO PARA CLASSIFICAR ---
    Conta Contábil: {conta}
    Centro de Custo: {centro}
    
    Responda APENAS a categoria exata da lista acima. Sem explicações adicionais.
    """
    
    payload = {
        "model": MODELO_OLLAMA, 
        "prompt": prompt,
        "stream": False,
        "temperature": 0.1 # Temperatura baixa para garantir consistência e evitar alucinação
    }
    
    try:
        r = requests.post(URL_OLLAMA, json=payload)
        if r.status_code == 200:
            return r.json().get('response', '').strip()
        return f"ERRO API: {r.status_code}"
    except Exception as e:
        return f"ERRO CONEXÃO: {e}. Verifique se o Ollama está rodando."

def main():
    print(f"--- Iniciando Classificador IA ({MODELO_OLLAMA}) ---")

    # Verifica se o arquivo de entrada existe
    if not os.path.exists(ARQUIVO_ENTRADA):
        print(f"\n[ERRO] Arquivo '{ARQUIVO_ENTRADA}' não encontrado.")
        print("Por favor, crie um arquivo CSV com o formato: CONTA;CENTRO_CUSTO")
        return

    print(f"Lendo dados de: {ARQUIVO_ENTRADA}...")
    
    # Tenta contar linhas para mostrar progresso
    try:
        with open(ARQUIVO_ENTRADA, 'r', encoding='utf-8') as f:
            total_linhas = sum(1 for line in f) - 1 # Desconta cabeçalho
    except:
        total_linhas = "?"

    # Processamento linha a linha (Streaming de arquivo)
    with open(ARQUIVO_ENTRADA, 'r', encoding='utf-8') as f_in, \
         open(ARQUIVO_SAIDA, 'w', newline='', encoding='utf-8') as f_out:
        
        # Ajuste o delimitador conforme seu CSV (; ou ,)
        leitor = csv.reader(f_in, delimiter=';') 
        escritor = csv.writer(f_out, delimiter=';')
        
        # Escreve cabeçalho no arquivo de saída
        escritor.writerow(['CONTA', 'CENTRO', 'CLASSIFICACAO_IA']) 
        
        # Tenta pular o cabeçalho do arquivo de entrada
        header = next(leitor, None)
        
        print(f"Processando {total_linhas} registros...")

        for i, linha in enumerate(leitor, 1):
            if len(linha) < 2: continue # Pula linhas vazias ou incompletas
            
            conta = linha[0].strip()
            centro = linha[1].strip()
            
            # Feedback visual no terminal (imprime na mesma linha)
            print(f"[{i}/{total_linhas}] Classificando: {conta} ({centro})...", end='\r')
            
            resultado = classificar_transacao(conta, centro)
            
            escritor.writerow([conta, centro, resultado])
            
    print(f"\n\n✅ SUCESSO! Classificação concluída.")
    print(f"Arquivo gerado: {ARQUIVO_SAIDA}")

if __name__ == "__main__":
    main()
