import json
import os
import pandas as pd


def carregar_regras_evento():
    """Lê as regras globais configuradas em config_evento.json."""
    caminho_config = "public/config/config_evento.json"
    min_trabalhos = 4
    max_trabalhos = 6
    dias_evento = 2

    if os.path.exists(caminho_config):
        try:
            with open(caminho_config, 'r', encoding='utf-8') as f:
                config = json.load(f)
                min_trabalhos = config.get("MIN_TRABALHOS_SESSAO", 4)
                max_trabalhos = config.get("MAX_TRABALHOS_ORIENTADOR_SESSAO", 6)
                dias_evento = config.get("DIAS_EVENTO", 2)
        except Exception:
            pass

    return min_trabalhos, max_trabalhos, dias_evento


def carregar_ensalamento(nome_base):
    """Carrega os arquivos CSV de ensalamento para todos os dias do evento e mapeia os orientadores."""
    dfs = []
    _, _, dias_evento = carregar_regras_evento()

    for dia in range(1, dias_evento + 1):
        caminho = f"public/csv/{nome_base}_dia{dia}.csv"
        try:
            df_dia = pd.read_csv(caminho, encoding="utf-8-sig")
            df_dia['Dia'] = dia
            dfs.append(df_dia)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            pass

    if not dfs:
        return None, None

    df_completo = pd.concat(dfs, ignore_index=True)

    # Cria a chave do bloco dividindo o nome da sessão no caractere '(' se existir
    df_completo['Bloco_ID'] = "D" + df_completo['Dia'].astype(str) + "-" + \
                              df_completo['Sessão'].astype(str).str.split(' \(').str[0]

    orientadores_por_bloco = {}
    for bloco in df_completo['Bloco_ID'].unique():
        df_bloco = df_completo[df_completo['Bloco_ID'] == bloco]
        orientadores_por_bloco[bloco] = df_bloco.groupby('Sala')['Orientador(a)'].apply(
            lambda x: list(set(x.dropna()))).to_dict()

    return df_completo, orientadores_por_bloco


def salvar_ensalamento(df, nome_base):
    """Reordena e recalcula os horários de cada slot antes de salvar os arquivos por dia."""
    PASTA_SAIDA_CSV = "public/csv"
    os.makedirs(PASTA_SAIDA_CSV, exist_ok=True)
    _, _, dias_evento = carregar_regras_evento()

    # Prepara o dataframe ordenado por dia, sessão e sala
    df_trabalhos = df.copy()

    # Tratamento seguro para conversão de horários
    df_trabalhos['Horario_DT'] = pd.to_datetime(df_trabalhos['Horário'], format='%H:%M', errors='coerce')
    df_corrigido = df_trabalhos.sort_values(by=['Dia', 'Sessão', 'Sala', 'Horario_DT']).reset_index(drop=True)

    lista_dfs_sessao = []
    sessoes_unicas = df_corrigido[['Dia', 'Sessão', 'Sala']].drop_duplicates()

    for _, sessao_info in sessoes_unicas.iterrows():
        df_sessao_atual = df_corrigido[
            (df_corrigido['Dia'] == sessao_info['Dia']) &
            (df_corrigido['Sessão'] == sessao_info['Sessão']) &
            (df_corrigido['Sala'] == sessao_info['Sala'])
            ].copy()

        sessao_str = str(sessao_info['Sessão'])
        if '(' in sessao_str and ')' in sessao_str:
            horario_inicio_str = sessao_str.split('(')[1].replace(')', '').strip()
        else:
            horario_inicio_str = '08:30'

        horario_atual = pd.to_datetime(horario_inicio_str, format='%H:%M', errors='coerce')
        if pd.isna(horario_atual):
            horario_atual = pd.to_datetime('08:30', format='%H:%M')

        novos_horarios = []
        for _ in range(len(df_sessao_atual)):
            novos_horarios.append(horario_atual.strftime('%H:%M'))
            horario_atual += pd.Timedelta(minutes=15)

        df_sessao_atual['Horário'] = novos_horarios
        lista_dfs_sessao.append(df_sessao_atual)

    if not lista_dfs_sessao:
        print("AVISO: Nenhum dado para salvar.")
        return

    df_final = pd.concat(lista_dfs_sessao, ignore_index=True)
    colunas_para_salvar = ['Sessão', 'Horário', 'Sala', 'Título', 'Apresentador(a)', 'Orientador(a)']

    for dia in range(1, dias_evento + 1):
        df_dia = df_final[df_final['Dia'] == dia]

        if not df_dia.empty:
            df_dia_salvar = df_dia[colunas_para_salvar]
            nome_arquivo = os.path.join(PASTA_SAIDA_CSV, f"{nome_base}_dia{dia}.csv")
            df_dia_salvar.to_csv(nome_arquivo, index=False, encoding="utf-8-sig", quoting=1)
            print(f"Arquivo '{nome_arquivo}' salvo com sucesso!")


