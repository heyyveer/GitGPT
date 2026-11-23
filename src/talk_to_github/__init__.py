"""
Talk to GitHub - Multi-Agent Repository Intelligence System
"""

import sys
import subprocess
from pathlib import Path


def main() -> None:
    """Launch the Talk to GitHub modern web application."""
    if "--streamlit" in sys.argv:
        print("Launching legacy Streamlit UI...")
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    else:
        print("Launching modern TalkToGitHub Web UI on http://localhost:8000...")
        import uvicorn
        uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
