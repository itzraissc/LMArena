"""
start.py - Wrapper de inicialização do LMArenaBridge para HF Spaces
- Gera config.json a partir da variável de ambiente AUTH_TOKEN
- Inicia Xvfb (display virtual necessário para o Camoufox)
- Lança uvicorn na porta 7860 (porta obrigatória do HF Spaces)
"""

import os
import sys
import json
import subprocess
import time
import signal
import importlib.util

# ── 1. Validar AUTH_TOKEN ──────────────────────────────────
auth_token = os.environ.get("AUTH_TOKEN", "").strip()

if not auth_token:
    print("=" * 65)
    print("ERRO: Variável de ambiente AUTH_TOKEN não foi definida!")
    print()
    print("Como obter o token:")
    print("  1. Acesse https://lmarena.ai e envie uma mensagem qualquer")
    print("  2. Abra DevTools (F12) → aba Application → Cookies")
    print("  3. Encontre o cookie chamado 'arena-auth-prod-v1'")
    print("  4. Copie o valor dele (começa com 'ey...')")
    print()
    print("Como definir no Hugging Face Spaces:")
    print("  Acesse seu Space → Settings → Variables and secrets")
    print("  Clique em 'New secret'")
    print("  Nome: AUTH_TOKEN")
    print("  Valor: <cole o token aqui>")
    print("=" * 65)
    sys.exit(1)

# ── 2. Gerar config.json ───────────────────────────────────
config_path = os.path.join("/app", "config.json")
config = {"auth_token": auth_token}

with open(config_path, "w") as f:
    json.dump(config, f, indent=2)

print(f"[OK] config.json gerado em {config_path}")

# ── 3. Iniciar display virtual (Xvfb) ─────────────────────
# O Camoufox (Firefox headless modificado) precisa de um display,
# mesmo em ambiente sem tela (servidor/container)
print("[...] Iniciando Xvfb (display virtual)...")

xvfb_proc = subprocess.Popen(
    ["Xvfb", ":99", "-screen", "0", "1280x720x24", "-ac"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

time.sleep(2)  # aguarda o Xvfb inicializar
os.environ["DISPLAY"] = ":99"
print(f"[OK] Xvfb iniciado (PID {xvfb_proc.pid})")


def cleanup(sig, frame):
    """Encerramento limpo ao receber SIGTERM/SIGINT."""
    print("\n[...] Encerrando processos...")
    xvfb_proc.terminate()
    sys.exit(0)


signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)

# ── 4. Iniciar o servidor na porta 7860 ───────────────────
print("[...] Iniciando LMArenaBridge...")
print("[OK] API endpoint: http://0.0.0.0:7860/api/v1")
print("[OK] Modelos disponíveis: http://0.0.0.0:7860/api/v1/models")
print()

# Adiciona o diretório raiz ao Python path
app_root = "/app"
if app_root not in sys.path:
    sys.path.insert(0, app_root)

import uvicorn

# Tentativa 1: importar via string de módulo (modo canônico do uvicorn)
try:
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=7860,
        log_level="info",
    )
except Exception as e_str:
    print(f"[WARN] Falha ao importar 'src.main:app' via string: {e_str}")
    print("[...] Tentando importação direta do módulo...")

    # Tentativa 2: importar o arquivo diretamente e pegar o objeto 'app'
    main_path = "/app/src/main.py"
    try:
        spec = importlib.util.spec_from_file_location("lmarena_main", main_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["lmarena_main"] = module
        spec.loader.exec_module(module)

        app_obj = getattr(module, "app", None)
        if app_obj is None:
            raise AttributeError("Objeto 'app' não encontrado em src/main.py")

        uvicorn.run(app_obj, host="0.0.0.0", port=7860, log_level="info")

    except Exception as e_direct:
        print(f"[ERRO] Falha ao iniciar o servidor: {e_direct}")
        print()
        print("Possíveis causas:")
        print("  - O arquivo src/main.py foi renomeado ou movido")
        print("  - O objeto 'app' tem outro nome no código-fonte")
        print("  - Dependência não instalada (cheque requirements.txt)")
        xvfb_proc.terminate()
        sys.exit(1)
