import streamlit as st
import math
import random
from PIL import Image, ImageDraw
import io
import zipfile
import tempfile

# --- Constants ---
SYMBOL_SIZE_DEFAULT = 80
MARGIN = 20

st.set_page_config(page_title="Spot It! Card Generator")
st.title("🔄 Spot It! Card Generator with Easy and Advanced Modes")

# --- Mode selection ---
mode = st.radio("Choose mode:", ["Easy", "Advanced"])

# --- Common inputs ---
n = st.slider("Symbols per card (n):", min_value=3, max_value=6, value=4)
total_symbols = n**2 - n + 1
image_files = st.file_uploader(f"Upload at least {total_symbols} images", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
card_size = st.slider("Card size (px):", 300, 800, 500)
border_thickness = st.slider("Border thickness:", 1, 10, 3)

# --- Math logic ---
def generate_spot_it_deck(n):
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


# --- Improved Drawing Logic with Collision ---
def draw_card(symbols, images, size, border):
    card = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    draw = ImageDraw.Draw(card)
    center = (size // 2, size // 2)
    radius = (size - SYMBOL_SIZE_DEFAULT) // 2

    placed_boxes = []
    max_attempts = 100

    for sym_id in symbols:
        placed = False
        symbol_size = SYMBOL_SIZE_DEFAULT

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

        if not placed:
            for smaller_size in range(SYMBOL_SIZE_DEFAULT - 10, 20, -10):
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





def draw_card_with_positions(symbols, images, positions, sizes, size=500, border=3):
    card = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    draw = ImageDraw.Draw(card)
    center = (size // 2, size // 2)
    radius = (size - MARGIN*2) // 2
    draw.ellipse([MARGIN, MARGIN, size - MARGIN, size - MARGIN], outline="black", width=border)
    for i, sym_id in enumerate(symbols):
        img = images[sym_id].resize((sizes[i], sizes[i]))
        x, y = positions[i]
        x = max(center[0] - radius + sizes[i]//2, min(x, center[0] + radius - sizes[i]//2))
        y = max(center[1] - radius + sizes[i]//2, min(y, center[1] + radius - sizes[i]//2))
        card.paste(img, (int(x - sizes[i]//2), int(y - sizes[i]//2)), img.convert("RGBA"))
    return card

if image_files and len(image_files) >= total_symbols:
    deck = generate_spot_it_deck(n)
    st.success(f"Generated {len(deck)} cards.")

    images = [Image.open(f).convert("RGBA") for f in image_files[:total_symbols]]
    final_cards = []

    for card_idx, card_symbols in enumerate(deck):
        st.markdown(f"### Card {card_idx + 1}")
        if mode == "Easy":
            card_img = draw_card(card_symbols, images, size=card_size, border=border_thickness)
            st.image(card_img, use_container_width=True)
            final_cards.append(card_img)
        else:
            center = card_size // 2
            radius = (card_size - MARGIN*2) // 2
            default_positions = []
            for i in range(len(card_symbols)):
                angle = 2 * math.pi * i / len(card_symbols)
                x = center + radius * math.cos(angle)
                y = center + radius * math.sin(angle)
                default_positions.append([x, y])
            positions = []
            sizes = []
            for i, sym_id in enumerate(card_symbols):
                st.write(f"Symbol {sym_id + 1}")
                pos_x = st.slider(f"X position (symbol {sym_id + 1}, card {card_idx + 1})", 
                                  MARGIN, card_size - MARGIN, int(default_positions[i][0]), key=f"x_{card_idx}_{i}")
                pos_y = st.slider(f"Y position (symbol {sym_id + 1}, card {card_idx + 1})", 
                                  MARGIN, card_size - MARGIN, int(default_positions[i][1]), key=f"y_{card_idx}_{i}")
                size_slider = st.slider(f"Size (symbol {sym_id + 1}, card {card_idx + 1})", 
                                        20, 120, SYMBOL_SIZE_DEFAULT, key=f"s_{card_idx}_{i}")
                positions.append([pos_x, pos_y])
                sizes.append(size_slider)
            card_img = draw_card_with_positions(card_symbols, images, positions, sizes, size=card_size, border=border_thickness)
            st.image(card_img, use_container_width=True)
            final_cards.append(card_img)

    if st.button("Export All Cards as ZIP"):
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = f"{tmpdir}/spot_it_cards.zip"
            with zipfile.ZipFile(zip_path, "w") as zipf:
                for i, card_img in enumerate(final_cards):
                    buf = io.BytesIO()
                    card_img.save(buf, format="PNG")
                    zipf.writestr(f"card_{i+1}.png", buf.getvalue())
            with open(zip_path, "rb") as f:
                st.download_button("Download ZIP", f, file_name="spot_it_cards.zip")
else:
    st.info(f"Upload at least {total_symbols} images to generate the cards.")
