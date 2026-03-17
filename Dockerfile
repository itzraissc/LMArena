# ============================================================
# LMArenaBridge - Dockerfile para Hugging Face Spaces
# Porta: 7860 (padrão HF Spaces)
# Auth: variável de ambiente AUTH_TOKEN (definida nas Settings)
# ============================================================

FROM python:3.11-slim

# HF Spaces exige que o app escute na porta 7860
EXPOSE 7860

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DISPLAY=:99 \
    APP_DIR=/app

# ── Dependências de sistema ────────────────────────────────
# Camoufox (browser headless) precisa de libs gráficas e Xvfb
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    wget \
    ca-certificates \
    xvfb \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    libnss3 \
    libnspr4 \
    libasound2 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    libxkbcommon0 \
    fonts-liberation \
    fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

# ── Clonar repositório ─────────────────────────────────────
WORKDIR ${APP_DIR}
RUN git clone --depth=1 https://github.com/CloudWaddie/LMArenaBridge.git . \
    && echo "Repositorio clonado com sucesso."

# ── Dependências Python ────────────────────────────────────
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt \
    && echo "requirements.txt instalado."

# ── Camoufox: baixar binários do browser ──────────────────
RUN pip install camoufox \
    && python -m camoufox fetch \
    && echo "Camoufox instalado."

# ── Script de inicialização ────────────────────────────────
COPY start.py /app/start.py

# ── Usuário não-root (segurança + compatibilidade HF) ─────
RUN useradd -m -u 1000 user \
    && chown -R user:user /app
USER user

# ── Healthcheck ────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=15s --start-period=90s --retries=3 \
    CMD curl -sf http://localhost:7860/api/v1/models > /dev/null \
     || curl -sf http://localhost:7860/health > /dev/null \
     || curl -sf http://localhost:7860/ > /dev/null

# ── Iniciar ────────────────────────────────────────────────
CMD ["python", "/app/start.py"]
