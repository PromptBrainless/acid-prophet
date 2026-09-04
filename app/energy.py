# /srv/dj-stream/app/energy.py
from __future__ import annotations

ENERGY_MAP = {
    1:  {"color": "#001F3F", "mood": "kosmisch / meditativ",      "label": "Ambient / Drone"},
    2:  {"color": "#006D77", "mood": "entspannt / träumerisch",   "label": "Chillout / Downtempo"},
    3:  {"color": "#2A9D8F", "mood": "relaxed",                   "label": "Downtempo+"},
    4:  {"color": "#52B788", "mood": "groovig / organisch",       "label": "Deep / Organic House"},
    5:  {"color": "#F4D35E", "mood": "positiv / sonnig",          "label": "House / Afro House"},
    6:  {"color": "#F4A261", "mood": "euphorisch / energetisch",  "label": "Progressive / Tech House"},
    7:  {"color": "#E76F51", "mood": "intensiv / treibend",       "label": "Trance / Melodic Techno"},
    8:  {"color": "#D62828", "mood": "psychedelisch / spirituell","label": "Techno / Uplifting / Darkpsy"},
    9:  {"color": "#9D4EDD", "mood": "futuristisch / basslastig", "label": "Psytrance / Hard Techno / Hardstyle"},
    10: {"color": "#FFFFFF", "mood": "maximale Energie",          "label": "DnB / Neurofunk / Hardcore / Frenchcore"},
}


def energy_to_color(energy: int) -> str:
    return ENERGY_MAP.get(energy, ENERGY_MAP[7])["color"]


def energy_to_mood(energy: int) -> str:
    return ENERGY_MAP.get(energy, ENERGY_MAP[7])["mood"]


def energy_to_label(energy: int) -> str:
    return ENERGY_MAP.get(energy, ENERGY_MAP[7])["label"]


def clamp_energy(n: int) -> int:
    return max(1, min(10, n))
