import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from PIL import Image, ImageDraw, ImageFont, ImageTk, ImageGrab
import os, sys, threading

YT_W, YT_H = 1280, 720
PV_W, PV_H = 854, 480

BG       = "#1a1a22"
SURFACE  = "#22222c"
SURFACE2 = "#2a2a36"
ACCENT   = "#4da6ff"
TEXT     = "#e8e8f0"
MUTED    = "#555577"
BORDER   = "#3a3a52"
DANGER   = "#ff4444"
SUCCESS  = "#44ffaa"
SEL_COL  = "#ff3333"

def resource_path(rel):
    try:
        base = sys._MEIPASS
    except AttributeError:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, rel)

def get_windows_fonts():
    fd = os.path.join(os.environ.get("WINDIR","C:\\Windows"),"Fonts")
    out = []
    if os.path.isdir(fd):
        for f in os.listdir(fd):
            if f.lower().endswith((".ttf",".otf")):
                out.append(f)
    return sorted(out)

def find_font(name):
    fd = os.path.join(os.environ.get("WINDIR","C:\\Windows"),"Fonts")
    p = os.path.join(fd, name)
    return p if os.path.exists(p) else None

def mkbtn(parent, text, cmd, color=ACCENT, bg=SURFACE2):
    return tk.Button(parent, text=text, command=cmd,
                     bg=bg, fg=color,
                     activebackground=ACCENT, activeforeground=BG,
                     relief="flat", bd=0, cursor="hand2",
                     font=("Segoe UI",9,"bold"), padx=10, pady=6,
                     highlightthickness=1, highlightbackground=ACCENT)

class ImageState:
    def __init__(self, path):
        self.path  = path
        self.ox    = 0.0   # pan X em fração do canvas
        self.oy    = 0.0   # pan Y em fração do canvas
        self.scale = 1.0   # zoom

