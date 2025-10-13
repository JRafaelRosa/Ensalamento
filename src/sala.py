import pandas as pd
import json  # <-- Nova importação


def carregar_config_geral():
    """Lê todos os arquivos de configuração e os retorna."""
    PASTA_CONFIG = "public/config"
    try:
        with open(f"{PASTA_CONFIG}/config_evento.json", 'r', encoding='utf-8') as f:
            config_evento = json.load(f)

        config_areas_df = pd.read_csv(f"{PASTA_CONFIG}/config_areas.csv").set_index('nome_base')
        mapa_salas_df = pd.read_csv(f"{PASTA_CONFIG}/mapa_salas.csv").set_index('codigo_logico')
        horarios_sessoes_df = pd.read_csv(f"{PASTA_CONFIG}/horarios_sessoes.csv")

        print("Arquivos de configuração carregados com sucesso.")
        return config_evento, config_areas_df, mapa_salas_df, horarios_sessoes_df
    except FileNotFoundError as e:
        print(f"ERRO CRÍTICO: Arquivo de configuração não encontrado: {e.filename}")
        print(f"Certifique-se que todos os arquivos de configuração estão na pasta '{PASTA_CONFIG}'.")
        print("Você pode gerá-los usando o script 'gerador_config.py'.")
        return None, None, None, None
    except Exception as e:
        print(f"Ocorreu um erro ao carregar as configurações: {e}")
        return None, None, None, None


def obter_info_area(nome_base, config_df):
    try:
        return config_df.loc[nome_base.upper()].to_dict()
    except KeyError:
        print(f"AVISO: Área '{nome_base}' não encontrada em 'config_areas.csv'.")
        return None


def obter_nome_fisico(codigo_logico, mapa_df):
    try:
        return mapa_df.loc[codigo_logico]['nome_fisico']
    except KeyError:
        return codigo_logico