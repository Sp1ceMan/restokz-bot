"""
Local tunnel manager for RestoKZ development.
Runs localtunnel, captures assigned URL, saves to tunnel_url.txt.

NOTE: In production (Railway), this script is NOT used.
      The API URL is automatically detected from RAILWAY_PUBLIC_DOMAIN env var.
"""
import subprocess
import re
import os
import sys


def main():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
            sys.stderr.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
        except Exception:
            pass

    print("=" * 60)
    print("  RestoKZ — Публичный HTTPS туннель для локальной разработки")
    print("=" * 60)
    print("Подключение к серверу туннелей для порта 8080...")

    cmd = "npx --yes localtunnel --port 8080 --subdomain restokz-app"
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        shell=True,
        encoding="utf-8",
        errors="replace"
    )

    url_saved = False
    for line in iter(proc.stdout.readline, ""):
        sys.stdout.write(line)
        sys.stdout.flush()
        match = re.search(r"https://[a-zA-Z0-9-]+\.loca\.lt", line)
        if match and not url_saved:
            url = match.group(0)
            url_saved = True
            base_dir = os.path.dirname(os.path.abspath(__file__))

            # Save URL to tunnel_url.txt (read by bot.py get_api_url())
            try:
                with open(os.path.join(base_dir, "tunnel_url.txt"), "w", encoding="utf-8") as f:
                    f.write(url)
                print(f"\n[OK] Туннель активен: {url}")
                print(f"[OK] Адрес сохранён в tunnel_url.txt\n")
            except Exception as e:
                print(f"Ошибка сохранения tunnel_url.txt: {e}")

            # Only update index.html DEFAULT_BACKEND_URL when:
            # - TUNNEL_URL env var is NOT set (not in production/Railway mode)
            # - RAILWAY_PUBLIC_DOMAIN env var is NOT set
            if not os.getenv("TUNNEL_URL") and not os.getenv("RAILWAY_PUBLIC_DOMAIN"):
                try:
                    html_path = os.path.join(base_dir, "index.html")
                    with open(html_path, "r", encoding="utf-8") as hf:
                        hcontent = hf.read()
                    hcontent = re.sub(
                        r'const DEFAULT_BACKEND_URL = ".*?";',
                        f'const DEFAULT_BACKEND_URL = "{url}";',
                        hcontent
                    )
                    with open(html_path, "w", encoding="utf-8") as hf:
                        hf.write(hcontent)
                    print(f"[OK] index.html синхронизирован с адресом туннеля: {url}\n")
                except Exception as e:
                    print(f"Ошибка обновления index.html: {e}")
            else:
                print("[INFO] Продакшн режим — index.html не обновляется (используется постоянный URL).\n")

    proc.wait()


if __name__ == "__main__":
    main()
