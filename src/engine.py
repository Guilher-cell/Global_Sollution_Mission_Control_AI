import os
from ollama import Client
from dotenv import load_dotenv
from pathlib import Path
from collections import deque

from src import telemetria as tel
from src import alertas as alr

load_dotenv()

# ─── Identificação da trilha ───────────────────────────────────────────────────
TRILHA = "mobilitysat"

# ─── Cliente Ollama Cloud ──────────────────────────────────────────────────────
client = Client(
    host="https://ollama.com",
    headers={"Authorization": "Bearer " + os.environ.get("OLLAMA_API_KEY", "")},
)


def llm(prompt: str, system: str = None, max_tokens: int = 900, temperature: float = 0.3) -> str:
    """
    Ponto único de contato com o modelo gpt-oss:120b via Ollama Cloud.
    Suporta system prompt separado para maior controle do comportamento.
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        resposta = client.chat(
            model="gpt-oss:120b",
            messages=messages,
            options={"num_predict": max_tokens, "temperature": temperature},
            stream=False,
        )
        return resposta["message"]["content"].strip()
    except Exception as e:
        return f"⚠️ Erro ao consultar IA: {e}"


def load_system_prompt() -> str:
    """Lê o system prompt do arquivo prompts/system_prompt.md."""
    path = Path("prompts/system_prompt.md")
    if path.exists():
        return path.read_text(encoding="utf-8")
    return "Você é um assistente de monitoramento de satélite GNSS."  # fallback


# ─── MissionEngine ─────────────────────────────────────────────────────────────
class MissionEngine:
    """
    Motor central da Mission Control AI.
    Gerencia telemetria, alertas, histórico de contexto e integração com a IA.
    """

    def __init__(self):
        self.trilha = TRILHA
        self.system_prompt = load_system_prompt()

        # Diferencial: memória de contexto — mantém os últimos 5 ciclos
        self._historico: deque = deque(maxlen=5)

        # Último snapshot de dados para uso no /status
        self._ultimo_dados: dict = {}
        self._ultimo_resultado: alr.ResultadoAvaliacao = alr.ResultadoAvaliacao()

        # Força anomalia no próximo ciclo (ativado via comando /simular)
        self._forcar_anomalia: bool = False

    def is_ready(self) -> bool:
        return True

    def _coletar_e_avaliar(self) -> tuple[dict, alr.ResultadoAvaliacao]:
        """Coleta telemetria e avalia alertas. Armazena no histórico."""
        dados = tel.coletar(anomalia=self._forcar_anomalia)
        self._forcar_anomalia = False  # reset após uso

        resultado = alr.avaliar(dados)

        # Registra no histórico de contexto
        entrada_historico = {
            "ciclo": dados["ciclo"],
            "timestamp": dados["timestamp"],
            "severidade": resultado.severidade_geral,
            "alertas": [a.parametro for a in resultado.alertas],
            "drift": dados["drift_oscilador_ns"],
            "potencia": dados["margem_potencia_pct"],
            "sinal": dados["integridade_sinal"],
        }
        self._historico.append(entrada_historico)

        self._ultimo_dados = dados
        self._ultimo_resultado = resultado
        return dados, resultado

    def _montar_prompt_usuario(self, dados: dict, resultado: alr.ResultadoAvaliacao, pergunta: str) -> str:
        """
        Monta o prompt dinâmico com:
        - Dados atuais da telemetria
        - Alertas detectados pelo Python
        - Histórico dos últimos ciclos (memória de contexto)
        - Pergunta do operador
        """
        # Seção de telemetria atual
        secao_dados = (
            f"=== TELEMETRIA ATUAL — Ciclo #{dados['ciclo']} ({dados['timestamp']}) ===\n"
            f"- Drift oscilador atômico : {dados['drift_oscilador_ns']:.3f} ns\n"
            f"- Sincronização constelação: {dados['sincronizacao_pct']:.2f}%\n"
            f"- Integridade sinal L1/L5 : {dados['integridade_sinal']:.2f}%\n"
            f"- Precisão efeméride      : {dados['precisao_efemeride_m']:.3f} m\n"
            f"- Margem de potência      : {dados['margem_potencia_pct']:.2f}%\n"
            f"- Modo degradado ativo    : {'Sim' if dados['modo_degradado'] else 'Não'}\n"
            f"- Severidade geral        : {resultado.severidade_geral}\n"
        )

        # Seção de alertas Python
        if resultado.alertas:
            linhas_alertas = []
            for a in resultado.alertas:
                linhas_alertas.append(
                    f"  [{a.severidade}] {a.parametro}: {a.valor_atual} {a.unidade} "
                    f"(limite: {a.threshold} {a.unidade})\n"
                    f"  Impacto terrestre: {a.impacto_terrestre}"
                )
                if a.acao_automatizada:
                    linhas_alertas.append(f"  Ação executada automaticamente: {a.acao_automatizada}")
            secao_alertas = "=== ALERTAS DETECTADOS ===\n" + "\n".join(linhas_alertas)
        else:
            secao_alertas = "=== ALERTAS ===\nNenhum alerta ativo. Missão operando normalmente."

        # Seção de histórico (diferencial: memória de contexto)
        if len(self._historico) > 1:
            linhas_hist = []
            for h in list(self._historico)[:-1]:  # exclui o ciclo atual
                linhas_hist.append(
                    f"  Ciclo {h['ciclo']} ({h['timestamp']}): "
                    f"Severidade={h['severidade']}, "
                    f"Drift={h['drift']:.2f}ns, "
                    f"Potência={h['potencia']:.1f}%, "
                    f"Sinal={h['sinal']:.1f}%"
                    + (f", Alertas=[{', '.join(h['alertas'])}]" if h["alertas"] else "")
                )
            secao_historico = (
                "=== HISTÓRICO DOS ÚLTIMOS CICLOS ===\n" + "\n".join(linhas_hist)
            )
        else:
            secao_historico = "=== HISTÓRICO ===\nPrimeiro ciclo de monitoramento."

        return (
            f"{secao_dados}\n"
            f"{secao_alertas}\n\n"
            f"{secao_historico}\n\n"
            f"=== PERGUNTA DO OPERADOR ===\n{pergunta}"
        )

    def analyze(self, pergunta: str) -> str:
        """
        Pipeline completo: coleta dados → avalia alertas → consulta IA → retorna análise.
        """
        # Comando especial: /simular
        if pergunta.strip().lower() == "/simular":
            self._forcar_anomalia = True
            pergunta = "Analise a situação de emergência e indique as ações prioritárias."

        dados, resultado = self._coletar_e_avaliar()
        prompt = self._montar_prompt_usuario(dados, resultado, pergunta)
        resposta_ia = llm(prompt, system=self.system_prompt)

        # Prefixa com telemetria e alertas para o avaliador ver a injeção dinâmica
        cabecalho = tel.formatar_para_exibicao(dados)
        alertas_str = alr.formatar_alertas(resultado)

        return f"{cabecalho}\n\n{alertas_str}\n\n{'─'*54}\n\n{resposta_ia}"

    def status_snapshot(self) -> str:
        """Retorna resumo rápido da missão sem nova consulta à IA."""
        if not self._ultimo_dados:
            dados, resultado = self._coletar_e_avaliar()
        else:
            dados = self._ultimo_dados
            resultado = self._ultimo_resultado

        cabecalho = tel.formatar_para_exibicao(dados)
        alertas_str = alr.formatar_alertas(resultado)
        hist_resumo = f"Ciclos monitorados nesta sessão: {len(self._historico)}"

        return f"{cabecalho}\n\n{alertas_str}\n\n{hist_resumo}"
