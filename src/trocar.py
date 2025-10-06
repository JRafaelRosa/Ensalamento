import pandas as pd
import os

MIN_TRABALHOS_SESSAO = 4
MAX_TRABALHOS_SESSAO = 6


def carregar_ensalamento(nome_base):
    """Carrega os CSVs do dia 1 e 2 em um único DataFrame."""
    dfs = []
    for dia in [1, 2]:
        # Usa o novo padrão de nome de arquivo que você definiu
        caminho = f"public/csv/{nome_base}_dia{dia}.csv"
        try:
            df_dia = pd.read_csv(caminho)
            df_dia['Dia'] = dia
            dfs.append(df_dia)
        except FileNotFoundError:
            pass  # Silenciosamente ignora se o arquivo de um dos dias não existir
    if not dfs:
        return None, None

    df_completo = pd.concat(dfs, ignore_index=True)

    # Cria o dicionário de controle de orientadores por bloco (forma mais segura)
    df_completo['Bloco_ID'] = "D" + df_completo['Dia'].astype(str) + "-" + df_completo['Sessão'].str.split(' \(').str[0]

    orientadores_por_bloco = {}
    for bloco in df_completo['Bloco_ID'].unique():
        orientadores_por_bloco[bloco] = df_completo[df_completo['Bloco_ID'] == bloco].groupby('Sala')[
            'Orientador(a)'].unique().apply(list).to_dict()

    return df_completo, orientadores_por_bloco


def salvar_ensalamento(df, nome_base):
    """Salva o DataFrame modificado de volta nos arquivos CSV."""
    PASTA_SAIDA_CSV = "public/csv"
    for dia in [1, 2]:
        colunas_para_salvar = ['Sessão', 'Horário', 'Sala', 'Título', 'Apresentador(a)', 'Orientador(a)']
        df_dia = df[df['Dia'] == dia][colunas_para_salvar]

        # Recalcula os horários para fechar buracos
        df_dia_corrigido = pd.DataFrame()
        sessoes_unicas = df_dia[['Sessão', 'Sala']].drop_duplicates()
        for _, sessao_info in sessoes_unicas.iterrows():
            df_sessao_atual = df_dia[
                (df_dia['Sessão'] == sessao_info['Sessão']) & (df_dia['Sala'] == sessao_info['Sala'])].copy()
            horario_inicio_str = sessao_info['Sessão'].split('(')[1].replace(')', '')
            horario_atual = pd.to_datetime(horario_inicio_str)
            novos_horarios = []
            for _ in range(len(df_sessao_atual)):
                novos_horarios.append(horario_atual.strftime('%H:%M'))
                horario_atual += pd.Timedelta(minutes=15)
            df_sessao_atual['Horário'] = novos_horarios
            df_dia_corrigido = pd.concat([df_dia_corrigido, df_sessao_atual])

        if not df_dia_corrigido.empty:
            # Usa o novo padrão de nome de arquivo
            nome_arquivo = os.path.join(PASTA_SAIDA_CSV, f"{nome_base}_dia{dia}.csv")
            df_dia_corrigido.to_csv(nome_arquivo, index=False, quoting=1)
            print(f"Arquivo '{nome_arquivo}' salvo com sucesso!")


def movimento_e_valido(orientador, bloco_alvo, sala_alvo, orientadores_por_bloco):
    """Verifica se um orientador pode ser alocado em uma determinada sessão/sala."""
    orientadores_no_bloco = orientadores_por_bloco.get(bloco_alvo, {})
    for sala, orientadores in orientadores_no_bloco.items():
        if sala != sala_alvo and orientador in orientadores:
            return False
    return True


