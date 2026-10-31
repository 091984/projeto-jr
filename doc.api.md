# Documentação do Dataset — fipeX Veículos Brasil (`alanwgt/fipex-veiculos-brasil`)

Resumo técnico do dataset público da Tabela FIPE hospedado no Hugging Face e utilizado neste pipeline de dados.

---

## 1. Visão Geral

- **Repositório Hugging Face:** [https://huggingface.co/datasets/alanwgt/fipex-veiculos-brasil](https://huggingface.co/datasets/alanwgt/fipex-veiculos-brasil)
- **Repositório GitHub / Releases:** [https://github.com/fipex-labs/dataset](https://github.com/fipex-labs/dataset)
- **Portal / API Relacionada:** [https://fipex.com.br/dados-e-api](https://fipex.com.br/dados-e-api)
- **Licença:** `CC0-1.0` (Domínio Público — uso livre sem restrições)
- **Categorias:** `tabular-regression`, `time-series-forecasting` (`1M < n < 10M` registros no histórico completo)

---

## 2. Organização e Arquivos Disponíveis

O repositório disponibiliza tanto o histórico completo quanto *dumps* mensais individuais por período de referência:

### 2.1. Dumps Mensais por Período (`YYYY/MM/`)
Localizados em pastas por ano e mês (ex.: `2026/09/`, `2026/10/`):

| Arquivo | Formato | Descrição |
| :--- | :--- | :--- |
| `YYYY/MM/fipex-prices.csv` | CSV (TSV `\t`) | Preços do mês de referência como publicados pela FIPE |
| `YYYY/MM/fipex-prices.parquet` | Parquet | Mesmos dados do período em formato colunar otimizado |

**URLs diretas (LFS Resolve) utilizadas no projeto:**
- **Setembro/2026 (`2026/09`):**
  `https://huggingface.co/datasets/alanwgt/fipex-veiculos-brasil/resolve/main/2026/09/fipex-prices.csv`
- **Outubro/2026 (`2026/10`):**
  `https://huggingface.co/datasets/alanwgt/fipex-veiculos-brasil/resolve/main/2026/10/fipex-prices.csv`

### 2.2. Histórico Completo (Raiz / Releases)

| Arquivo | Versão | Formato | Descrição |
| :--- | :--- | :--- | :--- |
| `fipex-prices-latest.csv` | Original | CSV (`\t`) | Dados históricos com os nomes originais de cada época |
| `fipex-prices-latest-merged.csv` | Consolidada | CSV (`\t`) | Modelos renomeados unificados sob a nomenclatura atual |
| `fipex-prices-latest.parquet` | Original | Parquet | Versão original em formato colunar comprimido |
| `fipex-prices-latest-merged.parquet` | Consolidada | Parquet | Versão consolidada em formato colunar comprimido |

---

## 3. Estrutura das Colunas (Schema Original — 12 Colunas)

Todos os arquivos do dataset seguem a estrutura abaixo:

| Coluna | Tipo Original | Descrição |
| :--- | :--- | :--- |
| `tipo_veiculo` | `string` | Categoria do veículo (`carro`, `moto`, `caminhão`) |
| `codigo_fipe` | `string` | Código único do veículo na Tabela FIPE (ex.: `002182-2`) |
| `nome_modelo` | `string` | Nome do modelo (ex.: `Corolla Altis 1.8 16V Aut. (Híbrido)`) |
| `nome_marca` | `string` | Nome do fabricante/marca (ex.: `Toyota`, `Fiat`, `VW - VolksWagen`) |
| `nome_combustivel` | `string` | Tipo de combustível por extenso (`Gasolina`, `Diesel`, `Álcool`, `Híbrido`, etc.) |
| `sigla_combustivel` | `string` | Sigla do combustível (`g`, `e`, `d`, `l`, `f`, `h`, `n`) |
| `ano_modelo` | `int` / `NULL` | Ano de fabricação do modelo (ou `NULL` quando `zero_km = true`) |
| `zero_km` | `bool` | Indica se o veículo é Zero KM (`true` ou `false`) |
| `valor_centavos` | `int` | Preço do veículo em centavos (evita imprecisão de ponto flutuante) |
| `valor_formatado` | `string` | Preço formatado em Reais (ex.: `R$ 173.645,00`) |
| `mes_referencia` | `int` | Mês de referência da tabela FIPE (`1` a `12`) |
| `ano_referencia` | `int` | Ano de referência da tabela FIPE (ex.: `2026`) |

---

## 4. Uso no Pipeline Local (`projeto-jr`)

1. **Coleta e Comparação (`comparar_fipe_set_out.py`):**
   - Baixa os dumps `2026/09/fipex-prices.csv` (`51.012` registros) e `2026/10/fipex-prices.csv` (`51.247` registros) do Hugging Face.
   - Realiza o `INNER JOIN` pelas chaves `(tipo_veiculo, codigo_fipe, sigla_combustivel, ano_modelo, zero_km)` tratando veículos Zero-KM (`IS NOT DISTINCT FROM`) e gera `fipe_comparacao_set_out.csv` (`51.003` registros) na raiz e em `raw/`.
2. **Ingestão (`pipeline/ingestao.py`):**
   - Carrega `raw/fipe_comparacao_set_out.csv` para a tabela `raw.fipe_comparacao_set_out` no banco DuckDB (`fipe.duckdb`) com todas as colunas em `VARCHAR`.
3. **Transformação (`pipeline/transformacao.py`):**
   - Lê `raw.fipe_comparacao_set_out`, seleciona as colunas de negócio, adiciona a coluna `variacao_mes` (`Subiu`, `Caiu` ou `Estável`) e grava tanto em `refined.fipe_comparacao_set_out` no `fipe.duckdb` quanto em `refined/refined.fipe_comparacao_set_out.csv`.
4. **Visualização (`pipeline/visualizacao_html.py` e `ui.py`):**
   - `uv run python -m pipeline.visualizacao_html`: abre a página HTML temática (azul, verde e amarelo) em `http://localhost:8000` com busca por nome do carro, placa ou código FIPE.
   - `uv run python ui.py`: abre o DuckDB UI em `http://localhost:4213`.
