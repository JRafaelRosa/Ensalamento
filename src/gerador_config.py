import pandas as pd
import os
import json

PASTA_CONFIG = "../public/config"
ARQUIVO_AREAS = os.path.join(PASTA_CONFIG, "config_areas.csv")
ARQUIVO_MAPA = os.path.join(PASTA_CONFIG, "mapa_salas.csv")
ARQUIVO_HORARIOS = os.path.join(PASTA_CONFIG, "horarios_sessoes.csv")
ARQUIVO_EVENTO = os.path.join(PASTA_CONFIG, "config_evento.json")


def criar_configs_interativo():
    """
    Guia o usuário para criar todos os arquivos de configuração do sistema.
    """
    print("--- Assistente de Criação de Novas Configurações ---")

    # (Passo 1, 2 e 3 para coletar áreas, salas e horários continuam os mesmos)
    print("\n--- PASSO 1: Definindo as Áreas do Evento ---")
    lista_de_areas = []
    i = 1
    while True:
        print(f"\n--- Configurando Área {i} ---")
        nome_base = input(f"Digite o nome base da área (ex: EXATAS): ").upper()
        if not nome_base: print("O nome base não pode ser vazio."); continue
        nome_completo = input(f"Digite o nome completo da área (para o título do PDF): ")
        codigo_area = input(f"Digite a sigla para '{nome_base}' (2 ou 3 letras, ex: EX, SOC): ").upper()
        try:
            num_salas = int(input(f"Quantas salas a área '{nome_base}' terá?: "))
        except ValueError:
            print("Número inválido. Assumindo 4.");
            num_salas = 4
        lista_de_areas.append({"nome_base": nome_base, "codigo_area": codigo_area, "num_salas": num_salas,
                               "nome_completo": nome_completo})
        i += 1
        if input("\nDeseja adicionar outra área? (s/n): ").lower() != 's': break
    df_areas = pd.DataFrame(lista_de_areas)
    print("\n[OK] Informações das áreas coletadas.")

    print("\n--- PASSO 2: Mapeando as Salas Físicas ---")
    lista_mapa_salas = [];
    salas_fisicas_usadas = set()
    for area in lista_de_areas:
        nome_base, codigo_area, num_salas = area['nome_base'], area['codigo_area'], area['num_salas']
        print(f"\n--- Mapeando salas para a área: {nome_base} ---")
        for i in range(num_salas):
            codigo_logico = f"{codigo_area}{i + 1}"
            while True:
                nome_fisico = input(f"Digite o nome da sala física para a SESSÃO '{codigo_logico}': ")
                if nome_fisico in salas_fisicas_usadas:
                    print(f"AVISO: A sala '{nome_fisico}' já foi usada.")
                    if input("Deseja usar mesmo assim? (s/n): ").lower() == 's': break
                else:
                    break
            salas_fisicas_usadas.add(nome_fisico)
            lista_mapa_salas.append({"codigo_logico": codigo_logico, "nome_fisico": nome_fisico})
    df_mapa = pd.DataFrame(lista_mapa_salas)
    print("\n[OK] Mapeamento das salas coletado.")

    print("\n--- PASSO 3: Definindo os Blocos de Horário Padrão ---")
    lista_sessoes_padrao = []
    try:
        num_sessoes_dia = int(input("Quantos blocos de sessão um dia terá? (ex: 3): "))
    except ValueError:
        print("Número inválido. Assumindo 3."); num_sessoes_dia = 3
    for i in range(num_sessoes_dia):
        print(f"\n--- Configurando Bloco {i + 1}/{num_sessoes_dia} ---")
        nome_sessao = input("Nome do bloco (ex: Manhã 1): ")
        horario_inicio = input("Horário de início (ex: 08:30): ")
        try:
            capacidade = int(input("Capacidade de trabalhos (ex: 6): "))
        except ValueError:
            print("Capacidade inválida. Assumindo 6."); capacidade = 6
        lista_sessoes_padrao.append(
            {"nome_sessao": nome_sessao, "horario_inicio": horario_inicio, "capacidade": capacidade})
    try:
        num_dias = int(input("\nO evento terá quantos dias de apresentação? (ex: 2): "))
    except ValueError:
        print("Número inválido. Assumindo 2."); num_dias = 2
    lista_horarios_sessoes = []
    for dia in range(1, num_dias + 1):
        for sala_fisica in sorted(list(salas_fisicas_usadas)):
            for sessao_padrao in lista_sessoes_padrao:
                lista_horarios_sessoes.append(
                    {"dia": dia, "sala_fisica": sala_fisica, "nome_sessao": sessao_padrao['nome_sessao'],
                     "horario_inicio": sessao_padrao['horario_inicio'], "capacidade": sessao_padrao['capacidade']})
    df_horarios = pd.DataFrame(lista_horarios_sessoes)
    print("\n[OK] Estrutura de horários gerada.")

    # --- PASSO 4: Configurações Gerais com Filtros Flexíveis ---
    print("\n--- PASSO 4: Definindo as Regras Gerais do Evento ---")
    regras_a_ignorar = {"GLOBAL": []}
    for area in lista_de_areas:
        regras_a_ignorar[area["nome_base"]] = []

    while True:
        if input("Deseja adicionar uma regra para ignorar arquivos de alunos? (s/n): ").lower() == 's':
            tipo_regra = input("  A regra é GLOBAL (g) ou para uma ÁREA específica (a)?: ").lower()
            nome_arquivo = input(
                "    Digite o nome do arquivo (ex: PIBIC_Jr.xlsx), que deve estar na pasta 'public/': ")
            caminho_arquivo = f"public/{nome_arquivo}"

            if tipo_regra == 'g':
                regras_a_ignorar["GLOBAL"].append(caminho_arquivo)
                print("Regra GLOBAL adicionada.")
            elif tipo_regra == 'a':
                area_especifica = input(
                    f"    Para qual área é esta regra? ({', '.join([a['nome_base'] for a in lista_de_areas])}): ").upper()
                if area_especifica in regras_a_ignorar:
                    regras_a_ignorar[area_especifica].append(caminho_arquivo)
                    print(f"Regra para '{area_especifica}' adicionada.")
                else:
                    print("Área inválida. Regra não adicionada.")
        else:
            break

    try:
        max_trab_orientador = int(input("Máximo de trabalhos de um orientador por sessão? (padrão: 4): "))
    except ValueError:
        max_trab_orientador = 4
    try:
        min_trab_sessao = int(input("Mínimo de trabalhos por sessão? (padrão: 4): "))
    except ValueError:
        min_trab_sessao = 4
    config_evento = {"ARQUIVOS_A_IGNORAR": regras_a_ignorar, "DIAS_EVENTO": num_dias,
                     "MAX_TRABALHOS_ORIENTADOR_SESSAO": max_trab_orientador, "MIN_TRABALHOS_SESSAO": min_trab_sessao}
    print("\n[OK] Regras gerais do evento coletadas.")

    # --- PASSO 5: Salvar Arquivos ---
    try:
        print(f"\n--- PASSO 5: Salvando arquivos de configuração em '{PASTA_CONFIG}'... ---")
        if not os.path.exists(PASTA_CONFIG):
            os.makedirs(PASTA_CONFIG);
            print(f"Pasta '{PASTA_CONFIG}' criada.")
        with open(ARQUIVO_EVENTO, 'w', encoding='utf-8') as f:
            json.dump(config_evento, f, indent=4)
        print(f"- '{ARQUIVO_EVENTO}' salvo.")
        df_areas.to_csv(ARQUIVO_AREAS, index=False);
        print(f"- '{ARQUIVO_AREAS}' salvo.")
        df_mapa.to_csv(ARQUIVO_MAPA, index=False);
        print(f"- '{ARQUIVO_MAPA}' salvo.")
        df_horarios.to_csv(ARQUIVO_HORARIOS, index=False);
        print(f"- '{ARQUIVO_HORARIOS}' salvo.")
        print("\nConfiguração concluída!")
    except Exception as e:
        print(f"\nOcorreu um erro ao salvar os arquivos: {e}")


