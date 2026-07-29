from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Colors
NAVY = "#09111F"
GREEN = "#20C997"
CYAN = "#30C7EC"
GOLD = "#F5B942"
OFF_WHITE = "#F6F8FA"
SLATE = "#8B949E"
DARK_SLATE = "#161b22"


def generate_svg(filename, is_dark):
    bg_color = NAVY if is_dark else OFF_WHITE
    text_main = OFF_WHITE if is_dark else NAVY
    text_sub = SLATE if is_dark else "#57606a"
    accent1 = GREEN
    accent2 = CYAN
    accent3 = GOLD
    pill_text = OFF_WHITE if is_dark else NAVY

    svg = f"""<svg width="100%" height="280" viewBox="0 0 1000 280" xmlns="http://www.w3.org/2000/svg">
    <!-- Background -->
    <rect width="1000" height="280" fill="{bg_color}" rx="12"/>
    
    <!-- Decorative Grid / Pattern -->
    <g stroke="{text_sub}" stroke-opacity="0.1" stroke-width="1">
        <line x1="0" y1="40" x2="1000" y2="40"/>
        <line x1="0" y1="240" x2="1000" y2="240"/>
    </g>

    <!-- Circular Chart (100,000 simulations) -->
    <g fill="none" stroke-width="12">
        <!-- Cyan arc (Top: 180 to 0 degrees) -->
        <path d="M 780,140 A 70,70 0 0,1 920,140" stroke="{accent2}" />
        <!-- Green arc (Bottom Right: 0 to 90 degrees) -->
        <path d="M 920,140 A 70,70 0 0,1 850,210" stroke="{accent1}" />
        <!-- Gold arc (Bottom Left: 90 to 180 degrees) -->
        <path d="M 850,210 A 70,70 0 0,1 780,140" stroke="{accent3}" />
    </g>
    
    <text x="850" y="135" font-family="system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif" font-size="28" font-weight="800" fill="{text_main}" text-anchor="middle">100,000</text>
    <text x="850" y="160" font-family="system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif" font-size="14" font-weight="400" fill="{text_sub}" text-anchor="middle">simulations</text>

    <!-- Content -->
    <g font-family="system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif">
        <text x="50" y="80" font-size="14" font-weight="600" fill="{accent2}" letter-spacing="2">DECISION SCIENCE × FOOTBALL</text>
        
        <text x="50" y="140" font-size="42" font-weight="800" fill="{text_main}">Probabilistic Football</text>
        <text x="50" y="185" font-size="42" font-weight="800" fill="{text_main}">Pool Optimiser</text>
        
        <text x="50" y="230" font-size="18" font-weight="400" fill="{text_sub}">Optimising decisions, not merely predicting scores.</text>
        
        <!-- Tech Pills -->
        <g transform="translate(600, 215)">
            <rect x="0" y="0" width="100" height="24" rx="12" fill="{accent1}"/>
            <text x="50" y="16" font-size="12" font-weight="600" fill="{pill_text}" text-anchor="middle">Dixon–Coles</text>
            
            <rect x="110" y="0" width="115" height="24" rx="12" fill="{accent3}"/>
            <text x="167.5" y="16" font-size="12" font-weight="600" fill="{pill_text}" text-anchor="middle">Expected Points</text>
            
            <rect x="235" y="0" width="95" height="24" rx="12" fill="{accent2}"/>
            <text x="282.5" y="16" font-size="12" font-weight="600" fill="{pill_text}" text-anchor="middle">Monte Carlo</text>
        </g>
    </g>
</svg>"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(svg)


def generate_social_preview(filename):
    # 1280x640 PNG
    width, height = 1280, 640
    img = Image.new("RGBA", (width, height), NAVY)
    draw = ImageDraw.Draw(img)

    # Try to load a nice font, fallback to default
    try:
        # Windows standard fonts
        title_font = ImageFont.truetype("arialbd.ttf", 80)
        subtitle_font = ImageFont.truetype("arialbd.ttf", 36)
        label_font = ImageFont.truetype("arialbd.ttf", 24)
        pill_font = ImageFont.truetype("arialbd.ttf", 28)
    except Exception:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        label_font = ImageFont.load_default()
        pill_font = ImageFont.load_default()

    # Draw label
    draw.text((100, 120), "DECISION SCIENCE × FOOTBALL", fill=CYAN, font=label_font)

    # Draw Title
    draw.text((100, 200), "PROBABILISTIC", fill=OFF_WHITE, font=title_font)
    draw.text((100, 290), "FOOTBALL POOL", fill=OFF_WHITE, font=title_font)
    draw.text((100, 380), "OPTIMISER", fill=OFF_WHITE, font=title_font)

    # Draw separator
    draw.line((100, 490, 1180, 490), fill=SLATE, width=2)

    # Draw footer pills
    pills = [
        ("Dixon–Coles", GREEN),
        ("Expected Points", GOLD),
        ("Monte Carlo", CYAN),
    ]

    x = 100
    y = 530
    padding_x = 24
    padding_y = 12

    for text, color in pills:
        bg_color = color + "1A"
        
        # Calculate text size
        bbox = draw.textbbox((0, 0), text, font=pill_font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        
        rect_w = text_w + padding_x * 2
        rect_h = text_h + padding_y * 2
        
        # Draw pill
        draw.rounded_rectangle([x, y, x + rect_w, y + rect_h], radius=rect_h//2, fill=bg_color)
        
        # Draw text inside pill (adjusting y slightly for visual centering)
        draw.text((x + padding_x, y + padding_y - 2), text, fill=color, font=pill_font)
        
        x += rect_w + 20

    # Draw some decorative abstract chart on the right
    draw.arc((800, 150, 1100, 450), start=180, end=360, fill=CYAN, width=15)
    draw.arc((800, 150, 1100, 450), start=0, end=90, fill=GREEN, width=15)
    draw.arc((800, 150, 1100, 450), start=90, end=180, fill=GOLD, width=15)

    # Stats - Center is at x=950, y=300
    draw.text((950, 280), "100,000", fill=OFF_WHITE, font=subtitle_font, anchor="mm")
    draw.text((950, 320), "simulations", fill=SLATE, font=label_font, anchor="mm")

    img = img.convert("RGB")
    img.save(filename)


if __name__ == "__main__":
    assets_dir = Path(__file__).parent.parent / "assets"
    assets_dir.mkdir(exist_ok=True)

    generate_svg(assets_dir / "hero-light.svg", is_dark=False)
    generate_svg(assets_dir / "hero-dark.svg", is_dark=True)
    generate_social_preview(assets_dir / "social-preview.png")
    print(f"Assets generated in {assets_dir.resolve()}")
