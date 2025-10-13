import pandas as pd
import os

MIN_TRABALHOS_SESSAO = 4
MAX_TRABALHOS_SESSAO = 6


def carregar_ensalamento(nome_base):
    dfs = [];
    for dia in [1, 2]:
        caminho = f"public/csv/{nome_base}_dia{dia}.csv"
        try:
            df_dia = pd.read_csv(caminho);
            df_dia['Dia'] = dia;
            dfs.append(df_dia)
        except FileNotFoundError:
            pass
    if not dfs: return None, None
    df_completo = pd.concat(dfs, ignore_index=True)
    df_completo['Bloco_ID'] = "D" + df_completo['Dia'].astype(str) + "-" + df_completo['Sessão'].str.split(' \(').str[0]
    orientadores_por_bloco = {}
    for bloco in df_completo['Bloco_ID'].unique():
        orientadores_por_bloco[bloco] = df_completo[df_completo['Bloco_ID'] == bloco].groupby('Sala')[
            'Orientador(a)'].unique().apply(list).to_dict()
    return df_completo, orientadores_por_bloco


def salvar_ensalamento(df, nome_base):
    PASTA_SAIDA_CSV = "public/csv"
    df['Horário'] = pd.to_datetime(df['Horário'], format='%H:%M')
    df_corrigido = df.sort_values(by=['Dia', 'Sessão', 'Sala', 'Horário']).reset_index(drop=True)
    lista_dfs_sessao = []
    sessoes_unicas = df_corrigido[['Dia', 'Sessão', 'Sala']].drop_duplicates()
    for _, sessao_info in sessoes_unicas.iterrows():
        df_sessao_atual = df_corrigido[
            (df_corrigido['Dia'] == sessao_info['Dia']) & (df_corrigido['Sessão'] == sessao_info['Sessão']) & (
                        df_corrigido['Sala'] == sessao_info['Sala'])].copy()
        horario_inicio_str = sessao_info['Sessão'].split('(')[1].replace(')', '')
        horario_atual = pd.to_datetime(horario_inicio_str)
        novos_horarios = []
        for _ in range(len(df_sessao_atual)):
            novos_horarios.append(horario_atual.strftime('%H:%M'))
            horario_atual += pd.Timedelta(minutes=15)
        df_sessao_atual['Horário'] = novos_horarios
        lista_dfs_sessao.append(df_sessao_atual)
    if not lista_dfs_sessao: print("AVISO: Nenhum dado para salvar."); return
    df_final = pd.concat(lista_dfs_sessao)
    for dia in [1, 2]:
        colunas_para_salvar = ['Sessão', 'Horário', 'Sala', 'Título', 'Apresentador(a)', 'Orientador(a)']
        df_dia = df_final[df_final['Dia'] == dia][colunas_para_salvar]
        nome_arquivo = os.path.join(PASTA_SAIDA_CSV, f"{nome_base}_dia{dia}.csv")
        if not df_dia.empty:
            df_dia.to_csv(nome_arquivo, index=False, quoting=1)
            print(f"Arquivo '{nome_arquivo}' salvo com sucesso!")


def movimento_e_valido(orientador, bloco_alvo, sala_alvo, orientadores_por_bloco):
    orientadores_no_bloco = orientadores_por_bloco.get(bloco_alvo, {})
    for sala, orientadores in orientadores_no_bloco.items():
        if sala != sala_alvo and orientador in orientadores: return False
    return True


def listar_por_orientador(df):
    orientador_input = input("Digite o nome (ou parte do nome) do(a) orientador(a): ").strip().lower()
    if not orientador_input: return
    resultados = df[df['Orientador(a)'].str.lower().str.contains(orientador_input, na=False)]
    if resultados.empty: print("Nenhum orientador encontrado."); return
    print("\n--- Trabalhos Encontrados ---")
    for _, trabalho in resultados.iterrows():
        print(f"Apresentador(a): {trabalho['Apresentador(a)']}",
              f"  - Dia: {trabalho['Dia']}, Sala: {trabalho['Sala']}, Horário: {trabalho['Horário']}\n", sep="\n")


