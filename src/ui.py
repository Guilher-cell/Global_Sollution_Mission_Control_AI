from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
import pyfiglet
from datetime import datetime

console = Console()
session = PromptSession(style=Style.from_dict({"prompt": "#06B6D4 bold"}))

_COR_PRINCIPAL = "#06B6D4"   # ciano — identidade visual
_COR_ALERTA    = "#F59E0B"   # âmbar
_COR_CRITICO   = "#EF4444"   # vermelho
_COR_OK        = "#22C55E"   # verde


def show_banner():
    """Exibe banner ASCII colorido e card de boas-vindas."""
    console.clear()

    linha1 = pyfiglet.figlet_format("Mission Control", font="ansi_shadow")
    linha2 = pyfiglet.figlet_format("Global Sollution Prompt Engeeniring", font="ansi_shadow")

    console.print(Text(linha1, style=f"bold {_COR_PRINCIPAL}"))
    console.print(Text(linha2, style="bold #A855F7"))
    console.print()

    console.print(
        Panel.fit(
            "[bold]Satélite GNSS de navegação[/bold] — estilo GPS / Galileo / GLONASS\n"
            "Monitoramento em tempo real de: drift oscilador · sincronização ·\n"
            "integridade de sinal L1/L5 · efeméride · margem de potência\n\n"
            "[dim]Use [bold cyan]/help[/bold cyan] para ver os comandos  ·  [bold cyan]/exit[/bold cyan] para sair\n"
            "Modelo: [bold]gpt-oss:120b[/bold] via Ollama Cloud[/dim]",
            title="◆ MISSION CONTROL — MOBILITYSAT",
            border_style=_COR_PRINCIPAL,
        )
    )
    console.print()


def show_response(text: str, severidade: str = "NORMAL"):
    """Renderiza resposta da IA em painel colorido conforme severidade."""
    now = datetime.now().strftime("%H:%M:%S")

    cor_borda = {
        "NORMAL":  _COR_OK,
        "ALERTA":  _COR_ALERTA,
        "CRÍTICO": _COR_CRITICO,
    }.get(severidade, _COR_PRINCIPAL)

    console.print(
        Panel(
            text,
            title=f"◆ Mission Control · MobilitySat [{severidade}]",
            subtitle=now,
            border_style=cor_borda,
            padding=(1, 2),
        )
    )


def show_help():
    """Exibe tabela de comandos disponíveis."""
    tabela = Table(box=box.ROUNDED, border_style=_COR_PRINCIPAL, show_header=True)
    tabela.add_column("Comando", style="bold cyan")
    tabela.add_column("Descrição")

    tabela.add_row("/status",   "Exibe snapshot atual da telemetria sem consultar a IA")
    tabela.add_row("/simular",  "Força cenário de anomalia crítica para testar os alertas")
    tabela.add_row("/about",    "Informações sobre o projeto e a trilha MobilitySat")
    tabela.add_row("/clear",    "Limpa o terminal e exibe o banner novamente")
    tabela.add_row("/help",     "Exibe esta tabela de comandos")
    tabela.add_row("/exit",     "Encerra o sistema")
    tabela.add_row("[pergunta]","Qualquer texto livre é enviado ao motor de análise com IA")

    console.print(Panel(tabela, title="◆ Comandos disponíveis", border_style=_COR_PRINCIPAL))


def show_about():
    """Exibe informações sobre o projeto."""
    console.print(
        Panel(
            "[bold]Mission Control AI — MobilitySat[/bold]\n"
            "FIAP · Ciência da Computação · Global Solution 2026.1\n"
            "Disciplina: Prompt Engineering and Artificial Intelligence\n\n"
            "[bold]Trilha:[/bold] 🚗 MobilitySat — GNSS e Mobilidade\n"
            "[bold]Satélite simulado:[/bold] GNSS de navegação (estilo GPS / Galileo / GLONASS)\n"
            "[bold]Setor de impacto:[/bold] Mobilidade e logística — frotas, agricultura de precisão,\n"
            "veículos autônomos\n\n"
            "[bold]Stack:[/bold] Python 3.10+ · Ollama Cloud (gpt-oss:120b) · Rich · prompt-toolkit\n"
            "[bold]Diferenciais:[/bold] Memória de contexto (últimos 5 ciclos) · Few-shot prompting",
            title="◆ Sobre o Projeto",
            border_style=_COR_PRINCIPAL,
        )
    )


def _detectar_severidade(texto: str) -> str:
    """Detecta a severidade pelo conteúdo do texto para colorir o painel."""
    t = texto.upper()
    if "CRÍTICO" in t or "EMERGÊNCIA" in t or "🚨" in t:
        return "CRÍTICO"
    if "ALERTA" in t or "⚠️" in t:
        return "ALERTA"
    return "NORMAL"


def run_cli(engine):
    """Loop principal da CLI."""
    show_banner()

    if not engine.is_ready():
        console.print(
            "  ⚠ Engine status: AGUARDANDO IMPLEMENTAÇÃO ✗\n", style="yellow"
        )

    while True:
        try:
            user_input = session.prompt("❯ ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Encerrando Mission Control AI...[/dim]")
            break

        if not user_input:
            continue

        cmd = user_input.lower()

        if cmd == "/exit":
            console.print("\n[dim]Missão encerrada. Até a próxima órbita. 🛰️[/dim]")
            break

        elif cmd == "/help":
            show_help()

        elif cmd == "/about":
            show_about()

        elif cmd == "/clear":
            show_banner()

        elif cmd == "/status":
            with console.status("[cyan]Coletando telemetria...[/cyan]"):
                resposta = engine.status_snapshot()
            severidade = _detectar_severidade(resposta)
            show_response(resposta, severidade)

        else:
            # Pergunta livre ou /simular — vai para o motor de análise com IA
            with console.status("[cyan]Analisando telemetria e consultando IA...[/cyan]"):
                resposta = engine.analyze(user_input)
            severidade = _detectar_severidade(resposta)
            show_response(resposta, severidade)
