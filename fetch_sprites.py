#!/usr/bin/env python3
from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen
from PIL import Image
ROOT = Path(__file__).resolve().parent
SPRITES = {
    "normal": "charizard.png",
    "mega_x": "charizard-megax.png",
    "mega_y": "charizard-megay.png",
}
def fetch():
    (ROOT / "assets").mkdir(exist_ok=True)
    for form, filename in SPRITES.items():
        target = ROOT / "assets" / (form + ".png")
        if target.exists():
            with Image.open(target) as img:
                img.verify()
            continue
        url = "https://play.pokemonshowdown.com/sprites/gen5/" + filename
        request = Request(url, headers={"User-Agent":"Mozilla/5.0","Accept":"image/png"})
        with urlopen(request, timeout=30) as response:
            raw = response.read(2000000)
        if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
            raise RuntimeError("Invalid PNG from " + url)
        with Image.open(BytesIO(raw)) as img:
            img.load()
            if min(img.size) < 20:
                raise RuntimeError("Invalid dimensions from "+url)
            img.convert("RGBA").save(target)
        print("Downloaded", target)
if __name__ == "__main__":
    fetch()
