import pandas as pd
import random
import os
from src.sala import obter_info_area


def carregar_dados(caminho_arquivo):
    try:
        if caminho_arquivo.lower().endswith('.csv'):
            df = pd.read_csv(caminho_arquivo)
        elif caminho_arquivo.lower().endswith('.xlsx'):
            df = pd.read_excel(caminho_arquivo)
        else:
            print("Erro: Formato de arquivo não suportado.");
            return None
        df.rename(columns={'Apresentador': 'Apresentador(a)', 'Título': 'Título', 'Área': 'Área',
                           'Orientador': 'Orientador(a)'}, inplace=True, errors='ignore')
        colunas_essenciais = ['Apresentador(a)', 'Título', 'Orientador(a)']
        if any(col not in df.columns for col in colunas_essenciais):
            print(f"ERRO: O arquivo não contém as colunas essenciais: {colunas_essenciais}");
            return None

        df.dropna(subset=colunas_essenciais, inplace=True)
        df.drop_duplicates(subset=['Apresentador(a)'], keep='first', inplace=True)
        print(f"Arquivo '{os.path.basename(caminho_arquivo)}' lido com {len(df)} trabalhos válidos.")
        return df
    except FileNotFoundError:
        print(f"Erro: Arquivo '{caminho_arquivo}' não foi encontrado.");
        return None


