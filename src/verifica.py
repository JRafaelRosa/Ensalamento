import json
import os
import pandas as pd

try:
    from src.sala import carregar_config_geral
    from src.gerar_ensalamento import carregar_dados
except ImportError:
    from sala import carregar_config_geral
    from gerar_ensalamento import carregar_dados


def verificar_consistencia(df):
    """Verifica a consistência do ensalamento em um DataFrame."""
    print("\n--- Iniciando verificação de consistência ---")
    erros_encontrados = False

    if df.empty:
        print("  [AVISO] Arquivo de ensalamento está vazio.")
        return

    col_sessao = 'Sessão' if 'Sessão' in df.columns else 'Sessao'
    col_orientador = 'Orientador(a)' if 'Orientador(a)' in df.columns else 'Orientador'
    col_sala = 'Sala'

    sessoes = df[col_sessao].unique()
    for sessao in sessoes:
        df_sessao = df[df[col_sessao] == sessao]
        contagem_salas = df_sessao.groupby(col_orientador)[col_sala].nunique()
        orientadores_em_conflito = contagem_salas[contagem_salas > 1]

        if not orientadores_em_conflito.empty:
            erros_encontrados = True
            for orientador, count in orientadores_em_conflito.items():
                salas = df_sessao[df_sessao[col_orientador] == orientador][col_sala].unique().tolist()
                salas_str = ", ".join(map(str, salas))
                print(
                    f"  [ERRO GRAVE] O orientador '{orientador}' está em {count} salas ({salas_str}) "
                    f"ao mesmo tempo durante a '{sessao}'."
                )

    if not erros_encontrados:
        print("--- Verificação de consistência: Nenhum erro encontrado! ---")
    else:
        print("--- Verificação de consistência: Foram encontrados problemas. ---")


def verificar(caminho_completo_arquivo):
    """Função principal do módulo: carrega um CSV e chama a verificação."""
    try:
        df = pd.read_csv(caminho_completo_arquivo, encoding="utf-8-sig")
        print(f"Arquivo '{caminho_completo_arquivo}' carregado para verificação.")
        verificar_consistencia(df)
    except FileNotFoundError:
        print(f"  [AVISO] Arquivo '{caminho_completo_arquivo}' não foi encontrado.")
    except Exception as e:
        print(f"  [ERRO] Ocorreu um erro ao processar o arquivo: {e}")


def verificar_nao_alocados(nome_base):
    """
    Compara o arquivo de entrada original com os CSVs de saída para encontrar
    alunos que não foram alocados, respeitando as regras de filtro.
    """
    print("\n--- Verificando Alunos Não Alocados ---")

    # 1. Carrega as configurações do evento
    config_evento, config_areas_df, _, _ = carregar_config_geral()
    if config_evento is None or config_areas_df is None:
        print("ERRO: Não foi possível carregar as configurações do evento.")
        return

    # 2. Localiza e carrega a planilha original da área
    caminho_arquivo_base = None
    try:
        config_areas_temp = config_areas_df.copy()
        if 'nome_base' in config_areas_temp.columns:
            config_areas_temp.set_index('nome_base', inplace=True)
        caminho_arquivo_base = config_areas_temp.loc[nome_base.upper()]['caminho_arquivo_base']
    except KeyError:
        caminho_arquivo_base = f"public/{nome_base}.xlsx"

    if not os.path.exists(caminho_arquivo_base):
        caminho_csv = f"public/{nome_base}.csv"
        if os.path.exists(caminho_csv):
            caminho_arquivo_base = caminho_csv

    df_original = carregar_dados(caminho_arquivo_base)
    if df_original is None or df_original.empty:
        print(f"ERRO: Não foi possível carregar o arquivo original de trabalhos '{caminho_arquivo_base}'.")
        return

    # 3. Aplica os mesmos filtros que o gerador de ensalamento
    todos_nomes_a_ignorar = set()
    regras_a_ignorar = config_evento.get("ARQUIVOS_A_IGNORAR", {})
    arquivos_filtro = regras_a_ignorar.get("GLOBAL", []) + regras_a_ignorar.get(nome_base.upper(), [])

    for arquivo_filtro in arquivos_filtro:
        if os.path.exists(arquivo_filtro):
            try:
                if arquivo_filtro.lower().endswith('.csv'):
                    df_filtro = pd.read_csv(arquivo_filtro, encoding="utf-8-sig")
                else:
                    df_filtro = pd.read_excel(arquivo_filtro)

                col_aluno = [c for c in df_filtro.columns if c.lower() in ['aluno', 'apresentador', 'apresentador(a)']]
                if col_aluno:
                    todos_nomes_a_ignorar.update(df_filtro[col_aluno[0]].dropna().astype(str).str.strip().tolist())
            except Exception:
                pass

    col_apresentador = 'Apresentador(a)' if 'Apresentador(a)' in df_original.columns else df_original.columns[0]

    if todos_nomes_a_ignorar:
        df_original = df_original[~df_original[col_apresentador].astype(str).str.strip().isin(todos_nomes_a_ignorar)]

    lista_original_apresentadores = set(df_original[col_apresentador].astype(str).str.strip())

    # 4. Carrega a lista de alunos alocados em todos os dias do evento
    alunos_alocados = set()
    dias_evento = config_evento.get("DIAS_EVENTO", 2)

    for dia in range(1, dias_evento + 1):
        caminho_csv_saida = f"public/csv/{nome_base}_dia{dia}.csv"
        if os.path.exists(caminho_csv_saida):
            try:
                df_dia = pd.read_csv(caminho_csv_saida, encoding="utf-8-sig")
                col_alocado = 'Apresentador(a)' if 'Apresentador(a)' in df_dia.columns else df_dia.columns[0]
                alunos_alocados.update(df_dia[col_alocado].astype(str).str.strip().tolist())
            except Exception:
                pass

    # 5. Compara as duas listas e exibe o resultado
    nao_alocados = lista_original_apresentadores - alunos_alocados

    print(f"Total de trabalhos na lista de entrada (após filtros): {len(lista_original_apresentadores)}")
    print(f"Total de trabalhos alocados no ensalamento: {len(alunos_alocados)}")

    if nao_alocados:
        print(f"\nAVISO: {len(nao_alocados)} trabalho(s) que deveriam ser alocados ficaram de fora!")
        print("Lista de não alocados:")
        for nome in sorted(list(nao_alocados)):
            print(f"- {nome}")
    else:
        print("\nSucesso! Todos os trabalhos válidos foram alocados.")