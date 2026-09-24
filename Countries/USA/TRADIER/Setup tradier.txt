"""One-off: write tradier_accounts.json beside this script.

SANDBOX is paper money (100,000 virtual, 15-minute delayed quotes).
USA_PHC is REAL money - orders there are live.
"""
import json, pathlib

ACCOUNTS = {
    "SANDBOX": {
        "env": "sandbox",
        "account": "VA75673164",
        "token": "ixKKJK0IFC7p8fuDOX6bj8n7CFQF",
    },
    "USA_PHC": {
        "env": "production",
        "account": "6YB92742",
        "token": "gMvpmPwKTqbrPJ89LLWis0yikyWP",
    },
    "USA_PHA": {
        "env": "production",
        "account": "6YB90990",
        "token": "gMvpmPwKTqbrPJ89LLWis0yikyWP",
    },
    "USA_PHE": {
        "env": "production",
        "account": "6YB90994",
        "token": "gMvpmPwKTqbrPJ89LLWis0yikyWP",
    },
    "USA_PCF": {
        "env": "production",
        "account": "6YB92716",
        "token": "gMvpmPwKTqbrPJ89LLWis0yikyWP",
    },
    "USA_PHIC": {
        "env": "production",
        "account": "6YB89227",
        "token": "gMvpmPwKTqbrPJ89LLWis0yikyWP",
    },
    "USA_PROPERTIES": {
        "env": "production",
        "account": "6YB91149",
        "token": "gMvpmPwKTqbrPJ89LLWis0yikyWP",
    },
    "USA_AEROSPACE": {
        "env": "production",
        "account": "6YB92272",
        "token": "gMvpmPwKTqbrPJ89LLWis0yikyWP",
    },
}

p = pathlib.Path(__file__).with_name('tradier_accounts.json')
p.write_text(json.dumps(ACCOUNTS, indent=2))
try:
    p.chmod(0o600)
except Exception:
    pass
print("wrote", p)
for n, a in ACCOUNTS.items():
    flag = "  <-- REAL MONEY" if a['env'] == 'production' else ""
    print(f"  {n:<10} {a['env']:<11} {a['account']}{flag}")
