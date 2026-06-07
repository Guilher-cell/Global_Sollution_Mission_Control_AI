from dataclasses import dataclass, field
from typing import List


# ─── Thresholds operacionais ───────────────────────────────────────────────────
THRESHOLD = {
    # Drift do oscilador atômico (nanosegundos)
    "drift_oscilador_critico":   10.0,   # acima → sinal GNSS inutilizável
    "drift_oscilador_alerta":    5.0,    # acima → precisão degradada

    # Sincronização com a constelação (%)
    "sincronizacao_critica":     80.0,   # abaixo → satélite isolado
    "sincronizacao_alerta":      95.0,   # abaixo → risco de desincronização

    # Integridade do sinal L1/L5 (%)
    "integridade_critica":       70.0,   # abaixo → sinal não confiável
    "integridade_alerta":        90.0,   # abaixo → qualidade reduzida

    # Precisão da efeméride (metros)
    "efemeride_critica":         2.0,    # acima → posicionamento inaceitável
    "efemeride_alerta":          0.8,    # acima → precisão comprometida

    # Margem de potência dos painéis solares (%)
    "potencia_critica":          20.0,   # abaixo → modo emergência
    "potencia_alerta":           40.0,   # abaixo → reduzir carga
}

SEVERIDADES = ["NORMAL", "ALERTA", "CRÍTICO"]


@dataclass
class Alerta:
    parametro: str
    severidade: str      # "ALERTA" ou "CRÍTICO"
    valor_atual: float
    threshold: float
    unidade: str
    descricao: str
    impacto_terrestre: str
    acao_automatizada: str = ""


@dataclass
class ResultadoAvaliacao:
    alertas: List[Alerta] = field(default_factory=list)
    severidade_geral: str = "NORMAL"
    acoes_executadas: List[str] = field(default_factory=list)

    def tem_critico(self) -> bool:
        return any(a.severidade == "CRÍTICO" for a in self.alertas)

    def tem_alerta(self) -> bool:
        return any(a.severidade == "ALERTA" for a in self.alertas)


def _checar_drift_oscilador(valor: float) -> Alerta | None:
    """Verifica o drift do oscilador atômico (coração do GNSS)."""
    if valor > THRESHOLD["drift_oscilador_critico"]:
        return Alerta(
            parametro="Drift do Oscilador Atômico",
            severidade="CRÍTICO",
            valor_atual=valor,
            threshold=THRESHOLD["drift_oscilador_critico"],
            unidade="ns",
            descricao=f"Drift de {valor:.3f} ns — acima do limite crítico de {THRESHOLD['drift_oscilador_critico']} ns.",
            impacto_terrestre=(
                "Erro de posicionamento acima de 3 metros. Frotas logísticas perdem rastreamento confiável, "
                "drones de precisão agrícola ficam fora de operação, e sistemas de veículos autônomos "
                "podem acionar parada de emergência."
            ),
            acao_automatizada="🔧 AÇÃO: Iniciando recalibração do oscilador via uplink de controle.",
        )
    if valor > THRESHOLD["drift_oscilador_alerta"]:
        return Alerta(
            parametro="Drift do Oscilador Atômico",
            severidade="ALERTA",
            valor_atual=valor,
            threshold=THRESHOLD["drift_oscilador_alerta"],
            unidade="ns",
            descricao=f"Drift de {valor:.3f} ns — acima do limite de alerta de {THRESHOLD['drift_oscilador_alerta']} ns.",
            impacto_terrestre=(
                "Precisão de posicionamento reduzida para sub-métrica. Agricultura de precisão pode "
                "apresentar sobreposição de tratamento. Monitorar evolução."
            ),
        )
    return None