def atualizar_configs_interativo():
    """Permite ao usuário carregar e modificar os arquivos de configuração existentes."""
    print("--- Ferramenta de Atualização de Configurações ---")
    while True:
        print("\nQual arquivo você deseja atualizar?")
        print("1. Mapeamento de Salas Físicas (mapa_salas.csv)")
        print("2. Horários e Sessões (horarios_sessoes.csv)")
        print("3. Regras Gerais do Evento (config_evento.json)")
        print("0. Voltar ao menu principal")
        resp = input("Escolha uma opção: ").strip()

        if resp == '0':
            break

        elif resp == '1':
            # ... (código da opção 1 sem alterações)
            try:
                df_mapa = pd.read_csv(ARQUIVO_MAPA);
                print("\n--- Mapeamento Atual ---");
                print(df_mapa.to_string())
                codigo_logico = input("\nDigite o 'codigo_logico' da sala a alterar: ").upper()
                if codigo_logico in df_mapa['codigo_logico'].values:
                    novo_nome = input(f"Digite o novo nome físico para '{codigo_logico}': ")
                    df_mapa.loc[df_mapa['codigo_logico'] == codigo_logico, 'nome_fisico'] = novo_nome
                    df_mapa.to_csv(ARQUIVO_MAPA, index=False);
                    print("Alteração salva!")
                else:
                    print("Código lógico não encontrado.")
            except FileNotFoundError:
                print(f"ERRO: Arquivo '{ARQUIVO_MAPA}' não encontrado.")
            except Exception as e:
                print(f"Ocorreu um erro: {e}")

        elif resp == '2':
            # ... (código da opção 2 sem alterações)
            try:
                df_horarios = pd.read_csv(ARQUIVO_HORARIOS);
                print("\n--- Horários Atuais ---");
                print(df_horarios.to_string())
                try:
                    idx = int(input("\nDigite o índice da linha a alterar (ou -1 para cancelar): "))
                    if idx == -1 or idx not in df_horarios.index: print("Cancelado."); continue
                    print("\nO que alterar?");
                    print("1. Horário de Início");
                    print("2. Capacidade");
                    print("3. Excluir")
                    edit_resp = input("Escolha: ").strip()
                    if edit_resp == '1':
                        df_horarios.loc[idx, 'horario_inicio'] = input("Novo horário (ex: 14:15): ")
                    elif edit_resp == '2':
                        df_horarios.loc[idx, 'capacidade'] = int(input("Nova capacidade (ex: 5): "))
                    elif edit_resp == '3':
                        df_horarios.drop(idx, inplace=True); print("Linha excluída.")
                    else:
                        print("Opção inválida."); continue
                    df_horarios.to_csv(ARQUIVO_HORARIOS, index=False);
                    print("Alteração salva!")
                except (ValueError, IndexError):
                    print("Entrada inválida.")
            except FileNotFoundError:
                print(f"ERRO: Arquivo '{ARQUIVO_HORARIOS}' não encontrado.")
            except Exception as e:
                print(f"Ocorreu um erro: {e}")

        elif resp == '3':
            try:
                # Se o arquivo não existir, cria um com estrutura padrão
                if not os.path.exists(ARQUIVO_EVENTO):
                    print("AVISO: 'config_evento.json' não encontrado. Criando um novo com valores padrão.")
                    with open(ARQUIVO_EVENTO, 'w', encoding='utf-8') as f:
                        json.dump({"ARQUIVOS_A_IGNORAR": {"GLOBAL": []}, "DIAS_EVENTO": 2,
                                   "MAX_TRABALHOS_ORIENTADOR_SESSAO": 4, "MIN_TRABALHOS_SESSAO": 4}, f, indent=4)

                with open(ARQUIVO_EVENTO, 'r+', encoding='utf-8') as f:
                    config_evento = json.load(f)
                    print("\n--- Regras Gerais Atuais ---")
                    # (Lógica de exibição e edição das regras, agora com global/específico)
                    # ... (código completo abaixo)
                    for chave, valor in config_evento.items():
                        if chave == "ARQUIVOS_A_IGNORAR":
                            print(f"- {chave}:")
                            regras = valor.get("GLOBAL", [])
                            if regras: print(f"  - GLOBAL: {', '.join(regras)}")
                            for area, arquivos in valor.items():
                                if area != "GLOBAL" and arquivos:
                                    print(f"  - {area}: {', '.join(arquivos)}")
                        else:
                            print(f"- {chave}: {valor}")
                    print("\nO que deseja alterar?")
                    print("1. Adicionar regra para ignorar arquivo")
                    print("2. Remover regra para ignorar arquivo")
                    print("3. Alterar outro valor (ex: MIN_TRABALHOS_SESSAO)")
                    edit_resp = input("Escolha: ").strip()
                    if edit_resp == '1':
                        tipo_regra = input("  A regra é GLOBAL (g) ou para uma ÁREA específica (a)?: ").lower()
                        caminho_arquivo = input("    Digite o caminho do arquivo a ignorar (ex: public/pibic.xlsx): ")
                        if tipo_regra == 'g':
                            config_evento["ARQUIVOS_A_IGNORAR"]["GLOBAL"].append(caminho_arquivo)
                        elif tipo_regra == 'a':
                            area_especifica = input("    Para qual área é esta regra?: ").upper()
                            if area_especifica in config_evento["ARQUIVOS_A_IGNORAR"]:
                                config_evento["ARQUIVOS_A_IGNORAR"][area_especifica].append(caminho_arquivo)
                            else:
                                print(
                                    f"Área '{area_especifica}' não encontrada nas regras. Crie-a primeiro se necessário.")
                        print("Regra adicionada.")
                    elif edit_resp == '2':
                        # Lógica para remover (simplificada: pede o caminho completo)
                        caminho_remover = input("Digite o caminho completo do arquivo a ser removido da lista: ")
                        removido = False
                        for chave, lista in config_evento["ARQUIVOS_A_IGNORAR"].items():
                            if caminho_remover in lista:
                                lista.remove(caminho_remover);
                                removido = True;
                                break
                        if removido:
                            print("Regra removida.")
                        else:
                            print("Arquivo não encontrado na lista de regras.")
                    elif edit_resp == '3':
                        chave_para_editar = input("Digite a chave que deseja alterar: ").upper()
                        if chave_para_editar in config_evento and chave_para_editar != "ARQUIVOS_A_IGNORAR":
                            novo_valor = input(f"Digite o novo valor para '{chave_para_editar}': ")
                            if novo_valor.isdigit():
                                config_evento[chave_para_editar] = int(novo_valor)
                            else:
                                config_evento[chave_para_editar] = novo_valor
                        else:
                            print("Chave inválida."); continue
                    else:
                        print("Opção inválida."); continue
                    f.seek(0);
                    f.truncate();
                    json.dump(config_evento, f, indent=4);
                    print("Alteração salva!")
            except Exception as e:
                print(f"Ocorreu um erro: {e}")
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    while True:
        print("\n=== ASSISTENTE DE CONFIGURAÇÃO ===")
        print("1. Criar NOVOS arquivos de configuração")
        print("2. ATUALIZAR configurações existentes")
        print("0. Sair")
        escolha_main = input("Escolha uma opção: ").strip()
        if escolha_main == '1':
            criar_configs_interativo();
            input("\nPressione Enter para continuar...")
        elif escolha_main == '2':
            atualizar_configs_interativo()
        elif escolha_main == '0':
            print("Saindo do programa.");
            break
        else:
            print("Opção inválida.")