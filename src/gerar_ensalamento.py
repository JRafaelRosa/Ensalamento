import pandas as pd
import random
import os


CONFIG = {
   "ARQUIVO_PIBIC_JR": "public/EAIC_PIBIC_Jr_2025-2026.xlsx",

   "NUM_SALAS": 4,
   "DIAS_EVENTO": 2,
   "SESSOES_POR_DIA": [
       {"nome": "Manhã 1", "horario_inicio": "08:30", "capacidade": 6, "duracao_slot_min": 15},
       {"nome": "Manhã 2", "horario_inicio": "10:00", "capacidade": 6, "duracao_slot_min": 15},
       {"nome": "Tarde", "horario_inicio": "14:00", "capacidade": 6, "duracao_slot_min": 15},
   ],
   "MAX_TRABALHOS_ORIENTADOR_SESSAO": 4,
   "MIN_TRABALHOS_SESSAO": 4,
}




def carregar_dados(caminho_arquivo):

   try:
       if caminho_arquivo.lower().endswith('.csv'):
           df = pd.read_csv(caminho_arquivo)
       elif caminho_arquivo.lower().endswith('.xlsx'):
           df = pd.read_excel(caminho_arquivo)
       else:
           print("Erro: Formato de arquivo não suportado."); return None
       df.rename(columns={'Apresentador': 'Apresentador(a)', 'Título': 'Título', 'Área': 'Área',
                          'Orientador': 'Orientador(a)'}, inplace=True, errors='ignore')
       colunas_essenciais = ['Apresentador(a)', 'Título', 'Orientador(a)']
       colunas_faltando = [col for col in colunas_essenciais if col not in df.columns]
       if colunas_faltando: print(f"\nERRO: O arquivo não contém as colunas: {colunas_faltando}"); return None
       print(f"Arquivo '{caminho_arquivo}' lido com sucesso com {len(df)} trabalhos.")
       return df
   except FileNotFoundError:
       print(f"Erro: Arquivo '{caminho_arquivo}' não foi encontrado."); return None




