"""
SPEC DA INGESTÃO (pipeline/ingestao.py)

Regras e motivações:
1. ESCOPO E NOMES:
   Grava no schema `raw` obedecendo ao mapa literal de arquivo `.csv.gz` para
   nome de tabela definido em `ARQUIVOS_TABELAS`.
2. PROIBIÇÕES (regra central desta etapa):
   Nenhuma conversão de tipo, nenhuma linha descartada ou deduplicada, nenhum
   nome de coluna alterado, nenhum valor corrigido, preenchido ou normalizado.
   Data continua texto, nulo continua nulo.
   Motivo: a fronteira entre "o dado que chegou" e "o dado que eu decidi"
   precisa existir na passagem de `raw` para `refined` (etapa 2). Se houver
   correção na ingestão, essa fronteira desaparece.
3. REEXECUÇÃO:
   Rodar dez vezes produz exatamente o mesmo resultado que rodar uma: cada
   tabela é recriada (CREATE OR REPLACE via `gravar`), nunca acrescentada,
   permitindo reexecutar sem medo de duplicar dados.
4. LEITURA DO ARQUIVO:
   Encoding declarado explicitamente como `utf-8` (nunca adivinhado). Os
   arquivos `.csv.gz` são lidos diretamente pelo pandas sem descompactar em
   disco. Campos vazios viram `NULL` (não são convertidos em string vazia).
5. TIPAGEM:
   Toda coluna entra como texto (`dtype=str`), com inferência de tipos desligada.
   Motivo: a inferência automática converte códigos com zero à esquerda (como
   CEP ou código FIPE) em número e elimina o zero sem aviso. A tipagem pertence
   à etapa 2, onde é uma decisão explícita.
6. SAÍDA NA TELA:
   Uma linha por tabela com o nome qualificado (`raw.<tabela>`) e a contagem de
   linhas lida do banco (retorno de `gravar`), com milhar separado por ponto,
   seguida de uma linha final com o total. `stdout` é reconfigurado para `utf-8`
   para evitar acentos embaralhados no Prompt de Comando do Windows.
7. ERRO:
   Antes de abrir o banco, verifica se todos os arquivos esperados existem em
   `PASTA_RAW`. Se faltar qualquer arquivo, lista os ausentes, informa a pasta
   verificada e encerra com `sys.exit(1)` sem iniciar uma ingestão parcial.
   Motivo: ingerir parte das tabelas em silêncio gera análises e dashboards
   incorretos que aparentam estar certos.
"""

import sys
import pandas as pd
from pipeline.db import PASTA_RAW, conectar, criar_schema, gravar

SCHEMA = "raw"

ARQUIVOS_TABELAS = {
    "fipe_2026_09.csv": "fipe_2026_09",
    "fipe_2026_10.csv": "fipe_2026_10",
    "fipe_comparacao_set_out.csv": "fipe_comparacao_set_out",
}


def formatar_milhar(valor: int) -> str:
    return f"{valor:,}".replace(",", ".")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")

    faltantes = [
        arquivo
        for arquivo in ARQUIVOS_TABELAS
        if not (PASTA_RAW / arquivo).is_file()
    ]
    if faltantes:
        print(f"Erro: arquivo(s) não encontrado(s) na pasta '{PASTA_RAW}':")
        for arquivo in faltantes:
            print(f"  - {arquivo}")
        sys.exit(1)

    con = conectar()
    try:
        criar_schema(con, SCHEMA)
        total = 0

        for arquivo, tabela in ARQUIVOS_TABELAS.items():
            caminho = PASTA_RAW / arquivo
            df = pd.read_csv(caminho, encoding="utf-8", dtype=str)
            gravados = gravar(con, df, SCHEMA, tabela)
            total += gravados
            print(f"{SCHEMA}.{tabela}: {formatar_milhar(gravados)}")

        print(f"Total: {formatar_milhar(total)}")
    finally:
        con.close()


if __name__ == "__main__":
    main()

