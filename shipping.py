"""Centralized Egypt governorate metadata and shipping configuration.

Business note: these placeholder shipping values are intentionally easy to edit and
must be replaced with the actual courier rates before production.
"""

from __future__ import annotations

EGYPT_GOVERNORATES = [
    {"code": "cairo", "name_en": "Cairo", "name_ar": "القاهرة"},
    {"code": "giza", "name_en": "Giza", "name_ar": "الجيزة"},
    {"code": "alexandria", "name_en": "Alexandria", "name_ar": "الإسكندرية"},
    {"code": "qalyubia", "name_en": "Qalyubia", "name_ar": "القليوبية"},
    {"code": "sharqia", "name_en": "Sharqia", "name_ar": "الشرقية"},
    {"code": "dakahlia", "name_en": "Dakahlia", "name_ar": "الدقهلية"},
    {"code": "gharbia", "name_en": "Gharbia", "name_ar": "الغربية"},
    {"code": "monufia", "name_en": "Monufia", "name_ar": "المنوفية"},
    {"code": "beheira", "name_en": "Beheira", "name_ar": "البحيرة"},
    {"code": "kafr_el_sheikh", "name_en": "Kafr El Sheikh", "name_ar": "كفر الشيخ"},
    {"code": "damietta", "name_en": "Damietta", "name_ar": "دمياط"},
    {"code": "port_said", "name_en": "Port Said", "name_ar": "بورسعيد"},
    {"code": "ismailia", "name_en": "Ismailia", "name_ar": "الإسماعيلية"},
    {"code": "suez", "name_en": "Suez", "name_ar": "السويس"},
    {"code": "north_sinai", "name_en": "North Sinai", "name_ar": "شمال سيناء"},
    {"code": "south_sinai", "name_en": "South Sinai", "name_ar": "جنوب سيناء"},
    {"code": "beni_suef", "name_en": "Beni Suef", "name_ar": "بني سويف"},
    {"code": "fayoum", "name_en": "Fayoum", "name_ar": "الفيوم"},
    {"code": "minya", "name_en": "Minya", "name_ar": "المنيا"},
    {"code": "assiut", "name_en": "Assiut", "name_ar": "أسيوط"},
    {"code": "sohag", "name_en": "Sohag", "name_ar": "سوهاج"},
    {"code": "qena", "name_en": "Qena", "name_ar": "قنا"},
    {"code": "luxor", "name_en": "Luxor", "name_ar": "الأقصر"},
    {"code": "aswan", "name_en": "Aswan", "name_ar": "أسوان"},
    {"code": "red_sea", "name_en": "Red Sea", "name_ar": "البحر الأحمر"},
    {"code": "new_valley", "name_en": "New Valley", "name_ar": "الوادي الجديد"},
    {"code": "matrouh", "name_en": "Matrouh", "name_ar": "مطروح"},
]

GOVERNORATE_LOOKUP = {item["code"]: item for item in EGYPT_GOVERNORATES}

# Placeholder shipping rates; replace before production with the actual business rates.
GOVERNORATE_SHIPPING_RATES = {
    "cairo": 35.0,
    "giza": 40.0,
    "alexandria": 45.0,
    "qalyubia": 30.0,
    "sharqia": 35.0,
    "dakahlia": 38.0,
    "gharbia": 32.0,
    "monufia": 32.0,
    "beheira": 34.0,
    "kafr_el_sheikh": 39.0,
    "damietta": 42.0,
    "port_said": 46.0,
    "ismailia": 40.0,
    "suez": 44.0,
    "north_sinai": 58.0,
    "south_sinai": 65.0,
    "beni_suef": 36.0,
    "fayoum": 37.0,
    "minya": 36.0,
    "assiut": 38.0,
    "sohag": 40.0,
    "qena": 42.0,
    "luxor": 48.0,
    "aswan": 52.0,
    "red_sea": 60.0,
    "new_valley": 62.0,
    "matrouh": 70.0,
}


def get_governorate_by_code(code: str):
    normalized = (code or "").strip().lower()
    return GOVERNORATE_LOOKUP.get(normalized)


def get_shipping_rate_for_governorate(code: str) -> float:
    normalized = (code or "").strip().lower()
    if normalized not in GOVERNORATE_SHIPPING_RATES:
        raise ValueError(f"Unsupported governorate code: {code}")
    return float(GOVERNORATE_SHIPPING_RATES[normalized])
