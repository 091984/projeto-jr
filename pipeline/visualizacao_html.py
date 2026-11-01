"""
SPEC DA VISUALIZAÇÃO HTML (pipeline/visualizacao_html.py)

Regras e motivações:
1. ESCOPO E FONTE DE DADOS:
   Lê exclusivamente de `refined.fipe_comparacao_set_out` no `fipe.duckdb`.
   Nunca escreve em `raw` nem em `refined`.
   Motivo: a camada de visualização apenas consome o dado já tratado na etapa 2.
2. IDENTIDADE VISUAL (CORES DE FUNDO AZUL, VERDE E AMARELO):
   Fundo da página estilizado com as cores azul (#002776), verde (#009C3B) e
   amarelo (#FFDF00), garantindo contraste e legibilidade nos cartões e na tabela.
   Motivo: identidade visual brasileira para consulta da Tabela FIPE.
3. BUSCA PELO NOME DO CARRO OU CÓDIGO FIPE:
   - Busca por nome do carro: filtra por marca e/ou modelo (`nome_marca`, `nome_modelo`)
     de forma parcial e case-insensitive.
   - Busca por código FIPE: filtra por `codigo_fipe` (ex.: `002182-2`).
   Motivo: permitir localizar rapidamente qualquer veículo entre os 51.003
   registros sem travar o navegador.
4. EXIBIÇÃO DO RESULTADO NA TELA:
   Mostra imediatamente na tela (sem recarregar a página) os resultados com:
   Marca, Modelo, Código FIPE, Ano (ou Zero KM), Combustível, Preço Setembro,
   Preço Outubro, Diferença (R$) e Variação no Mês (`variacao_mes`) com destaque
   visual por cor.
   Motivo: conferência visual rápida e comparativa da variação mensal de preços.
5. EXECUÇÃO, SAÍDA E ERRO:
   - Antes de subir o servidor, verifica se `fipe.duckdb` e a tabela
     `refined.fipe_comparacao_set_out` existem; se faltarem, orienta a rodar a
     transformação e encerra com `sys.exit(1)`.
   - Abre o navegador automaticamente, imprime a URL e "Ctrl+C para encerrar"
     (com `stdout` em `utf-8`), e fecha a conexão de forma limpa no `Ctrl+C` sem
     traceback.
"""

import json
import sys
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pipeline.db import PASTA_RAW, conectar

CAMINHO_BANCO = PASTA_RAW.parent / "fipe.duckdb"
PORTA = 8000

