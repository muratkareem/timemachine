"""Render actual launch capture text to frames; Pillow is an optional authoring tool."""

import json
import shlex
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

capture = Path(sys.argv[1])
data = json.loads((capture / "evidence.json").read_text())
frames = capture / "frames"
frames.mkdir(exist_ok=False)
font_path = next(
    (
        p
        for p in (
            "/System/Library/Fonts/Menlo.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        )
        if Path(p).is_file()
    ),
    None,
)
font = ImageFont.truetype(font_path, 19) if font_path else ImageFont.load_default(size=19)
for index, stage in enumerate(data["stages"]):
    image = Image.new("RGB", (1600, 1000), "#101820")
    draw = ImageDraw.Draw(image)
    draw.text((38, 25), "TimeMachine v0.2.0 | actual CLI capture", font=font, fill="#7ee0c3")
    draw.text((38, 65), data["mode"], font=font, fill="#cbd5e1")
    draw.text((38, 112), stage["title"], font=font, fill="#ffffff")
    lines = []
    for line in stage["text"].splitlines():
        lines.extend(textwrap.wrap(line, width=126, replace_whitespace=False) or [""])
    if len(lines) > 30:
        lines = lines[:29] + ["[continued in evidence.json / demo.cast]"]
    draw.multiline_text((38, 164), "\n".join(lines), font=font, fill="#dce4ed", spacing=6)
    draw.text(
        (38, 950),
        f"Exit {stage['exit_code']} | six-second presentation hold | disposable fixture",
        font=font,
        fill="#92a4b6",
    )
    image.save(frames / f"{index:02}.png")
print(
    "ffmpeg -y -framerate 1/6 -i "
    + shlex.quote(str(frames / "%02d.png"))
    + " -c:v libx264 -r 30 -pix_fmt yuv420p -movflags +faststart "
    + shlex.quote(str(capture / "demo.mp4"))
)
