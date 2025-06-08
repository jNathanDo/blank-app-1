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
st.title("Spot It! Card Generator")

# --- Mode selection ---
mode = st.radio("Select Mode:", ["Easy", "Advanced"])

# --- User inputs ---
n = st.slider("Symbols per card (n):", min_value=3, max_value=8, value=4)
card_size = st.slider("Card size (px)", min_value=300, max_value=800, value=500)
border_thickness = st.slider("Border thickness (px)", min_value=0, max_value=20, value=3)
image_files = st.file_uploader("Upload at least {} images".format(n**2 - n + 1), type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)

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

# --- Drawing logic for advanced ---
def draw_card_with_positions(symbols, images, positions, sizes, size):
    card = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    draw = ImageDraw.Draw(card)

    for sym_id, pos, sz in zip(symbols, positions, sizes):
        img = images[sym_id].resize((sz, sz))
        x = int(pos[0] - sz / 2)
        y = int(pos[1] - sz / 2)
        card.paste(img, (x, y), img.convert('RGBA'))

    draw.ellipse([MARGIN, MARGIN, size - MARGIN, size - MARGIN], outline="black", width=border_thickness)
    return card

# --- Main logic ---
total_needed = n**2 - n + 1

# Handle image loading
if image_files:
    images = [Image.open(f).convert("RGBA") for f in image_files[:total_needed]]
    st.session_state["images"] = images

if st.button("Generate Cards"):
    if len(image_files) < total_needed:
        st.error(f"You need to upload at least {total_needed} images.")
    else:
        deck = generate_spot_it_deck(n)
        st.success(f"Generated {len(deck)} cards.")

        st.session_state["deck"] = deck
        st.session_state["generated"] = True  # flag to show UI below
        st.session_state["card_size"] = card_size
        st.session_state["border_thickness"] = border_thickness

# --- Render Cards ---
if st.session_state.get("generated", False) and "deck" in st.session_state and "images" in st.session_state:
    deck = st.session_state["deck"]
    images = st.session_state["images"]
    card_size = st.session_state["card_size"]
    border_thickness = st.session_state["border_thickness"]

    final_cards = []

    for card_idx, card_symbols in enumerate(deck):
        if mode == "Easy":
            card_img = draw_card(card_symbols, images, card_size, border_thickness)
            st.image(card_img, caption=f"Card {card_idx + 1}", use_container_width=True)
            final_cards.append(card_img)
        else:
            st.subheader(f"Advanced Card {card_idx + 1}")
            default_positions = [[card_size // 2, card_size // 2] for _ in range(len(card_symbols))]

            # Setup session state keys
            for i, sym_id in enumerate(card_symbols):
                key_prefix = f"card{card_idx}_sym{i}"
                if f"{key_prefix}_x" not in st.session_state:
                    st.session_state[f"{key_prefix}_x"] = default_positions[i][0]
                if f"{key_prefix}_y" not in st.session_state:
                    st.session_state[f"{key_prefix}_y"] = default_positions[i][1]
                if f"{key_prefix}_s" not in st.session_state:
                    st.session_state[f"{key_prefix}_s"] = SYMBOL_SIZE_DEFAULT

            # Sliders
            positions = []
            sizes = []
            for i, sym_id in enumerate(card_symbols):
                key_prefix = f"card{card_idx}_sym{i}"
                st.write(f"Symbol {sym_id + 1}")
                pos_x = st.slider(f"X position (symbol {sym_id + 1})",
                                  0, card_size, st.session_state[f"{key_prefix}_x"], key=f"{key_prefix}_x")
                pos_y = st.slider(f"Y position (symbol {sym_id + 1})",
                                  0, card_size, st.session_state[f"{key_prefix}_y"], key=f"{key_prefix}_y")
                size_slider = st.slider(f"Size (symbol {sym_id + 1})",
                                        20, 150, st.session_state[f"{key_prefix}_s"], key=f"{key_prefix}_s")
                positions.append([pos_x, pos_y])
                sizes.append(size_slider)

            card_img = draw_card_with_positions(card_symbols, images, positions, sizes, card_size, border_thickness)
            st.image(card_img, use_container_width=True)
            final_cards.append(card_img)

    # ZIP Export
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

