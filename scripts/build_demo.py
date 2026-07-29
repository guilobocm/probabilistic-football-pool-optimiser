from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

NAVY = "#09111F"
SLATE = "#8B949E"
GREEN = "#20C997"
WHITE = "#F6F8FA"
CYAN = "#30C7EC"


def create_terminal_gif(filename):
    width, height = 800, 400
    frames = []

    # Try to load mono font
    try:
        font = ImageFont.truetype("consola.ttf", 20)
        bold_font = ImageFont.truetype("consolab.ttf", 20)
    except Exception:
        font = ImageFont.load_default()
        bold_font = font

    lines_script = [
        ("$ uv run python -m src.pipeline.run_all", WHITE, 5),
        ("Loading calibrated match probabilities...", SLATE, 3),
        ("Generating Dixon-Coles score matrices...", SLATE, 4),
        ("Optimising picks under Classic rules...", GREEN, 5),
        ("Running 100,000 deterministic tournament simulations...", CYAN, 8),
        ("Writing outputs/sample/match_picks.csv", SLATE, 2),
        ("Writing outputs/sample/simulation_summary.json", SLATE, 2),
        ("Pipeline completed successfully in 12.4s.", GREEN, 15),
    ]

    def draw_bg():
        img = Image.new("RGB", (width, height), NAVY)
        draw = ImageDraw.Draw(img)
        # MacOS-like terminal header
        draw.rectangle([0, 0, width, 40], fill="#161b22")
        draw.ellipse([15, 15, 25, 25], fill="#ff5f56")
        draw.ellipse([35, 15, 45, 25], fill="#ffbd2e")
        draw.ellipse([55, 15, 65, 25], fill="#27c93f")
        return img, draw

    current_lines = []
    for text, color, duration in lines_script:
        current_lines.append((text, color))

        # Add frames to simulate typing/loading
        img, draw = draw_bg()
        y = 60
        for i, (l_text, l_color) in enumerate(current_lines):
            # Make the prompt part bold/white
            if l_text.startswith("$"):
                draw.text((20, y), "$", fill=GREEN, font=bold_font)
                draw.text((40, y), l_text[2:], fill=WHITE, font=font)
            else:
                draw.text((20, y), l_text, fill=l_color, font=font)
            y += 35

        # Duplicate this frame 'duration' times (each frame = 200ms)
        for _ in range(duration):
            frames.append(img.copy())

    # Add an ending pause
    for _ in range(10):
        frames.append(frames[-1].copy())

    frames[0].save(
        filename, save_all=True, append_images=frames[1:], duration=200, loop=0
    )


if __name__ == "__main__":
    assets_dir = Path(__file__).parent.parent / "assets"
    assets_dir.mkdir(exist_ok=True)
    create_terminal_gif(assets_dir / "demo.gif")
    print(f"Generated {assets_dir / 'demo.gif'}")