def movimento_e_valido(orientador, bloco_alvo, sala_alvo, orientadores_por_bloco):
    """Verifica se um orientador já possui aluno em outra sala na mesma sessão e bloco de horário."""
    orientadores_no_bloco = orientadores_por_bloco.get(bloco_alvo, {})
    for sala, orientadores in orientadores_no_bloco.items():
        if sala != sala_alvo and orientador in orientadores:
            return False
    return True


def listar_por_orientador(df):
    """Filtra e exibe os trabalhos atribuídos a um determinado orientador."""
    orientador_input = input("Digite o nome (ou parte do nome) do(a) orientador(a): ").strip().lower()
    if not orientador_input:
        return

    col_orientador = 'Orientador(a)' if 'Orientador(a)' in df.columns else df.columns[0]
    resultados = df[df[col_orientador].astype(str).str.lower().str.contains(orientador_input, na=False)]

    if resultados.empty:
        print("Nenhum orientador encontrado.")
        return

    print("\n--- Trabalhos Encontrados ---")
    for _, trabalho in resultados.iterrows():
        apresentador = trabalho.get('Apresentador(a)', trabalho.get('Apresentador', 'N/A'))
        dia = trabalho.get('Dia', '1')
        sala = trabalho.get('Sala', 'N/A')
        horario = trabalho.get('Horário', 'N/A')

        print(f"Apresentador(a): {apresentador}")
        print(f"  - Dia: {dia}, Sala: {sala}, Horário: {horario}\n")


