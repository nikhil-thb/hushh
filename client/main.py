"""
Hushh Tunnel CLI — main entrypoint.

Commands:
    hushh login              Authenticate with the server
    hushh logout             Clear local credentials
    hushh whoami             Show current user info
    hushh http <port>        Start an HTTP tunnel
    hushh status             Show active tunnels
    hushh stop <subdomain>   Stop a specific tunnel via API
    hushh version            Show version
"""

from __future__ import annotations

import asyncio
import sys
from typing import Annotated, Optional

import structlog
import typer
from rich.console import Console
from rich.table import Table


from client.auth import AuthError, login as _login, whoami as _whoami
from client.config import clear_config, load_config, save_config, ClientConfig, DEFAULT_SERVER_URL
from client.display import (
    console,
    print_banner,
    print_disconnected,
    print_error,
    print_info,
    print_reconnecting,
    print_request,
    print_success,
    print_tunnel_url,
)
from client.tunnel import TunnelClient

app = typer.Typer(
    name="hushh",
    help="Hushh Tunnel — expose localhost over HTTPS.",
    no_args_is_help=True,
    rich_markup_mode="rich",
    add_completion=False,
)

_VERSION = "0.1.0"

log = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# hushh login
# ---------------------------------------------------------------------------


@app.command("login")
def cmd_login(
    api_key: Annotated[Optional[str], typer.Argument(help="Optional API key to login directly.")] = None,
    email: Annotated[str, typer.Option("--email", "-e", help="Your account email.")] = "",
    password: Annotated[str, typer.Option("--password", "-p", hide_input=True, help="Your password.")] = "",
    server: Annotated[str, typer.Option("--server", help="Server base URL.")] = DEFAULT_SERVER_URL,
) -> None:
    """Authenticate with the Hushh server and save credentials locally."""
    print_banner()

    async def _run() -> None:
        try:
            if api_key:
                import httpx
                async with httpx.AsyncClient(base_url=server, timeout=10) as client:
                    resp = await client.get("/api/dashboard/stats", headers={"Authorization": f"Bearer {api_key}"})
                    if resp.status_code == 401:
                        print_error("Invalid API key.")
                        raise typer.Exit(1)
                    
                    config = ClientConfig(server_url=server, api_key=api_key, email="authenticated")
                    save_config(config)
                    print_success("Logged in successfully via API key")
            else:
                em = email or typer.prompt("Email")
                pw = password or typer.prompt("Password", hide_input=True)
                email_out, key_out = await _login(em, pw, server_url=server)
                print_success(f"Logged in as [bold]{email_out}[/bold]")
                
            print_info("API key saved to [bold]~/.hushh/config.json[/bold]")
        except AuthError as exc:
            print_error(str(exc))
            raise typer.Exit(1) from exc

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# hushh logout
# ---------------------------------------------------------------------------


@app.command("logout")
def cmd_logout() -> None:
    """Clear local credentials."""
    clear_config()
    print_success("Logged out. Local credentials removed.")


# ---------------------------------------------------------------------------
# hushh whoami
# ---------------------------------------------------------------------------


@app.command("whoami")
def cmd_whoami() -> None:
    """Show currently authenticated user."""
    config = load_config()
    if not config.is_authenticated:
        print_error("Not logged in. Run `hushh login` first.")
        raise typer.Exit(1)

    console.print(f"  [dim]Email:[/dim]  [bold]{config.email or 'unknown'}[/bold]")
    console.print(f"  [dim]Server:[/dim] [bold]{config.server_url}[/bold]")
    console.print(f"  [dim]Key:[/dim]    [bold]{(config.api_key or '')[:12]}…[/bold]")


# ---------------------------------------------------------------------------
# hushh http
# ---------------------------------------------------------------------------