HTML_PAGINA = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Consulta Tabela FIPE — Setembro vs Outubro 2026</title>
  <style>
    :root {
      --azul: #002776;
      --verde: #009c3b;
      --amarelo: #ffdf00;
      --branco: #ffffff;
      --cinza-claro: #f4f7fb;
      --texto: #10203a;
    }
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
    }
    body {
      min-height: 100vh;
      background: linear-gradient(135deg, var(--verde) 0%, var(--amarelo) 50%, var(--azul) 100%);
      background-attachment: fixed;
      color: var(--texto);
      padding: 24px 16px;
    }
    .container {
      max-width: 1220px;
      margin: 0 auto;
    }
    header {
      background: linear-gradient(90deg, var(--azul) 0%, #0038a8 65%, var(--verde) 100%);
      color: var(--branco);
      border: 3px solid var(--amarelo);
      border-radius: 14px;
      padding: 22px 26px;
      box-shadow: 0 10px 26px rgba(0, 0, 0, 0.28);
      margin-bottom: 20px;
    }
    header h1 {
      font-size: 1.75rem;
      color: var(--amarelo);
      margin-bottom: 6px;
    }
    header p {
      font-size: 0.96rem;
      opacity: 0.95;
    }
    .painel-busca {
      background: rgba(255, 255, 255, 0.96);
      border-left: 8px solid var(--verde);
      border-right: 8px solid var(--azul);
      border-top: 3px solid var(--amarelo);
      border-radius: 14px;
      padding: 20px;
      box-shadow: 0 8px 22px rgba(0, 0, 0, 0.2);
      margin-bottom: 20px;
    }
    .campos {
      display: grid;
      grid-template-columns: 2fr 1.2fr 1fr auto;
      gap: 12px;
      align-items: end;
    }
    @media (max-width: 860px) {
      .campos {
        grid-template-columns: 1fr;
      }
    }
    .grupo label {
      display: block;
      font-weight: 700;
      font-size: 0.86rem;
      color: var(--azul);
      margin-bottom: 6px;
    }
    .grupo input, .grupo select {
      width: 100%;
      padding: 11px 13px;
      border: 2px solid #cbd5e1;
      border-radius: 8px;
      font-size: 0.96rem;
      outline: none;
      transition: border-color 0.2s;
    }
    .grupo input:focus, .grupo select:focus {
      border-color: var(--verde);
    }
    button.btn-buscar {
      background: linear-gradient(135deg, var(--verde), #007a2f);
      color: var(--branco);
      font-weight: 700;
      border: 2px solid var(--amarelo);
      border-radius: 8px;
      padding: 11px 22px;
      font-size: 0.98rem;
      cursor: pointer;
      transition: transform 0.1s, opacity 0.2s;
    }
    button.btn-buscar:hover {
      opacity: 0.94;
      transform: translateY(-1px);
    }
    .status-barra {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
      margin-top: 14px;
      font-size: 0.9rem;
      color: var(--azul);
      font-weight: 600;
    }
    .badge-placa {
      display: inline-block;
      background: var(--azul);
      color: var(--amarelo);
      border: 2px solid var(--amarelo);
      padding: 4px 12px;
      border-radius: 6px;
      font-weight: 800;
      letter-spacing: 1px;
    }
    .resultados-box {
      background: rgba(255, 255, 255, 0.97);
      border-radius: 14px;
      border-top: 5px solid var(--azul);
      border-bottom: 5px solid var(--verde);
      box-shadow: 0 10px 26px rgba(0, 0, 0, 0.22);
      overflow-x: auto;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      min-width: 900px;
    }
    thead {
      background: var(--azul);
      color: var(--amarelo);
    }
    th, td {
      padding: 12px 14px;
      text-align: left;
      border-bottom: 1px solid #e2e8f0;
      font-size: 0.9rem;
    }
    tbody tr:nth-child(even) {
      background: var(--cinza-claro);
    }
    tbody tr:hover {
      background: #fff9c4;
    }
    .tag-subiu {
      background: #dcfce7;
      color: #166534;
      border: 1px solid #86efac;
      padding: 4px 8px;
      border-radius: 6px;
      font-weight: 700;
      white-space: nowrap;
    }
    .tag-caiu {
      background: #fee2e2;
      color: #991b1b;
      border: 1px solid #fca5a5;
      padding: 4px 8px;
      border-radius: 6px;
      font-weight: 700;
      white-space: nowrap;
    }
    .tag-estavel {
      background: #e0f2fe;
      color: #075985;
      border: 1px solid #7dd3fc;
      padding: 4px 8px;
      border-radius: 6px;
      font-weight: 700;
      white-space: nowrap;
    }
    .vazio {
      padding: 32px;
      text-align: center;
      color: var(--azul);
      font-weight: 600;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>Consulta Tabela FIPE — Comparativo Setembro vs Outubro (2026)</h1>
      <p>Fonte: <strong>refined.fipe_comparacao_set_out</strong> (fipe.duckdb) | Pesquise pelo nome do carro ou código FIPE</p>
    </header>

    <section class="painel-busca">
      <form id="form-busca" onsubmit="executarBusca(event)">
        <div class="campos">
          <div class="grupo">
            <label for="input-carro">Nome do Carro (Marca ou Modelo)</label>
            <input id="input-carro" type="text" placeholder="Ex.: Corolla, Civic, Gol 1.0, Hilux..." />
          </div>
          <div class="grupo">
            <label for="input-codigo">Código FIPE</label>
            <input id="input-codigo" type="text" placeholder="Ex.: 002182-2" />
          </div>
          <div class="grupo">
            <label for="select-tipo">Tipo de Veículo</label>
            <select id="select-tipo">
              <option value="carro">Carros</option>
              <option value="">Todos</option>
              <option value="moto">Motos</option>
              <option value="caminhão">Caminhões</option>
            </select>
          </div>
          <button type="submit" class="btn-buscar">Buscar na FIPE</button>
        </div>
      </form>
      <div class="status-barra">
        <span id="info-resultado">Carregando veículos...</span>
      </div>
    </section>

    <section class="resultados-box">
      <table>
        <thead>
          <tr>
            <th>Tipo</th>
            <th>Cód. FIPE</th>
            <th>Marca</th>
            <th>Modelo</th>
            <th>Ano</th>
            <th>Comb.</th>
            <th>Setembro/2026</th>
            <th>Outubro/2026</th>
            <th>Diferença (R$)</th>
            <th>Variação no Mês</th>
          </tr>
        </thead>
        <tbody id="corpo-tabela">
          <tr><td colspan="10" class="vazio">Digite o nome do carro ou código FIPE acima para consultar.</td></tr>
        </tbody>
      </table>
    </section>
  </div>

  <script>
    function classeVariacao(texto) {
      if (texto.startsWith("Subiu")) return "tag-subiu";
      if (texto.startsWith("Caiu")) return "tag-caiu";
      return "tag-estavel";
    }

    async function executarBusca(event) {
      if (event) event.preventDefault();
      const carro = document.getElementById("input-carro").value.trim();
      const codigo = document.getElementById("input-codigo").value.trim();
      const tipo = document.getElementById("select-tipo").value;

      const params = new URLSearchParams({ carro, codigo, tipo });
      const resp = await fetch("/api/busca?" + params.toString());
      const dados = await resp.json();

      const infoResultado = document.getElementById("info-resultado");
      const tbody = document.getElementById("corpo-tabela");

      infoResultado.textContent = `Exibindo ${dados.itens.length} de ${dados.total_encontrado.toLocaleString("pt-BR")} registro(s) encontrado(s)`;

      if (dados.itens.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="vazio">Nenhum veículo encontrado para os filtros informados.</td></tr>';
        return;
      }

      tbody.innerHTML = dados.itens.map(item => `
        <tr>
          <td>${item.tipo_veiculo}</td>
          <td><strong>${item.codigo_fipe}</strong></td>
          <td>${item.nome_marca}</td>
          <td><strong>${item.nome_modelo}</strong></td>
          <td>${item.zero_km === "true" ? "Zero KM" : (item.ano_modelo || "Zero KM")}</td>
          <td>${item.sigla_combustivel.toUpperCase()}</td>
          <td>${item.valor_formatado_set}</td>
          <td><strong>${item.valor_formatado_out}</strong></td>
          <td>R$ ${Number(item.diferenca_reais).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
          <td><span class="${classeVariacao(item.variacao_mes)}">${item.variacao_mes}</span></td>
        </tr>
      `).join("");
    }

    window.addEventListener("DOMContentLoaded", () => executarBusca());
  </script>
</body>
</html>
"""


def verificar_banco_e_tabela():
    if not CAMINHO_BANCO.is_file():
        print(
            f"Erro: banco '{CAMINHO_BANCO.name}' não encontrado. "
            "Execute antes: uv run python -m pipeline.ingestao && uv run python -m pipeline.transformacao"
        )
        sys.exit(1)

    con = conectar()
    existe = con.execute(
        """
        SELECT count(*)
        FROM information_schema.tables
        WHERE table_schema = 'refined' AND table_name = 'fipe_comparacao_set_out'
        """
    ).fetchone()[0]
    if not existe:
        con.close()
        print(
            "Erro: tabela 'refined.fipe_comparacao_set_out' não encontrada no fipe.duckdb. "
            "Execute antes: uv run python -m pipeline.transformacao"
        )
        sys.exit(1)
    return con


def consultar_veiculos(con, carro: str, codigo: str, tipo: str) -> dict:
    filtros = []
    params = []

    if tipo:
        filtros.append("tipo_veiculo = ?")
        params.append(tipo)

    if carro:
        for termo in carro.split():
            filtros.append("(nome_marca ILIKE ? OR nome_modelo ILIKE ?)")
            params.extend([f"%{termo}%", f"%{termo}%"])

    if codigo:
        filtros.append("codigo_fipe ILIKE ?")
        params.append(f"%{codigo.strip()}%")

    where_sql = f"WHERE {' AND '.join(filtros)}" if filtros else ""

    total_encontrado = con.execute(
        f"SELECT count(*) FROM refined.fipe_comparacao_set_out {where_sql}",
        params,
    ).fetchone()[0]

    linhas = con.execute(
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
            variacao_mes
        FROM refined.fipe_comparacao_set_out
        {where_sql}
        ORDER BY nome_marca, nome_modelo, ano_modelo DESC
        LIMIT 100
        """,
        params,
    ).fetchall()

    colunas = [
        "tipo_veiculo",
        "codigo_fipe",
        "nome_marca",
        "nome_modelo",
        "sigla_combustivel",
        "ano_modelo",
        "zero_km",
        "valor_formatado_set",
        "valor_formatado_out",
        "diferenca_reais",
        "variacao_percentual",
        "variacao_mes",
    ]
    itens = [dict(zip(colunas, linha)) for linha in linhas]

    return {
        "total_encontrado": total_encontrado,
        "itens": itens,
    }


def criar_handler(con):
    class FipeHTMLHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == "/api/busca":
                qs = urllib.parse.parse_qs(parsed.query)
                carro = qs.get("carro", [""])[0]
                codigo = qs.get("codigo", [""])[0]
                tipo = qs.get("tipo", [""])[0]
                resposta = consultar_veiculos(con, carro, codigo, tipo)
                corpo = json.dumps(resposta, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(corpo)))
                self.end_headers()
                self.wfile.write(corpo)
            else:
                corpo = HTML_PAGINA.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(corpo)))
                self.end_headers()
                self.wfile.write(corpo)

        def log_message(self, format, *args):
            # Silencia logs HTTP por requisição para manter o terminal limpo conforme a spec
            pass

    return FipeHTMLHandler


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    con = verificar_banco_e_tabela()
    servidor = HTTPServer(("localhost", PORTA), criar_handler(con))
    url = f"http://localhost:{PORTA}"

    print(f"Visualização HTML da FIPE disponível em: {url}")
    print("Ctrl+C para encerrar")
    webbrowser.open(url)

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()
        con.close()


if __name__ == "__main__":
    main()

