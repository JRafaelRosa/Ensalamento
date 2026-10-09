import os
import json
import pandas as pd
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from fpdf.fonts import FontFace

try:
    from src.sala import obter_info_area, obter_nome_fisico
except ImportError:
    from sala import obter_info_area, obter_nome_fisico

# Definição de Cores Padrão
COLOR_AZUL_FUNDO = (220, 230, 240)
COLOR_AZUL_TEXTO = (20, 50, 120)
COLOR_CINZA_ZEBRA = (240, 240, 240)


def sanitize_text(text):
    """Sanitiza o texto para codificação latin-1 mantendo acentuação compatível com o FPDF standard fonts."""
    if text is None:
        return ""
    s = str(text)
    substituicoes = {
        '–': '-', '—': '-', '“': '"', '”': '"', '‘': "'", '’': "'", '…': '...'
    }
    for orig, sub in substituicoes.items():
        s = s.replace(orig, sub)

    return s.encode('latin-1', 'replace').decode('latin-1')


def obter_data_evento_por_dia(nome_base_arquivo):
    """Lê o arquivo config_evento.json e retorna a data exata do dia correspondente."""
    caminho_config = "public/config/config_evento.json"
    datas_evento = []

    if os.path.exists(caminho_config):
        try:
            with open(caminho_config, 'r', encoding='utf-8') as f:
                config = json.load(f)
                datas_evento = config.get("DATAS_EVENTO", [])
        except Exception:
            pass

    if "_dia" in nome_base_arquivo:
        try:
            dia_num = int(nome_base_arquivo.split('_dia')[1].split('.')[0])
            if datas_evento and 1 <= dia_num <= len(datas_evento):
                return datas_evento[dia_num - 1]
        except Exception:
            pass

    return ""


