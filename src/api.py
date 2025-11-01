import json
import time
from typing import Dict, Any

import requests


class WhatsAppAPI:
    def __init__(self, config: Dict[str, Any]):
        self.mode = config.get("mode", "export")
        self.token = config.get("cloud_api_token", "")
        self.phone_number_id = config.get("phone_number_id", "")

    def can_send(self) -> bool:
        return self.mode == "api" and bool(self.token and self.phone_number_id)

    def send_text(self, to_number: str, body: str) -> Dict[str, Any]:
        if not self.can_send():
            return {"status": "skipped", "reason": "export-mode"}
        url = f"https://graph.facebook.com/v20.0/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"body": body}
        }
        try:
            r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
            if r.status_code in (200, 201):
                return {"status": "sent", "response": r.json()}
            return {"status": "error", "code": r.status_code, "response": r.text}
        except Exception as e:
            return {"status": "exception", "error": str(e)}

    def send_media(self, to_number: str, body: str, media_url: str, media_type: str = "image") -> Dict[str, Any]:
        if not self.can_send():
            return {"status": "skipped", "reason": "export-mode"}
        url = f"https://graph.facebook.com/v20.0/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        media_type = media_type if media_type in {"image", "video", "document"} else "image"
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": media_type,
            media_type: {"link": media_url, "caption": body}
        }
        try:
            r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
            if r.status_code in (200, 201):
                return {"status": "sent", "response": r.json()}
            return {"status": "error", "code": r.status_code, "response": r.text}
        except Exception as e:
            return {"status": "exception", "error": str(e)}
