import os
import json
import pandas as pd


def carregar_config_geral():
    """Lê todos os ficheiros de configuração do evento com validação detalhada."""
    PASTA_CONFIG = os.path.normpath("public/config")

    arquivo_json = os.path.join(PASTA_CONFIG, "config_evento.json")
    arquivo_areas = os.path.join(PASTA_CONFIG, "config_areas.csv")
    arquivo_mapa = os.path.join(PASTA_CONFIG, "mapa_salas.csv")
    arquivo_horarios = os.path.join(PASTA_CONFIG, "horarios_sessoes.csv")

    # Verifica se os 4 ficheiros existem fisicamente
    for arq in [arquivo_json, arquivo_areas, arquivo_mapa, arquivo_horarios]:
        if not os.path.exists(arq):
            print(f"[ERRO CRÍTICO] Ficheiro não encontrado: {arq}")
            return None, None, None, None

    try:
        # 1. Carrega JSON
        with open(arquivo_json, 'r', encoding='utf-8') as f:
            config_evento = json.load(f)

        # 2. Carrega Áreas
        config_areas_df = pd.read_csv(arquivo_areas, encoding="utf-8-sig")
        if 'nome_base' in config_areas_df.columns:
            config_areas_df['nome_base'] = config_areas_df['nome_base'].astype(str).str.strip().str.upper()
            config_areas_df.set_index('nome_base', inplace=True)

        # 3. Carrega Mapa de Salas
        mapa_salas_df = pd.read_csv(arquivo_mapa, encoding="utf-8-sig")
        if 'codigo_logico' in mapa_salas_df.columns:
            mapa_salas_df['codigo_logico'] = mapa_salas_df['codigo_logico'].astype(str).str.strip().str.upper()
            mapa_salas_df.set_index('codigo_logico', inplace=True)

        # 4. Carrega Horários
        horarios_sessoes_df = pd.read_csv(arquivo_horarios, encoding="utf-8-sig")

        print("Ficheiros de configuração carregados com sucesso.")
        return config_evento, config_areas_df, mapa_salas_df, horarios_sessoes_df

    except Exception as e:
        print(f"[ERRO AO CARREGAR CONFIGURAÇÕES]: {e}")
        return None, None, None, None


def obter_info_area(nome_base, config_df):
    if config_df is None or nome_base is None:
        return None

    nome_chave = str(nome_base).strip().upper()
    try:
        if config_df.index.name == 'nome_base':
            return config_df.loc[nome_chave].to_dict()
        elif 'nome_base' in config_df.columns:
            df_temp = config_df.set_index('nome_base')
            return df_temp.loc[nome_chave].to_dict()
        else:
            return config_df.loc[nome_chave].to_dict()
    except KeyError:
        print(f"AVISO: Área '{nome_chave}' não encontrada em 'config_areas.csv'.")
        return None


def obter_nome_fisico(codigo_logico, mapa_df):
    if mapa_df is None or codigo_logico is None:
        return str(codigo_logico)

    codigo_chave = str(codigo_logico).strip().upper()
    try:
        if mapa_df.index.name == 'codigo_logico':
            valor = mapa_df.loc[codigo_chave]['nome_fisico']
        elif 'codigo_logico' in mapa_df.columns:
            df_temp = mapa_df.set_index('codigo_logico')
            valor = df_temp.loc[codigo_chave]['nome_fisico']
        else:
            valor = mapa_df.loc[codigo_chave]['nome_fisico']

        return str(valor)
    except KeyError:
        return codigo_chave