import streamlit as st
import qrcode
from PIL import Image, ImageDraw
import io

# ---------- Page config ----------
st.set_page_config(
    page_title="QR Code Generator",
    page_icon="📱",
    layout="centered",
)

# ---------- Header ----------
st.title("📱 QR Code Generator")
st.caption("Create QR codes for URLs, text, and contacts — with optional logo overlay.")

st.divider()

# ---------- Input type tabs ----------
tab_url, tab_text, tab_contact = st.tabs(["🔗 URL", "📝 Text", "👤 Contact"])

qr_data = ""

with tab_url:
    url_input = st.text_input(
        "Website URL",
        placeholder="example.com or https://example.com",
        help="https:// is added automatically if omitted.",
    )
    if url_input.strip():
        u = url_input.strip()
        qr_data = u if u.lower().startswith(("http://", "https://")) else f"https://{u}"

with tab_text:
    text_input = st.text_area(
        "Text Content",
        placeholder="Enter any text to encode...",
        height=120,
    )
    if text_input.strip():
        qr_data = text_input.strip()

with tab_contact:
    c1, c2 = st.columns(2)
    first_name = c1.text_input("First Name", placeholder="John")
    last_name = c2.text_input("Last Name", placeholder="Doe")
    phone = st.text_input("Phone", placeholder="+1 (555) 123-4567")
    email = st.text_input("Email", placeholder="john@example.com")
    org = st.text_input("Organization", placeholder="Company Name")
    website = st.text_input("Website", placeholder="https://example.com")

    if any([first_name, last_name, phone, email]):
        lines = [
            "BEGIN:VCARD", "VERSION:3.0",
            f"N:{last_name};{first_name}",
            f"FN:{' '.join(filter(None, [first_name, last_name]))}",
        ]
        if phone:   lines.append(f"TEL:{phone}")
        if email:   lines.append(f"EMAIL:{email}")
        if org:     lines.append(f"ORG:{org}")
        if website: lines.append(f"URL:{website}")
        lines.append("END:VCARD")
        qr_data = "\n".join(lines)

st.divider()

# ---------- Settings ----------
settings_left, settings_right = st.columns(2)

with settings_left:
    st.subheader("🖼️ Logo Overlay")
    logo_file = st.file_uploader(
        "Upload a logo image",
        type=["png", "jpg", "jpeg", "webp"],
        help="The logo is placed in the center of the QR code.",
    )

    logo_size_pct = st.slider(
        "Logo Size (%)",
        min_value=15, max_value=60, value=45, step=1,
        help="Percentage of QR code area the logo occupies (longest side).",
    )

    if logo_file and not qr_data:
        st.info("Enter a URL, text, or contact info above to generate a QR code with your logo.")

with settings_right:
    st.subheader("🔳 QR Density")
    ec_labels = [
        "Low (L) — Fewest dots, 7% recovery, best for print",
        "Medium (M) — Fewer dots, 15% recovery, good balance",
        "Quartile (Q) — More dots, 25% recovery, with small logo",
        "High (H) — Most dots, 30% recovery, with large logo",
    ]
    ec_values = [
        qrcode.constants.ERROR_CORRECT_L,
        qrcode.constants.ERROR_CORRECT_M,
        qrcode.constants.ERROR_CORRECT_Q,
        qrcode.constants.ERROR_CORRECT_H,
    ]
    ec_index = st.radio(
        "Error correction level",
        range(len(ec_labels)),
        index=2,
        format_func=lambda i: ec_labels[i],
    )
    ec_level = ec_values[ec_index]

    if logo_file and ec_index == 0:
        st.warning("⚠️ Low density with a logo may make the QR code unscannable. Consider Medium or higher.")

st.divider()

# --- Output size ---
st.subheader("📐 Output Size")
size_options = {
    "256px (Small)": 256,
    "512px (Medium)": 512,
    "1024px (Large)": 1024,
    "1536px (XL)": 1536,
    "2048px (XXL)": 2048,
    "4096px (Print)": 4096,
}
size_label = st.select_slider(
    "Download resolution",
    options=list(size_options.keys()),
    value="1024px (Large)",
)
qr_pixel_size = size_options[size_label]
st.caption(f"Downloaded image will be {qr_pixel_size} × {qr_pixel_size} pixels.")

st.divider()


# ---------- QR generation logic ----------
def generate_qr(data: str, size: int, ec: int, logo_bytes=None, logo_pct: int = 45) -> Image.Image:
    """Generate a QR code PIL image, optionally with a centered logo."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=ec,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
    img = img.resize((size, size), Image.LANCZOS)

    if logo_bytes:
        logo = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")

        # Maintain aspect ratio
        nat_w, nat_h = logo.size
        aspect = nat_w / nat_h
        max_dim = int(size * logo_pct / 100)

        if aspect >= 1:
            lw = max_dim
            lh = int(max_dim / aspect)
        else:
            lh = max_dim
            lw = int(max_dim * aspect)

        logo = logo.resize((lw, lh), Image.LANCZOS)

        # White rounded-rect background
        pad = max(6, int(min(lw, lh) * 0.08))
        bg_w, bg_h = lw + pad * 2, lh + pad * 2
        bg = Image.new("RGBA", (bg_w, bg_h), (0, 0, 0, 0))
        bg_draw = ImageDraw.Draw(bg)
        radius = int(min(bg_w, bg_h) * 0.12)
        bg_draw.rounded_rectangle([0, 0, bg_w, bg_h], radius=radius, fill=(255, 255, 255, 255))

        # Paste logo onto background (centered)
        bg.paste(logo, (pad, pad), logo)

        # Paste onto QR
        pos_x = (size - bg_w) // 2
        pos_y = (size - bg_h) // 2
        img.paste(bg, (pos_x, pos_y), bg)

    return img.convert("RGB")


# ---------- QR Code Output ----------
st.subheader("Generated QR Code")

if qr_data:
    logo_bytes = logo_file.read() if logo_file else None
    qr_img = generate_qr(qr_data, qr_pixel_size, ec_level, logo_bytes, logo_size_pct)

    # Center the preview
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(qr_img, use_container_width=True)
        st.caption("Scan with any camera app")

        # Download button
        buf = io.BytesIO()
        qr_img.save(buf, format="PNG", dpi=(300, 300))
        buf.seek(0)

        st.download_button(
            label="⬇️  Download QR Code",
            data=buf,
            file_name="qrcode.png",
            mime="image/png",
            use_container_width=True,
            type="primary",
        )

    with st.expander("📋 Show encoded data"):
        st.code(qr_data, language=None)
else:
    st.info("👆 Fill in a URL, text, or contact info above to generate your QR code.")

# ---------- Footer ----------
st.divider()
st.caption("No data stored · Free to use")
