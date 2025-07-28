# staticdash/_postinstall.py
import shutil
import subprocess
import sys

def ensure_chrome():
    chrome_exists = shutil.which("google-chrome") or shutil.which("chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if chrome_exists:
        return  # Chrome is already installed

    try:
        subprocess.run(
            [sys.executable, "-m", "plotly._kaleido", "plotly_get_chrome"],
            check=True,
            input='y\n',
            text=True
        )
    except Exception as e:
        print("[StaticDash] Warning: Could not install Chrome automatically. Plot rendering may fail.")
        print(e)
