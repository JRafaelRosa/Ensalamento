import pandas as pd
import os
from src.sala import carregar_config_geral
from src.gerar_ensalamento import carregar_dados


def verificar_consistencia(df):
    """Verifica a consistência do ensalamento em um DataFrame."""
    print("\n--- Iniciando verificação de consistência ---")
    erros_encontrados = False
    sessoes = df['Sessão'].unique()
    for sessao in sessoes:
        df_sessao = df[df['Sessão'] == sessao]
        contagem_salas = df_sessao.groupby('Orientador(a)')['Sala'].nunique()
        orientadores_em_conflito = contagem_salas[contagem_salas > 1]
        if not orientadores_em_conflito.empty:
            erros_encontrados = True
            for orientador, count in orientadores_em_conflito.items():
                salas = df_sessao[df_sessao['Orientador(a)'] == orientador]['Sala'].unique().tolist()
                print(
                    f"  [ERRO GRAVE] O orientador '{orientador}' está em {count} salas ({', '.join(salas)}) ao mesmo tempo durante a '{sessao}'.")
    if not erros_encontrados:
        print("--- Verificação de consistência: Nenhum erro encontrado! ---")
    else:
        print("--- Verificação de consistência: Foram encontrados problemas. ---")


def verificar(caminho_completo_arquivo):
    """Função principal do módulo: carrega um CSV e chama a verificação."""
    try:
        df = pd.read_csv(caminho_completo_arquivo)
        print(f"Arquivo '{caminho_completo_arquivo}' carregado para verificação.")
        verificar_consistencia(df)
    except FileNotFoundError:
        print(f"  [AVISO] Arquivo '{caminho_completo_arquivo}' não foi encontrado.")
    except Exception as e:
        print(f"  [ERRO] Ocorreu um erro ao processar o arquivo: {e}")


# --- FUNÇÃO ATUALIZADA ---
def verificar_nao_alocados(nome_base):
    """
    Compara o arquivo de entrada original com os CSVs de saída para encontrar
    alunos que não foram alocados, respeitando as regras de filtro.
    """
    print("\n--- Verificando Alunos Não Alocados ---")

    # 1. Carrega a lista original de trabalhos
    df_original = carregar_dados(f"public/{nome_base}.xlsx")
    if df_original is None:
        return

    # 2. Carrega as configurações do evento para saber quais filtros aplicar
    config_evento, _, _, _ = carregar_config_geral()
    if config_evento is None:
        print("ERRO: Não foi possível carregar as configurações do evento.")
        return

    # 3. Aplica os mesmos filtros que o gerador de ensalamento
    todos_nomes_a_ignorar = set()
    regras_a_ignorar = config_evento.get("ARQUIVOS_A_IGNORAR", {})
    # Junta filtros GLOBAIS com os específicos da ÁREA
    arquivos_filtro = regras_a_ignorar.get("GLOBAL", []) + regras_a_ignorar.get(nome_base.upper(), [])

    for arquivo_filtro in arquivos_filtro:
        try:
            df_filtro = pd.read_excel(arquivo_filtro)
            if 'Aluno' in df_filtro.columns:
                todos_nomes_a_ignorar.update(df_filtro['Aluno'].tolist())
        except Exception:
            # Ignora erros de arquivo de filtro aqui, pois o gerador também avisaria
            pass

    if todos_nomes_a_ignorar:
        df_original = df_original[~df_original['Apresentador(a)'].isin(todos_nomes_a_ignorar)]

    lista_original_apresentadores = set(df_original['Apresentador(a)'])

    # 4. Carrega a lista de alunos que foram de fato alocados
    alunos_alocados = set()
    for dia in [1, 2]:
        try:
            df_dia = pd.read_csv(f"public/csv/{nome_base}_dia{dia}.csv")
            alunos_alocados.update(df_dia['Apresentador(a)'].tolist())
        except FileNotFoundError:
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