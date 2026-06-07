"""
src/telemetria.py
Simulação de telemetria para satélite GNSS (MobilitySat).
Parâmetros baseados em sistemas reais como GPS Block III e Galileo.
"""

import random
import time
from datetime import datetime


# ─── Faixas operacionais normais ───────────────────────────────────────────────
FAIXAS_NORMAIS = {
    "drift_oscilador_ns":   (0.0, 5.0),      # desvio do oscilador atômico em nanosegundos
    "sincronizacao_pct":    (97.0, 100.0),   # sincronização com a constelação em %
    "integridade_sinal":    (90.0, 100.0),   # integridade do sinal L1/L5 em %
    "precisao_efemeride_m": (0.01, 0.5),     # erro de efeméride em metros
    "margem_potencia_pct":  (40.0, 100.0),   # margem de potência dos painéis solares em %
}

# ─── Estado interno do ciclo de simulação ──────────────────────────────────────
_ciclo = 0
_modo_degradado = False  # ativado automaticamente quando energia crítica


def _valor_com_drift(chave: str, forca_anomalia: bool = False) -> float:
    """Gera valor simulado com drift gradual e possibilidade de anomalia."""
    global _ciclo, _modo_degradado

    baixo, alto = FAIXAS_NORMAIS[chave]

    if forca_anomalia:
        # Força valores fora da faixa normal para testes
        if chave == "drift_oscilador_ns":
            return round(random.uniform(15.0, 30.0), 3)
        if chave == "sincronizacao_pct":
            return round(random.uniform(60.0, 80.0), 2)
        if chave == "integridade_sinal":
            return round(random.uniform(55.0, 75.0), 2)
        if chave == "precisao_efemeride_m":
            return round(random.uniform(2.0, 8.0), 3)
        if chave == "margem_potencia_pct":
            return round(random.uniform(5.0, 18.0), 2)

    # Deriva gradual a cada ciclo (simula desgaste realista)
    fator_drift = (_ciclo % 20) * 0.02

    if chave == "drift_oscilador_ns":
        base = random.gauss(2.0 + fator_drift, 0.8)
        return round(max(0.0, base), 3)

    if chave == "sincronizacao_pct":
        base = random.gauss(99.0 - fator_drift * 0.5, 0.5)
        return round(min(100.0, max(0.0, base)), 2)

    if chave == "integridade_sinal":
        base = random.gauss(97.0 - fator_drift * 0.3, 1.0)
        if _modo_degradado:
            base -= 10.0
        return round(min(100.0, max(0.0, base)), 2)

    if chave == "precisao_efemeride_m":
        base = random.gauss(0.15 + fator_drift * 0.05, 0.05)
        return round(max(0.01, base), 3)

    if chave == "margem_potencia_pct":
        base = random.gauss(75.0 - fator_drift * 1.5, 5.0)
        return round(min(100.0, max(0.0, base)), 2)

    return round(random.uniform(baixo, alto), 3)


def coletar(anomalia: bool = False) -> dict:
    """
    Coleta leitura atual da telemetria do satélite GNSS.

    Args:
        anomalia: Se True, força valores críticos para teste de alertas.

    Returns:
        Dicionário com todos os parâmetros de telemetria e metadados.
    """
    global _ciclo, _modo_degradado

    _ciclo += 1

    dados = {
        "ciclo":                _ciclo,
        "timestamp":            datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "drift_oscilador_ns":   _valor_com_drift("drift_oscilador_ns", anomalia),
        "sincronizacao_pct":    _valor_com_drift("sincronizacao_pct", anomalia),
        "integridade_sinal":    _valor_com_drift("integridade_sinal", anomalia),
        "precisao_efemeride_m": _valor_com_drift("precisao_efemeride_m", anomalia),
        "margem_potencia_pct":  _valor_com_drift("margem_potencia_pct", anomalia),
        "modo_degradado":       _modo_degradado,
    }

    # Ativa modo degradado automaticamente se energia crítica
    if dados["margem_potencia_pct"] < 20.0:
        _modo_degradado = True
        dados["modo_degradado"] = True
    elif dados["margem_potencia_pct"] > 35.0:
        _modo_degradado = False
        dados["modo_degradado"] = False

    return dados


def formatar_para_exibicao(dados: dict) -> str:
    """Formata os dados de telemetria para exibição no terminal."""
    icone_potencia = "🔋" if dados["margem_potencia_pct"] > 40 else "⚠️"
    icone_sinal    = "📡" if dados["integridade_sinal"] > 90 else "⚠️"
    icone_drift    = "⏱️" if dados["drift_oscilador_ns"] < 5 else "🚨"
    modo_str       = " [MODO DEGRADADO ATIVO]" if dados["modo_degradado"] else ""

    return (
        f"┌─ TELEMETRIA GNSS — Ciclo #{dados['ciclo']} — {dados['timestamp']}{modo_str}\n"
        f"│  {icone_drift}  Drift oscilador atômico : {dados['drift_oscilador_ns']:.3f} ns\n"
        f"│  🔗  Sincronização constelação: {dados['sincronizacao_pct']:.2f} %\n"
        f"│  {icone_sinal}  Integridade sinal L1/L5 : {dados['integridade_sinal']:.2f} %\n"
        f"│  🗺️   Precisão de efeméride   : {dados['precisao_efemeride_m']:.3f} m\n"
        f"│  {icone_potencia}  Margem de potência      : {dados['margem_potencia_pct']:.2f} %\n"
        f"└──────────────────────────────────────────────────────"
    )