class KioThumb(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("KioThumb")
        self.geometry("1150x720")
        self.minsize(950,620)
        self.configure(bg=BG)
        self.resizable(True,True)

        # Ícone
        try:
            ip = resource_path("icone.png")
            self._ico = tk.PhotoImage(file=ip)
            self.iconphoto(True, self._ico)
        except: pass

        # Estado
        self.img_states   = []
        self.current_idx  = 0
        self.custom_fonts = {}
        self.logo_pil     = None
        self.selected     = None   # None | "image" | "text" | "logo"
        self._drag_sx     = 0
        self._drag_sy     = 0
        self._drag_ref    = {}
        self._list_drag_start = None

        # Vars globais
        self.prefix_var     = tk.StringVar(value="#")
        self.start_var      = tk.IntVar(value=1)
        self.font_var       = tk.StringVar(value="arialbd.ttf")
        self.font_size_var  = tk.IntVar(value=72)
        self.text_color     = "#ffffff"
        self.outline_on     = tk.BooleanVar(value=True)
        self.outline_color  = "#000000"
        self.outline_sz_var = tk.IntVar(value=3)
        self.logo_on        = tk.BooleanVar(value=False)
        self.logo_size_var  = tk.IntVar(value=180)
        self.qty_var        = tk.IntVar(value=5)

        # Posições globais (fração 0-1)
        self.text_fx = 0.05
        self.text_fy = 0.78
        self.logo_fx = 0.72
        self.logo_fy = 0.04

        self._build()
        self._refresh_preview()
        self.bind("<Control-v>", self._paste)
        self.bind("<Control-V>", self._paste)

    # ══════════════════════════════════════════════════════════════════════════
    # BUILD UI
    # ══════════════════════════════════════════════════════════════════════════
    def _build(self):
        # ── Header ──
        hdr = tk.Frame(self, bg=BG, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        try:
            ic = Image.open(resource_path("icone.png")).convert("RGBA")
            ic.thumbnail((42,42))
            self._hico = ImageTk.PhotoImage(ic)
            tk.Label(hdr, image=self._hico, bg=BG).pack(side="left",padx=(14,8),pady=6)
        except: pass
        tk.Label(hdr, text="KioThumb", bg=BG, fg=ACCENT,
                 font=("Times New Roman",22,"bold")).pack(side="left",pady=6)
        tk.Label(hdr, text="Gerador de Thumbnails para Longplay", bg=BG, fg=MUTED,
                 font=("Segoe UI",8)).pack(side="left",padx=12)
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        # Colunas
        left = tk.Frame(body, bg=SURFACE, width=180)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        self._build_left(left)

        right = tk.Frame(body, bg=SURFACE, width=235)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)
        self._build_right(right)

        mid = tk.Frame(body, bg=BG)
        mid.pack(side="left", fill="both", expand=True)
        self._build_center(mid)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")
        self._build_footer()

    # ── Esquerda ──────────────────────────────────────────────────────────────
    def _build_left(self, p):
        tk.Label(p, text="IMAGENS", bg=SURFACE, fg=MUTED,
                 font=("Segoe UI",8,"bold")).pack(pady=(10,4),padx=8,anchor="w")
        mkbtn(p, "+ Adicionar", self._add_images).pack(fill="x",padx=8,pady=(0,2))
        tk.Label(p, text="ou Ctrl+V para colar print",
                 bg=SURFACE, fg="#333355", font=("Segoe UI",7)).pack(padx=8,anchor="w")
        tk.Frame(p, bg=BORDER, height=1).pack(fill="x", pady=6)

        c = tk.Canvas(p, bg=SURFACE, highlightthickness=0)
        sb = tk.Scrollbar(p, orient="vertical", command=c.yview)
        c.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        c.pack(side="left", fill="both", expand=True)
        self._list_inner = tk.Frame(c, bg=SURFACE)
        win = c.create_window((0,0), window=self._list_inner, anchor="nw")
        self._list_inner.bind("<Configure>", lambda e: c.configure(scrollregion=c.bbox("all")))
        c.bind("<Configure>", lambda e: c.itemconfig(win, width=e.width))

    def _refresh_list(self):
        for w in self._list_inner.winfo_children():
            w.destroy()
        for i, st in enumerate(self.img_states):
            self._make_item(i, st)

    def _make_item(self, i, st):
        is_cur = (i == self.current_idx)
        bg2 = ACCENT if is_cur else SURFACE2
        fg2 = BG if is_cur else TEXT

        fr = tk.Frame(self._list_inner, bg=bg2, cursor="hand2",
                      highlightthickness=1,
                      highlightbackground=ACCENT if is_cur else BORDER)
        fr.pack(fill="x", padx=6, pady=2)

        try:
            im = Image.open(st.path).convert("RGB")
            im.thumbnail((46,32))
            ph = ImageTk.PhotoImage(im)
            ll = tk.Label(fr, image=ph, bg=bg2)
            ll.image = ph
            ll.pack(side="left",padx=3,pady=3)
        except:
            tk.Label(fr, text="?", bg=bg2, fg=fg2,
                     font=("Segoe UI",10)).pack(side="left",padx=4)

        name = os.path.basename(st.path)
        if len(name)>14: name=name[:12]+"…"
        tk.Label(fr, text=f"#{i+1} {name}", bg=bg2, fg=fg2,
                 font=("Segoe UI",8)).pack(side="left",fill="x",expand=True)

        tk.Button(fr, text="✕", bg=bg2, fg=DANGER, relief="flat", bd=0,
                  cursor="hand2", font=("Segoe UI",8),
                  command=lambda idx=i: self._remove(idx)).pack(side="right",padx=3)

        for w in fr.winfo_children():
            if not isinstance(w, tk.Button):
                w.bind("<ButtonPress-1>",   lambda e,idx=i: self._lpress(e,idx))
                w.bind("<B1-Motion>",       lambda e,idx=i: self._lmotion(e,idx))
                w.bind("<ButtonRelease-1>", lambda e,idx=i: self._lrelease(e,idx))
        fr.bind("<ButtonPress-1>",   lambda e,idx=i: self._lpress(e,idx))
        fr.bind("<B1-Motion>",       lambda e,idx=i: self._lmotion(e,idx))
        fr.bind("<ButtonRelease-1>", lambda e,idx=i: self._lrelease(e,idx))

    def _lpress(self, e, idx):
        self._list_drag_start = (idx, e.y_root)

    def _lmotion(self, e, idx):
        pass

    def _lrelease(self, e, idx):
        if self._list_drag_start is None: return
        orig, y0 = self._list_drag_start
        dy = e.y_root - y0
        new = orig
        if dy < -20 and orig > 0:         new = orig-1
        elif dy > 20 and orig < len(self.img_states)-1: new = orig+1
        if new != orig:
            self.img_states.insert(new, self.img_states.pop(orig))
            if self.current_idx == orig: self.current_idx = new
            elif self.current_idx == new: self.current_idx = orig
        else:
            self.current_idx = idx
        self._list_drag_start = None
        self._refresh_list()
        self._refresh_preview()

    # ── Centro ────────────────────────────────────────────────────────────────
    def _build_center(self, p):
        fr = tk.Frame(p, bg=BG)
        fr.pack(expand=True)
        self.cv = tk.Canvas(fr, width=PV_W, height=PV_H, bg="#111118",
                            cursor="crosshair",
                            highlightthickness=2, highlightbackground=ACCENT)
        self.cv.pack(pady=20)
        self.cv.bind("<ButtonPress-1>",   self._cvpress)
        self.cv.bind("<B1-Motion>",       self._cvdrag)
        self.cv.bind("<ButtonRelease-1>", self._cvrelease)
        self.cv.bind("<MouseWheel>",      self._cvscroll)

    # ── Direita ───────────────────────────────────────────────────────────────
    def _build_right(self, p):
        c = tk.Canvas(p, bg=SURFACE, highlightthickness=0)
        sb = tk.Scrollbar(p, orient="vertical", command=c.yview)
        c.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        c.pack(fill="both", expand=True)
        inn = tk.Frame(c, bg=SURFACE)
        win = c.create_window((0,0), window=inn, anchor="nw")
        inn.bind("<Configure>", lambda e: c.configure(scrollregion=c.bbox("all")))
        c.bind("<Configure>", lambda e: c.itemconfig(win, width=e.width))

        pad = dict(padx=10, pady=2)

        def sec(txt):
            tk.Frame(inn, bg=BORDER, height=1).pack(fill="x",pady=(10,4))
            tk.Label(inn, text=txt, bg=SURFACE, fg=MUTED,
                     font=("Segoe UI",7,"bold")).pack(anchor="w",padx=10)

        # Texto
        tk.Label(inn, text="TEXTO / NUMERAÇÃO", bg=SURFACE, fg=MUTED,
                 font=("Segoe UI",7,"bold")).pack(anchor="w",padx=10,pady=(12,4))

        r = tk.Frame(inn,bg=SURFACE); r.pack(fill="x",**pad)
        tk.Label(r,text="Prefixo:",bg=SURFACE,fg=TEXT,font=("Segoe UI",9)).pack(side="left")
        e=tk.Entry(r,textvariable=self.prefix_var,width=6,
                   bg=SURFACE2,fg=TEXT,insertbackground=TEXT,relief="flat",
                   highlightthickness=1,highlightbackground=BORDER,
                   highlightcolor=ACCENT,font=("Segoe UI",9))
        e.pack(side="left",padx=4)
        e.bind("<KeyRelease>",lambda e:self._refresh_preview())

        r2=tk.Frame(inn,bg=SURFACE); r2.pack(fill="x",**pad)
        tk.Label(r2,text="Início em:",bg=SURFACE,fg=TEXT,font=("Segoe UI",9)).pack(side="left")
        e2=tk.Entry(r2,textvariable=self.start_var,width=5,
                    bg=SURFACE2,fg=TEXT,insertbackground=TEXT,relief="flat",
                    highlightthickness=1,highlightbackground=BORDER,
                    highlightcolor=ACCENT,font=("Segoe UI",9))
        e2.pack(side="left",padx=4)
        e2.bind("<KeyRelease>",lambda e:self._refresh_preview())

        sec("FONTE")
        tk.Label(inn,text="Fonte:",bg=SURFACE,fg=TEXT,font=("Segoe UI",8)).pack(anchor="w",padx=10)
        self.font_combo=ttk.Combobox(inn,textvariable=self.font_var,
                                      font=("Segoe UI",8),state="readonly")
        self.font_combo["values"]=get_windows_fonts()
        self.font_combo.pack(fill="x",padx=10,pady=2)
        self.font_combo.bind("<<ComboboxSelected>>",lambda e:self._refresh_preview())

        mkbtn(inn,"⊕ Importar fonte (.ttf/.otf)",self._import_font).pack(fill="x",padx=10,pady=3)
        self._imp_lbl=tk.Label(inn,text="",bg=SURFACE,fg=SUCCESS,font=("Segoe UI",7))
        self._imp_lbl.pack(anchor="w",padx=10)

        tk.Label(inn,text="Tamanho da fonte:",bg=SURFACE,fg=TEXT,
                 font=("Segoe UI",8)).pack(anchor="w",padx=10,pady=(6,0))
        fs=tk.Frame(inn,bg=SURFACE); fs.pack(fill="x",padx=10,pady=2)
        self._fs_lbl=tk.Label(fs,text=str(self.font_size_var.get()),
                               bg=SURFACE,fg=ACCENT,font=("Segoe UI",9,"bold"),width=4)
        self._fs_lbl.pack(side="right")
        tk.Scale(fs,from_=8,to=300,orient="horizontal",variable=self.font_size_var,
                 showvalue=False,bg=SURFACE,troughcolor=SURFACE2,activebackground=ACCENT,
                 highlightthickness=0,
                 command=lambda v:(self._fs_lbl.config(text=v),self._refresh_preview())
                 ).pack(side="left",fill="x",expand=True)

        sec("COR E CONTORNO")
        cr=tk.Frame(inn,bg=SURFACE); cr.pack(fill="x",padx=10,pady=3)
        tk.Label(cr,text="Cor do texto:",bg=SURFACE,fg=TEXT,font=("Segoe UI",8)).pack(side="left")
        self._tcol=tk.Button(cr,bg=self.text_color,width=3,relief="flat",cursor="hand2",
                              highlightthickness=1,highlightbackground=BORDER,
                              command=self._pick_text)
        self._tcol.pack(side="left",padx=6)

        tk.Checkbutton(inn,text="Contorno",variable=self.outline_on,
                       bg=SURFACE,fg=TEXT,selectcolor=SURFACE2,
                       activebackground=SURFACE,font=("Segoe UI",8),
                       command=self._refresh_preview).pack(anchor="w",padx=10)

        ocr=tk.Frame(inn,bg=SURFACE); ocr.pack(fill="x",padx=10,pady=2)
        tk.Label(ocr,text="Cor do contorno:",bg=SURFACE,fg=TEXT,font=("Segoe UI",8)).pack(side="left")
        self._ocol=tk.Button(ocr,bg=self.outline_color,width=3,relief="flat",cursor="hand2",
                              highlightthickness=1,highlightbackground=BORDER,
                              command=self._pick_outline)
        self._ocol.pack(side="left",padx=6)

        tk.Label(inn,text="Espessura do contorno:",bg=SURFACE,fg=TEXT,
                 font=("Segoe UI",8)).pack(anchor="w",padx=10,pady=(4,0))
        os_=tk.Frame(inn,bg=SURFACE); os_.pack(fill="x",padx=10,pady=2)
        self._os_lbl=tk.Label(os_,text=str(self.outline_sz_var.get()),
                               bg=SURFACE,fg=ACCENT,font=("Segoe UI",9,"bold"),width=3)
        self._os_lbl.pack(side="right")
        tk.Scale(os_,from_=1,to=20,orient="horizontal",variable=self.outline_sz_var,
                 showvalue=False,bg=SURFACE,troughcolor=SURFACE2,activebackground=ACCENT,
                 highlightthickness=0,
                 command=lambda v:(self._os_lbl.config(text=v),self._refresh_preview())
                 ).pack(side="left",fill="x",expand=True)

        sec("LOGO DO JOGO (opcional)")
        tk.Checkbutton(inn,text="Adicionar logo",variable=self.logo_on,
                       bg=SURFACE,fg=TEXT,selectcolor=SURFACE2,
                       activebackground=SURFACE,font=("Segoe UI",8),
                       command=self._refresh_preview).pack(anchor="w",padx=10)

        self._logo_fr=tk.Frame(inn,bg=SURFACE)
        self._logo_fr.pack(fill="x",padx=10)
        mkbtn(self._logo_fr,"📂 Escolher PNG da logo",self._pick_logo).pack(fill="x",pady=3)
        self._logo_lbl=tk.Label(self._logo_fr,text="Nenhuma logo",
                                bg=SURFACE,fg="#333355",font=("Segoe UI",7))
        self._logo_lbl.pack(anchor="w")

        tk.Label(self._logo_fr,text="Tamanho da logo:",bg=SURFACE,fg=TEXT,
                 font=("Segoe UI",8)).pack(anchor="w",pady=(6,0))
        ls=tk.Frame(self._logo_fr,bg=SURFACE); ls.pack(fill="x",pady=2)
        self._ls_lbl=tk.Label(ls,text=str(self.logo_size_var.get()),
                               bg=SURFACE,fg=ACCENT,font=("Segoe UI",9,"bold"),width=4)
        self._ls_lbl.pack(side="right")
        tk.Scale(ls,from_=20,to=1000,orient="horizontal",variable=self.logo_size_var,
                 showvalue=False,bg=SURFACE,troughcolor=SURFACE2,activebackground=ACCENT,
                 highlightthickness=0,
                 command=lambda v:(self._ls_lbl.config(text=v),self._refresh_preview())
                 ).pack(side="left",fill="x",expand=True)

    # ── Rodapé ────────────────────────────────────────────────────────────────
    def _build_footer(self):
        ft=tk.Frame(self,bg=SURFACE,height=50)
        ft.pack(fill="x")
        ft.pack_propagate(False)

        lf=tk.Frame(ft,bg=SURFACE); lf.pack(side="left",padx=16,pady=10)
        tk.Label(lf,text="Quantidade:",bg=SURFACE,fg=TEXT,
                 font=("Segoe UI",9)).pack(side="left")
        tk.Spinbox(lf,from_=1,to=999,textvariable=self.qty_var,
                   width=5,bg=SURFACE2,fg=TEXT,relief="flat",
                   buttonbackground=SURFACE2,font=("Segoe UI",9)).pack(side="left",padx=6)

        cf=tk.Frame(ft,bg=SURFACE); cf.pack(side="left",expand=True)
        self._gen_btn=mkbtn(cf,"▶  GERAR THUMBNAILS",self._generate,color=BG,bg=ACCENT)
        self._gen_btn.config(font=("Segoe UI",10,"bold"),pady=8,padx=24)
        self._gen_btn.pack()

        rf=tk.Frame(ft,bg=SURFACE); rf.pack(side="right",padx=16)
        self._res_lbl=tk.Label(rf,text="",bg=SURFACE,fg="#252535",font=("Segoe UI",7))
        self._res_lbl.pack()
        self._update_res()

    # ══════════════════════════════════════════════════════════════════════════
    # PREVIEW
    # ══════════════════════════════════════════════════════════════════════════
    def _refresh_preview(self, *_):
        try:
            st  = self.img_states[self.current_idx] if self.img_states else None
            num = self.start_var.get() + self.current_idx
            img = self._compose(st, num, PV_W, PV_H)
            self._pvphoto = ImageTk.PhotoImage(img)
            self.cv.delete("all")
            self.cv.create_image(0,0,anchor="nw",image=self._pvphoto)
            self._draw_sel()
        except Exception as ex:
            self.cv.delete("all")
            self.cv.create_text(PV_W//2,PV_H//2,
                                text=f"Preview indisponível\n{ex}",
                                fill=MUTED,font=("Segoe UI",10),justify="center")

    def _compose(self, st, number, W, H):
        """Composição final. W,H pode ser PV ou YT."""
        base = Image.new("RGB",(W,H),"#111118")

        # ── Imagem de fundo ──
        if st and os.path.exists(st.path):
            try:
                src = Image.open(st.path).convert("RGB")
                sw, sh = src.size

                # Escala base para cobrir o canvas × zoom do usuário
                base_scale = max(W/sw, H/sh) * st.scale
                nw = max(1, int(sw * base_scale))
                nh = max(1, int(sh * base_scale))
                scaled = src.resize((nw, nh), Image.LANCZOS)

                # Centro + offset de pan (em pixels do canvas escalado)
                cx = nw//2 + int(st.ox * W)
                cy = nh//2 + int(st.oy * H)

                left = cx - W//2
                top  = cy - H//2
                right = left + W
                bot   = top  + H

                # Clamp
                if left < 0:    left,right = 0, W
                if top  < 0:    top, bot   = 0, H
                if right > nw:  left,right = nw-W, nw
                if bot   > nh:  top, bot   = nh-H, nh

                left  = max(0, min(left,  nw-1))
                top   = max(0, min(top,   nh-1))
                right = max(1, min(right, nw))
                bot   = max(1, min(bot,   nh))

                crop = scaled.crop((left,top,right,bot))
                if crop.size != (W,H):
                    crop = crop.resize((W,H), Image.LANCZOS)
                base.paste(crop,(0,0))
            except Exception:
                pass

        draw = ImageDraw.Draw(base)

        # ── Texto ──
        label = f"{self.prefix_var.get()}{number}"
        fsize = max(8, int(self.font_size_var.get() * W / YT_W))
        font  = self._load_font(fsize)
        tx = int(self.text_fx * W)
        ty = int(self.text_fy * H)

        if self.outline_on.get():
            osz = max(1, int(self.outline_sz_var.get() * W / YT_W))
            for dx in range(-osz, osz+1):
                for dy in range(-osz, osz+1):
                    if dx or dy:
                        draw.text((tx+dx,ty+dy),label,font=font,fill=self.outline_color)
        draw.text((tx,ty),label,font=font,fill=self.text_color)

        # ── Logo ──
        if self.logo_on.get() and self.logo_pil:
            # Escala o tamanho da logo proporcionalmente ao canvas/YT
            lsz = max(10, int(self.logo_size_var.get() * W / YT_W))
            logo = self.logo_pil.copy()
            logo.thumbnail((lsz,lsz), Image.LANCZOS)
            lx = int(self.logo_fx * W)
            ly = int(self.logo_fy * H)
            if logo.mode=="RGBA":
                base.paste(logo,(lx,ly),logo)
            else:
                base.paste(logo,(lx,ly))

        return base

    def _draw_sel(self):
        if self.selected is None: return
        if self.selected=="text":
            tx=int(self.text_fx*PV_W); ty=int(self.text_fy*PV_H)
            fsize=max(8,int(self.font_size_var.get()*PV_W/YT_W))
            self.cv.create_rectangle(tx-6,ty-6,tx+fsize*5,ty+fsize+10,
                                     outline=SEL_COL,width=2,dash=(4,3))
        elif self.selected=="logo" and self.logo_on.get() and self.logo_pil:
            lsz=max(10,int(self.logo_size_var.get()*PV_W/YT_W))
            lx=int(self.logo_fx*PV_W); ly=int(self.logo_fy*PV_H)
            self.cv.create_rectangle(lx-6,ly-6,lx+lsz+6,ly+lsz+6,
                                     outline=SEL_COL,width=2,dash=(4,3))
        elif self.selected=="image":
            self.cv.create_rectangle(4,4,PV_W-4,PV_H-4,
                                     outline=SEL_COL,width=2,dash=(6,4))

    # ══════════════════════════════════════════════════════════════════════════
    # HIT TEST
    # ══════════════════════════════════════════════════════════════════════════
    def _hit(self, x, y):
        # Texto
        tx=int(self.text_fx*PV_W); ty=int(self.text_fy*PV_H)
        fsize=max(8,int(self.font_size_var.get()*PV_W/YT_W))
        if tx-6<=x<=tx+fsize*5 and ty-6<=y<=ty+fsize+10:
            return "text"
        # Logo
        if self.logo_on.get() and self.logo_pil:
            lsz=max(10,int(self.logo_size_var.get()*PV_W/YT_W))
            lx=int(self.logo_fx*PV_W); ly=int(self.logo_fy*PV_H)
            if lx-6<=x<=lx+lsz+6 and ly-6<=y<=ly+lsz+6:
                return "logo"
        return "image"

    # ══════════════════════════════════════════════════════════════════════════
    # CANVAS EVENTOS
    # ══════════════════════════════════════════════════════════════════════════
    def _cvpress(self, e):
        self.selected = self._hit(e.x, e.y)
        self._drag_sx = e.x
        self._drag_sy = e.y
        st = self.img_states[self.current_idx] if self.img_states else None
        self._drag_ref = {
            "tx": self.text_fx, "ty": self.text_fy,
            "lx": self.logo_fx, "ly": self.logo_fy,
            "ox": st.ox if st else 0.0,
            "oy": st.oy if st else 0.0,
        }
        self._refresh_preview()

    def _cvdrag(self, e):
        if self.selected is None: return
        dx = (e.x - self._drag_sx) / PV_W
        dy = (e.y - self._drag_sy) / PV_H
        if self.selected=="text":
            self.text_fx = max(0.0,min(0.95,self._drag_ref["tx"]+dx))
            self.text_fy = max(0.0,min(0.95,self._drag_ref["ty"]+dy))
        elif self.selected=="logo":
            self.logo_fx = max(0.0,min(0.95,self._drag_ref["lx"]+dx))
            self.logo_fy = max(0.0,min(0.95,self._drag_ref["ly"]+dy))
        elif self.selected=="image" and self.img_states:
            st = self.img_states[self.current_idx]
            # INVERTIDO: mouse pra cima = imagem desce (ox/oy subtraem)
            st.ox = self._drag_ref["ox"] - dx
            st.oy = self._drag_ref["oy"] - dy
        self._refresh_preview()

    def _cvrelease(self, e):
        pass

    def _cvscroll(self, e):
        delta = 1 if e.delta > 0 else -1
        hit = self._hit(e.x, e.y)
        if hit=="logo" and self.logo_on.get() and self.logo_pil:
            new = max(20,min(1000,self.logo_size_var.get()+delta*15))
            self.logo_size_var.set(new)
            self._ls_lbl.config(text=str(new))
        elif self.img_states:
            st = self.img_states[self.current_idx]
            st.scale = max(0.1,min(10.0,st.scale+delta*0.05))
        self._refresh_preview()

    # ══════════════════════════════════════════════════════════════════════════
    # AÇÕES
    # ══════════════════════════════════════════════════════════════════════════
    def _add_images(self):
        paths = filedialog.askopenfilenames(
            title="Selecionar imagens",
            filetypes=[("Imagens","*.png *.jpg *.jpeg *.bmp *.webp"),("Todos","*.*")])
        for p in paths:
            if not any(s.path==p for s in self.img_states):
                self.img_states.append(ImageState(p))
        self._refresh_list()
        self._refresh_preview()

    def _remove(self, idx):
        self.img_states.pop(idx)
        if self.current_idx >= len(self.img_states):
            self.current_idx = max(0,len(self.img_states)-1)
        self._refresh_list()
        self._refresh_preview()

    def _paste(self, event=None):
        try:
            img = ImageGrab.grabclipboard()
            if img is None:
                messagebox.showinfo("KioThumb","Nenhuma imagem encontrada.\nPressione Print Screen antes.")
                return
            if isinstance(img, Image.Image):
                import tempfile
                tmp = tempfile.mktemp(suffix=".png")
                img.save(tmp)
                self.img_states.append(ImageState(tmp))
                self._refresh_list()
                self._refresh_preview()
        except Exception as ex:
            messagebox.showerror("KioThumb",f"Erro ao colar:\n{ex}")

    def _import_font(self):
        p = filedialog.askopenfilename(title="Importar fonte",
                                       filetypes=[("Fontes","*.ttf *.otf")])
        if not p: return
        name = os.path.basename(p)
        self.custom_fonts[name] = p
        self.font_combo["values"] = list(self.font_combo["values"]) + [name]
        self.font_var.set(name)
        self._imp_lbl.config(text=f"✔ {name}")
        self._refresh_preview()

    def _pick_text(self):
        c = colorchooser.askcolor(color=self.text_color,title="Cor do texto")
        if c and c[1]:
            self.text_color=c[1]; self._tcol.config(bg=c[1]); self._refresh_preview()

    def _pick_outline(self):
        c = colorchooser.askcolor(color=self.outline_color,title="Cor do contorno")
        if c and c[1]:
            self.outline_color=c[1]; self._ocol.config(bg=c[1]); self._refresh_preview()

    def _pick_logo(self):
        p = filedialog.askopenfilename(title="Logo do jogo",
                                       filetypes=[("PNG","*.png"),("Imagens","*.png *.jpg *.jpeg"),("Todos","*.*")])
        if not p: return
        self.logo_pil = Image.open(p).convert("RGBA")
        name = os.path.basename(p)
        self._logo_lbl.config(text=name[:24] if len(name)<=24 else name[:22]+"…")
        self._refresh_preview()

    def _load_font(self, size):
        sel  = self.font_var.get()
        path = self.custom_fonts.get(sel) or find_font(sel)
        try:
            if path and os.path.exists(path):
                return ImageFont.truetype(path,size)
        except: pass
        try:    return ImageFont.truetype("arial.ttf",size)
        except: return ImageFont.load_default()

    # ── Geração ───────────────────────────────────────────────────────────────
    def _generate(self):
        qty = self.qty_var.get()
        n   = len(self.img_states)
        if n==0:
            messagebox.showwarning("KioThumb","Adicione pelo menos uma imagem!"); return
        if n>1 and n<qty:
            ok = messagebox.askyesno("KioThumb — Atenção",
                f"Você pediu {qty} thumbnail(s), mas adicionou apenas {n} imagem(ns).\n\n"
                f"A imagem #{n} será repetida nas thumbnails restantes.\n\nContinuar?")
            if not ok: return

        folder = filedialog.askdirectory(title="Onde salvar as thumbnails?")
        if not folder: return

        self._gen_btn.config(state="disabled",text="Gerando…")
        self.update_idletasks()

        def worker():
            try:
                start = self.start_var.get()
                for i in range(qty):
                    num = start+i
                    st  = self.img_states[0] if n==1 else (
                          self.img_states[i] if i<n else self.img_states[n-1])
                    img = self._compose(st, num, YT_W, YT_H)
                    pref = "".join(c for c in self.prefix_var.get().strip()
                                   if c.isalnum() or c in "-_") or "thumb"
                    img.convert("RGB").save(
                        os.path.join(folder,f"{pref}{num}.jpg"),
                        "JPEG",quality=92,optimize=True)
                self.after(0,lambda: messagebox.showinfo("KioThumb",
                    f"✔ {qty} thumbnail(s) salva(s) em:\n{folder}"))
            except Exception as ex:
                self.after(0,lambda: messagebox.showerror("KioThumb",f"Erro:\n{ex}"))
            finally:
                self.after(0,lambda: self._gen_btn.config(
                    state="normal",text="▶  GERAR THUMBNAILS"))

        threading.Thread(target=worker,daemon=True).start()

    # ── Monitor recursos ──────────────────────────────────────────────────────
    def _update_res(self):
        try:
            import psutil
            proc = psutil.Process(os.getpid())
            cpu  = proc.cpu_percent(interval=None)
            ram  = proc.memory_info().rss/1024/1024
            self._res_lbl.config(text=f"cpu {cpu:.0f}%  ram {ram:.0f}mb")
            if ram>800:
                messagebox.showwarning("KioThumb",
                    "Uso de memória muito alto. Encerrando para proteger seu PC.")
                self.destroy(); return
        except: pass
        self.after(3000,self._update_res)

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__=="__main__":
    try:
        import psutil
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable,"-m","pip","install","psutil"])
        import psutil
    KioThumb().mainloop()
