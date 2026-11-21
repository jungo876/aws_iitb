"""Generate clearly-marked SPECIMEN documents for the "Try with sample documents" demo.

Persona: Priyanka Kumari (fictional). Deliberate real-world problems:
  * bank clerk misspelt her name as "PRIANKA KUMARI"
  * income certificate issued 12/03/2025 (too old)
No real emblems, logos or institutions are used.
"""
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = os.path.join(os.path.dirname(__file__), "..", "frontend", "samples")
FONTS = "C:/Windows/Fonts/"


def font(size, bold=False):
    return ImageFont.truetype(FONTS + ("arialbd.ttf" if bold else "arial.ttf"), size)


def paper(w, h, tint=(250, 248, 240)):
    img = Image.new("RGB", (w, h), tint)
    px = img.load()
    rnd = random.Random(7)
    for _ in range(w * h // 40):
        x, y = rnd.randrange(w), rnd.randrange(h)
        c = px[x, y]
        d = rnd.randint(-8, 4)
        px[x, y] = tuple(max(0, min(255, v + d)) for v in c)
    return img


def watermark(img, text="SPECIMEN - SAMPLE FOR DEMO - NOT A REAL DOCUMENT"):
    w, h = img.size
    layer = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(int(h / 22), True)
    for i, y in enumerate(range(0, h * 2, int(h / 4))):
        d.text((-200 + (i % 2) * 300, y), (text + "     ") * 3, font=f, fill=(200, 40, 40, 38))
    layer = layer.rotate(18, expand=False).crop((w // 2, h // 2, w // 2 + w, h // 2 + h))
    img.paste(layer, (0, 0), layer)
    d2 = ImageDraw.Draw(img)
    d2.rectangle((0, h - 34, w, h), fill=(200, 40, 40))
    d2.text((w // 2, h - 17), "SPECIMEN • Generated for KagazCheck demo • Fictional person", font=font(18, True),
            fill="white", anchor="mm")
    return img


def photo_box(d, box):
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=(214, 222, 232), outline=(120, 130, 140), width=2)
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    d.ellipse((cx - 38, cy - 70, cx + 38, cy + 6), fill=(160, 170, 185))
    d.rounded_rectangle((cx - 70, cy + 14, cx + 70, y1 - 6), radius=30, fill=(160, 170, 185))


def finish(img, name, angle=0.0):
    img = watermark(img)
    if angle:
        img = img.rotate(angle, expand=True, fillcolor=(60, 60, 60))
    img = img.filter(ImageFilter.GaussianBlur(0.4))
    os.makedirs(OUT, exist_ok=True)
    img.save(os.path.join(OUT, name), "JPEG", quality=84)
    print("wrote", name, img.size)


def aadhaar():
    w, h = 1100, 700
    img = paper(w, h, (252, 252, 250))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, w, 90), fill=(255, 153, 51))
    d.rectangle((0, 90, w, 100), fill=(255, 255, 255))
    d.rectangle((0, 100, w, 110), fill=(19, 136, 8))
    d.text((40, 45), "UNIQUE IDENTITY CARD (AADHAAR-STYLE SPECIMEN)", font=font(34, True), fill=(30, 30, 30), anchor="lm")
    photo_box(d, (50, 150, 270, 420))
    x = 320
    d.text((x, 165), "Priyanka Kumari", font=font(40, True), fill=(20, 20, 20))
    d.text((x, 235), "DOB: 14/08/2005", font=font(34), fill=(20, 20, 20))
    d.text((x, 290), "FEMALE", font=font(34), fill=(20, 20, 20))
    d.text((x, 345), "Address: Ward 7, Gaya, Bihar 823001", font=font(26), fill=(60, 60, 60))
    d.text((w // 2, 520), "1234 5678 4821", font=font(64, True), fill=(10, 10, 10), anchor="mm")
    d.line((80, 580, w - 80, 580), fill=(200, 30, 30), width=4)
    d.text((w // 2, 615), "Specimen number - not a valid identity number", font=font(24), fill=(90, 90, 90), anchor="mm")
    finish(img, "aadhaar.jpg", angle=-1.2)


def passbook():
    w, h = 1100, 760
    img = paper(w, h, (240, 246, 252))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, w, 100), fill=(18, 60, 120))
    d.text((40, 50), "DEMO GRAMIN BANK", font=font(44, True), fill="white", anchor="lm")
    d.text((w - 40, 50), "SAVINGS ACCOUNT PASSBOOK", font=font(24, True), fill=(200, 220, 255), anchor="rm")
    rows = [
        ("Branch", "Gaya Main Road"),
        ("IFSC", "DEMO0004587"),
        ("Account No.", "30218845577712"),
        ("Account Holder Name", "PRIANKA KUMARI"),
        ("Father / Husband", "RAMESH PRASAD"),
        ("Address", "Ward 7, Gaya, Bihar 823001"),
        ("Mode of Operation", "SINGLE"),
        ("Date of Opening", "02/07/2023"),
    ]
    y = 140
    for k, v in rows:
        d.text((60, y), k, font=font(28), fill=(70, 80, 100))
        d.text((420, y), ":  " + v, font=font(30, True), fill=(15, 20, 30))
        d.line((60, y + 48, w - 60, y + 48), fill=(205, 215, 230), width=1)
        y += 64
    d.text((w - 70, h - 90), "Branch Manager (specimen)", font=font(22), fill=(90, 90, 90), anchor="rm")
    finish(img, "bank.jpg", angle=0.8)


def marksheet():
    w, h = 1000, 1300
    img = paper(w, h, (250, 247, 236))
    d = ImageDraw.Draw(img)
    d.rectangle((20, 20, w - 20, h - 50), outline=(120, 90, 40), width=6)
    d.text((w // 2, 90), "STATE SCHOOL EXAMINATION BOARD", font=font(40, True), fill=(90, 50, 10), anchor="mm")
    d.text((w // 2, 140), "(Specimen board for demonstration)", font=font(24), fill=(90, 70, 40), anchor="mm")
    d.text((w // 2, 210), "SECONDARY SCHOOL EXAMINATION 2021", font=font(32, True), fill=(30, 30, 30), anchor="mm")
    d.text((w // 2, 255), "MARKS STATEMENT CUM CERTIFICATE", font=font(28), fill=(30, 30, 30), anchor="mm")
    rows = [
        ("Name of Candidate", "PRIYANKA KUMARI"),
        ("Father's Name", "RAMESH PRASAD"),
        ("Mother's Name", "SUNITA DEVI"),
        ("Date of Birth", "14/08/2005"),
        ("Roll Code / Roll No.", "71045 / 2100123"),
        ("School", "Govt. High School, Gaya"),
    ]
    y = 320
    for k, v in rows:
        d.text((70, y), k, font=font(28), fill=(60, 50, 40))
        d.text((420, y), ":  " + v, font=font(30, True), fill=(20, 20, 20))
        y += 58
    y += 30
    d.rectangle((70, y, w - 70, y + 50), fill=(235, 225, 200))
    for x, t in ((90, "Subject"), (620, "Marks"), (800, "Max")):
        d.text((x, y + 12), t, font=font(26, True), fill=(40, 30, 20))
    y += 60
    for sub, m in (("Hindi", 78), ("English", 71), ("Mathematics", 84), ("Science", 80), ("Social Science", 76)):
        d.text((90, y), sub, font=font(26), fill=(30, 30, 30))
        d.text((620, y), str(m), font=font(26), fill=(30, 30, 30))
        d.text((800, y), "100", font=font(26), fill=(30, 30, 30))
        y += 46
    d.text((90, y + 30), "Result: PASSED - FIRST DIVISION", font=font(30, True), fill=(20, 80, 20))
    d.text((w - 90, h - 130), "Controller of Examinations (specimen)", font=font(22), fill=(90, 90, 90), anchor="rm")
    finish(img, "marksheet.jpg", angle=-0.6)


def certificate(name, title, body_lines, issue, ref):
    w, h = 1000, 1250
    img = paper(w, h, (252, 252, 247))
    d = ImageDraw.Draw(img)
    d.rectangle((25, 25, w - 25, h - 55), outline=(40, 70, 40), width=4)
    d.text((w // 2, 90), "OFFICE OF THE CIRCLE OFFICER", font=font(34, True), fill=(30, 50, 30), anchor="mm")
    d.text((w // 2, 135), "Gaya Sadar, District Gaya (Specimen office)", font=font(24), fill=(60, 60, 60), anchor="mm")
    d.text((w // 2, 215), title, font=font(42, True), fill=(20, 20, 20), anchor="mm")
    d.text((70, 280), f"Certificate No: {ref}", font=font(24), fill=(60, 60, 60))
    d.text((w - 70, 280), f"Date of issue: {issue}", font=font(24, True), fill=(30, 30, 30), anchor="ra")
    y = 360
    for line in body_lines:
        d.text((70, y), line, font=font(29), fill=(25, 25, 25))
        y += 52
    d.text((w - 80, h - 210), "Circle Officer (specimen)", font=font(24, True), fill=(40, 40, 40), anchor="rm")
    d.text((w - 80, h - 175), "Digitally signed - demo only", font=font(20), fill=(100, 100, 100), anchor="rm")
    finish(img, name, angle=0.5)


if __name__ == "__main__":
    aadhaar()
    passbook()
    marksheet()
    certificate("income.jpg", "INCOME CERTIFICATE", [
        "This is to certify that Priyanka Kumari,",
        "D/O Ramesh Prasad, resident of Ward 7, Gaya,",
        "Bihar, has a total annual family income from",
        "all sources of Rs. 1,80,000/-",
        "(Rupees One Lakh Eighty Thousand only).",
        "",
        "This certificate is issued on the basis of the",
        "report of the Revenue Officer.",
    ], "12/03/2025", "BRCCO/2025/118842")
    certificate("caste.jpg", "CASTE CERTIFICATE", [
        "This is to certify that Priyanka Kumari,",
        "D/O Ramesh Prasad, resident of Ward 7, Gaya,",
        "Bihar, belongs to the Ravidas caste, which is",
        "recognised as a Scheduled Caste (SC) under",
        "the Constitution (Scheduled Castes) Order, 1950.",
    ], "05/06/2022", "BCCCO/2022/056121")
