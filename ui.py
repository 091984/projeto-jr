"""
SPEC DO ui.py (Explorador visual do banco no navegador)

Regras e motivações:
- U1. O QUE FAZ:
  Abre o arquivo `fipe.duckdb` localizado na raiz do projeto, instala e carrega
  a extensão `ui` do DuckDB (`INSTALL ui; LOAD ui;`) e executa `CALL start_ui()`,
  subindo o servidor local em http://localhost:4213 e abrindo o navegador.
- U2. FICA DE PÉ ATÉ CTRL+C:
  Como a extensão `ui` serve enquanto a conexão com o DuckDB estiver ativa, o
  script mantém o processo vivo, imprime a URL e a instrução "Ctrl+C para
  encerrar" e, ao receber `KeyboardInterrupt`, fecha a conexão e encerra sem
  exibir traceback.
  Motivo: o arquivo `.duckdb` aceita apenas um processo gravando por vez; manter
  o servidor ativo bloqueia a ingestão com erro de lock ("Could not set lock on
  file"), portanto encerrar de forma limpa e previsível faz parte da ferramenta.
- U3. NÃO CRIA BANCO:
  Verifica a existência de `fipe.duckdb` antes de abrir conexão. Caso não
  exista, informa que é necessário executar a ingestão antes e encerra com
  `sys.exit(1)`. Por esse motivo, não utiliza `conectar()` de `pipeline/db.py`.
  Motivo: abrir um banco recém-criado e vazio no navegador pareceria uma
  ingestão quebrada.
- U4. SEPARAÇÃO:
  `ui.py` e `pipeline/ingestao.py` são totalmente independentes e não importam
  um ao outro: a ingestão não sobe servidor nem depende da extensão `ui`.
- U5. SAÍDA NA TELA:
  Reconfigura `stdout` para `utf-8` para exibir acentuação corretamente no
  Prompt de Comando do Windows.
"""

import sys
import time
from pathlib import Path
import duckdb

CAMINHO_BANCO = Path(__file__).resolve().parent / "fipe.duckdb"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")

    if not CAMINHO_BANCO.is_file():
        print(
            f"Erro: banco '{CAMINHO_BANCO.name}' não encontrado em '{CAMINHO_BANCO.parent}'. "
            "Execute a ingestão antes (uv run python -m pipeline.ingestao)."
        )
        sys.exit(1)

    con = duckdb.connect(str(CAMINHO_BANCO))
    try:
        con.execute("INSTALL ui;")
        con.execute("LOAD ui;")
        con.execute("CALL start_ui();")
        print("DuckDB UI disponível em: http://localhost:4213")
        print("Ctrl+C para encerrar")

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        con.close()


if __name__ == "__main__":
    main()