def trocar(nome_base):
    df, orientadores_por_bloco = carregar_ensalamento(nome_base)
    if df is None:
        print("Não foi possível carregar os arquivos. Execute a 'Opção 3 - Gerar Ensalamento' primeiro.")
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
            print("Opção inválida.");
            continue

        aluno_input = input("Digite o nome do(a) apresentador(a) que deseja mover: ").strip()
        if not aluno_input: continue
        trabalho_original_series = df[df['Apresentador(a)'].str.lower() == aluno_input.lower()]
        if trabalho_original_series.empty:
            print("ERRO: Apresentador(a) não encontrado(a).");
            continue
        trabalho_original = trabalho_original_series.iloc[0];
        idx_original = trabalho_original_series.index[0]
        print("\nTrabalho encontrado:", f"  - Apresentador(a): {trabalho_original['Apresentador(a)']}",
              f"  - Local Atual: Dia {trabalho_original['Dia']}, Sala {trabalho_original['Sala']}, Horário: {trabalho_original['Horário']}",
              sep='\n')

        # --- LÓGICA DE BUSCA INTELIGENTE ---
        print("\nBuscando todas as opções de movimentação válidas. Aguarde...")
        opcoes_validas = []
        df_sessao_origem = df[
            (df['Bloco_ID'] == trabalho_original['Bloco_ID']) & (df['Sala'] == trabalho_original['Sala'])]

        # 1. Busca por TROCAS válidas
        for idx_alvo, trabalho_alvo in df.iterrows():
            if idx_alvo == idx_original: continue  # Não trocar consigo mesmo

            mov_A_valido = movimento_e_valido(trabalho_original['Orientador(a)'], trabalho_alvo['Bloco_ID'],
                                              trabalho_alvo['Sala'], orientadores_por_bloco)
            mov_B_valido = movimento_e_valido(trabalho_alvo['Orientador(a)'], trabalho_original['Bloco_ID'],
                                              trabalho_original['Sala'], orientadores_por_bloco)

            if mov_A_valido and mov_B_valido:
                opcoes_validas.append({"tipo": "TROCAR", "idx_alvo": idx_alvo, "alvo": trabalho_alvo})

        # 2. Busca por MOVIMENTOS válidos para slots vagos
        if len(df_sessao_origem) - 1 >= MIN_TRABALHOS_SESSAO:
            sessoes_com_vagas = df.groupby(['Dia', 'Sessão', 'Sala', 'Bloco_ID']).filter(
                lambda x: len(x) < MAX_TRABALHOS_SESSAO)
            sessoes_unicas_com_vagas = sessoes_com_vagas[['Dia', 'Sessão', 'Sala', 'Bloco_ID']].drop_duplicates()
            for _, sessao_alvo in sessoes_unicas_com_vagas.iterrows():
                if movimento_e_valido(trabalho_original['Orientador(a)'], sessao_alvo['Bloco_ID'], sessao_alvo['Sala'],
                                      orientadores_por_bloco):
                    opcoes_validas.append({"tipo": "MOVER", "destino": sessao_alvo.to_dict()})

        if not opcoes_validas: print("\nNenhuma movimentação ou troca válida encontrada."); continue

        print("\nOpções válidas encontradas:")
        for i, opcao in enumerate(opcoes_validas):
            if opcao['tipo'] == 'MOVER':
                destino = opcao['destino']
                print(
                    f" {i + 1}. MOVER para um slot vago na Sala {destino['Sala']} ({destino['Sessão']}, Dia {destino['Dia']})")
            else:
                alvo = opcao['alvo']
                print(
                    f" {i + 1}. TROCAR com '{alvo['Apresentador(a)']}' (Sala {alvo['Sala']}, Dia {alvo['Dia']}, Horário {alvo['Horário']})")

        try:
            escolha = int(input("Escolha o número da opção desejada (ou 0 para cancelar): ").strip())
            if escolha == 0 or escolha > len(opcoes_validas): print("Operação cancelada."); continue

            opcao_escolhida = opcoes_validas[escolha - 1]

            if opcao_escolhida['tipo'] == 'MOVER':
                destino = opcao_escolhida['destino']
                df.loc[idx_original, ['Dia', 'Sessão', 'Sala', 'Bloco_ID', 'Horário']] = [destino['Dia'],
                                                                                          destino['Sessão'],
                                                                                          destino['Sala'],
                                                                                          destino['Bloco_ID'], '23:59']
                print("\nMovimentação realizada!")
            elif opcao_escolhida['tipo'] == 'TROCAR':
                idx_alvo = opcao_escolhida['idx_alvo']
                loc_original = (trabalho_original['Dia'], trabalho_original['Sessão'], trabalho_original['Horário'],
                                trabalho_original['Sala'], trabalho_original['Bloco_ID'])
                trabalho_alvo = df.loc[idx_alvo]
                loc_alvo = (trabalho_alvo['Dia'], trabalho_alvo['Sessão'], trabalho_alvo['Horário'],
                            trabalho_alvo['Sala'], trabalho_alvo['Bloco_ID'])
                df.loc[idx_original, ['Dia', 'Sessão', 'Horário', 'Sala', 'Bloco_ID']] = loc_alvo
                df.loc[idx_alvo, ['Dia', 'Sessão', 'Horário', 'Sala', 'Bloco_ID']] = loc_original
                print("\nTroca realizada!")

            if input("Deseja salvar as alterações nos arquivos CSV? (s/n): ").strip().lower() == 's':
                salvar_ensalamento(df, nome_base);
                print("Recarregando ensalamento atualizado...")
                df, orientadores_por_bloco = carregar_ensalamento(nome_base)
            else:
                print("Alterações descartadas.")
                df, orientadores_por_bloco = carregar_ensalamento(nome_base)
        except (ValueError, IndexError):
            print("ERRO: Opção inválida.")