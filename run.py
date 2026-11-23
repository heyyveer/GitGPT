"""
TalkToGitHub - Modern Full-Stack Entry Point
"""
import sys
import socket
import webbrowser
import uvicorn
from pathlib import Path

def find_available_port(preferred: int = 8000, candidates=(8001, 8080, 5000)) -> int:
    """Find the first available port among preferred and candidates."""
    for port in (preferred, *candidates):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("0.0.0.0", port))
                return port
        except OSError:
            continue
    return preferred

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    port = find_available_port()

    print("=" * 65)
    print("⚡ TalkToGitHub — Autonomous Multi-Agent Code Intelligence")
    print("=" * 65)
    print(f"🌐 Launching modern web application on http://localhost:{port} ...")
    print("=" * 65)

    # Check if frontend dist exists
    dist_dir = Path(__file__).resolve().parent / "frontend" / "dist"
    if not dist_dir.exists():
        print("⚠️ Warning: Frontend dist not found. Run 'npm run build' inside frontend/")

    try:
        webbrowser.open(f"http://localhost:{port}")
    except Exception:
        pass

    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()