def _gerar_ensalamento_principal(arquivo_entrada, config_evento, config_areas_df, mapa_salas_df, horarios_sessoes_df):
    nome_base = os.path.splitext(os.path.basename(arquivo_entrada))[0]
    info_area = obter_info_area(nome_base, config_areas_df)
    if info_area is None: return
    df_trabalhos = carregar_dados(arquivo_entrada)
    if df_trabalhos is None: return

    todos_nomes_a_ignorar = set()
    regras_a_ignorar = config_evento.get("ARQUIVOS_A_IGNORAR", {})
    arquivos_filtro = regras_a_ignorar.get("GLOBAL", []) + regras_a_ignorar.get(nome_base.upper(), [])
    for arquivo_filtro in arquivos_filtro:
        try:
            df_filtro = pd.read_excel(arquivo_filtro)
            if 'Aluno' in df_filtro.columns:
                todos_nomes_a_ignorar.update(df_filtro['Aluno'].dropna().tolist())
                print(
                    f"Filtro: Carregados {len(df_filtro['Aluno'].dropna())} nomes do arquivo '{os.path.basename(arquivo_filtro)}'.")
        except Exception:
            pass

    if todos_nomes_a_ignorar:
        len_antes = len(df_trabalhos)
        df_trabalhos = df_trabalhos[~df_trabalhos['Apresentador(a)'].isin(todos_nomes_a_ignorar)]
        print(f"Filtro Total: {len_antes - len(df_trabalhos)} trabalhos foram removidos.")

    total_de_trabalhos_para_alocar = len(df_trabalhos)
    print(f"Total de trabalhos para ensalamento: {total_de_trabalhos_para_alocar}")
    trabalhos_para_alocar = df_trabalhos.to_dict('records')
    random.shuffle(trabalhos_para_alocar)

    for trab in trabalhos_para_alocar:
        trab['motivo_falha'] = "Sem vagas compatíveis ou concorrência alta"

    sessoes = []
    salas_logicas_area = [f"{info_area['codigo_area']}{i + 1}" for i in range(info_area['num_salas'])]
    mapa_salas_area = mapa_salas_df[mapa_salas_df.index.isin(salas_logicas_area)]
    salas_fisicas_area = mapa_salas_area['nome_fisico'].tolist()
    horarios_sessoes_area = horarios_sessoes_df[horarios_sessoes_df['sala_fisica'].isin(salas_fisicas_area)]

    for _, sessao_info_row in horarios_sessoes_area.iterrows():
        codigo_logico_sala = mapa_salas_area[mapa_salas_area['nome_fisico'] == sessao_info_row['sala_fisica']].index[0]
        sessoes.append({
            "id": len(sessoes), "Dia": sessao_info_row['dia'], "Nome_Sessao": sessao_info_row['nome_sessao'],
            "Sala": codigo_logico_sala, "Capacidade": sessao_info_row['capacidade'],
            "Horario_Inicio": sessao_info_row['horario_inicio'], "Duracao_Slot": 15, "Trabalhos": []
        })

    if not sessoes:
        print("\n!!! ERRO CRÍTICO: Nenhuma sessão foi criada. Verifique a correspondência de nomes de salas. !!!\n")
        print("Nenhum trabalho foi alocado.");
        return

    print("Iniciando Fase 1: Alocação Inicial com sistema de penalidades...")
    orientadores_por_sessao_bloco = {}
    for sessao in sessoes:
        if not trabalhos_para_alocar: break
        bloco_sessao_id = f"D{sessao['Dia']}-{sessao['Nome_Sessao']}"
        if bloco_sessao_id not in orientadores_por_sessao_bloco: orientadores_por_sessao_bloco[bloco_sessao_id] = {}

        while len(sessao["Trabalhos"]) < sessao["Capacidade"]:
            if not trabalhos_para_alocar: break
            melhor_candidato_idx, menor_penalidade = -1, float('inf')

            for i, candidato in enumerate(trabalhos_para_alocar):
                penalidade = 0
                orientador_candidato = candidato['Orientador(a)']

                conflito = any(orientador_candidato in orientadores for sala, orientadores in
                               orientadores_por_sessao_bloco[bloco_sessao_id].items() if sala != sessao["Sala"])
                if conflito:
                    candidato['motivo_falha'] = "Conflito de orientador"
                    continue

                orientadores_nesta_sala = [t['Orientador(a)'] for t in sessao["Trabalhos"]]
                contagem_na_sala = orientadores_nesta_sala.count(orientador_candidato)

                if len(set(orientadores_nesta_sala + [orientador_candidato])) == 1 and len(
                    sessao["Trabalhos"]) > 1: penalidade += 200
                if contagem_na_sala >= config_evento['MAX_TRABALHOS_ORIENTADOR_SESSAO']: penalidade += 100
                if orientadores_nesta_sala and orientadores_nesta_sala[-1] == orientador_candidato: penalidade += 50
                penalidade += contagem_na_sala * 10
                if contagem_na_sala == 0: penalidade -= 5

                if penalidade < menor_penalidade:
                    menor_penalidade = penalidade
                    melhor_candidato_idx = i

            if melhor_candidato_idx != -1:
                trabalho_escolhido = trabalhos_para_alocar.pop(melhor_candidato_idx)
                sessao["Trabalhos"].append(trabalho_escolhido)
                if sessao["Sala"] not in orientadores_por_sessao_bloco[bloco_sessao_id]:
                    orientadores_por_sessao_bloco[bloco_sessao_id][sessao["Sala"]] = []
                if trabalho_escolhido['Orientador(a)'] not in orientadores_por_sessao_bloco[bloco_sessao_id][
                    sessao["Sala"]]:
                    orientadores_por_sessao_bloco[bloco_sessao_id][sessao["Sala"]].append(
                        trabalho_escolhido['Orientador(a)'])
            else:
                break

    print("Iniciando Fase 2: Rebalanceamento Inteligente...");
    for _ in range(30):
        sessoes_muito_vazias = [s for s in sessoes if 0 < len(s["Trabalhos"]) < config_evento["MIN_TRABALHOS_SESSAO"]]
        if not sessoes_muito_vazias: break
        sessao_alvo = min(sessoes_muito_vazias, key=lambda s: len(s["Trabalhos"]))
        movimento_feito = False

        for sessao_fonte in reversed(sessoes):
            if movimento_feito: break
            if len(sessao_fonte["Trabalhos"]) > config_evento["MIN_TRABALHOS_SESSAO"]:
                for k in range(len(sessao_fonte["Trabalhos"]) - 1, -1, -1):
                    trabalho_movel = sessao_fonte["Trabalhos"][k]
                    orientador_movel = trabalho_movel.get('Orientador(a)', '')

                    bloco_alvo_id = f"D{sessao_alvo['Dia']}-{sessao_alvo['Nome_Sessao']}"
                    conflito = any(orientador_movel in orientadores for sala, orientadores in
                                   orientadores_por_sessao_bloco.get(bloco_alvo_id, {}).items() if
                                   sala != sessao_alvo["Sala"])

                    if conflito: continue

                    trabalho_removido = sessao_fonte["Trabalhos"].pop(k)
                    sessao_alvo["Trabalhos"].append(trabalho_removido)

                    bloco_fonte_id = f"D{sessao_fonte['Dia']}-{sessao_fonte['Nome_Sessao']}"
                    orientadores_na_fonte_agora = [t.get('Orientador(a)') for t in sessao_fonte["Trabalhos"]]
                    if orientadores_na_fonte_agora.count(orientador_movel) == 0:
                        if orientador_movel in orientadores_por_sessao_bloco[bloco_fonte_id][sessao_fonte["Sala"]]:
                            orientadores_por_sessao_bloco[bloco_fonte_id][sessao_fonte["Sala"]].remove(orientador_movel)

                    if sessao_alvo["Sala"] not in orientadores_por_sessao_bloco.get(bloco_alvo_id, {}):
                        orientadores_por_sessao_bloco[bloco_alvo_id][sessao_alvo["Sala"]] = []

                    if orientador_movel not in orientadores_por_sessao_bloco[bloco_alvo_id][sessao_alvo["Sala"]]:
                        orientadores_por_sessao_bloco[bloco_alvo_id][sessao_alvo["Sala"]].append(orientador_movel)

                    movimento_feito = True
                    break
    print("Rebalanceamento finalizado.")

    print("Iniciando Fase 3: Consolidação de Sessões Pequenas...");
    tentativas = 0
    while tentativas < 5:
        sessoes_muito_vazias = sorted(
            [s for s in sessoes if 0 < len(s["Trabalhos"]) < config_evento["MIN_TRABALHOS_SESSAO"]],
            key=lambda s: len(s["Trabalhos"]))
        if not sessoes_muito_vazias:
            print("Consolidação concluída.")
            break

        sessao_a_esvaziar = sessoes_muito_vazias[0]
        trabalhos_para_mover = list(sessao_a_esvaziar["Trabalhos"])

        trabalhos_movidos_na_rodada = 0
        for trabalho_a_mover in trabalhos_para_mover:
            movido = False
            for sessao_destino in sessoes:
                if sessao_destino['id'] == sessao_a_esvaziar['id'] or len(sessao_destino['Trabalhos']) >= \
                        sessao_destino['Capacidade']:
                    continue

                orientador_a_mover = trabalho_a_mover['Orientador(a)']
                bloco_destino_id = f"D{sessao_destino['Dia']}-{sessao_destino['Nome_Sessao']}"
                conflito = any(orientador_a_mover in orientadores for sala, orientadores in
                               orientadores_por_sessao_bloco.get(bloco_destino_id, {}).items() if
                               sala != sessao_destino["Sala"])

                if not conflito:
                    sessao_a_esvaziar['Trabalhos'].remove(trabalho_a_mover)
                    sessao_destino['Trabalhos'].append(trabalho_a_mover)

                    bloco_origem_id = f"D{sessao_a_esvaziar['Dia']}-{sessao_a_esvaziar['Nome_Sessao']}"
                    orientadores_por_sessao_bloco[bloco_origem_id][sessao_a_esvaziar['Sala']].remove(orientador_a_mover)

                    if sessao_destino['Sala'] not in orientadores_por_sessao_bloco.get(bloco_destino_id, {}):
                        orientadores_por_sessao_bloco[bloco_destino_id][sessao_destino['Sala']] = []

                    orientadores_por_sessao_bloco[bloco_destino_id][sessao_destino['Sala']].append(orientador_a_mover)

                    trabalhos_movidos_na_rodada += 1
                    movido = True
                    break
            if movido:
                print(
                    f"Trabalho '{trabalho_a_mover['Apresentador(a)']}' consolidado da sessão {sessao_a_esvaziar['id']} para {sessao_destino['id']}.")

        if trabalhos_movidos_na_rodada == 0:
            print(
                f"AVISO: Não foi possível mover trabalhos da sessão {sessao_a_esvaziar['id']}. Pode haver um impasse.")
            tentativas += 1

    print("Iniciando Fase 4: Repescagem de trabalhos não alocados...")
    if trabalhos_para_alocar:
        for trabalho_nao_alocado in list(trabalhos_para_alocar):
            orientador = trabalho_nao_alocado['Orientador(a)']
            melhor_sessao = None

            sessoes_candidatas = sorted(sessoes, key=lambda s: len(s['Trabalhos']))

            for sessao in sessoes_candidatas:
                if len(sessao['Trabalhos']) < sessao['Capacidade']:
                    orientadores_na_sessao = [t['Orientador(a)'] for t in sessao['Trabalhos']]
                    if orientador in orientadores_na_sessao and orientadores_na_sessao.count(orientador) < \
                            config_evento['MAX_TRABALHOS_ORIENTADOR_SESSAO']:
                        melhor_sessao = sessao
                        break

            if not melhor_sessao:
                for sessao in sessoes_candidatas:
                    if len(sessao['Trabalhos']) < sessao['Capacidade']:
                        bloco_sessao_id = f"D{sessao['Dia']}-{sessao['Nome_Sessao']}"
                        conflito = any(orientador in orientadores for sala, orientadores in
                                       orientadores_por_sessao_bloco.get(bloco_sessao_id, {}).items() if
                                       sala != sessao["Sala"])
                        if not conflito:
                            melhor_sessao = sessao
                            break
                        else:
                            trabalho_nao_alocado['motivo_falha'] = "Conflito de orientador (Repescagem)"

            if melhor_sessao:
                print(
                    f"Repescagem: Alocando '{trabalho_nao_alocado['Apresentador(a)']}' na sessão {melhor_sessao['id']}")
                melhor_sessao['Trabalhos'].append(trabalho_nao_alocado)
                trabalhos_para_alocar.remove(trabalho_nao_alocado)

                bloco_sessao_id = f"D{melhor_sessao['Dia']}-{melhor_sessao['Nome_Sessao']}"
                if melhor_sessao['Sala'] not in orientadores_por_sessao_bloco.get(bloco_sessao_id, {}):
                    orientadores_por_sessao_bloco[bloco_sessao_id][melhor_sessao['Sala']] = []
                if orientador not in orientadores_por_sessao_bloco[bloco_sessao_id][melhor_sessao['Sala']]:
                    orientadores_por_sessao_bloco[bloco_sessao_id][melhor_sessao['Sala']].append(orientador)

    ensalamento_final = []
    for sessao in sessoes:
        if not sessao['Trabalhos']: continue
        horario_atual = pd.to_datetime(sessao['Horario_Inicio'])
        sessao['Trabalhos'].sort(key=lambda x: str(x.get('Orientador(a)', '')))
        for trabalho in sessao['Trabalhos']:
            ensalamento_final.append({
                "Dia": sessao['Dia'], "Nome_Sessao": sessao['Nome_Sessao'],
                "Sessão": f"{sessao['Nome_Sessao']} ({pd.to_datetime(sessao['Horario_Inicio']).strftime('%H:%M')})",
                "Horário": horario_atual.strftime('%H:%M'), "Sala": sessao['Sala'],
                "Título": trabalho['Título'], "Apresentador(a)": trabalho['Apresentador(a)'],
                "Orientador(a)": trabalho['Orientador(a)']
            })
            horario_atual += pd.Timedelta(minutes=sessao['Duracao_Slot'])

    if not ensalamento_final and trabalhos_para_alocar: print("Nenhum trabalho foi alocado."); return
    df_final = pd.DataFrame(ensalamento_final)
    PASTA_SAIDA_CSV = "public/csv"
    if not os.path.exists(PASTA_SAIDA_CSV): os.makedirs(PASTA_SAIDA_CSV)

    for dia in range(1, config_evento['DIAS_EVENTO'] + 1):
        df_dia = df_final[df_final['Dia'] == dia]
        if df_dia.empty and not trabalhos_para_alocar: continue
        df_dia_final = df_dia[['Sessão', 'Horário', 'Sala', 'Título', 'Apresentador(a)', 'Orientador(a)']]
        nome_arquivo_saida = os.path.join(PASTA_SAIDA_CSV, f"{nome_base}_dia{dia}.csv")
        df_dia_final.to_csv(nome_arquivo_saida, index=False, quoting=1)
        print(f"Arquivo '{nome_arquivo_saida}' gerado.")

    print("\n" + "=" * 40 + "\n" + " RELATÓRIO FINAL DE ALOCAÇÃO ".center(40, "=") + "\n" + "=" * 40)
    total_alocados = len(ensalamento_final)
    total_nao_alocados = len(trabalhos_para_alocar)
    print(f"Total de trabalhos para ensalamento: {total_de_trabalhos_para_alocar}")
    print(f"Trabalhos alocados com sucesso:    {total_alocados}")
    print(f"Trabalhos NÃO alocados:            {total_nao_alocados}")
    if total_nao_alocados > 0:
        print("\n" + "-" * 40 + "\n" + " LISTA DE TRABALHOS NÃO ALOCADOS ".center(40, "-") + "\n" + "-" * 40)
        for i, trab in enumerate(trabalhos_para_alocar):
            print(f"{i + 1}. Apresentador(a): {trab.get('Apresentador(a)', 'N/A')}")
            print(f"   Orientador(a):  {trab.get('Orientador(a)', 'N/A')}")
            print(f"   Motivo:         {trab.get('motivo_falha', 'Desconhecido')}")
    print("=" * 40)


def ensalamento(nome_base, config_evento, config_areas_df, mapa_salas_df, horarios_sessoes_df):
    if nome_base:
        try:
            caminho_completo = config_areas_df.loc[nome_base.upper()]['caminho_arquivo_base']
            if not os.path.exists(caminho_completo):
                print(f"ERRO: O arquivo base '{caminho_completo}' não foi encontrado.")
                return
        except KeyError:
            print(f"ERRO: Área '{nome_base}' não encontrada. Não foi possível achar o arquivo base.")
            return

        _gerar_ensalamento_principal(caminho_completo, config_evento, config_areas_df, mapa_salas_df,
                                     horarios_sessoes_df)
    else:
        print("Nenhum nome de arquivo fornecido.")