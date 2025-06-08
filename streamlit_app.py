import streamlit as st
import math
from PIL import Image, ImageDraw
import io
import zipfile
import tempfile

# --- Constants ---
CARD_SIZE = 500
SYMBOL_SIZE = 80
MARGIN = 20

st.set_page_config(page_title="Spot It! Card Generator")
st.title("🔄 Spot It! Card Generator")

# --- User inputs ---
n = st.slider("Symbols per card (n):", min_value=3, max_value=8, value=4)
image_files = st.file_uploader("Upload at least {} images".format(n**2 - n + 1), type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
image_overlap = st.slider("How much symbols go past the border (%)", min_value=0, max_value=100, value=20)
border_thickness = st.slider("Border thickness (px)", min_value=0, max_value=20, value=3)

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

# --- Drawing logic ---
def draw_card(symbols, images, size=CARD_SIZE, overlap_pct=20, border=3):
    card = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    draw = ImageDraw.Draw(card)
    center = (size // 2, size // 2)
    overlap_radius = int((size - SYMBOL_SIZE) // 2 * (1 + overlap_pct / 100))

    for i, sym_id in enumerate(symbols):
        angle = 2 * math.pi * i / len(symbols)
        x = center[0] + overlap_radius * math.cos(angle) - SYMBOL_SIZE // 2
        y = center[1] + overlap_radius * math.sin(angle) - SYMBOL_SIZE // 2
        img = images[sym_id].resize((SYMBOL_SIZE, SYMBOL_SIZE))
        card.paste(img, (int(x), int(y)), img.convert('RGBA'))

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
            zip_path = f"{tmpdirname}/cards.zip"
            with zipfile.ZipFile(zip_path, "w") as zipf:
                for idx, card_symbols in enumerate(deck):
                    card_img = draw_card(card_symbols, images, overlap_pct=image_overlap, border=border_thickness)
                    buf = io.BytesIO()
                    card_img.save(buf, format='PNG')
                    img_bytes = buf.getvalue()
                    zipf.writestr(f"card_{idx+1}.png", img_bytes)
                    st.image(card_img, caption=f"Card {idx+1}", use_column_width=True)

            with open(zip_path, "rb") as f:
                st.download_button("📦 Download All Cards (ZIP)", f, file_name="spot_it_cards.zip")