def trocar(nome_base):
    """Interface CLI interativa para mover apresentadores e ajustar o ensalamento."""
    min_trabalhos, max_trabalhos, _ = carregar_regras_evento()
    df, orientadores_por_bloco = carregar_ensalamento(nome_base)

    if df is None or df.empty:
        print(f"Não foi possível carregar os arquivos para '{nome_base}'. Execute a geração de ensalamento primeiro.")
        return

    while True:
        print("\n--- Ferramenta de Ajuste Manual ---")
        print("1. Ajustar posição de um(a) apresentador(a)")
        print("2. Listar trabalhos por orientador")
        print("0. Voltar ao menu principal")
        resp = input("Escolha uma opção: ").strip()

        if resp == '0':
            break
        elif resp == '2':
            listar_por_orientador(df)
            input("Pressione Enter para continuar...")
            continue
        elif resp != '1':
            print("Opção inválida.")
            continue

        aluno_input = input("Digite o nome do(a) apresentador(a) que deseja mover: ").strip()
        if not aluno_input:
            continue

        col_apresentador = 'Apresentador(a)' if 'Apresentador(a)' in df.columns else df.columns[0]
        trabalho_original_series = df[df[col_apresentador].astype(str).str.lower() == aluno_input.lower()]

        if trabalho_original_series.empty:
            print("ERRO: Apresentador(a) não encontrado(a).")
            continue

        trabalho_original = trabalho_original_series.iloc[0]
        idx_original = trabalho_original_series.index[0]

        print("\nTrabalho encontrado:")
        print(f"  - Apresentador(a): {trabalho_original.get('Apresentador(a)', 'N/A')}")
        print(
            f"  - Local Atual    : Dia {trabalho_original.get('Dia', '1')}, Sala {trabalho_original.get('Sala', 'N/A')}, Horário: {trabalho_original.get('Horário', 'N/A')}")

        print("\nBuscando todas as opções de movimentação válidas. Aguarde...")
        opcoes_validas = []

        df_sessao_origem = df[
            (df['Bloco_ID'] == trabalho_original['Bloco_ID']) &
            (df['Sala'] == trabalho_original['Sala'])
            ]

        # 1. Busca por TROCAS válidas com outros trabalhos
        for idx_alvo, trabalho_alvo in df.iterrows():
            if idx_alvo == idx_original:
                continue

            mov_A_valido = movimento_e_valido(
                trabalho_original['Orientador(a)'],
                trabalho_alvo['Bloco_ID'],
                trabalho_alvo['Sala'],
                orientadores_por_bloco
            )
            mov_B_valido = movimento_e_valido(
                trabalho_alvo['Orientador(a)'],
                trabalho_original['Bloco_ID'],
                trabalho_original['Sala'],
                orientadores_por_bloco
            )

            if mov_A_valido and mov_B_valido:
                opcoes_validas.append({"tipo": "TROCAR", "idx_alvo": idx_alvo, "alvo": trabalho_alvo})

        # 2. Busca por MOVIMENTOS para sessões com vagas
        if len(df_sessao_origem) - 1 >= min_trabalhos:
            sessoes_com_vagas = df.groupby(['Dia', 'Sessão', 'Sala', 'Bloco_ID']).filter(
                lambda x: len(x) < max_trabalhos
            )
            sessoes_unicas_com_vagas = sessoes_com_vagas[['Dia', 'Sessão', 'Sala', 'Bloco_ID']].drop_duplicates()

            for _, sessao_alvo in sessoes_unicas_com_vagas.iterrows():
                if movimento_e_valido(
                        trabalho_original['Orientador(a)'],
                        sessao_alvo['Bloco_ID'],
                        sessao_alvo['Sala'],
                        orientadores_por_bloco
                ):
                    opcoes_validas.append({"tipo": "MOVER", "destino": sessao_alvo.to_dict()})

        if not opcoes_validas:
            print("\nNenhuma movimentação ou troca válida encontrada para este trabalho.")
            continue

        print("\nOpções válidas encontradas:")
        for i, opcao in enumerate(opcoes_validas):
            if opcao['tipo'] == 'MOVER':
                destino = opcao['destino']
                print(
                    f" {i + 1}. MOVER para um slot vago na Sala {destino['Sala']} ({destino['Sessão']}, Dia {destino['Dia']})")
            else:
                alvo = opcao['alvo']
                print(
                    f" {i + 1}. TROCAR com '{alvo.get('Apresentador(a)', 'N/A')}' (Sala {alvo.get('Sala', 'N/A')}, Dia {alvo.get('Dia', '1')}, Horário {alvo.get('Horário', 'N/A')})")

        try:
            escolha = int(input("\nEscolha o número da opção desejada (ou 0 para cancelar): ").strip())
            if escolha == 0 or escolha > len(opcoes_validas):
                print("Operação cancelada.")
                continue

            opcao_escolhida = opcoes_validas[escolha - 1]

            if opcao_escolhida['tipo'] == 'MOVER':
                destino = opcao_escolhida['destino']
                df.loc[idx_original, ['Dia', 'Sessão', 'Sala', 'Bloco_ID']] = [
                    destino['Dia'],
                    destino['Sessão'],
                    destino['Sala'],
                    destino['Bloco_ID']
                ]
                print("\nMovimentação realizada!")

            elif opcao_escolhida['tipo'] == 'TROCAR':
                idx_alvo = opcao_escolhida['idx_alvo']

                loc_original = (
                    trabalho_original['Dia'],
                    trabalho_original['Sessão'],
                    trabalho_original['Horário'],
                    trabalho_original['Sala'],
                    trabalho_original['Bloco_ID']
                )

                trabalho_alvo = df.loc[idx_alvo]
                loc_alvo = (
                    trabalho_alvo['Dia'],
                    trabalho_alvo['Sessão'],
                    trabalho_alvo['Horário'],
                    trabalho_alvo['Sala'],
                    trabalho_alvo['Bloco_ID']
                )

                df.loc[idx_original, ['Dia', 'Sessão', 'Horário', 'Sala', 'Bloco_ID']] = loc_alvo
                df.loc[idx_alvo, ['Dia', 'Sessão', 'Horário', 'Sala', 'Bloco_ID']] = loc_original
                print("\nTroca realizada!")

            confirmar = input("Deseja salvar as alterações nos arquivos CSV? (s/n): ").strip().lower()
            if confirmar == 's':
                salvar_ensalamento(df, nome_base)
                print("Recarregando ensalamento atualizado...")
                df, orientadores_por_bloco = carregar_ensalamento(nome_base)
            else:
                print("Alterações descartadas.")
                df, orientadores_por_bloco = carregar_ensalamento(nome_base)

        except (ValueError, IndexError) as e:
            print(f"ERRO: Opção inválida ({e}).")