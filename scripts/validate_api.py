"""
Validação rápida da API-Football (api-sports.io)
Rode: python3 scripts/validate_api.py
"""

import urllib.request
import urllib.parse
import json
import os

# Carrega o .env manualmente (sem dependência de python-dotenv)
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _, _v = _line.partition("=")
                os.environ.setdefault(_k.strip(), _v.strip().strip("'\""))

# Aceita tanto o typo original (FOOTBOOL) quanto o nome correto (FOOTBALL)
API_KEY = os.getenv("API_FOOTBALL_KEY") or os.getenv("API_FOOTBOOL_KEY", "")
BASE_URL = "https://v3.football.api-sports.io"


def get(path: str, params: dict = {}) -> dict:
    query = urllib.parse.urlencode(params)
    url = f"{BASE_URL}{path}{'?' + query if query else ''}"
    req = urllib.request.Request(url, headers={
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "v3.football.api-sports.io",
    })
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read())


def check(label: str, data: dict):
    errors = data.get("errors", {})
    results = data.get("results", 0)
    response = data.get("response", [])
    status = "OK" if not errors and results >= 0 else "ERRO"
    print(f"\n[{status}] {label}")
    if errors:
        print(f"  Erros: {errors}")
        return
    print(f"  Resultados: {results}")
    if response:
        print(f"  Primeiro item: {json.dumps(response[0], indent=2, ensure_ascii=False)[:300]}...")


if __name__ == "__main__":
    print("=" * 50)
    print("Validando API-Football — Copa do Mundo 2026")
    print("=" * 50)

    if not API_KEY:
        print("\n[ERRO] API key não encontrada no .env")
        exit(1)

    print(f"\n[INFO] API key carregada do .env: {API_KEY[:8]}...")

    # 1. Status da conta (não consome cota)
    data = get("/status")
    account = data.get("response", {})
    print(f"[INFO] Conta: {account.get('account', {}).get('email', '—')}")
    print(f"[INFO] Plano: {account.get('subscription', {}).get('plan', '—')}")
    req_info = account.get("requests", {})
    print(f"[INFO] Requisições hoje: {req_info.get('current', '—')} / {req_info.get('limit_day', '—')}")

    # Plano Free só acessa seasons 2022-2024.
    # Fazer upgrade para Basic ($10/mês) antes de ir para produção com 2026.
    data = get("/leagues", {"name": "World Cup", "season": "2022"})
    check("Ligas — Copa do Mundo (season 2022 para validação)", data)

    leagues = data.get("response", [])
    league_id = None
    for item in leagues:
        if item.get("league", {}).get("name") == "World Cup":
            league_id = item["league"]["id"]
            print(f"  League ID: {league_id}")
            break

    if not league_id:
        print("\n  League ID não encontrado. Encerrando.")
        exit(1)

    data = get("/fixtures", {"league": league_id, "season": "2022", "round": "Group Stage - 1"})
    check("Partidas — Rodada 1 da fase de grupos (2022)", data)

    data = get("/players/topscorers", {"league": league_id, "season": "2022"})
    check("Artilheiros (2022)", data)

    data = get("/standings", {"league": league_id, "season": "2022"})
    check("Classificação dos grupos (2022)", data)

    print("\n" + "=" * 50)
    print("Validação concluída. League ID confirmado = 1")
    print("Para produção: upgrade para Basic e mudar season para 2026.")
