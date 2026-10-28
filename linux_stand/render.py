"""Render saved DXF, not a simulated CAD screenshot; no GOST geometry claims."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from PIL import Image, ImageDraw, ImageFont

WATERMARK = 'nanoCAD НЕ запускался / не скриншот CAD'

def render(source: Path, target: Path) -> None:
    doc = ezdxf.readfile(source)
    if doc.audit().has_errors:
        raise ValueError(f'DXF audit failed: {source}')
    fig = plt.figure(figsize=(16, 12), dpi=100)
    ax = fig.add_axes((.03, .10, .94, .80))
    Frontend(RenderContext(doc), MatplotlibBackend(ax)).draw_layout(doc.modelspace(), finalize=True)
    # ezdxf finalize adjusts figure size: restore the requested raster canvas.
    fig.set_size_inches(16, 12, forward=True)
    fig.savefig(target, dpi=100); plt.close(fig)
    with Image.open(target) as original:
        image = original.convert('RGB')
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype('DejaVuSans.ttf', 22)
    draw.rectangle((0, 0, 1599, 65), fill='#fff0dd')
    draw.text((24, 20), 'LINUX DXF RENDER / TEST GEOMETRY / NOT A GOST FORM', font=font, fill='#9b2020')
    box = draw.textbbox((0, 0), WATERMARK, font=font)
    draw.text((1580 - (box[2] - box[0]), 1150), WATERMARK, font=font, fill='#9b2020')
    image.quantize(colors=64).save(target, optimize=True)
