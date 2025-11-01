import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Dict, Any

import pandas as pd
import threading
import time
import requests

from .utils import load_config, parse_contacts, filter_contacts, render_template, wa_click_to_chat, save_qr
from .api import WhatsAppAPI


class App(tk.Tk):
    def __init__(self, base_dir: str):
        super().__init__()
        self.title("WhatsApp Marketing Pack")
        self.geometry("980x640")
        self.base_dir = base_dir
        self.config_data = load_config(base_dir)
        self.api = WhatsAppAPI(self.config_data)

        self.contacts: List[Dict[str, Any]] = []
        self.relay_url: str = self.config_data.get("relay_url", "").strip()
        self.relay_secret: str = self.config_data.get("relay_secret", "").strip()
        self._poller_thread = None
        self._stop_poller = threading.Event()

        nb = ttk.Notebook(self)
        self.tab_contacts = ttk.Frame(nb)
        self.tab_templates = ttk.Frame(nb)
        self.tab_campaign = ttk.Frame(nb)
        self.tab_logs = ttk.Frame(nb)
        nb.add(self.tab_contacts, text="Contacts")
        nb.add(self.tab_templates, text="Templates")
        nb.add(self.tab_campaign, text="Campaign")
        nb.add(self.tab_logs, text="Logs")
        nb.pack(fill=tk.BOTH, expand=True)

        self._build_contacts()
        self._build_templates()
        self._build_campaign()
        self._build_logs()

        # Start inbound poller if relay configured
        if self.relay_url and self.relay_secret:
            self._start_inbound_poller()

    # Contacts tab
    def _build_contacts(self):
        frm = self.tab_contacts
        top = ttk.Frame(frm)
        top.pack(fill=tk.X, padx=8, pady=8)
        ttk.Button(top, text="Import CSV", command=self._import_csv).pack(side=tk.LEFT)
        self.lbl_count = ttk.Label(top, text="No contacts loaded")
        self.lbl_count.pack(side=tk.LEFT, padx=8)

        cols = ("name", "phone", "tags", "valid")
        self.tree = ttk.Treeview(frm, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
            self.tree.column(c, width=200 if c != "valid" else 80)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def _import_csv(self):
        path = filedialog.askopenfilename(title="Select contacts CSV", filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            self.contacts = parse_contacts(path)
            for row in self.tree.get_children():
                self.tree.delete(row)
            for c in self.contacts:
                self.tree.insert("", tk.END, values=(c["name"], c["phone"], c["tags"], c["valid"]))
            valid_count = sum(1 for c in self.contacts if c.get("valid"))
            self.lbl_count.config(text=f"Contacts loaded: {len(self.contacts)} (valid: {valid_count})")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # Templates tab
    def _build_templates(self):
        frm = self.tab_templates
        top = ttk.Frame(frm)
        top.pack(fill=tk.X, padx=8, pady=8)

        ttk.Label(top, text="Title").grid(row=0, column=0, sticky=tk.W)
        self.tpl_title = ttk.Entry(top, width=60)
        self.tpl_title.grid(row=0, column=1, sticky=tk.W, padx=6)

        ttk.Label(top, text="Body").grid(row=1, column=0, sticky=tk.NW)
        self.tpl_body = tk.Text(top, width=80, height=10)
        self.tpl_body.grid(row=1, column=1, sticky=tk.W, padx=6)

        ttk.Label(top, text="Media URL (optional)").grid(row=2, column=0, sticky=tk.W)
        self.tpl_media = ttk.Entry(top, width=60)
        self.tpl_media.grid(row=2, column=1, sticky=tk.W, padx=6)

        self.preview_box = tk.Text(frm, width=100, height=8)
        self.preview_box.pack(fill=tk.X, padx=8, pady=8)
        ttk.Button(frm, text="Preview with sample", command=self._preview_template).pack(padx=8, pady=4, anchor=tk.W)

    def _preview_template(self):
        body = self.tpl_body.get("1.0", tk.END).strip()
        sample = render_template(body, {"name": "Customer"})
        self.preview_box.delete("1.0", tk.END)
        self.preview_box.insert(tk.END, sample)

    # Campaign tab
    def _build_campaign(self):
        frm = self.tab_campaign
        top = ttk.Frame(frm)
        top.pack(fill=tk.X, padx=8, pady=8)

        ttk.Label(top, text="Filter by tags (e.g., student;gaming)").grid(row=0, column=0, sticky=tk.W)
        self.seg_tags = ttk.Entry(top, width=40)
        self.seg_tags.grid(row=0, column=1, sticky=tk.W, padx=6)

        ttk.Label(top, text="Media Type").grid(row=0, column=2, sticky=tk.W)
        self.media_type = ttk.Combobox(top, values=["text", "image", "video", "document"], width=12)
        self.media_type.set("text")
        self.media_type.grid(row=0, column=3, sticky=tk.W, padx=6)

        btns = ttk.Frame(frm)
        btns.pack(fill=tk.X, padx=8, pady=8)
        ttk.Button(btns, text="Export links", command=self._export_links).pack(side=tk.LEFT)
        ttk.Button(btns, text="Export QR images", command=self._export_qr).pack(side=tk.LEFT, padx=6)
        ttk.Button(btns, text="Send (API)", command=self._send_api).pack(side=tk.LEFT, padx=6)

        self.result_table = ttk.Treeview(frm, columns=("phone", "status", "info"), show="headings")
        for c, w in [("phone", 160), ("status", 100), ("info", 600)]:
            self.result_table.heading(c, text=c.capitalize())
            self.result_table.column(c, width=w)
        self.result_table.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        ttk.Button(frm, text="Export results CSV", command=self._export_results_csv).pack(padx=8, pady=6, anchor=tk.W)

    def _segment(self) -> List[Dict[str, Any]]:
        tag_q = self.seg_tags.get().strip()
        return filter_contacts(self.contacts, tag_q)

    def _render_current_body(self, context: Dict[str, Any]) -> str:
        body = self.tpl_body.get("1.0", tk.END).strip()
        return render_template(body, context)

    def _export_links(self):
        seg = self._segment()
        if not seg:
            messagebox.showwarning("No contacts", "No matching valid contacts.")
            return
        out_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not out_path:
            return
        rows = []
        for c in seg:
            body = self._render_current_body({"name": c.get("name") or ""})
            link = wa_click_to_chat(c["phone"], body)
            rows.append({"name": c.get("name"), "phone": c["phone"], "link": link})
        pd.DataFrame(rows).to_csv(out_path, index=False, encoding="utf-8")
        messagebox.showinfo("Done", f"Saved {len(rows)} links.")

    def _export_qr(self):
        seg = self._segment()
        if not seg:
            messagebox.showwarning("No contacts", "No matching valid contacts.")
            return
        out_dir = filedialog.askdirectory(title="Select output folder")
        if not out_dir:
            return
        count = 0
        for c in seg:
            body = self._render_current_body({"name": c.get("name") or ""})
            link = wa_click_to_chat(c["phone"], body)
            fname = f"qr_{c['phone']}.png"
            save_qr(link, os.path.join(out_dir, fname))
            count += 1
        messagebox.showinfo("Done", f"Saved {count} QR images.")

    def _send_api(self):
        if not self.api.can_send():
            messagebox.showwarning("Export mode", "API credentials not set. Edit config.json or use Export features.")
            return
        seg = self._segment()
        if not seg:
            messagebox.showwarning("No contacts", "No matching valid contacts.")
            return
        media_type = self.media_type.get()
        media_url = self.tpl_media.get().strip()
        self.result_table.delete(*self.result_table.get_children())
        sent = 0
        for c in seg:
            body = self._render_current_body({"name": c.get("name") or ""})
            if media_type == "text" or not media_url:
                res = self.api.send_text(c["phone"], body)
            else:
                res = self.api.send_media(c["phone"], body, media_url, media_type)
            status = res.get("status")
            info = res.get("response") or res.get("reason") or res.get("error") or res.get("code")
            self.result_table.insert("", tk.END, values=(c["phone"], status, str(info)[:200]))
            if status == "sent":
                sent += 1
        messagebox.showinfo("Done", f"Attempted {len(seg)} sends. Sent: {sent}")

    # Logs tab
    def _build_logs(self):
        frm = self.tab_logs
        ttk.Label(frm, text="Inbound messages (from relay)").pack(padx=8, pady=4, anchor=tk.W)
        self.inbound_table = ttk.Treeview(frm, columns=("time", "phone", "type", "text"), show="headings")
        for c, w in [("time", 160), ("phone", 160), ("type", 100), ("text", 520)]:
            self.inbound_table.heading(c, text=c.capitalize())
            self.inbound_table.column(c, width=w)
        self.inbound_table.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        ttk.Label(frm, text="Outbound results are in Campaign tab; use 'Export results CSV'.").pack(padx=8, pady=6, anchor=tk.W)

    def _export_results_csv(self):
        items = self.result_table.get_children()
        if not items:
            messagebox.showwarning("No data", "No results to export.")
            return
        out_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not out_path:
            return
        rows = []
        for iid in items:
            phone, status, info = self.result_table.item(iid, "values")
            rows.append({"phone": phone, "status": status, "info": info})
        pd.DataFrame(rows).to_csv(out_path, index=False, encoding="utf-8")
        messagebox.showinfo("Done", f"Saved {len(rows)} rows.")

    # Inbound relay poller
    def _start_inbound_poller(self):
        def run():
            while not self._stop_poller.is_set():
                try:
                    url = self.relay_url.rstrip('/') + f"/pull?secret={self.relay_secret}"
                    r = requests.get(url, timeout=20)
                    if r.status_code == 200:
                        items = r.json() or []
                        if items:
                            self.after(0, self._append_inbound_items, items)
                except Exception:
                    pass
                time.sleep(3)

        self._poller_thread = threading.Thread(target=run, daemon=True)
        self._poller_thread.start()

    def _append_inbound_items(self, items: List[Dict[str, Any]]):
        for it in items:
            ts = it.get("timestamp") or ""
            phone = it.get("phone") or ""
            typ = it.get("type") or "text"
            text = (it.get("text") or "").replace("\n", " ")
            self.inbound_table.insert("", tk.END, values=(ts, phone, typ, text[:300]))

    def destroy(self):
        try:
            self._stop_poller.set()
        except Exception:
            pass
        return super().destroy()


def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    app = App(base_dir)
    app.mainloop()


if __name__ == "__main__":
    main()
