"""
banner_ascii.py
Gerador standalone de banner ASCII para o Mission Control AI — MobilitySat.
Use para experimentar fontes e customizar o visual do projeto.

Uso:
  python banner_ascii.py              # Exibe o banner padrão
  python banner_ascii.py -fonts       # Lista todas as fontes disponíveis
  python banner_ascii.py -font slant  # Testa uma fonte específica
  python banner_ascii.py -demo        # Demonstra 8 fontes diferentes
"""

import sys
import pyfiglet
from rich.console import Console
from rich.align import Align
from rich.text import Text
from rich.panel import Panel

console = Console()


def banner_padrao():
    """Exibe o banner padrão do projeto."""
    linha1 = pyfiglet.figlet_format("Global Solution", font="ansi_shadow")
    linha2 = pyfiglet.figlet_format("Mission Control AI", font="ansi_shadow")
    linha3 = pyfiglet.figlet_format("MobilitySat", font="small")

    console.print(Align.center(Text(linha1, style="bold #A855F7")))
    console.print(Align.center(Text(linha2, style="bold #06B6D4")))
    console.print(Align.center(Text(linha3, style="bold #22C55E")))
    console.print(
        Align.center(
            Text(
                "── 2026.1 · Prompt Engineering and AI · FIAP · Trilha GNSS e Mobilidade ──",
                style="italic #8484A0",
            )
        )
    )


def listar_fontes():
    """Lista todas as fontes disponíveis no PyFiglet."""
    fontes = pyfiglet.FigletFont.getFonts()
    console.print(Panel(
        "\n".join(sorted(fontes)),
        title=f"[cyan]Fontes disponíveis ({len(fontes)} no total)[/cyan]",
        border_style="#06B6D4",
    ))


def testar_fonte(nome_fonte: str, texto: str = "MobilitySat"):
    """Testa uma fonte específica."""
    try:
        resultado = pyfiglet.figlet_format(texto, font=nome_fonte)
        console.print(Text(resultado, style="bold #06B6D4"))
        console.print(f"[dim]Fonte: {nome_fonte}[/dim]")
    except pyfiglet.FontNotFound:
        console.print(f"[red]Fonte '{nome_fonte}' não encontrada.[/red]")


def demo_fontes():
    """Demonstra 8 fontes diferentes lado a lado."""
    fontes_demo = ["ansi_shadow", "slant", "small", "banner3", "doom", "epic", "block", "larry3d"]
    for fonte in fontes_demo:
        try:
            console.rule(f"[dim]{fonte}[/dim]")
            resultado = pyfiglet.figlet_format("GNSS", font=fonte)
            console.print(Text(resultado, style="bold #06B6D4"))
        except Exception:
            console.print(f"[dim]Fonte {fonte} indisponível[/dim]")


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        banner_padrao()
    elif "-fonts" in args:
        listar_fontes()
    elif "-demo" in args:
        demo_fontes()
    elif "-font" in args:
        idx = args.index("-font")
        fonte = args[idx + 1] if idx + 1 < len(args) else "slant"
        texto_idx = args.index("-text") if "-text" in args else -1
        texto = args[texto_idx + 1] if texto_idx >= 0 and texto_idx + 1 < len(args) else "MobilitySat"
        testar_fonte(fonte, texto)
    else:
        banner_padrao()
