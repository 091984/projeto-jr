# Documentação Resumida — FIPE API v2

Resumo dos principais tópicos para consumo da API REST da Tabela FIPE (`fipe.api.br`).

---

## 1. Visão Geral

- **Base URL:** `https://fipe.api.br/api/v2`
- **Formato de resposta:** JSON (`application/json; charset=utf-8`)
- **Tipos de veículos (`{vehicleType}`):**
  - `cars` — Carros e utilitários pequenos (código `1`)
  - `motorcycles` — Motos (código `2`)
  - `trucks` — Caminhões e micro-ônibus (código `3`)

---

## 2. Principais Endpoints

| Método | Endpoint | Descrição |
| :--- | :--- | :--- |
| `GET` | `/references` | Lista os meses de referência disponíveis na FIPE (`code`, `month`). |
| `GET` | `/{vehicleType}/brands` | Lista todas as marcas do tipo de veículo (`code`, `name`). |
| `GET` | `/{vehicleType}/brands/{brandId}/models` | Lista todos os modelos de uma marca (`code`, `name`). |
| `GET` | `/{vehicleType}/brands/{brandId}/models/{modelId}/years` | Lista os anos/combustíveis disponíveis para um modelo (`code`, `name`). |
| `GET` | `/{vehicleType}/brands/{brandId}/models/{modelId}/years/{yearId}` | Retorna o preço e os dados completos FIPE do veículo. |
| `GET` | `/{vehicleType}/{fipeCode}/years` | Lista os anos disponíveis diretamente pelo código FIPE (ex.: `002182-2`). |
| `GET` | `/{vehicleType}/{fipeCode}/years/{yearId}` | Consulta preço e detalhes usando o código FIPE e o ano. |

> **Parâmetro opcional:** Todos os endpoints aceitam `?reference={code}` na query string para consultar valores de uma tabela de referência histórica específica.

---

## 3. Exemplo Prático de Consulta

### Requisição
```bash
curl https://fipe.api.br/api/v2/cars/brands/56/models/9984/years/2025-6
```
- `cars`: Tipo do veículo (Carros)
- `56`: Código da marca (**Toyota**)
- `9984`: Código do modelo (**Corolla Altis 1.8 16V Aut. (Híbrido)**)
- `2025-6`: Código do ano/combustível (`2025` Híbrido)

### Resposta (JSON)
```json
{
  "vehicleType": 1,
  "price": "R$ 173.645,00",
  "brand": "Toyota",
  "model": "Corolla Altis 1.8 16V Aut. (Híbrido)",
  "modelYear": 2025,
  "fuel": "Híbrido",
  "codeFipe": "002182-2",
  "referenceMonth": "outubro de 2026",
  "fuelAcronym": "H"
}
```

---

## 4. Limites de Requisição (Rate Limit & Throttling)

A API controla o tráfego através dos seguintes cabeçalhos HTTP de resposta:

- **Limite por minuto (Throttling):**
  - `x-throttle-limit`: `50` requisições por minuto.
  - `x-throttle-remaining`: Requisições restantes na janela atual de 1 minuto.
  - `x-throttle-reset`: Timestamp Unix de quando a janela de 1 minuto será reiniciada.
- **Limite diário (Rate Limit):**
  - `x-ratelimit-limit`: `500` requisições por dia (plano gratuito sem token) ou até `1000+` com token.
  - `x-ratelimit-remaining`: Requisições restantes no dia.
  - `x-ratelimit-reset`: Tempo restante (em segundos) para o reset diário.
- **Autenticação opcional:**
  - Envie o header `X-Subscription-Token: SEU_TOKEN` caso possua um token cadastrado para ampliar a cota diária.

---

## 5. Arquivos Locais Gerados no Projeto

- **`marcas_modelos_fipe.csv`**: Tabela CSV local contendo todas as **108 marcas** e **7.386 modelos** de carros (`brand_code`, `brand_name`, `model_code`, `model_name`).
- **`fetch_fipe_marcas_modelos.py`**: Script Python que percorre todas as marcas na API respeitando automaticamente o limite de *throttling* (`x-throttle-remaining` / HTTP `429`) e salva o CSV local.