def listar_por_orientador(df):
    """Filtra e exibe os trabalhos de um orientador específico."""
    orientador_input = input("Digite o nome (ou parte do nome) do(a) orientador(a): ").strip().lower()
    if not orientador_input: return

    resultados = df[df['Orientador(a)'].str.lower().str.contains(orientador_input, na=False)]
    if resultados.empty:
        print("Nenhum orientador encontrado com esse nome.")
        return

    print("\n--- Trabalhos Encontrados ---")
    for _, trabalho in resultados.iterrows():
        print(f"Apresentador(a): {trabalho['Apresentador(a)']}")
        print(f"  - Orientador(a): {trabalho['Orientador(a)']}")
        print(f"  - Dia: {trabalho['Dia']}, Sala: {trabalho['Sala']}, Horário: {trabalho['Horário']}\n")


# --- FUNÇÃO RENOMEADA PARA 'trocar' ---
def trocar(nome_base):
    """Função principal interativa para ajustes manuais."""
    df, orientadores_por_bloco = carregar_ensalamento(nome_base)
    if df is None:
        print("Não foi possível carregar os arquivos de ensalamento. Execute a opção 'Gerar Ensalamento' primeiro.")
        return

    while True:
        print("\n--- Ferramenta de Ajuste Manual ---")
        print("1. Mover um(a) apresentador(a)")
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

        trabalho_original = trabalho_original_series.iloc[0]
        idx_original = trabalho_original_series.index[0]

        print("\nTrabalho encontrado:",
              f"  - Dia: {trabalho_original['Dia']}, Sala: {trabalho_original['Sala']}, Horário: {trabalho_original['Horário']}",
              sep='\n')

        dia_alvo = input("Digite o DIA de destino (1 ou 2): ").strip()
        sessao_alvo_input = input(
            "Digite a SESSÃO ('Manhã 1', 'Manhã 2', 'Tarde') ou PERÍODO ('manhã', 'tarde'): ").strip().lower()
        sala_alvo = input(f"Digite a SALA de destino (ex: E1, E2...): ").strip().upper()

        if dia_alvo not in ['1', '2']: print("ERRO: Dia inválido."); continue
        dia_alvo = int(dia_alvo)

        sessoes_a_procurar = []
        if sessao_alvo_input == 'manhã':
            sessoes_a_procurar = ['Manhã 1', 'Manhã 2']
        elif sessao_alvo_input == 'tarde':
            sessoes_a_procurar = ['Tarde']
        elif sessao_alvo_input in ['manhã 1', 'manha 1']:
            sessoes_a_procurar = ['Manhã 1']
        elif sessao_alvo_input in ['manhã 2', 'manha 2']:
            sessoes_a_procurar = ['Manhã 2']
        else:
            sessoes_a_procurar = [sessao_alvo_input.title()]

        opcoes_validas = []
        df_sessao_origem = df[
            (df['Bloco_ID'] == trabalho_original['Bloco_ID']) & (df['Sala'] == trabalho_original['Sala'])]

        for sessao_alvo_nome in sessoes_a_procurar:
            df_sessao_alvo = df[
                (df['Dia'] == dia_alvo) & (df['Sessão'].str.contains(sessao_alvo_nome)) & (df['Sala'] == sala_alvo)]
            bloco_alvo_id = f"D{dia_alvo}-{sessao_alvo_nome}"

            if len(df_sessao_alvo) < MAX_TRABALHOS_SESSAO and len(df_sessao_origem) - 1 >= MIN_TRABALHOS_SESSAO:
                if movimento_e_valido(trabalho_original['Orientador(a)'], bloco_alvo_id, sala_alvo,
                                      orientadores_por_bloco):
                    opcoes_validas.append({"tipo": "MOVER", "dia_alvo": dia_alvo, "sessao_alvo_nome": sessao_alvo_nome,
                                           "sala_alvo": sala_alvo, "bloco_alvo_id": bloco_alvo_id})

            for idx_alvo, trabalho_alvo in df_sessao_alvo.iterrows():
                mov_A_valido = movimento_e_valido(trabalho_original['Orientador(a)'], bloco_alvo_id, sala_alvo,
                                                  orientadores_por_bloco)
                mov_B_valido = movimento_e_valido(trabalho_alvo['Orientador(a)'], trabalho_original['Bloco_ID'],
                                                  trabalho_original['Sala'], orientadores_por_bloco)
                if mov_A_valido and mov_B_valido:
                    opcoes_validas.append({"tipo": "TROCAR", "idx_alvo": idx_alvo, "alvo": trabalho_alvo})

        if not opcoes_validas: print("\nNenhuma movimentação ou troca válida encontrada para este destino."); continue

        print("\nOpções válidas encontradas:")
        for i, opcao in enumerate(opcoes_validas):
            if opcao['tipo'] == 'MOVER':
                print(
                    f" {i + 1}. MOVER para um slot vago na Sala {opcao['sala_alvo']} ({opcao['sessao_alvo_nome']}, Dia {opcao['dia_alvo']})")
            else:
                alvo = opcao['alvo'];
                print(
                    f" {i + 1}. TROCAR com '{alvo['Apresentador(a)']}' (Sala {alvo['Sala']}, Horário {alvo['Horário']})")

        try:
            escolha = int(input("Escolha o número da opção desejada (ou 0 para cancelar): ").strip())
            if escolha == 0 or escolha > len(opcoes_validas): print("Operação cancelada."); continue

            opcao_escolhida = opcoes_validas[escolha - 1]

            if opcao_escolhida['tipo'] == 'MOVER':
                # Remove o trabalho da sua posição original
                trabalho_movido = df.loc[idx_original].to_dict()
                df.drop(idx_original, inplace=True)

                # Adiciona o trabalho à nova sessão (sem horário definido ainda)
                trabalho_movido['Dia'] = opcao_escolhida['dia_alvo']
                trabalho_movido['Sala'] = opcao_escolhida['sala_alvo']
                trabalho_movido['Bloco_ID'] = opcao_escolhida['bloco_alvo_id']
                sessao_alvo_completa = df[(df['Dia'] == opcao_escolhida['dia_alvo']) & df['Sessão'].str.contains(
                    opcao_escolhida['sessao_alvo_nome'])]['Sessão'].iloc[0]
                trabalho_movido['Sessão'] = sessao_alvo_completa

                df = pd.concat([df, pd.DataFrame([trabalho_movido])], ignore_index=True)
                print("\nMovimentação realizada com sucesso no sistema! Os horários serão recalculados ao salvar.")

            elif opcao_escolhida['tipo'] == 'TROCAR':
                idx_alvo = opcao_escolhida['idx_alvo']
                loc_original = (trabalho_original['Dia'], trabalho_original['Sessão'], trabalho_original['Horário'],
                                trabalho_original['Sala'], trabalho_original['Bloco_ID'])
                trabalho_alvo = df.loc[idx_alvo]
                loc_alvo = (trabalho_alvo['Dia'], trabalho_alvo['Sessão'], trabalho_alvo['Horário'],
                            trabalho_alvo['Sala'], trabalho_alvo['Bloco_ID'])
                df.loc[idx_original, ['Dia', 'Sessão', 'Horário', 'Sala', 'Bloco_ID']] = loc_alvo
                df.loc[idx_alvo, ['Dia', 'Sessão', 'Horário', 'Sala', 'Bloco_ID']] = loc_original
                print("\nTroca realizada com sucesso no sistema!")

            confirmar_salvar = input("Deseja salvar as alterações nos arquivos CSV? (s/n): ").strip().lower()
            if confirmar_salvar == 's':
                salvar_ensalamento(df, nome_base)
                print("Recarregando ensalamento atualizado...")
                df, orientadores_por_bloco = carregar_ensalamento(nome_base)
            else:
                print("Alterações descartadas.")
                df, orientadores_por_bloco = carregar_ensalamento(nome_base)
        except (ValueError, IndexError):
            print("ERRO: Opção inválida.")