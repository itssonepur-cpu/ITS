import csv
import json
import os
import re
from typing import List, Dict, Any

import qrcode

PHONE_RE = re.compile(r"^\d{8,15}$")


def load_config(base_dir: str) -> Dict[str, Any]:
    cfg_path = os.path.join(base_dir, "config.json")
    if not os.path.exists(cfg_path):
        cfg_path = os.path.join(base_dir, "config.example.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_contacts(csv_path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("name") or "").strip()
            phone = (row.get("phone") or "").strip()
            tags = (row.get("tags") or "").strip()
            valid = bool(PHONE_RE.match(phone))
            rows.append({"name": name, "phone": phone, "tags": tags, "valid": valid})
    return rows


def filter_contacts(contacts: List[Dict[str, Any]], tag_query: str) -> List[Dict[str, Any]]:
    if not tag_query:
        return [c for c in contacts if c.get("valid")]
    tag_q = tag_query.lower()
    out = []
    for c in contacts:
        if not c.get("valid"):
            continue
        tags = (c.get("tags") or "").lower()
        if all(t.strip() in tags for t in tag_q.split(";") if t.strip()):
            out.append(c)
    return out


def render_template(text: str, context: Dict[str, Any]) -> str:
    out = text
    for k, v in context.items():
        out = out.replace(f"{{{{{k}}}}}", str(v))
    return out


def wa_click_to_chat(number: str, text: str) -> str:
    from urllib.parse import quote
    return f"https://wa.me/{number}?text={quote(text)}"


def save_qr(link: str, out_path: str) -> None:
    img = qrcode.make(link)
    img.save(out_path)
