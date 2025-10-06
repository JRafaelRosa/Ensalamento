# Sistema de Geração de Ensalamento – EAIC 2025 UEPG

Sistema desenvolvido em Python para gerar automaticamente o ensalamento do EAIC (Encontro Anual de Iniciação Científica) da UEPG.  
Ele lê as planilhas com os trabalhos, distribui em sessões, verifica regras de conflito, e gera relatórios prontos em PDF.

---

## 1. Instalação

1. **Instalar o Python**  
   Verifique se o Python 3 está instalado:  
   ```bash
   python --version
   ```
   Caso não esteja, baixe em: [https://www.python.org/downloads/](https://www.python.org/downloads/)

2. **Instalar as bibliotecas necessárias**  
   O sistema usa três bibliotecas principais:
   - `pandas` (leitura e manipulação de planilhas)
   - `openpyxl` (suporte a arquivos `.xlsx`)
   - `fpdf2` (geração dos relatórios em PDF)

   Instale com o comando:
   ```bash
   pip install pandas openpyxl fpdf2
   ```

3. **(Opcional)** Para registrar dependências:
   ```bash
   pip freeze > requirements.txt
   ```

---

## 2. Estrutura do Projeto

Organize as pastas da seguinte forma:

```
EAIC_ALG/
│
├── main.py                  # Script principal do sistema (menu interativo)
├── gerar_pdf.py             # Gera todos os relatórios PDF de uma vez
│
├── src/                     # Lógica e módulos auxiliares
│   ├── gerar_ensalamento.py # Algoritmo de geração
│   ├── verifica.py          # Verifica consistência
│   ├── pdf_ensalamento.py   # Geração de PDFs
│   ├── trocar.py            # Ajuste manual de apresentações
│   ├── consultor.py         # Consulta por orientador/apresentador
│   └── DejaVuSans.ttf       # Fonte opcional (acentos e caracteres especiais)
│
├── public/                  # Dados de entrada e resultados intermediários
│   ├── EXATAS.xlsx
│   ├── HUMANAS.xlsx
│   ├── EAIC_PIBIC_Jr_2025-2026.xlsx
│   └── csv/
│
└── pdfs/                    # Relatórios finais em PDF
```

---

## 3. Configuração

Antes de rodar o sistema, ajuste os parâmetros no código conforme o evento.

### Arquivo: `src/gerar_ensalamento.py`
Contém o dicionário `CONFIG` que define:

- `ARQUIVO_PIBIC_JR`: caminho do arquivo de entrada.
- `NUM_SALAS`: quantidade de salas.
- `DIAS_EVENTO`: número de dias.
- `SESSOES_POR_DIA`: horários e nomes das sessões.
- `MIN_TRABALHOS_POR_SESSAO`: quantidade mínima de apresentações por sessão.
- `MAX_POR_ORIENTADOR`: máximo de trabalhos de um mesmo orientador por sessão.

### Arquivo: `src/pdf_ensalamento.py`
Contém:
- `MAPEAMENTO_AREAS`: nomes completos das áreas (ex: “EXATAS” → “Ciências Exatas e da Terra”).
- `MAPEAMENTO_SALAS`: nomes físicos das salas.

Esses valores devem refletir a estrutura real do evento.

---

## 4. Como Usar (Passo a Passo)

### Passo 1 – Preparar os dados
Coloque os arquivos `.xlsx` com as listas de trabalhos dentro da pasta:
```
public/
```
O nome do arquivo define o nome da área (exemplo: `EXATAS.xlsx` → área “EXATAS”).

---

### Passo 2 – Rodar o programa principal
No terminal, dentro da pasta do projeto:
```bash
python main.py
```

O sistema abrirá um menu com as opções.  
A ordem recomendada é:

1. **Gerar Ensalamento (opção 3)**  
   - Cria os arquivos `.csv` dentro de `public/csv/` com a distribuição inicial.

2. **Verificar Ensalamento (opção 2)**  
   - Confere se não há erros, como:
     - orientador em duas salas no mesmo horário,
     - sessões com poucos trabalhos,
     - excesso de trabalhos do mesmo orientador.

3. **Gerar PDF (opção 4)**  
   - Cria os relatórios formatados dentro de `pdfs/`.

4. **Ajuste Manual (opção 6)**  
   - Permite trocar trabalhos entre sessões, se necessário.

Outras opções são auxiliares (visualização e consulta).

---

### Passo 3 – Gerar todos os PDFs automaticamente
Se quiser gerar relatórios para todas as áreas de uma só vez:
```bash
def processar()
def gerar_pdf()
```
---

## 5. Como o Sistema Funciona

O processo de geração é dividido em duas fases:

1. **Fase 1 – Alocação inicial**
   - Lê os arquivos `.xlsx` e cria uma lista de trabalhos.
   - Preenche as sessões de forma sequencial, respeitando:
     - número de salas,
     - número de dias,
     - limite de orientadores por sessão.

2. **Fase 2 – Rebalanceamento**
   - Analisa as sessões criadas e faz ajustes automáticos.
   - Redistribui trabalhos para equilibrar o número de apresentações por sessão e evitar repetições de orientadores.

Após essas duas etapas:
- Os resultados parciais são salvos em `public/csv/`.
- Os PDFs finais são salvos em `pdfs/`.

A função `processar()` automatiza todas essas etapas: leitura, geração, verificação e exportação, criando os arquivos completos com um único comando.

---

## 6. Exemplo de Execução

```bash
> python main.py

=== Sistema de Ensalamento EAIC ===
[1] Visualizar dados
[2] Verificar ensalamento
[3] Gerar ensalamento
[4] Gerar PDFs
[5] Consultar por nome
[6] Ajuste manual
Escolha uma opção: 3
Digite o nome da área (ex: EXATAS): EXATAS
Gerando ensalamento para EXATAS...
Processo concluído. Arquivos salvos em public/csv/
```

---

## 7. Saídas Geradas

**Pasta `public/csv/`**  
Arquivos intermediários com os dados processados:
```
EXATAS_dia1.csv
EXATAS_dia2.csv
```

**Pasta `pdfs/`**  
Relatórios finais prontos para impressão:
```
relatorio_EXATAS_dia1.pdf
relatorio_EXATAS_dia2.pdf
```

---

## 8. Manutenção

Para adaptar o sistema a outro evento:
- Edite `CONFIG` em `gerar_ensalamento.py`.
- Atualize os nomes em `MAPEAMENTO_AREAS` e `MAPEAMENTO_SALAS`.
- Mantenha a estrutura de pastas idêntica.

---

**Autor:** João Rafael dos Santos da Rosa  
**Instituição:** Universidade Estadual de Ponta Grossa (UEPG)  
**Uso:** Automação do ensalamento do EAIC  