class PDF(FPDF):
    def __init__(self, orientation='P', unit='mm', format='A4', area_name='Relatório', event_date=''):
        super().__init__(orientation, unit, format)

        nome_limpo = area_name.upper()
        if nome_limpo.endswith(" - EAIC"):
            self.area_name = nome_limpo
        else:
            self.area_name = f"{nome_limpo} - EAIC"

        self.event_date = event_date

    def header(self):
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(*COLOR_AZUL_TEXTO)
        self.cell(0, 8, sanitize_text(self.area_name), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.set_font('Helvetica', 'B', 12)
        self.cell(0, 8, 'UNIVERSIDADE ESTADUAL DE PONTA GROSSA', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')

        if self.event_date:
            self.cell(0, 8, sanitize_text(f"Data: {self.event_date}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')

        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', align='C')


def obter_ordem_sessao(sessao_str):
    """Mapeia o nome da sessão para uma ordem cronológica estrita."""
    sessao_lower = str(sessao_str).lower()
    if 'manhã 1' in sessao_lower or 'manha 1' in sessao_lower:
        return 1
    elif 'manhã 2' in sessao_lower or 'manha 2' in sessao_lower:
        return 2
    elif 'tarde' in sessao_lower:
        return 3
    elif 'noite' in sessao_lower:
        return 4
    return 99


def pdf_ensalamento(caminho_completo_do_arquivo_csv, config_areas_df, mapa_salas_df):
    if not caminho_completo_do_arquivo_csv:
        print("Nenhum nome de arquivo fornecido.")
        return

    try:
        df = pd.read_csv(caminho_completo_do_arquivo_csv, encoding="utf-8-sig")
        print(f"\nLendo o arquivo '{caminho_completo_do_arquivo_csv}' para gerar o PDF...")
    except FileNotFoundError:
        print(f"  [ERRO] Arquivo CSV '{caminho_completo_do_arquivo_csv}' não foi encontrado. PDF não gerado.")
        return
    except Exception as e:
        print(f"  [ERRO] Ocorreu um erro ao ler o arquivo: {e}")
        return

    if df.empty:
        print(f"  [AVISO] O arquivo CSV '{caminho_completo_do_arquivo_csv}' está vazio. Nenhum PDF foi gerado.")
        return

    nome_base_arquivo = os.path.basename(caminho_completo_do_arquivo_csv)
    nome_area_base = nome_base_arquivo.split('_dia')[0].upper()
    info_area = obter_info_area(nome_area_base, config_areas_df)

    if info_area is None:
        print(f"  [ERRO] Informações da área '{nome_area_base}' não encontradas nas configurações.")
        return

    nome_area_completo = info_area.get('nome_completo', nome_area_base)
    data_do_evento = obter_data_evento_por_dia(nome_base_arquivo)

    pdf = PDF('P', 'mm', 'A4', area_name=nome_area_completo, event_date=data_do_evento)
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    FONTE_PADRAO = "Helvetica"

    # --- ORDENAÇÃO CRONOLÓGICA DAS SESSÕES ---
    df['Ordem_Sessao'] = df['Sessão'].apply(obter_ordem_sessao)
    df['Horario_DT'] = pd.to_datetime(df['Horário'], format='%H:%M', errors='coerce')

    df_ordenado = df.sort_values(by=['Ordem_Sessao', 'Sala', 'Horario_DT']).reset_index(drop=True)
    sessoes_agrupadas = df_ordenado.groupby(['Sessão', 'Sala'], sort=False)

    for (nome_sessao, nome_sala_logica), df_grupo in sessoes_agrupadas:
        if pdf.get_y() > 230:
            pdf.add_page()

        if "Manhã 1" in str(nome_sessao):
            novo_titulo_sessao = "Horário (08h30 - 10h00)"
        elif "Manhã 2" in str(nome_sessao):
            novo_titulo_sessao = "Horário (10h30 - 12h00)"
        elif "Tarde" in str(nome_sessao):
            novo_titulo_sessao = "Horário (14h00 - 15h30)"
        else:
            novo_titulo_sessao = str(nome_sessao)

        nome_sala_fisica = obter_nome_fisico(nome_sala_logica, mapa_salas_df)
        sala_fisica_str = str(nome_sala_fisica).strip().upper()
        if not sala_fisica_str.startswith("SALA"):
            sala_fisica_str = f"SALA {sala_fisica_str}"

        titulo_sala_final = f"SESSÃO {nome_sala_logica} - {sala_fisica_str}"

        pdf.set_font(FONTE_PADRAO, 'B', 14)
        pdf.set_fill_color(*COLOR_AZUL_FUNDO)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 9, sanitize_text(novo_titulo_sessao), new_x=XPos.LMARGIN, new_y=YPos.NEXT, border=0, align='C', fill=True)

        pdf.set_font(FONTE_PADRAO, 'B', 12)
        pdf.cell(0, 7, sanitize_text(titulo_sala_final), new_x=XPos.LMARGIN, new_y=YPos.NEXT, border=0, align='C', fill=True)
        pdf.ln(4)

        dados_tabela = [[sanitize_text(col) for col in ["Horário", "Apresentador(a)", "Orientador(a)", "Título"]]]

        for _, trabalho in df_grupo.iterrows():
            horario_inicio_slot_str = str(trabalho.get('Horário', '08:30'))
            try:
                horario_inicio_slot_dt = pd.to_datetime(horario_inicio_slot_str, format='%H:%M', errors='coerce')
                if pd.isna(horario_inicio_slot_dt):
                    intervalo_horario = horario_inicio_slot_str
                else:
                    horario_fim_slot_dt = horario_inicio_slot_dt + pd.Timedelta(minutes=15)
                    horario_fim_slot_str = horario_fim_slot_dt.strftime('%H:%M')
                    intervalo_horario = f"{horario_inicio_slot_str}-{horario_fim_slot_str}"
            except Exception:
                intervalo_horario = horario_inicio_slot_str

            dados_tabela.append([
                sanitize_text(intervalo_horario),
                sanitize_text(trabalho.get('Apresentador(a)', '')),
                sanitize_text(trabalho.get('Orientador(a)', '')),
                sanitize_text(trabalho.get('Título', ''))
            ])

        headings_style = FontFace(emphasis="BOLD", color=(0, 0, 0), fill_color=COLOR_AZUL_FUNDO)
        zebra_style = FontFace(fill_color=COLOR_CINZA_ZEBRA)

        pdf.set_font(FONTE_PADRAO, size=9)
        pdf.set_text_color(0, 0, 0)

        with pdf.table(
                col_widths=(22, 40, 40, 88),
                text_align=("CENTER", "LEFT", "LEFT", "LEFT"),
                line_height=5.5,
                headings_style=headings_style
        ) as table:
            for i, data_row in enumerate(dados_tabela):
                row = table.row()
                if i > 0 and i % 2 != 0:
                    row.style = zebra_style
                for datum in data_row:
                    row.cell(datum)

        pdf.ln(12)

    PASTA_SAIDA = "pdfs/"
    os.makedirs(PASTA_SAIDA, exist_ok=True)

    nome_base_saida = os.path.splitext(os.path.basename(caminho_completo_do_arquivo_csv))[0]
    nome_arquivo_saida = os.path.join(PASTA_SAIDA, f"{nome_base_saida}.pdf")

    try:
        pdf.output(nome_arquivo_saida)
        print(f"PDF gerado com sucesso! Verifique o arquivo: '{nome_arquivo_saida}'")
    except Exception as e:
        print(f"\nOcorreu um erro ao salvar o PDF: {e}")