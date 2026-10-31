# SPEC — Visualização HTML da Tabela FIPE (`app_html.py`)

Estou construindo a etapa de visualização em HTML do pipeline de dados sobre o dataset público da FIPE. Trabalho com **spec-driven development**: a spec abaixo é a fonte da verdade e o código é consequência dela. Não acrescente requisito que não esteja escrito aqui. Se algo estiver ambíguo, pergunte antes de escrever código.

---

## STACK
- Python 3.14, dependências gerenciadas com `uv`
- DuckDB (`fipe.duckdb` na raiz do projeto)
- Servidor HTTP nativo (`http.server`) ou geração/serviço de página HTML5 + CSS3 + JavaScript embutido
- Nenhum framework externo pesado obrigatório: script executável direto pela linha de comando

## O QUE JÁ EXISTE (use, não reimplemente)
- `pipeline/db.py`: `conectar()`
- O schema `refined` no banco `fipe.duckdb`, contendo a tabela `refined.fipe_comparacao_set_out` (e o arquivo espelho `refined/refined.fipe_comparacao_set_out.csv`) com as 12 colunas:
  `tipo_veiculo`, `codigo_fipe`, `nome_marca`, `nome_modelo`, `sigla_combustivel`, `ano_modelo`, `zero_km`, `valor_formatado_set`, `valor_formatado_out`, `diferenca_reais`, `variacao_percentual`, `variacao_mes`

## ARTEFATO A PRODUZIR
`pipeline/visualizacao_html.py` (ou `app_html.py` na raiz), executável com:
```bash
uv run python -m pipeline.visualizacao_html
```

---

## SPEC

### 1. ESCOPO E FONTE DE DADOS
- Lê exclusivamente da tabela `refined.fipe_comparacao_set_out` no banco `fipe.duckdb` (nunca lê nem escreve em `raw`).
- **Motivo:** garantir que a interface apresente apenas os dados já tratados e com a coluna calculada `variacao_mes` da camada `refined`.

### 2. IDENTIDADE VISUAL (CORES DE FUNDO AZUL, VERDE E AMARELO)
- A página HTML deve utilizar paleta com as cores de fundo **azul, verde e amarelo** (ex.: gradiente ou seções combinando Azul `#002776`, Verde `#009C3B` e Amarelo `#FFDF00`, com contraste legível nos cartões e na tabela de resultados).
- **Motivo:** identidade visual temática para consulta da Tabela FIPE nacional, destacando cabeçalho, barra de pesquisa e indicadores de variação mensal.

### 3. BUSCA PELO NOME DO CARRO OU PLACA
- A interface deve exibir um campo de busca interativo com filtro por:
  1. **Nome do carro (Marca / Modelo):** busca parcial e insensível a maiúsculas/minúsculas (`ILIKE`) em `nome_marca` e `nome_modelo` (ex.: `"Corolla"`, `"Toyota Corolla"`, `"Gol 1.0"`).
  2. **Placa ou Código FIPE:** aceita formato de placa brasileira (antiga `ABC-1234` ou Mercosul `ABC1D23`) e/ou `codigo_fipe` (`002182-2`). Como a base pública da FIPE é tabelada por modelo e não possui cadastro individual de placas do SENATRAN, quando o usuário digitar uma placa válida, o sistema deve exibir o aviso da placa consultada junto ao filtro de modelo/veículo correspondente (ou permitir vincular a placa na consulta na tela).
- Opcionalmente, seletor de **Ano (`ano_modelo`)** e **Tipo de Veículo (`carro`, `moto`, `caminhão`)** para refinar o resultado na tela.
- **Motivo:** permitir que o usuário encontre rapidamente qualquer veículo entre os `51.003` registros sem travar o navegador.

### 4. EXIBIÇÃO DO RESULTADO NA TELA
- Ao pesquisar, o resultado aparece imediatamente na tela (sem recarregar a página inteira, via requisição local `/api/busca?q=...` ou filtragem dinâmica), exibindo:
  - Marca (`nome_marca`) e Modelo (`nome_modelo`)
  - Código FIPE (`codigo_fipe`), Ano (`ano_modelo` ou `Zero KM`) e Combustível (`sigla_combustivel`)
  - Preço em Setembro (`valor_formatado_set`) e Preço em Outubro (`valor_formatado_out`)
  - Diferença em R$ (`diferenca_reais`) e Variação no Mês (`variacao_mes` com destaque visual: verde para queda/estabilidade ou indicador colorido para alta/baixa).
- Limitar a listagem simultânea na tela (ex.: até 100 resultados por busca) informando a quantidade total encontrada.
- **Motivo:** manter a renderização do HTML rápida e legível mesmo em buscas genéricas (como `"Fiat"` ou `"VW"`).

### 5. EXECUÇÃO E ERRO
- Antes de subir o servidor/gerar o HTML, verifica se o arquivo `fipe.duckdb` e a tabela `refined.fipe_comparacao_set_out` existem.
- Caso não existam: informa qual etapa precisa ser executada antes (`uv run python -m pipeline.transformacao`) e encerra com `sys.exit(1)`.
- `stdout` reconfigurado para `utf-8`.
- Mantém o servidor local ativo (ex.: `http://localhost:8000`), abre o navegador automaticamente e encerra de forma limpa no `Ctrl+C` (fechando a conexão com o banco sem exibir traceback).

---

## CRITÉRIOS DE ACEITE
- Rodar o comando abre a página HTML no navegador com o fundo nas cores azul, verde e amarelo.
- Digitar o nome de um carro (ex.: `"Corolla"` ou `"Civic"`) ou placa/código exibe imediatamente os resultados correspondentes de `refined.fipe_comparacao_set_out` na tela com os preços de setembro, outubro e a variação mensal.
- `Ctrl+C` no terminal encerra o servidor sem traceback e libera o arquivo `fipe.duckdb`.
- Se a tabela `refined.fipe_comparacao_set_out` não existir, o script para com mensagem clara e `sys.exit(1)`.

## ENTREGA
1. A spec como docstring no topo do arquivo, com o motivo de cada regra.
2. O código, comentado só onde a decisão não é óbvia.
3. Uma lista final do que você assumiu e que não estava na spec.

