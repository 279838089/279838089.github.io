#!/usr/bin/env python3
"""Fetch pixel-art sprites with retries. A temporary outage must not block Pages."""
from io import BytesIO
from pathlib import Path
from time import sleep
from urllib.request import Request, urlopen
from PIL import Image

ROOT = Path(__file__).resolve().parent
SPRITES = {
    "normal": "charizard.png",
    "mega_x": "charizard-megax.png",
    "mega_y": "charizard-megay.png",
}
BASE = "https://play.pokemonshowdown.com/sprites/gen5/"

def fetch():
    folder = ROOT / "assets"
    folder.mkdir(exist_ok=True)
    for form, filename in SPRITES.items():
        target = folder / (form + ".png")
        if target.exists():
            try:
                with Image.open(target) as image:
                    image.verify()
                print("Using existing", target, flush=True)
                continue
            except Exception:
                target.unlink()
        url = BASE + filename
        for attempt in range(1, 5):
            try:
                request = Request(url, headers={"User-Agent":"Mozilla/5.0", "Accept":"image/png"})
                with urlopen(request, timeout=20) as response:
                    raw = response.read(2000000)
                if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
                    raise RuntimeError("The remote response is not PNG")
                with Image.open(BytesIO(raw)) as image:
                    image.load()
                    if min(image.size) < 20:
                        raise RuntimeError("Unexpected sprite dimensions")
                    image.convert("RGBA").save(target)
                print("Downloaded", form, target, flush=True)
                break
            except Exception as error:
                print("WARN: download failed", form, "attempt", attempt, str(error), flush=True)
                if attempt < 4:
                    sleep(attempt * 2)
        else:
            # A future rendering job should still refresh weather and calendar.
            # The renderer will use a fallback sprite or a text label.
            print("WARN: sprite missing; continuing with a fallback:", form, flush=True)

if __name__ == "__main__":
    fetch()
