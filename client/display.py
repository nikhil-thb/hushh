"""
Rich terminal display helpers for the Hushh CLI.

Provides:
- ``print_banner()``        — startup banner
- ``print_tunnel_url()``    — the big URL box shown after connection
- ``print_request()``       — per-request log line
- ``print_error()``         — styled error message
- ``print_success()``       — styled success message
- ``print_info()``          — styled info message
- ``print_disconnected()``  — disconnect notification
"""

from __future__ import annotations

from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

_STATUS_COLORS = {
    range(200, 300): "green",
    range(300, 400): "cyan",
    range(400, 500): "yellow",
    range(500, 600): "red",
}


def _status_color(code: int) -> str:
    for rng, color in _STATUS_COLORS.items():
        if code in rng:
            return color
    return "white"


def print_banner() -> None:
    """Print the Hushh Tunnel startup banner."""
    banner = Text()
    banner.append("  ██╗  ██╗██╗   ██╗███████╗██╗  ██╗██╗  ██╗\n", style="bold magenta")
    banner.append("  ██║  ██║██║   ██║██╔════╝██║  ██║██║  ██║\n", style="bold magenta")
    banner.append("  ███████║██║   ██║███████╗███████║███████║\n", style="bold magenta")
    banner.append("  ██╔══██║██║   ██║╚════██║██╔══██║██╔══██║\n", style="bold magenta")
    banner.append("  ██║  ██║╚██████╔╝███████║██║  ██║██║  ██║\n", style="bold magenta")
    banner.append("  ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝\n", style="bold magenta")
    banner.append("        Tunnel  ·  Secure  ·  Open Source\n", style="dim")
    console.print(banner)


def print_tunnel_url(subdomain: str, tunnel_url: str, local_port: int) -> None:
    """Print the connected tunnel info panel."""
    content = Text()
    content.append("✔ Connected\n\n", style="bold green")
    content.append("Tunnel URL:\n", style="dim")
    content.append(f"  {tunnel_url}\n\n", style="bold cyan underline")
    content.append("Forwarding:\n", style="dim")
    content.append(f"  {tunnel_url}\n", style="cyan")
    content.append("    → \n", style="dim")
    content.append(f"  http://localhost:{local_port}\n", style="yellow")

    console.print(
        Panel(
            content,
            title="[bold magenta]Hushh Tunnel[/bold magenta]",
            border_style="magenta",
            padding=(1, 2),
        )
    )
    console.print(
        "  Press [bold]Ctrl+C[/bold] to stop.\n",
        style="dim",
    )

    # Print request table header
    table_header = Table.grid(padding=(0, 1))
    table_header.add_column(style="dim", width=8)
    table_header.add_column(style="dim", width=6)
    table_header.add_column(style="dim")
    table_header.add_row("TIME", "STATUS", "PATH")
    console.print(table_header)


def print_request(method: str, path: str, status_code: int) -> None:
    """Print a single proxied request line."""
    color = _status_color(status_code)
    now = datetime.now().strftime("%H:%M:%S")

    row = Table.grid(padding=(0, 1))
    row.add_column(style="dim", width=8)
    row.add_column(width=8)
    row.add_column(width=6)
    row.add_column()
    row.add_row(
        now,
        f"[bold]{method:<6}[/bold]",
        f"[{color}]{status_code}[/{color}]",
        path,
    )
    console.print(row)


def print_error(message: str) -> None:
    console.print(f"[bold red]✗ Error:[/bold red] {message}")


def print_success(message: str) -> None:
    console.print(f"[bold green]✔[/bold green] {message}")


def print_info(message: str) -> None:
    console.print(f"[dim]ℹ[/dim] {message}")


def print_disconnected(reason: str) -> None:
    console.print(f"\n[yellow]⚡ Disconnected:[/yellow] {reason}")


def print_reconnecting(attempt: int, delay: float) -> None:
    console.print(f"[dim]↻ Reconnecting (attempt {attempt}, waiting {delay:.0f}s)…[/dim]")