def _gerar_ensalamento_principal(arquivo_entrada):
   df_trabalhos = carregar_dados(arquivo_entrada)
   if df_trabalhos is None: return


   try:
       df_pibic_jr = pd.read_excel(CONFIG["ARQUIVO_PIBIC_JR"])
       coluna_nomes_pibic = 'Aluno'
       if coluna_nomes_pibic in df_pibic_jr.columns:
           nomes_pibic_jr = set(df_pibic_jr[coluna_nomes_pibic])
           len_antes = len(df_trabalhos);
           df_trabalhos = df_trabalhos[~df_trabalhos['Apresentador(a)'].isin(nomes_pibic_jr)];
           len_depois = len(df_trabalhos)
           print(
               f"Filtro: {len_antes - len_depois} trabalhos do PIBIC Jr. removidos. Total para ensalamento: {len_depois}")
       else:
           print(f"AVISO: Coluna '{coluna_nomes_pibic}' não encontrada em '{CONFIG['ARQUIVO_PIBIC_JR']}'.")
   except FileNotFoundError:
       print(f"AVISO: Arquivo de filtro '{CONFIG['ARQUIVO_PIBIC_JR']}' não encontrado.")
   except Exception as e:
       print(f"Erro ao filtrar PIBIC Jr.: {e}")


   trabalhos_para_alocar = df_trabalhos.to_dict('records')
   random.shuffle(trabalhos_para_alocar)


   nome_base = os.path.splitext(os.path.basename(arquivo_entrada))[0]
   codigo_area = nome_base[:2].upper()


   sessoes = []
   salas = [f"{codigo_area}{i + 1}" for i in range(CONFIG['NUM_SALAS'])]


   for dia in range(1, CONFIG['DIAS_EVENTO'] + 1):
       for sessao_info in CONFIG['SESSOES_POR_DIA']:
           for sala in salas:
               sessoes.append({"Dia": dia, "Nome_Sessao": sessao_info['nome'], "Sala": sala,
                               "Capacidade": sessao_info['capacidade'],
                               "Horario_Inicio": sessao_info['horario_inicio'],
                               "Duracao_Slot": sessao_info['duracao_slot_min'], "Trabalhos": []})


   print("Iniciando Fase 1: Alocação Inicial...")
   orientadores_por_sessao_bloco = {}
   for sessao in sessoes:
       if not trabalhos_para_alocar: break
       bloco_sessao_id = f"D{sessao['Dia']}-{sessao['Nome_Sessao']}"
       if bloco_sessao_id not in orientadores_por_sessao_bloco: orientadores_por_sessao_bloco[bloco_sessao_id] = {}
       while len(sessao["Trabalhos"]) < sessao["Capacidade"]:
           if not trabalhos_para_alocar: break
           melhor_candidato_idx, menor_penalidade = -1, float('inf')
           for i, candidato in enumerate(trabalhos_para_alocar):
               penalidade = 0;
               orientador_candidato = candidato['Orientador(a)'];
               conflito = False
               for sala_existente, orientadores in orientadores_por_sessao_bloco[bloco_sessao_id].items():
                   if sala_existente != sessao["Sala"] and orientador_candidato in orientadores: conflito = True; break
               if conflito: continue
               orientadores_nesta_sala = [t['Orientador(a)'] for t in sessao["Trabalhos"]];
               contagem_na_sala = orientadores_nesta_sala.count(orientador_candidato)
               if len(set(orientadores_nesta_sala + [orientador_candidato])) == 1 and len(
                   sessao["Trabalhos"]) > 1: penalidade += 200
               if contagem_na_sala >= CONFIG['MAX_TRABALHOS_ORIENTADOR_SESSAO']: penalidade += 100
               if orientadores_nesta_sala and orientadores_nesta_sala[-1] == orientador_candidato: penalidade += 50
               penalidade += contagem_na_sala * 10
               if contagem_na_sala == 0: penalidade -= 5
               if penalidade < menor_penalidade: menor_penalidade = penalidade; melhor_candidato_idx = i
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


   print("Iniciando Fase 2: Rebalanceamento Inteligente...")
   for _ in range(30):
       sessoes_muito_vazias = [s for s in sessoes if 0 < len(s["Trabalhos"]) < CONFIG["MIN_TRABALHOS_SESSAO"]]
       if not sessoes_muito_vazias: break
       sessao_alvo = min(sessoes_muito_vazias, key=lambda s: len(s["Trabalhos"]))
       movimento_feito = False
       for sessao_fonte in reversed(sessoes):
           if movimento_feito: break
           if len(sessao_fonte["Trabalhos"]) > CONFIG["MIN_TRABALHOS_SESSAO"]:
               for k in range(len(sessao_fonte["Trabalhos"]) - 1, -1, -1):
                   trabalho_movel = sessao_fonte["Trabalhos"][k];
                   orientador_movel = trabalho_movel.get('Orientador(a)', '');
                   conflito = False
                   bloco_alvo_id = f"D{sessao_alvo['Dia']}-{sessao_alvo['Nome_Sessao']}"
                   if bloco_alvo_id not in orientadores_por_sessao_bloco: orientadores_por_sessao_bloco[
                       bloco_alvo_id] = {}
                   orientadores_bloco_alvo = orientadores_por_sessao_bloco.get(bloco_alvo_id, {})
                   for sala_existente, orientadores in orientadores_bloco_alvo.items():
                       if sala_existente != sessao_alvo[
                           "Sala"] and orientador_movel in orientadores: conflito = True; break
                   if conflito: continue
                   trabalho_removido = sessao_fonte["Trabalhos"].pop(k)
                   sessao_alvo["Trabalhos"].append(trabalho_removido)
                   if sessao_alvo["Sala"] not in orientadores_bloco_alvo: orientadores_bloco_alvo[
                       sessao_alvo["Sala"]] = []
                   if orientador_movel not in orientadores_bloco_alvo[sessao_alvo["Sala"]]: orientadores_bloco_alvo[
                       sessao_alvo["Sala"]].append(orientador_movel)
                   bloco_fonte_id = f"D{sessao_fonte['Dia']}-{sessao_fonte['Nome_Sessao']}"
                   orientadores_na_fonte = [t.get('Orientador(a)', '') for t in sessao_fonte["Trabalhos"]]
                   if orientadores_na_fonte.count(orientador_movel) == 0:
                       if orientador_movel in orientadores_por_sessao_bloco[bloco_fonte_id][sessao_fonte["Sala"]]:
                           orientadores_por_sessao_bloco[bloco_fonte_id][sessao_fonte["Sala"]].remove(orientador_movel)
                   movimento_feito = True;
                   break
   else:
       print("Rebalanceamento finalizado.")


   ensalamento_final = []
   for sessao in sessoes:
       horario_atual = pd.to_datetime(sessao['Horario_Inicio'])
       sessao['Trabalhos'].sort(key=lambda x: str(x.get('Orientador(a)', '')))
       for trabalho in sessao['Trabalhos']:
           ensalamento_final.append({"Dia": sessao['Dia'], "Nome_Sessao": sessao['Nome_Sessao'],
                                     "Sessão": f"{sessao['Nome_Sessao']} ({pd.to_datetime(sessao['Horario_Inicio']).strftime('%H:%M')})",
                                     "Horário": horario_atual.strftime('%H:%M'), "Sala": sessao['Sala'],
                                     "Título": trabalho['Título'], "Apresentador(a)": trabalho['Apresentador(a)'],
                                     "Orientador(a)": trabalho['Orientador(a)']})
           horario_atual += pd.Timedelta(minutes=sessao['Duracao_Slot'])


   if not ensalamento_final: print("Nenhum trabalho foi alocado."); return
   df_final = pd.DataFrame(ensalamento_final)
   PASTA_SAIDA_CSV = "public/csv"
   if not os.path.exists(PASTA_SAIDA_CSV): os.makedirs(PASTA_SAIDA_CSV)


   for dia in range(1, CONFIG['DIAS_EVENTO'] + 1):
       df_dia = df_final[df_final['Dia'] == dia]
       if df_dia.empty and not trabalhos_para_alocar: continue
       colunas_saida = ['Sessão', 'Horário', 'Sala', 'Título', 'Apresentador(a)', 'Orientador(a)']
       df_dia_final = df_dia[colunas_saida]
       nome_arquivo_saida = os.path.join(PASTA_SAIDA_CSV, f"{nome_base}_dia{dia}.csv")
       df_dia_final.to_csv(nome_arquivo_saida, index=False, quoting=1)
       print(f"Arquivo '{nome_arquivo_saida}' gerado.")
   if trabalhos_para_alocar: print(f"\nAVISO: {len(trabalhos_para_alocar)} trabalhos não puderam ser alocados.")




def ensalamento(nome_base):
   if nome_base:
       caminho_completo = f"public/{nome_base}.xlsx"
       _gerar_ensalamento_principal(caminho_completo)
   else:
       print("Nenhum nome de arquivo fornecido.")


