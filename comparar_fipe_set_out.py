"""
Script para baixar/preparar as tabelas FIPE de Setembro (2026/09) e Outubro (2026/10)
do dataset fipeX e realizar o JOIN comparativo de preços entre os dois meses,
salvando os CSVs na pasta principal (raiz) e na pasta raw/.
"""

import sys
import urllib.request
from pathlib import Path
import duckdb
import pandas as pd

RAIZ = Path(__file__).resolve().parent
PASTA_RAW = RAIZ / "raw"

URLS_LFS = {
    "fipe_2026_09.csv": "https://huggingface.co/datasets/alanwgt/fipex-veiculos-brasil/resolve/main/2026/09/fipex-prices.csv",
    "fipe_2026_10.csv": "https://huggingface.co/datasets/alanwgt/fipex-veiculos-brasil/resolve/main/2026/10/fipex-prices.csv",
}


def baixar_ou_carregar_mes(nome_arquivo: str, url: str) -> pd.DataFrame:
    caminho_raw = PASTA_RAW / nome_arquivo
    caminho_raiz = RAIZ / nome_arquivo

    if not caminho_raw.is_file():
        print(f"Baixando {nome_arquivo}...")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            caminho_raw.write_bytes(resp.read())

    primeira_linha = caminho_raw.open("r", encoding="utf-8").readline()
    sep = "\t" if "\t" in primeira_linha else ","
    df = pd.read_csv(caminho_raw, sep=sep, encoding="utf-8", dtype=str)

    # Salva padronizado separado por vírgula na pasta raw/ e na raiz
    df.to_csv(caminho_raw, index=False, encoding="utf-8")
    df.to_csv(caminho_raiz, index=False, encoding="utf-8")
    return df


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    PASTA_RAW.mkdir(exist_ok=True)

    df_set = baixar_ou_carregar_mes("fipe_2026_09.csv", URLS_LFS["fipe_2026_09.csv"])
    df_out = baixar_ou_carregar_mes("fipe_2026_10.csv", URLS_LFS["fipe_2026_10.csv"])

    con = duckdb.connect()
    try:
        query_join = """
        SELECT
            out.tipo_veiculo,
            out.codigo_fipe,
            out.nome_marca,
            out.nome_modelo,
            out.nome_combustivel,
            out.sigla_combustivel,
            out.ano_modelo,
            out.zero_km,
            set_tb.valor_centavos AS valor_centavos_set,
            set_tb.valor_formatado AS valor_formatado_set,
            out.valor_centavos AS valor_centavos_out,
            out.valor_formatado AS valor_formatado_out,
            CAST(CAST(out.valor_centavos AS BIGINT) - CAST(set_tb.valor_centavos AS BIGINT) AS VARCHAR) AS diferenca_centavos,
            CAST(ROUND((CAST(out.valor_centavos AS DOUBLE) - CAST(set_tb.valor_centavos AS DOUBLE)) / 100.0, 2) AS VARCHAR) AS diferenca_reais,
            CAST(
                ROUND(
                    ((CAST(out.valor_centavos AS DOUBLE) - CAST(set_tb.valor_centavos AS DOUBLE)) * 100.0)
                    / NULLIF(CAST(set_tb.valor_centavos AS DOUBLE), 0),
                    2
                ) AS VARCHAR
            ) AS variacao_percentual
        FROM df_out AS out
        INNER JOIN df_set AS set_tb
            ON out.tipo_veiculo = set_tb.tipo_veiculo
           AND out.codigo_fipe = set_tb.codigo_fipe
           AND out.sigla_combustivel = set_tb.sigla_combustivel
           AND out.ano_modelo = set_tb.ano_modelo
           AND out.zero_km = set_tb.zero_km
        ORDER BY out.tipo_veiculo, out.nome_marca, out.nome_modelo, out.ano_modelo
        """
        df_join = con.execute(query_join).df()
    finally:
        con.close()

    nome_comparacao = "fipe_comparacao_set_out.csv"
    df_join.to_csv(PASTA_RAW / nome_comparacao, index=False, encoding="utf-8")
    df_join.to_csv(RAIZ / nome_comparacao, index=False, encoding="utf-8")

    print(f"Setembro (2026/09): {len(df_set):,}".replace(",", ".") + " registros")
    print(f"Outubro  (2026/10): {len(df_out):,}".replace(",", ".") + " registros")
    print(f"JOIN Comparação Set vs Out: {len(df_join):,}".replace(",", ".") + " registros")
    print(f"Arquivos salvos em '{RAIZ}' e '{PASTA_RAW}'.")


if __name__ == "__main__":
    main()

