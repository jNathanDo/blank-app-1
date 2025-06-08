import streamlit as st
import math
import random
from PIL import Image, ImageDraw
import io
import zipfile
import tempfile

# --- Constants ---
CARD_SIZE = 500
SYMBOL_SIZE = 80
MARGIN = 20

st.set_page_config(page_title="Spot It! Card Generator")
st.title("Spot It! Card Generator")

# --- User inputs ---
n = st.slider("Symbols per card (n):", min_value=3, max_value=8, value=4)
mode = st.radio("Mode:", ["Easy (Auto placement)", "Advanced (Interactive drag & resize)"])
image_files = st.file_uploader("Upload at least {} images".format(n**2 - n + 1), type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
border_thickness = st.slider("Border thickness (px)", min_value=0, max_value=20, value=3)
card_size = st.slider("Card size (px)", min_value=300, max_value=1000, value=CARD_SIZE, step=50)

# --- Math logic ---
def generate_spot_it_deck(n):
    total_symbols = n**2 - n + 1
    cards = []

    for i in range(n):
        card = [0] + [i * (n - 1) + j + 1 for j in range(n - 1)]
        cards.append(card)

    for i in range(n - 1):
        for j in range(n - 1):
            card = [i + 1]
            for k in range(n - 1):
                val = n + (n - 1) * k + ((i * k + j) % (n - 1))
                card.append(val)
            cards.append(card)

    return cards

# --- Collision detection ---
def is_overlapping(new_box, placed_boxes):
    for box in placed_boxes:
        if not (new_box[2] <= box[0] or new_box[0] >= box[2] or
                new_box[3] <= box[1] or new_box[1] >= box[3]):
            return True
    return False

# --- Drawing logic ---
def draw_card(symbols, images, size=CARD_SIZE, border=3):
    card = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    draw = ImageDraw.Draw(card)
    center = (size // 2, size // 2)
    radius = (size - SYMBOL_SIZE) // 2

    placed_boxes = []
    max_attempts = 100

    for sym_id in symbols:
        placed = False
        symbol_size = SYMBOL_SIZE

        for attempt in range(max_attempts):
            angle = random.uniform(0, 2 * math.pi)
            r = random.uniform(0, radius)
            cx = center[0] + r * math.cos(angle)
            cy = center[1] + r * math.sin(angle)

            x1 = cx - symbol_size / 2
            y1 = cy - symbol_size / 2
            x2 = cx + symbol_size / 2
            y2 = cy + symbol_size / 2

            # Check within circle bounds
            corners = [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]
            if any(math.hypot(c[0]-center[0], c[1]-center[1]) > radius for c in corners):
                continue

            # Check overlap
            if is_overlapping((x1, y1, x2, y2), placed_boxes):
                continue

            placed_boxes.append((x1, y1, x2, y2))
            img = images[sym_id].resize((symbol_size, symbol_size))
            card.paste(img, (int(x1), int(y1)), img.convert('RGBA'))
            placed = True
            break

        # If can't place without overlap, try reducing size and retry
        if not placed:
            for smaller_size in range(SYMBOL_SIZE - 10, 20, -10):
                symbol_size = smaller_size
                for attempt in range(max_attempts):
                    angle = random.uniform(0, 2 * math.pi)
                    r = random.uniform(0, radius)
                    cx = center[0] + r * math.cos(angle)
                    cy = center[1] + r * math.sin(angle)

                    x1 = cx - symbol_size / 2
                    y1 = cy - symbol_size / 2
                    x2 = cx + symbol_size / 2
                    y2 = cy + symbol_size / 2

                    corners = [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]
                    if any(math.hypot(c[0]-center[0], c[1]-center[1]) > radius for c in corners):
                        continue

                    if is_overlapping((x1, y1, x2, y2), placed_boxes):
                        continue

                    placed_boxes.append((x1, y1, x2, y2))
                    img = images[sym_id].resize((symbol_size, symbol_size))
                    card.paste(img, (int(x1), int(y1)), img.convert('RGBA'))
                    placed = True
                    break
                if placed:
                    break

    if border > 0:
        draw.ellipse([MARGIN, MARGIN, size - MARGIN, size - MARGIN], outline="black", width=border)
    return card

# --- Main app logic ---
if st.button("Generate Cards"):
    total_needed = n**2 - n + 1
    if len(image_files) < total_needed:
        st.error(f"You need to upload at least {total_needed} images.")
    else:
        deck = generate_spot_it_deck(n)
        st.success(f"Generated {len(deck)} cards.")

        # Load images and assign to symbol IDs
        images = []
        for f in image_files[:total_needed]:
            img = Image.open(f).convert("RGBA")
            images.append(img)

        # Create temp ZIP
        with tempfile.TemporaryDirectory() as tmpdirname:
            zip_path = f"{tmpdirname}/spot_it_cards.zip"
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for i, card_symbols in enumerate(deck):
                    card_img = draw_card(card_symbols, images, size=card_size, border=border_thickness)
                    buf = io.BytesIO()
                    card_img.save(buf, format="PNG")
                    zipf.writestr(f"card_{i + 1}.png", buf.getvalue())

            with open(zip_path, "rb") as f:
                st.download_button("Download ZIP of Cards", f, file_name="spot_it_cards.zip")