def _checar_sincronizacao(valor: float) -> Alerta | None:
    """Verifica sincronização com a constelação GNSS."""
    if valor < THRESHOLD["sincronizacao_critica"]:
        return Alerta(
            parametro="Sincronização com Constelação",
            severidade="CRÍTICO",
            valor_atual=valor,
            threshold=THRESHOLD["sincronizacao_critica"],
            unidade="%",
            descricao=f"Sincronização em {valor:.2f}% — abaixo do mínimo crítico de {THRESHOLD['sincronizacao_critica']}%.",
            impacto_terrestre=(
                "Satélite operando de forma isolada. Receptores terrestres podem perder sinal de navegação "
                "em regiões que dependem deste satélite para cobertura. Operadores de frota afetados."
            ),
            acao_automatizada="🔧 AÇÃO: Ativando protocolo de re-sincronização de emergência com satélites vizinhos.",
        )
    if valor < THRESHOLD["sincronizacao_alerta"]:
        return Alerta(
            parametro="Sincronização com Constelação",
            severidade="ALERTA",
            valor_atual=valor,
            threshold=THRESHOLD["sincronizacao_alerta"],
            unidade="%",
            descricao=f"Sincronização em {valor:.2f}% — abaixo do limite de alerta de {THRESHOLD['sincronizacao_alerta']}%.",
            impacto_terrestre=(
                "Qualidade do posicionamento reduzida em até 15% na área de cobertura deste satélite. "
                "Aplicações de precisão centimétrica serão afetadas primeiro."
            ),
        )
    return None


def _checar_integridade_sinal(valor: float) -> Alerta | None:
    """Verifica a integridade do sinal L1/L5."""
    if valor < THRESHOLD["integridade_critica"]:
        return Alerta(
            parametro="Integridade do Sinal L1/L5",
            severidade="CRÍTICO",
            valor_atual=valor,
            threshold=THRESHOLD["integridade_critica"],
            unidade="%",
            descricao=f"Integridade em {valor:.2f}% — abaixo do mínimo crítico de {THRESHOLD['integridade_critica']}%.",
            impacto_terrestre=(
                "Sinal não confiável para aplicações de segurança crítica. Aviação civil e operações de "
                "resgate que usam GNSS de precisão devem recorrer a sistemas de backup imediatamente."
            ),
            acao_automatizada="🔧 AÇÃO: Emitindo NANU (Notice Advisory to NAVSTAR Users) — alertando receptores terrestres.",
        )
    if valor < THRESHOLD["integridade_alerta"]:
        return Alerta(
            parametro="Integridade do Sinal L1/L5",
            severidade="ALERTA",
            valor_atual=valor,
            threshold=THRESHOLD["integridade_alerta"],
            unidade="%",
            descricao=f"Integridade em {valor:.2f}% — abaixo do limite de alerta de {THRESHOLD['integridade_alerta']}%.",
            impacto_terrestre=(
                "Qualidade de rastreamento reduzida para aplicações de logística. "
                "Plantadeiras autônomas podem precisar de correção diferencial adicional."
            ),
        )
    return None


def _checar_efemeride(valor: float) -> Alerta | None:
    """Verifica a precisão da efeméride (predição de posição orbital)."""
    if valor > THRESHOLD["efemeride_critica"]:
        return Alerta(
            parametro="Precisão da Efeméride",
            severidade="CRÍTICO",
            valor_atual=valor,
            threshold=THRESHOLD["efemeride_critica"],
            unidade="m",
            descricao=f"Erro de efeméride em {valor:.3f} m — acima do crítico de {THRESHOLD['efemeride_critica']} m.",
            impacto_terrestre=(
                "Erro de posicionamento acumulado inaceitável para aplicações de precisão. "
                "Veículos autônomos em teste com este sinal devem pausar operação. "
                "Upload de efeméride corrigida é urgente."
            ),
            acao_automatizada="🔧 AÇÃO: Solicitando upload de efeméride corrigida ao segmento de controle.",
        )
    if valor > THRESHOLD["efemeride_alerta"]:
        return Alerta(
            parametro="Precisão da Efeméride",
            severidade="ALERTA",
            valor_atual=valor,
            threshold=THRESHOLD["efemeride_alerta"],
            unidade="m",
            descricao=f"Erro de efeméride em {valor:.3f} m — acima do alerta de {THRESHOLD['efemeride_alerta']} m.",
            impacto_terrestre=(
                "Posicionamento sub-métrico comprometido. Agricultura de precisão centimétrica "
                "pode precisar de correção RTK adicional nesta janela."
            ),
        )
    return None


