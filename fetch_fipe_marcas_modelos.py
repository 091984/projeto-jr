import csv
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = "https://fipe.api.br/api/v2/cars"
OUTPUT_CSV = Path("marcas_modelos_fipe.csv")


def fetch_json(url: str) -> tuple[list | dict, dict]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
    )
    while True:
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                headers = {k.lower(): v for k, v in resp.headers.items()}
                data = json.loads(resp.read().decode("utf-8"))
                return data, headers
        except urllib.error.HTTPError as e:
            if e.code == 429:
                reset_ts = int(e.headers.get("x-throttle-reset", 0))
                wait_sec = max(reset_ts - int(time.time()) + 1, 5)
                print(f"Rate limit (429) atingido. Aguardando {wait_sec}s...")
                time.sleep(wait_sec)
            else:
                raise


def main() -> None:
    print("Buscando marcas...")
    brands, headers = fetch_json(f"{BASE_URL}/brands")
    print(f"Total de marcas encontradas: {len(brands)}")

    rows: list[dict[str, str]] = []

    for idx, brand in enumerate(brands, start=1):
        brand_code = str(brand["code"])
        brand_name = str(brand["name"])

        models, headers = fetch_json(f"{BASE_URL}/brands/{brand_code}/models")
        for model in models:
            rows.append(
                {
                    "brand_code": brand_code,
                    "brand_name": brand_name,
                    "model_code": str(model["code"]),
                    "model_name": str(model["name"]),
                }
            )

        remaining = int(headers.get("x-throttle-remaining", 10))
        reset_ts = int(headers.get("x-throttle-reset", 0))
        print(
            f"[{idx}/{len(brands)}] Marca: {brand_name} ({len(models)} modelos) "
            f"| Throttle restante: {remaining}"
        )

        if remaining <= 1 and idx < len(brands):
            wait_sec = max(reset_ts - int(time.time()) + 1, 2)
            print(f"Aguardando reset da janela de throttle ({wait_sec}s)...")
            time.sleep(wait_sec)

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["brand_code", "brand_name", "model_code", "model_name"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nConcluído! {len(rows)} modelos salvos em '{OUTPUT_CSV.resolve()}'.")


if __name__ == "__main__":
    main()

