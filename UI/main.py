import io
import threading
import webbrowser
import requests
from requests.exceptions import RequestException, Timeout
from PIL import Image
import customtkinter as ctk

API_BASE = "http://0.0.0.0:8711/search?query="  # local API endpoint

# ---- HTTP / image helpers ----
CONNECT_TIMEOUT = 3
READ_TIMEOUT = 10

def api_search(query: str):
    url = API_BASE + requests.utils.quote(query or "")
    try:
        resp = requests.get(url)
        data = resp.json()
        if not isinstance(data, list):
            raise ValueError("API did not return a list")
        return data, None
    except Timeout:
        return [], "Request timed out. Try again or refine the query."
    except RequestException as e:
        return [], f"Request error: {e}"
    except ValueError as e:
        return [], f"Parse error: {e}"

def fetch_image(url: str, size=(100, 150)):
    try:
        r = requests.get(url)
        img = Image.open(io.BytesIO(r.content)).convert("RGB")
        img.thumbnail(size, Image.LANCZOS)
        return ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
    except Exception:
        ph = Image.new("RGB", size, (180, 180, 180))
        return ctk.CTkImage(light_image=ph, dark_image=ph, size=size)

def open_url(url: str):
    if url:
        webbrowser.open(url)

# ---- UI ----
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Book Search")
        self.geometry("900x700")
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        # top-level layout
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # top controls
        top = ctk.CTkFrame(self)
        top.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(top, text="Search").grid(row=0, column=0, padx=(8,6), pady=8)
        self.q_var = ctk.StringVar()
        self.entry = ctk.CTkEntry(top, textvariable=self.q_var, placeholder_text="Type a query and press Enter")
        self.entry.grid(row=0, column=1, sticky="ew", padx=6, pady=8)
        self.entry.bind("<Return>", lambda e: self.on_search())

        self.btn = ctk.CTkButton(top, text="Search", command=self.on_search)
        self.btn.grid(row=0, column=2, padx=(6,8), pady=8)

        # status + loading
        self.status = ctk.CTkLabel(top, text="", anchor="w", text_color=("gray20","gray70"))
        self.status.grid(row=1, column=0, columnspan=2, sticky="w", padx=8, pady=(0,8))

        self.loading_var = ctk.StringVar(value="")
        self.loading_lbl = ctk.CTkLabel(top, textvariable=self.loading_var)
        self.loading_lbl.grid(row=1, column=2, padx=(6,8), pady=(0,8), sticky="e")

        self._loading_anim_running = False
        self._loading_anim_job = None

        # scrollable results
        self.scroll = ctk.CTkScrollableFrame(self, label_text="Results")
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0,12))
        self.scroll.grid_columnconfigure(1, weight=1)  # text column expands

        # Bind mouse wheel scroll
        self.scroll.bind("<MouseWheel>", self.on_mouse_wheel)

        # image cache to prevent GC
        self._image_cache = []  # keep CTkImage references alive

    # ----- helpers -----
    def _set_inputs_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self.btn.configure(state=state)
        self.entry.configure(state=state)

    def _start_loading_anim(self, text_base="Loading"):
        if self._loading_anim_running:
            return
        self._loading_anim_running = True
        dots = ["", ".", "..", "..."]
        idx = {"i": 0}
        def step():
            if not self._loading_anim_running:
                self.loading_var.set("")
                return
            self.loading_var.set(f"{text_base}{dots[idx['i'] % len(dots)]}")
            idx["i"] += 1
            self._loading_anim_job = self.after(300, step)
        step()

    def _stop_loading_anim(self):
        self._loading_anim_running = False
        if self._loading_anim_job is not None:
            self.after_cancel(self._loading_anim_job)
            self._loading_anim_job = None
        self.loading_var.set("")

    def set_status(self, msg: str):
        self.status.configure(text=msg)

    # ----- search flow -----
    def on_search(self):
        query = self.q_var.get().strip()
        self.set_status("Searching...")
        self._set_inputs_enabled(False)      # disable controls until load completes
        self._start_loading_anim("Loading")  # start spinner-like animation
        threading.Thread(target=self._search_thread, args=(query,), daemon=True).start()

    def _search_thread(self, query: str):
        data, err = api_search(query)
        self.after(0, self._populate_results, data, err)

    # ----- results rendering -----
    def _clear_results(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        self._image_cache.clear()

    def _populate_results(self, items, err):
        self._clear_results()
        if err:
            self.set_status(err)
        else:
            self.set_status(f"Found {len(items)} result(s).")
        # build rows: [image] [title/path] [button]
        for r, it in enumerate(items):
            title = it.get("title") or "Untitled"
            path = it.get("path") or ""
            img_url = it.get("img") or ""
            dl = it.get("download")

            # image placeholder
            img_lbl = ctk.CTkLabel(self.scroll, text="")
            img_lbl.grid(row=r, column=0, padx=8, pady=8, sticky="w")

            # async image load to keep UI snappy
            def load_img(label=img_lbl, url=img_url):
                ctk_img = fetch_image(url)
                self._image_cache.append(ctk_img)
                self.after(0, lambda: label.configure(image=ctk_img))
            threading.Thread(target=load_img, daemon=True).start()

            # text column
            text_frame = ctk.CTkFrame(self.scroll)
            text_frame.grid(row=r, column=1, padx=8, pady=8, sticky="nsew")
            text_frame.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(text_frame, text=title, anchor="w", wraplength=560, justify="left").grid(
                row=0, column=0, sticky="w", padx=8, pady=(6,2)
            )
            ctk.CTkLabel(text_frame, text=path, anchor="w", text_color=("gray20", "gray70")).grid(
                row=1, column=0, sticky="w", padx=8, pady=(0,6)
            )

            # action button
            btn_text = "Open Download" if dl else "No Download"
            ctk.CTkButton(self.scroll, text=btn_text,
                          state=("normal" if dl else "disabled"),
                          command=(lambda link=dl: open_url(link))
            ).grid(row=r, column=2, padx=8, pady=8, sticky="e")

        # stop animation and re-enable inputs
        self._stop_loading_anim()
        self._set_inputs_enabled(True)

    # ----- mouse wheel scroll handling -----
    def on_mouse_wheel(self, event):
        # Scroll up or down using mouse wheel
        self.scroll.yview_scroll(-1 if event.delta > 0 else 1, "units")

def main():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
