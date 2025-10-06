import pandas as pd


def verificar_consistencia(df):
    """
    Verifica a consistência do ensalamento para duas regras críticas.
    """
    print("--- Iniciando verificação de consistência do ensalamento ---")
    erros_encontrados = False

    # (A lógica de verificação continua a mesma, sem alterações)
    print("- Verificando limite de trabalhos por sessão/sala...")
    sessoes_salas = df.groupby(['Sessão', 'Sala'])
    for (nome_sessao, nome_sala), grupo in sessoes_salas:
        contagem_orientador = grupo['Orientador(a)'].value_counts()
        orientadores_com_limite = contagem_orientador[contagem_orientador >= 6]
        if not orientadores_com_limite.empty:
            for orientador, count in orientadores_com_limite.items():
                print(
                    f"[AVISO] O orientador '{orientador}' tem {count} trabalhos na sala '{nome_sala}' durante a sessão '{nome_sessao}'."
                )
                erros_encontrados = True

    print("- Verificando conflito de salas para orientadores...")
    sessoes = df['Sessão'].unique()
    for sessao in sessoes:
        df_sessao = df[df['Sessão'] == sessao]
        contagem_salas_por_orientador = df_sessao.groupby('Orientador(a)')['Sala'].nunique()
        orientadores_em_conflito = contagem_salas_por_orientador[contagem_salas_por_orientador > 1]

        if not orientadores_em_conflito.empty:
            for orientador, count in orientadores_em_conflito.items():
                salas = df_sessao[df_sessao['Orientador(a)'] == orientador]['Sala'].unique().tolist()
                print(
                    f"[ERRO GRAVE] O orientador '{orientador}' está em {count} salas ({', '.join(salas)}) ao mesmo tempo durante a sessão '{sessao}'."
                )
                erros_encontrados = True

    if not erros_encontrados:
        print("--- Verificação concluída. Nenhum erro de consistência encontrado. ---")
    else:
        print("--- Verificação concluída. Foram encontrados problemas no ensalamento. ---")


def formatar_ensalamento_por_sala(df):
    """
    Exibe a programação formatada e agrupada por Sessão e Sala.
    """
    print("\n" + "=" * 70)
    print(" VISUALIZAÇÃO DO ENSALAMENTO ".center(70, "="))
    print("=" * 70 + "\n")

    sessoes_agrupadas = df.groupby(['Sessão', 'Sala'])

    for (nome_sessao, nome_sala), df_grupo in sessoes_agrupadas:
        print(f"--- SESSÃO: {nome_sessao} | SALA: {nome_sala} ---")

        for _, trabalho in df_grupo.iterrows():
            horario = trabalho['Horário']
            aluno = trabalho['Apresentador(a)']
            orientador = trabalho['Orientador(a)']
            titulo = trabalho['Título']
            print(f"  {horario} | {aluno} | {orientador} | {titulo}")

        print()  # Adiciona uma linha em branco para separar


def verificar(caminho_completo_arquivo):
    """
    Função principal do módulo: carrega, verifica e AGORA TAMBÉM EXIBE.
    """
    try:
        df = pd.read_csv(caminho_completo_arquivo)
        print(f"Arquivo '{caminho_completo_arquivo}' carregado.")

        # 1. Roda a verificação de consistência (como antes)
        verificar_consistencia(df)

        # 2. Roda a formatação para exibir no terminal (a parte que faltava)
        formatar_ensalamento_por_sala(df)

    except FileNotFoundError:
        print(f"  [ERRO] Arquivo '{caminho_completo_arquivo}' não foi encontrado.")
    except Exception as e:
        print(f"  [ERRO] Ocorreu um erro ao processar o arquivo: {e}")