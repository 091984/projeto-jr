"""
SPEC DA TRANSFORMAÇÃO (pipeline/transformacao.py)

Regras e motivações:
1. ESCOPO:
   Lê exclusivamente do schema `raw` e escreve no schema `refined` do banco
   `fipe.duckdb` e na pasta `refined/`, sem nunca alterar `raw`. Seleciona da
   tabela `raw.fipe_comparacao_set_out` as colunas:
   `tipo_veiculo`, `codigo_fipe`, `nome_marca`, `nome_modelo`, `sigla_combustivel`,
   `ano_modelo`, `zero_km`, `valor_formatado_set`, `valor_formatado_out`,
   `diferenca_reais`, `variacao_percentual`, e adiciona a coluna `variacao_mes`
   com a síntese da variação de um mês para o outro.
   Motivo: preservar `raw` intocado garante que o dado bruto possa ser
   reprocessado a qualquer momento sem nova coleta.
2. NOMES:
   Mantém os nomes originais das colunas selecionadas e da tabela
   (`fipe_comparacao_set_out`), acrescentando apenas `variacao_mes`.
   Motivo: manter consistência e rastreabilidade direta entre `raw` e `refined`.
3. TIPOS:
   Mantém os tipos originais (`VARCHAR`) vindos da camada `raw`.
   Motivo: evitar perda ou alteração silenciosa de formatação textual nesta etapa.
4. SAÍDA NA TELA:
   Reconfigura `stdout` para `utf-8` (compatibilidade com Prompt de Comando do
   Windows) e exibe por tabela a contagem gravada no banco, as colunas geradas
   e o arquivo salvo na pasta `refined/`.
5. REEXECUÇÃO E ERRO:
   Recria a tabela de destino com `CREATE OR REPLACE TABLE` via `gravar()`
   (idempotência: rodar várias vezes produz o mesmo resultado). Antes de
   transformar, verifica se as tabelas de entrada existem no schema `raw`; caso
   falte alguma, lista as ausentes, orienta a rodar a ingestão e encerra com
   `sys.exit(1)`.
"""

import sys
from pipeline.db import PASTA_RAW, conectar, criar_schema, gravar

SCHEMA_ORIGEM = "raw"
SCHEMA_DESTINO = "refined"
PASTA_REFINED = PASTA_RAW.parent / "refined"
TABELAS_ORIGEM = ["fipe_comparacao_set_out"]


def formatar_milhar(valor: int) -> str:
    return f"{valor:,}".replace(",", ".")


def verificar_tabelas_raw(con) -> list[str]:
    existentes = {
        row[0]
        for row in con.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = ?
            """,
            [SCHEMA_ORIGEM],
        ).fetchall()
    }
    return [t for t in TABELAS_ORIGEM if t not in existentes]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")

    con = conectar()
    try:
        faltantes = verificar_tabelas_raw(con)
        if faltantes:
            print(f"Erro: tabela(s) não encontrada(s) no schema '{SCHEMA_ORIGEM}':")
            for tabela in faltantes:
                print(f"  - {SCHEMA_ORIGEM}.{tabela}")
            print("Execute a ingestão antes: uv run python -m pipeline.ingestao")
            sys.exit(1)

        PASTA_REFINED.mkdir(exist_ok=True)
        criar_schema(con, SCHEMA_DESTINO)
        total = 0

        for tabela in TABELAS_ORIGEM:
            df_refined = con.execute(
                f"""
                SELECT
                    tipo_veiculo,
                    codigo_fipe,
                    nome_marca,
                    nome_modelo,
                    sigla_combustivel,
                    ano_modelo,
                    zero_km,
                    valor_formatado_set,
                    valor_formatado_out,
                    diferenca_reais,
                    variacao_percentual,
                    CASE
                        WHEN TRY_CAST(diferenca_reais AS DOUBLE) > 0
                            THEN 'Subiu (+' || variacao_percentual || '%)'
                        WHEN TRY_CAST(diferenca_reais AS DOUBLE) < 0
                            THEN 'Caiu (' || variacao_percentual || '%)'
                        ELSE 'Estável (0.0%)'
                    END AS variacao_mes
                FROM {SCHEMA_ORIGEM}.{tabela}
                """
            ).df()

            caminho_csv = PASTA_REFINED / f"{SCHEMA_DESTINO}.{tabela}.csv"
            df_refined.to_csv(caminho_csv, index=False, encoding="utf-8")

            contagem = gravar(con, df_refined, SCHEMA_DESTINO, tabela)
            colunas = list(df_refined.columns)
            total += contagem

            print(f"{SCHEMA_DESTINO}.{tabela}: {formatar_milhar(contagem)} linhas")
            print(f"Colunas ({len(colunas)}): {', '.join(colunas)}")
            print(f"Arquivo salvo em: {caminho_csv}")

        print(f"Total: {formatar_milhar(total)}")
    finally:
        con.close()


if __name__ == "__main__":
    main()