@app.command("http")
def cmd_http(
    port: Annotated[int, typer.Argument(help="Local port to expose, e.g. 3000")],
    subdomain: Annotated[
        Optional[str],
        typer.Option("--subdomain", "-s", help="Custom subdomain (e.g. myapi)."),
    ] = None,
    server: Annotated[
        Optional[str],
        typer.Option("--server", help="Override server URL."),
    ] = None,
    reconnect: Annotated[bool, typer.Option("--reconnect/--no-reconnect", help="Auto-reconnect on disconnect.")] = True,
) -> None:
    """
    Expose a local HTTP service over a public HTTPS tunnel.

    Example:

        hushh http 3000

        hushh http 8080 --subdomain myapi
    """
    config = load_config()
    if not config.is_authenticated:
        print_error("Not logged in. Run `hushh login` first.")
        raise typer.Exit(1)

    if server:
        config = ClientConfig(
            server_url=server,
            api_key=config.api_key,
            email=config.email,
        )

    print_banner()
    print_info(f"Tunneling [bold]http://localhost:{port}[/bold] → [bold]{config.server_url}[/bold]")

    _reconnect_attempt = 0

    def on_connected(sub: str, url: str) -> None:
        nonlocal _reconnect_attempt
        _reconnect_attempt = 0
        print_tunnel_url(sub, url, port)

    def on_request(method: str, path: str, status_code: int) -> None:
        print_request(method, path, status_code)

    def on_disconnect(reason: str) -> None:
        print_disconnected(reason)

    client = TunnelClient(
        config=config,
        local_port=port,
        requested_subdomain=subdomain,
        max_retries=0 if reconnect else 1,
        on_connected=on_connected,
        on_request=on_request,
        on_disconnect=on_disconnect,
    )

    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        console.print("\n[dim]Stopped by user.[/dim]")
        client.stop()


# ---------------------------------------------------------------------------
# hushh status
# ---------------------------------------------------------------------------


@app.command("status")
def cmd_status() -> None:
    """List your active tunnels via the server API."""
    config = load_config()
    if not config.is_authenticated:
        print_error("Not logged in.")
        raise typer.Exit(1)

    import httpx

    async def _run() -> None:
        async with httpx.AsyncClient(base_url=config.server_url, timeout=10) as client:
            try:
                resp = await client.get(
                    "/api/tunnels",
                    headers={"Authorization": f"Bearer {config.api_key}"},
                )
            except httpx.RequestError as exc:
                print_error(f"Network error: {exc}")
                raise typer.Exit(1) from exc

        if resp.status_code == 401:
            print_error("Not authenticated. Run `hushh login`.")
            raise typer.Exit(1)

        tunnels = resp.json()
        if not tunnels:
            print_info("No active tunnels.")
            return

        table = Table(title="Active Tunnels", style="magenta")
        table.add_column("Subdomain", style="cyan bold")
        table.add_column("URL", style="cyan underline")
        table.add_column("Port", style="yellow")
        table.add_column("Last Seen")
        for t in tunnels:
            table.add_row(
                t["subdomain"],
                t["tunnel_url"],
                str(t["local_port"]),
                t["last_seen_at"],
            )
        console.print(table)

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# hushh stop
# ---------------------------------------------------------------------------


@app.command("stop")
def cmd_stop(
    subdomain: Annotated[str, typer.Argument(help="Subdomain of the tunnel to stop.")],
) -> None:
    """Disconnect a tunnel via the server API."""
    config = load_config()

    import httpx

    async def _run() -> None:
        async with httpx.AsyncClient(base_url=config.server_url, timeout=10) as client:
            resp = await client.delete(
                f"/api/tunnels/{subdomain}",
                headers={"Authorization": f"Bearer {config.api_key}"},
            )
        if resp.status_code == 204:
            print_success(f"Tunnel [bold]{subdomain}[/bold] disconnected.")
        elif resp.status_code == 404:
            print_error(f"Tunnel [bold]{subdomain}[/bold] not found.")
        else:
            print_error(f"Failed: {resp.status_code} {resp.text}")

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# hushh version
# ---------------------------------------------------------------------------


@app.command("version")
def cmd_version() -> None:
    """Show the Hushh CLI version."""
    console.print(f"[bold magenta]Hushh Tunnel[/bold magenta] v{_VERSION}")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    app()


if __name__ == "__main__":
    main()
