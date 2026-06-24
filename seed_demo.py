"""Seed demo data so the marketplace looks alive on first run.

Run once after setup:  python seed_demo.py
Creates several pre-verified demo students, an admin (via init), and a catalogue
of listings with generated cover images. Idempotent: re-running won't duplicate.
"""
from __future__ import annotations

import io

from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import select

import config
from models.db_models import User
from models.schemas import Condition, ProductCreate, UserCreate
from services import auth, catalog
from services.db import init_db, session_scope

PW = "Demo#Pass123"

_GRADIENTS = [
    ((79, 70, 229), (124, 58, 237)),
    ((14, 165, 233), (37, 99, 235)),
    ((5, 150, 105), (16, 185, 129)),
    ((245, 158, 11), (249, 115, 22)),
    ((219, 39, 119), (147, 51, 234)),
    ((8, 145, 178), (13, 148, 136)),
]


def _cover(title: str, idx: int) -> bytes:
    """Generate a 600x420 gradient cover with the product title."""
    w, h = 600, 420
    c1, c2 = _GRADIENTS[idx % len(_GRADIENTS)]
    base = Image.new("RGB", (w, h))
    px = base.load()
    for y in range(h):
        t = y / h
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        for x in range(w):
            px[x, y] = (r, g, b)
    draw = ImageDraw.Draw(base)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 40)
    except Exception:
        font = ImageFont.load_default()
    # Word-wrap the title.
    words, lines, line = title.split(), [], ""
    for word in words:
        trial = (line + " " + word).strip()
        if draw.textlength(trial, font=font) > w - 80:
            lines.append(line)
            line = word
        else:
            line = trial
    if line:
        lines.append(line)
    y = h // 2 - len(lines) * 26
    for ln in lines:
        tw = draw.textlength(ln, font=font)
        draw.text(((w - tw) / 2, y), ln, fill="white", font=font)
        y += 52
    buf = io.BytesIO()
    base.save(buf, format="PNG")
    return buf.getvalue()


DEMO_USERS = [
    ("Ada Obi", "ada.obi@calebuniversity.edu.ng"),
    ("Tunde Bello", "tunde.bello@calebuniversity.edu.ng"),
    ("Chioma Eze", "chioma.eze@calebuniversity.edu.ng"),
    ("Daniel Okoro", "daniel.okoro@calebuniversity.edu.ng"),
    ("Fatima Sani", "fatima.sani@calebuniversity.edu.ng"),
    ("Emeka Nwosu", "emeka.nwosu@calebuniversity.edu.ng"),
]

# (title, description, price, condition, category, quantity)
DEMO_LISTINGS = [
    ("Used Calculus Textbook", "Lightly used MTH101 textbook, no torn pages.",
     "3500.00", Condition.used, "Textbooks", 1),
    ("Intro to Programming (Python)", "CSC course material, clean copy.",
     "4000.00", Condition.used, "Textbooks", 2),
    ("iPhone Charging Cable", "Original Lightning cable, works perfectly.",
     "2000.00", Condition.new, "Electronics & Gadgets", 5),
    ("Scientific Calculator", "Casio fx-991EX, all functions working.",
     "5500.00", Condition.new, "Electronics & Gadgets", 1),
    ("Wireless Earbuds", "Great sound, comes with charging case.",
     "9000.00", Condition.used, "Electronics & Gadgets", 1),
    ("USB Flash Drive 64GB", "Brand new, sealed.",
     "3000.00", Condition.new, "Electronics & Gadgets", 4),
    ("Hostel Reading Lamp", "Rechargeable LED lamp, perfect for night study.",
     "4500.00", Condition.used, "Furniture & Hostel", 2),
    ("Standing Fan", "Quiet, 3 speeds, lightly used.",
     "12000.00", Condition.used, "Furniture & Hostel", 1),
    ("Denim Jacket (M)", "Trendy denim jacket, barely worn.",
     "6000.00", Condition.used, "Clothing & Fashion", 1),
    ("Nike Sneakers (Size 42)", "Clean white sneakers, great condition.",
     "15000.00", Condition.used, "Clothing & Fashion", 1),
    ("Maths Tutoring (1 hr)", "Calculus & algebra help from a 400L student.",
     "1500.00", Condition.new, "Services", 10),
    ("Laptop Repair & Setup", "Software cleanup, OS install, virus removal.",
     "5000.00", Condition.new, "Services", 10),
]


def _verify(email: str) -> None:
    with session_scope() as s:
        u = s.scalar(select(User).where(User.email == email))
        if u:
            u.is_verified = True


def main() -> None:
    init_db(seed=True)
    cats = {c["name"]: c["category_id"] for c in catalog.list_categories()}

    user_ids: list[int] = []
    for name, email in DEMO_USERS:
        with session_scope() as s:
            existing = s.scalar(select(User).where(User.email == email))
            if existing:
                user_ids.append(existing.user_id)
                continue
        uid = auth.register(UserCreate(full_name=name, email=email, password=PW))
        _verify(email)
        user_ids.append(uid)

    if not catalog.search(include_sold=True):
        for i, (title, desc, price, cond, cat, qty) in enumerate(DEMO_LISTINGS):
            seller = user_ids[i % len(user_ids)]
            catalog.create_listing(
                seller,
                ProductCreate(
                    title=title, description=desc, price=price, condition=cond,
                    quantity=qty, category_id=cats.get(cat, list(cats.values())[0]),
                ),
                _cover(title, i),
            )

    print("✅ Demo data seeded.")
    print(f"   {len(DEMO_USERS)} students (password: {PW}):")
    for name, email in DEMO_USERS:
        print(f"     - {email}")
    print(f"   Admin: admin@{config.INSTITUTION_DOMAIN}  (password: Admin#12345)")
    print(f"   Listings: {len(catalog.search(include_sold=True))}")


if __name__ == "__main__":
    main()