def _checar_potencia(valor: float) -> Alerta | None:
    """Verifica a margem de potência dos painéis solares."""
    if valor < THRESHOLD["potencia_critica"]:
        return Alerta(
            parametro="Margem de Potência",
            severidade="CRÍTICO",
            valor_atual=valor,
            threshold=THRESHOLD["potencia_critica"],
            unidade="%",
            descricao=f"Potência em {valor:.2f}% — abaixo do mínimo crítico de {THRESHOLD['potencia_critica']}%.",
            impacto_terrestre=(
                "Risco de interrupção total do serviço GNSS neste satélite. Se o satélite entrar em "
                "modo de sobrevivência, receptores na faixa de cobertura perderão sinal. "
                "Operadores de frota e usuários de navegação serão afetados diretamente."
            ),
            acao_automatizada=(
                "🔧 AÇÃO: Ativando MODO DE ECONOMIA DE ENERGIA — desligando transponders secundários. "
                "Redirecionando painéis solares para posição de máxima captação."
            ),
        )
    if valor < THRESHOLD["potencia_alerta"]:
        return Alerta(
            parametro="Margem de Potência",
            severidade="ALERTA",
            valor_atual=valor,
            threshold=THRESHOLD["potencia_alerta"],
            unidade="%",
            descricao=f"Potência em {valor:.2f}% — abaixo do alerta de {THRESHOLD['potencia_alerta']}%.",
            impacto_terrestre=(
                "Satélite próximo de zona de risco energético. Redução de carga não essencial "
                "recomendada para preservar missão principal de navegação."
            ),
        )
    return None


def avaliar(dados: dict) -> ResultadoAvaliacao:
    """
    Avalia todos os parâmetros de telemetria e retorna alertas e ações automáticas.
    Toda a lógica de decisão é Python — não depende da IA.
    """
    resultado = ResultadoAvaliacao()

    # Executa todas as verificações
    verificacoes = [
        _checar_drift_oscilador(dados["drift_oscilador_ns"]),
        _checar_sincronizacao(dados["sincronizacao_pct"]),
        _checar_integridade_sinal(dados["integridade_sinal"]),
        _checar_efemeride(dados["precisao_efemeride_m"]),
        _checar_potencia(dados["margem_potencia_pct"]),
    ]

    for alerta in verificacoes:
        if alerta is not None:
            resultado.alertas.append(alerta)
            if alerta.acao_automatizada:
                resultado.acoes_executadas.append(alerta.acao_automatizada)

    # Define severidade geral
    if resultado.tem_critico():
        resultado.severidade_geral = "CRÍTICO"
    elif resultado.tem_alerta():
        resultado.severidade_geral = "ALERTA"
    else:
        resultado.severidade_geral = "NORMAL"

    return resultado


def formatar_alertas(resultado: ResultadoAvaliacao) -> str:
    """Formata os alertas para exibição no terminal."""
    if not resultado.alertas:
        return "✅ Todos os parâmetros dentro dos limites operacionais normais."

    linhas = []
    for a in resultado.alertas:
        emoji = "🚨" if a.severidade == "CRÍTICO" else "⚠️"
        linhas.append(f"{emoji} [{a.severidade}] {a.parametro}: {a.valor_atual} {a.unidade}")
        linhas.append(f"   └─ {a.descricao}")
        if a.acao_automatizada:
            linhas.append(f"   └─ {a.acao_automatizada}")
    return "\n".join(linhas)
