"""
SPEC DO pipeline/db.py (Módulo de conexão compartilhado pelas etapas da pipeline)

Expõe exatamente três funções e uma constante:
  - PASTA_RAW: Path da pasta raw/ com os arquivos .csv.gz
  - conectar(): abre o fipe.duckdb na raiz do projeto, criando se faltar
  - criar_schema(con, nome): executa CREATE SCHEMA IF NOT EXISTS
  - gravar(con, df, schema, tabela): grava o DataFrame e devolve a contagem lida do banco

Regras e motivações:
- D1. CAMINHOS: PASTA_RAW e fipe.duckdb são resolvidos a partir da localização
  do próprio db.py (a pasta acima de pipeline/), nunca do diretório corrente.
  Motivo: rodar o script de outra pasta não pode criar um fipe.duckdb vazio no
  lugar errado, o que pareceria uma ingestão quebrada.
- D2. TRÊS FUNÇÕES E UMA CONSTANTE, NADA MAIS: db.py não lê CSV, não conhece
  nome de tabela, não imprime nada e não converte tipo. Quem decide tudo isso é
  cada etapa.
  Motivo: as etapas seguintes importam este arquivo; regra de negócio escondida
  aqui valeria para todas as etapas sem aparecer em nenhuma spec.
- D3. gravar: Recria a tabela (CREATE OR REPLACE TABLE schema.tabela) com as
  colunas e os tipos do DataFrame, sem alterar nada (coluna str vira VARCHAR,
  nulo continua NULL) e sem deixar view ou tabela temporária para trás. Devolve
  SELECT count(*) da tabela recém-gravada, lido do banco.
  Motivo: a contagem que aparece na tela tem que ser a do que foi efetivamente
  gravado no banco, não a do que estava na memória.
- D4. CONEXÃO: conectar() devolve a conexão aberta; quem chama é quem fecha.
  db.py não guarda conexão global, nem abre ou cria arquivo ao ser importado.
"""

from pathlib import Path
import duckdb

PASTA_RAW = Path(__file__).resolve().parent.parent / "raw"


def conectar():
    return duckdb.connect(str(PASTA_RAW.parent / "fipe.duckdb"))


def criar_schema(con, nome):
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {nome}")


def gravar(con, df, schema, tabela):
    # DuckDB lê a variável local `df` diretamente no escopo sem criar view ou tabela temporária
    con.execute(f"CREATE OR REPLACE TABLE {schema}.{tabela} AS SELECT * FROM df")
    return con.execute(f"SELECT count(*) FROM {schema}.{tabela}").fetchone()[0]

