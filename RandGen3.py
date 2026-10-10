import json
import math
import os
import random
import tkinter as tk
import traceback
from tkinter import font as tkfont
from tkinter import messagebox, ttk


DATA_FILE = "school_data.json"
LOG_FILE = "error_log.txt"

# ---------------------------------------------------------------------------
# Настройки внешнего вида
# ---------------------------------------------------------------------------
# Общий множитель размера шрифта: 1.0 — мелко, 1.3 — крупно для проектора.
FONT_SCALE = 1.3

# Принцип оформления: ВСЁ, НА ЧТО МОЖНО НАЖАТЬ, — сплошные насыщенные кнопки
# с тёмной окантовкой. Всё, что только показывает информацию, — светлое.
BG = "#CFE0F2"  # фон окон — «небо»
CARD = "#FFFFFF"  # карточки
BORDER = "#667C9C"  # рамки карточек
TEXT = "#0B1B33"  # основной текст
MUTED = "#33445E"  # второстепенный текст

PRIMARY = "#1D4ED8"
TEAL = "#0F766E"
VIOLET = "#6D28D9"
SLATE_DARK = "#334155"
ORANGE = "#B45309"
AMBER_BG = "#FBE3A1"  # блок «Никто»
AMBER_TEXT = "#5B2A00"
CHIP_BG = "#E3ECF7"  # плашка с весом/диапазоном
VIOLET_BG = "#EDE9FE"  # светлая плашка «оценок»


def load_data():
  if os.path.exists(DATA_FILE):
    try:
      with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        users_vals = list(data.get("users", {}).values())
        if users_vals and isinstance(users_vals[0], str):
          old_users = data["users"]
          new_data = {"users": {}}
          for name, pwd in old_users.items():
            new_data["users"][name] = {
                "password": pwd,
                "classes": {},
                "round_counter": 0,
            }
          return new_data
        return data
    except json.JSONDecodeError:
      pass
  return {
      "users": {
          "admin": {
              "password": "1234",
              "classes": {
                  "10А": [{
                      "name": "Тайнов Алексей",
                      "grades": 0,
                      "selected": False,
                      "last_round": 0,
                  }]
              },
              "round_counter": 0,
          }
      }
  }


def save_data(data):
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)


app_data = load_data()
app_data.setdefault("nobody_configs", {})


root = tk.Tk()
root.withdraw()
root.title("Авторизация")
root.configure(bg=BG)

try:
  icon = tk.PhotoImage(file="icon.png")
  root.iconphoto(True, icon)
except Exception:
  pass


# ---------------------------------------------------------------------------
# Если где-то случится ошибка: пишем её в error_log.txt и показываем окно,
# а не даём программе молча упасть.
# ---------------------------------------------------------------------------
_reporting = {"busy": False}


def report_exception(exc, val, tb):
  text = "".join(traceback.format_exception(exc, val, tb))
  try:
    with open(LOG_FILE, "a", encoding="utf-8") as f:
      f.write(text + "\n")
  except OSError:
    pass
  try:
    print(text)
  except Exception:
    pass
  if _reporting["busy"]:
    return
  _reporting["busy"] = True
  try:
    messagebox.showerror(
        "Ошибка",
        f"Что-то пошло не так:\n\n{val}\n\nПодробности записаны в файл"
        f" {LOG_FILE}",
    )
  except Exception:
    pass
  finally:
    _reporting["busy"] = False


root.report_callback_exception = report_exception


# ---------------------------------------------------------------------------
# Шрифт и ttk-стили
# ---------------------------------------------------------------------------
def pick_font():
  available = set(tkfont.families(root))
  for name in (
      "Segoe UI",
      "SF Pro Text",
      "Helvetica Neue",
      "Ubuntu",
      "Noto Sans",
      "DejaVu Sans",
      "Arial",
  ):
    if name in available:
      return name
  return "Helvetica"


FONT = pick_font()


def F(size, weight="normal"):
  return (FONT, max(8, round(size * FONT_SCALE)), weight)


def FM(size):
  """Моноширинный шрифт для чисел (вес/диапазон)."""
  return ("Courier", max(8, round(size * FONT_SCALE)), "bold")


style = ttk.Style(root)
try:
  style.theme_use("clam")
except tk.TclError:
  pass
style.layout(
    "Modern.Vertical.TScrollbar",
    [(
        "Vertical.Scrollbar.trough",
        {
            "children": [(
                "Vertical.Scrollbar.thumb",
                {"expand": "1", "sticky": "nswe"},
            )],
            "sticky": "ns",
        },
    )],
)
style.configure(
    "Modern.Vertical.TScrollbar",
    background="#7F93AE",
    troughcolor=BG,
    bordercolor=BG,
    lightcolor="#7F93AE",
    darkcolor="#7F93AE",
    relief="flat",
    gripcount=0,
    width=16,
)
style.map("Modern.Vertical.TScrollbar", background=[("active", "#5F7594")])


# ---------------------------------------------------------------------------
# Учёт открытых окон (чтобы двойное нажатие не открывало два одинаковых окна)
# ---------------------------------------------------------------------------
_single = {}


def reveal(win):
  """Показать окно, поднять его и передать ему фокус.

  Без этого на macOS первое нажатие в новом окне может уйти на «активацию»
  окна, а не на кнопку — отсюда ощущение, что кнопка «не нажимается».
  """
  win.deiconify()
  try:
    win.lift()
    win.focus_force()
  except tk.TclError:
    pass


def reuse_window(key):
  """Если окно с таким ключом уже открыто — выводим его вперёд и True."""
  win = _single.get(key)
  try:
    if win is not None and win.winfo_exists():
      reveal(win)
      return True
  except tk.TclError:
    pass
  return False


def replace_single(key, win):
  """Закрыть прежнее окно с этим ключом и запомнить новое."""
  old = _single.get(key)
  if old is not None and old is not win:
    try:
      old.destroy()
    except tk.TclError:
      pass
  _single[key] = win


# ---------------------------------------------------------------------------
# Свои виджеты
# ---------------------------------------------------------------------------
def round_rect(cv, x1, y1, x2, y2, r=8, **kw):
  pts = [
      x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
      x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
      x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
  ]  # fmt: skip
  return cv.create_polygon(pts, smooth=True, **kw)


class Btn(tk.Frame):
  """Кнопка для обычных окон. Срабатывает сразу в момент нажатия.

  Рамка — это фон внешнего Frame (а не highlightthickness у Label, который
  на macOS рисуется неровными линиями).

  Смысл цветов:
    primary — главное действие (синий)      add     — добавить (бирюзовый)
    success — «плюс», включить (зелёный)    minus   — «минус» (оранжевый)
    danger  — удалить / обнулить (красный)  info    — выбор (голубой)
    guest   — гость (фиолетовый)            neutral — закрыть / отмена (серый)
  """

  THEMES = {
      # (обычный, при наведении, нажатый/окантовка)
      "primary": ("#1D4ED8", "#1E3FA8", "#142C78"),
      "add": ("#0F766E", "#0B5F58", "#073E39"),
      "success": ("#15803D", "#106630", "#0A4521"),
      "minus": ("#C2410C", "#9F3509", "#6E2406"),
      "danger": ("#C0392B", "#9E2D21", "#6B1D15"),
      "info": ("#0E7490", "#0A5C73", "#063F4F"),
      "guest": ("#6D28D9", "#5720B0", "#3C1679"),
      "neutral": ("#475569", "#364152", "#222A36"),
  }

  def __init__(
      self, master, text, command=None, theme="primary", size=12,
      padx=18, pady=9, width=None,
  ):  # fmt: skip
    bg, hover, press = self.THEMES[theme]
    super().__init__(master, bg=press, cursor="hand2")
    opts = {}
    if width:
      opts["width"] = width
    self.lbl = tk.Label(
        self,
        text=text,
        bg=bg,
        fg="#FFFFFF",
        font=F(size, "bold"),
        padx=padx,
        pady=pady,
        cursor="hand2",
        **opts,
    )
    self.lbl.pack(fill="both", expand=True, padx=2, pady=2)
    self._theme = theme
    self._cmd = command
    self._down = False
    self._inside = False
    for w in (self, self.lbl):
      w.bind("<Enter>", self._on_enter)
      w.bind("<Leave>", self._on_leave)
      w.bind("<ButtonPress-1>", self._on_press)
      w.bind("<ButtonRelease-1>", self._on_release)

  def _paint(self, idx):
    try:
      self.lbl.config(bg=self.THEMES[self._theme][idx])
    except tk.TclError:
      pass

  def _on_enter(self, e=None):
    self._inside = True
    if not self._down:
      self._paint(1)

  def _on_leave(self, e=None):
    self._inside = False
    if not self._down:
      self._paint(0)

  def _on_press(self, e=None):
    self._down = True
    self._paint(2)
    if self._cmd:
      root.after(30, self._cmd)

  def _on_release(self, e=None):
    self._down = False
    self._paint(1 if self._inside else 0)


class CBtn:
  """Кнопка, нарисованная на холсте (для списка учеников).

  Нажатия обрабатываются не самими рисунками, а общим обработчиком холста
  по координатам курсора (см. show_students_window). Это надёжнее, чем
  привязка к элементам холста: клик не зависит от того, какой элемент Tk
  считает «текущим», и не теряется при перерисовке или пролёте чайки.
  """

  def __init__(self, cv, hits, x1, y1, x2, y2, text, command, theme, font):
    self.cv = cv
    self.cmd = command
    self.theme = theme
    self.box = (x1, y1, x2, y2)
    self.hover = False
    bg, hv, press = Btn.THEMES[theme]
    r = min(10, (y2 - y1) / 2)
    self.rect = round_rect(
        cv, x1, y1, x2, y2, r, fill=bg, outline=press, width=2, tags="ui"
    )  # fmt: skip
    self.txt = cv.create_text(
        (x1 + x2) / 2, (y1 + y2) / 2, text=text, fill="#FFFFFF", font=font,
        tags="ui",
    )  # fmt: skip
    hits.append(self)

  def _paint(self, idx):
    try:
      self.cv.itemconfig(
          self.rect, fill=Btn.THEMES[self.theme][idx],
          outline=Btn.THEMES[self.theme][2],
      )
    except tk.TclError:
      pass

  def set_hover(self, on):
    self.hover = on
    self._paint(1 if on else 0)

  def press(self):
    self._paint(2)
    if self.cmd:
      root.after(20, self.cmd)

  def release(self):
    self._paint(1 if self.hover else 0)

  def restyle(self, text, theme):
    self.theme = theme
    try:
      self.cv.itemconfig(self.txt, text=text)
    except tk.TclError:
      pass
    self._paint(1 if self.hover else 0)


class CCheck:
  """Чекбокс, нарисованный на холсте (с увеличенной зоной нажатия)."""

  def __init__(self, cv, hits, x, y, size, value, on_toggle):
    self.cv = cv
    self.x, self.y, self.s = x, y, size
    self.value = value
    self.on_toggle = on_toggle
    pad = 12
    self.box = (x - pad, y - pad, x + size + pad, y + size + pad)
    self.dtag = f"chk{id(self)}"
    self._draw()
    hits.append(self)

  def _draw(self):
    cv, x, y, s = self.cv, self.x, self.y, self.s
    cv.delete(self.dtag)
    on = self.value
    tags = ("ui", self.dtag)
    round_rect(
        cv, x + 2, y + 2, x + s - 2, y + s - 2, 7,
        fill=PRIMARY if on else "#FFFFFF",
        outline=PRIMARY if on else "#475569",
        width=3, tags=tags,
    )  # fmt: skip
    if on:
      cv.create_line(
          x + s * 0.26, y + s * 0.52, x + s * 0.43, y + s * 0.70,
          x + s * 0.76, y + s * 0.30,
          fill="white", width=3.5, capstyle="round", joinstyle="round",
          tags=tags,
      )  # fmt: skip

  def set_hover(self, on):
    pass

  def press(self):
    self.value = not self.value
    self._draw()
    self.on_toggle(self.value)

  def release(self):
    pass


class CheckBox(tk.Frame):
  """Крупный чекбокс для обычных окон (нижняя панель)."""

  def __init__(
      self, master, variable, text="", command=None, bg=CARD, box=30,
      font_size=12,
  ):  # fmt: skip
    super().__init__(master, bg=bg, cursor="hand2")
    self.var = variable
    self.command = command
    self.box = box
    self.cv = tk.Canvas(
        self, width=box, height=box, bg=bg, highlightthickness=0, bd=0
    )
    self.cv.pack(side="left")
    self.cv.bind("<ButtonPress-1>", self._toggle)
    if text:
      lbl = tk.Label(
          self, text=text, bg=bg, fg=TEXT, font=F(font_size), cursor="hand2"
      )
      lbl.pack(side="left", padx=(8, 0))
      lbl.bind("<ButtonPress-1>", self._toggle)
    self.bind("<ButtonPress-1>", self._toggle)
    self._draw()

  def _toggle(self, e=None):
    self.var.set(not self.var.get())
    self._draw()
    if self.command:
      self.command()

  def _draw(self):
    self.cv.delete("all")
    s = self.box
    on = self.var.get()
    round_rect(
        self.cv, 2, 2, s - 2, s - 2, 7,
        fill=PRIMARY if on else "#FFFFFF",
        outline=PRIMARY if on else "#475569",
        width=3,
    )  # fmt: skip
    if on:
      self.cv.create_line(
          s * 0.26, s * 0.52, s * 0.43, s * 0.70, s * 0.76, s * 0.30,
          fill="white", width=3.5, capstyle="round", joinstyle="round",
      )  # fmt: skip


def make_entry(parent, size=13, show=None, justify="left", width=None):
  e = tk.Entry(
      parent,
      font=F(size),
      relief="flat",
      bd=0,
      bg="#FFFFFF",
      fg=TEXT,
      insertbackground=TEXT,
      highlightthickness=2,
      highlightbackground=BORDER,
      highlightcolor=PRIMARY,
      justify=justify,
      show=show or "",
  )
  if width:
    e.config(width=width)
  return e


def field_label(parent, text, bg=CARD):
  return tk.Label(
      parent, text=text, bg=bg, fg=MUTED, font=F(11, "bold"), anchor="w"
  )


def card_frame(parent, bg=CARD):
  return tk.Frame(
      parent, bg=bg, highlightbackground=BORDER, highlightthickness=2
  )


def accent_bar(parent, color=PRIMARY):
  """Цветная полоска сверху карточки (у каждого окна свой цвет)."""
  tk.Frame(parent, height=10, bg=color).pack(fill="x")


# ---------------------------------------------------------------------------
# Чайка (рисуется на холсте списка поверх всего, без отдельных окон)
# ---------------------------------------------------------------------------
def draw_bird(cv, x, y, d, s, a):
  """Простая чайка сбоку. d: 1 = летит вправо, -1 = влево.

  a ∈ [-1, 1] — фаза взмаха крыла (1 — крыло вверху, -1 — внизу).
  state="disabled" — чайка не перехватывает клики по кнопкам под ней.
  """

  def pts(*pairs):
    out = []
    for px, py in pairs:
      out += [x + d * px * s, y + py * s]
    return out

  kw = {"tags": "bird", "state": "disabled"}
  outline = "#334155"
  dark = "#111827"
  ty = -34 * a
  cv.create_polygon(
      pts((-11, -1), (-30, -6), (-30, 5)),
      fill="white", outline=outline, width=1.5, **kw,
  )  # хвост  # fmt: skip
  cv.create_oval(
      pts((-15, -5), (12, 6)),
      fill="white", outline=outline, width=1.5, **kw,
  )  # тело  # fmt: skip
  cv.create_oval(
      pts((6, -12), (18, -1)),
      fill="white", outline=outline, width=1.5, **kw,
  )  # голова  # fmt: skip
  cv.create_polygon(
      pts((17, -8), (27, -6), (17, -3)),
      fill="#F4B400", outline=outline, width=1, **kw,
  )  # клюв  # fmt: skip
  cv.create_oval(
      pts((22, -6.4), (24.2, -4.4)), fill="#DC2626", outline="", **kw
  )  # красное пятнышко на клюве
  cv.create_oval(
      pts((11.5, -8.5), (14.5, -5.5)), fill=dark, outline="", **kw
  )  # глаз
  cv.create_polygon(
      pts((7, -3), (-3, ty * 0.5 - 3), (-20, ty), (-12, -3)),
      smooth=True, fill="#B4C0CF", outline=outline, width=1.5, **kw,
  )  # крыло  # fmt: skip
  cv.create_polygon(
      pts((-20, ty), (-13, 0.8 * ty - 1), (-15.5, 0.55 * ty - 1)),
      fill=dark, outline="", **kw,
  )  # чёрный кончик крыла  # fmt: skip


# ---------------------------------------------------------------------------
# Окна
# ---------------------------------------------------------------------------
def center_win(win, w, h):
  win.update_idletasks()
  sw = win.winfo_screenwidth()
  sh = win.winfo_screenheight()
  # не даём окну быть больше экрана (например, на проекторе 1024x768)
  w = min(w, sw - 40)
  h = min(h, sh - 90)
  x = (sw // 2) - (w // 2)
  y = max(0, (sh // 2) - (h // 2) - 20)
  win.geometry(f"{w}x{h}+{x}+{y}")


def new_window(title, parent=None):
  win = tk.Toplevel(parent)
  win.withdraw()
  win.title(title)
  win.configure(bg=BG)
  if parent is not None:
    win.transient(parent)
  return win


def show_centered(win, min_w=0, min_h=0, pad_w=0, pad_h=0):
  win.update_idletasks()
  w = max(min_w, win.winfo_reqwidth() + pad_w)
  h = max(min_h, win.winfo_reqheight() + pad_h)
  center_win(win, w, h)
  win.resizable(True, True)
  reveal(win)


def ask_string(parent, title, prompt):
  """Замена simpledialog.askstring в общем стиле приложения."""
  if reuse_window("ask"):
    return None
  dlg = new_window(title, parent)
  _single["ask"] = dlg
  result = {"value": None}

  body = tk.Frame(dlg, bg=BG)
  body.pack(fill="both", expand=True, padx=28, pady=24)
  tk.Label(
      body, text=prompt, bg=BG, fg=TEXT, font=F(13), anchor="w",
      justify="left",
  ).pack(fill="x")  # fmt: skip
  ent = make_entry(body, size=14)
  ent.pack(fill="x", ipady=10, pady=(12, 20))

  def ok(e=None):
    result["value"] = ent.get()
    dlg.destroy()

  btns = tk.Frame(body, bg=BG)
  btns.pack(fill="x")
  Btn(btns, "OK", ok, theme="primary").pack(side="right", padx=(10, 0))
  Btn(btns, "Отмена", dlg.destroy, theme="neutral").pack(side="right")
  ent.bind("<Return>", ok)
  dlg.bind("<Escape>", lambda e: dlg.destroy())

  show_centered(dlg, 560, 0)
  try:
    dlg.wait_visibility()
    dlg.grab_set()
  except tk.TclError:
    pass
  ent.focus_set()
  dlg.wait_window()
  return result["value"]


# ---------------------------------------------------------------------------
# Авторизация
# ---------------------------------------------------------------------------
center_win(root, 600, 720)
root.resizable(True, True)
root.minsize(480, 520)
root.deiconify()

login_card = card_frame(root)
login_card.pack(expand=True, fill="both", padx=30, pady=30)
accent_bar(login_card, PRIMARY)
login_inner = tk.Frame(login_card, bg=CARD)
login_inner.pack(expand=True, fill="x", padx=40)

tk.Label(
    login_inner, text="Здравствуйте!", bg=CARD, fg=TEXT, font=F(24, "bold")
).pack(pady=(0, 4))
tk.Label(
    login_inner,
    text="Необходимо авторизоваться",
    bg=CARD,
    fg=PRIMARY,
    font=F(12, "bold"),
).pack(pady=(0, 22))

field_label(login_inner, "Имя").pack(fill="x", pady=(0, 4))
entry_name = make_entry(login_inner)
entry_name.pack(fill="x", ipady=9, pady=(0, 14))
field_label(login_inner, "Пароль").pack(fill="x", pady=(0, 4))
entry_pass = make_entry(login_inner, show="*")
entry_pass.pack(fill="x", ipady=9, pady=(0, 22))


def try_login():
  name = entry_name.get().strip()
  password = entry_pass.get().strip()
  if not name or not password:
    messagebox.showwarning("Внимание", "Заполните все поля!", parent=root)
    return
  if name in app_data["users"]:
    if app_data["users"][name]["password"] == password:
      open_main_window(name)
    else:
      messagebox.showerror("Ошибка", "Неверный пароль!", parent=root)
  else:
    if messagebox.askyesno(
        "Пользователь не найден",
        "Ваше имя не найдено. Зарегистрироваться?",
        parent=root,
    ):
      app_data["users"][name] = {
          "password": password,
          "classes": {},
          "round_counter": 0,
      }
      save_data(app_data)
      messagebox.showinfo(
          "Успех", "Регистрация прошла успешно!", parent=root
      )
      open_main_window(name)


def open_guest_window():
  if reuse_window("guest"):
    return
  guest_win = new_window("Гостевой режим", root)
  _single["guest"] = guest_win

  card = card_frame(guest_win)
  card.pack(fill="both", expand=True, padx=28, pady=28)
  accent_bar(card, VIOLET)
  inner = tk.Frame(card, bg=CARD)
  inner.pack(expand=True, fill="x", padx=40)

  tk.Label(
      inner, text="Диапазон чисел", bg=CARD, fg=TEXT, font=F(20, "bold")
  ).pack(pady=(0, 16))
  field_label(inner, "ОТ").pack(fill="x", pady=(0, 4))
  ent_from = make_entry(inner, size=16, justify="center")
  ent_from.pack(fill="x", ipady=8, pady=(0, 12))
  field_label(inner, "ДО").pack(fill="x", pady=(0, 4))
  ent_to = make_entry(inner, size=16, justify="center")
  ent_to.pack(fill="x", ipady=8, pady=(0, 20))

  def generate():
    try:
      start_val = int(ent_from.get())
      end_val = int(ent_to.get())
      if start_val > end_val:
        messagebox.showwarning(
            "Ошибка", "'ОТ' не может быть больше 'ДО'!", parent=guest_win
        )
        return
    except ValueError:
      messagebox.showwarning(
          "Ошибка", "Введите целые числа!", parent=guest_win
      )
      return
    chosen = random.randint(start_val, end_val)
    res_win = new_window("Результат", guest_win)
    replace_single("guest_res", res_win)

    rc = card_frame(res_win)
    rc.pack(fill="both", expand=True, padx=24, pady=24)
    accent_bar(rc, VIOLET)
    tk.Label(
        rc, text="Выпало число:", bg=CARD, fg=MUTED, font=F(18, "bold")
    ).pack(pady=(26, 4), padx=60)
    tk.Label(
        rc, text=str(chosen), bg=CARD, fg=PRIMARY, font=F(72, "bold")
    ).pack(pady=8)
    Btn(rc, "Закрыть", res_win.destroy, theme="neutral", size=13).pack(
        pady=(10, 26)
    )

    show_centered(res_win, 700, 460, 20, 10)

  Btn(inner, "Сгенерировать", generate, theme="primary", size=14).pack(fill="x")

  ent_from.bind("<Return>", lambda e: ent_to.focus_set())
  ent_to.bind("<Return>", lambda e: generate())

  center_win(guest_win, 600, 660)
  guest_win.resizable(True, True)
  reveal(guest_win)
  ent_from.focus_set()


Btn(login_inner, "Войти", try_login, theme="primary", size=13).pack(
    fill="x", pady=(0, 10)
)
Btn(
    login_inner, "Войти как гость", open_guest_window, theme="guest",
    size=12,
).pack(fill="x")  # fmt: skip

entry_name.bind("<Return>", lambda e: entry_pass.focus_set())
entry_pass.bind("<Return>", lambda e: try_login())
entry_name.focus_set()


# ---------------------------------------------------------------------------
# Главное меню (выбор класса)
# ---------------------------------------------------------------------------
def open_main_window(user_name):
  if reuse_window("main"):
    return
  root.withdraw()
  win = new_window("Главное меню")
  _single["main"] = win

  head = tk.Frame(win, bg=BG)
  head.pack(fill="x", padx=32, pady=(26, 6))
  tk.Label(
      head,
      text=f"Добро пожаловать, {user_name}!",
      bg=BG,
      fg=TEXT,
      font=F(22, "bold"),
      anchor="w",
  ).pack(fill="x")
  tk.Label(
      head, text="Выберите класс", bg=BG, fg=PRIMARY, font=F(13, "bold"),
      anchor="w",
  ).pack(fill="x", pady=(2, 0))  # fmt: skip

  user_classes = app_data["users"][user_name]["classes"]

  list_card = card_frame(win)
  list_card.pack(fill="both", expand=True, padx=32, pady=(12, 14))
  listbox = tk.Listbox(
      list_card,
      font=F(15),
      bg=CARD,
      fg=TEXT,
      bd=0,
      relief="flat",
      highlightthickness=0,
      activestyle="none",
      selectbackground=PRIMARY,
      selectforeground="#FFFFFF",
      exportselection=False,
  )
  listbox.pack(fill="both", expand=True, padx=12, pady=12)

  def refresh_classes():
    listbox.delete(0, tk.END)
    for cls in sorted(user_classes.keys()):
      listbox.insert(tk.END, cls)

  refresh_classes()

  def do_add_class():
    new_name = ask_string(
        win, "Новый класс", "Введите название (например, 10А):"
    )
    if new_name and new_name.strip():
      name = new_name.strip()
      if name in user_classes:
        messagebox.showwarning(
            "Внимание", "Такой класс уже существует!", parent=win
        )
      else:
        user_classes[name] = []
        save_data(app_data)
        refresh_classes()

  def do_open_class():
    sel = listbox.curselection()
    if not sel:
      messagebox.showwarning(
          "Внимание", "Сначала выберите класс!", parent=win
      )
      return
    show_students_window(listbox.get(sel[0]), user_name)

  def do_delete_class():
    sel = listbox.curselection()
    if not sel:
      messagebox.showwarning(
          "Внимание", "Сначала выберите класс для удаления!", parent=win
      )
      return
    class_to_del = listbox.get(sel[0])
    if messagebox.askyesno(
        "Подтверждение удаления",
        f"Удалить класс «{class_to_del}»?\nВсе ученики и данные будут"
        " потеряны.",
        parent=win,
    ):
      del user_classes[class_to_del]
      save_data(app_data)
      refresh_classes()
      messagebox.showinfo(
          "Готово", f"Класс {class_to_del} успешно удалён.", parent=win
      )

  def on_class_double_click(e):
    # выбираем класс прямо под курсором и открываем его
    idx = listbox.nearest(e.y)
    if idx < 0 or idx >= listbox.size():
      return
    bbox = listbox.bbox(idx)
    if bbox is None or not (bbox[1] <= e.y <= bbox[1] + bbox[3]):
      return  # двойной клик по пустому месту под списком
    listbox.selection_clear(0, tk.END)
    listbox.selection_set(idx)
    listbox.activate(idx)
    root.after(20, do_open_class)

  listbox.bind("<Double-Button-1>", on_class_double_click)
  listbox.bind("<Return>", lambda e: do_open_class())

  btn_row = tk.Frame(win, bg=BG)
  btn_row.pack(fill="x", padx=28, pady=(0, 26))
  Btn(btn_row, "Открыть класс", do_open_class, theme="primary").pack(
      side="left", expand=True, fill="x", padx=4
  )
  Btn(btn_row, "Добавить класс", do_add_class, theme="add").pack(
      side="left", expand=True, fill="x", padx=4
  )
  Btn(btn_row, "Удалить класс", do_delete_class, theme="danger").pack(
      side="left", expand=True, fill="x", padx=4
  )

  win.protocol("WM_DELETE_WINDOW", root.destroy)

  center_win(win, 800, 700)
  win.resizable(True, True)
  reveal(win)


# ---------------------------------------------------------------------------
# Список учеников
# ---------------------------------------------------------------------------
def show_students_window(class_name, user_name):
  key = ("students", user_name, class_name)
  if reuse_window(key):
    return
  stu_win = new_window(f"Ученики класса {class_name}")
  _single[key] = stu_win

  user_data = app_data["users"][user_name]
  students = user_data["classes"][class_name]
  nobody_cfg = app_data["nobody_configs"].setdefault(
      class_name, {"prob": 10, "enabled": True}
  )

  equal_chances_var = tk.BooleanVar(value=False)

  # Шрифты и размеры строк списка
  f_name = F(13, "bold")
  f_num = F(12, "bold")
  f_chip = F(11, "bold")
  f_pm = F(15, "bold")
  f_x = F(12, "bold")
  f_tog = F(11, "bold")
  m_name = tkfont.Font(root=root, font=f_name)
  m_chip = tkfont.Font(root=root, font=f_chip)
  m_tog = tkfont.Font(root=root, font=f_tog)
  lh = m_name.metrics("linespace")
  row_h = max(60, lh + 30)  # высота строки ученика
  bh = row_h - 24  # высота кнопок в строке
  bw = int(bh * 1.35)  # ширина маленьких кнопок
  PAD = 24

  grade_items = []  # [(ученик, id текста)] — для обновления без перерисовки
  layout = {"w": 0, "h": 0}
  hits = []  # все нажимаемые элементы списка (кнопки, галочки)
  mouse = {"hover": None, "down": None}

  # Шапка
  header = tk.Frame(stu_win, bg=BG)
  header.pack(side=tk.TOP, fill=tk.X, padx=24, pady=(18, 8))
  tk.Label(
      header, text=f"Класс {class_name}", bg=BG, fg=TEXT, font=F(22, "bold")
  ).pack(side=tk.LEFT)
  # Информационная плашка — светлая (не кнопка). Рамка — фон внешнего Frame.
  count_box = tk.Frame(header, bg=PRIMARY)
  count_box.pack(side=tk.LEFT, padx=(16, 0), pady=(6, 0))
  count_lbl = tk.Label(
      count_box, text="", bg=CHIP_BG, fg=PRIMARY, font=F(11, "bold"),
      padx=14, pady=4,
  )  # fmt: skip
  count_lbl.pack(padx=2, pady=2)

  def update_count():
    sel = sum(1 for s in students if s["selected"])
    count_lbl.config(text=f"Учеников: {len(students)}  ·  выбрано: {sel}")

  # Нижняя панель управления (размещается внизу окна)
  bar = tk.Frame(stu_win, bg=CARD)
  bar.pack(side=tk.BOTTOM, fill=tk.X)
  tk.Frame(stu_win, height=2, bg=BORDER).pack(side=tk.BOTTOM, fill=tk.X)
  bottom_frame = tk.Frame(bar, bg=CARD)
  bottom_frame.pack(fill=tk.X, padx=14, pady=12)

  # Холст со списком: и строки, и кнопки, и чайки рисуются прямо на нём.
  canvas = tk.Canvas(
      stu_win, bg=BG, highlightthickness=0, bd=0, yscrollincrement=30
  )
  scrollbar = ttk.Scrollbar(
      stu_win,
      orient="vertical",
      style="Modern.Vertical.TScrollbar",
      command=canvas.yview,
  )
  canvas.configure(yscrollcommand=scrollbar.set)
  scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
  canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

  def update_region():
    w = max(canvas.winfo_width(), 1)
    h = max(layout["h"], canvas.winfo_height())
    canvas.configure(scrollregion=(0, 0, w, h))

  def on_configure(event):
    if event.width != layout["w"]:
      layout["w"] = event.width
      draw_list()
    else:
      update_region()

  canvas.bind("<Configure>", on_configure)

  # --- Нажатия в списке: ищем кнопку по координатам курсора ---------------
  def find_hit(e):
    x = canvas.canvasx(e.x)
    y = canvas.canvasy(e.y)
    for h in reversed(hits):
      x1, y1, x2, y2 = h.box
      if x1 - 3 <= x <= x2 + 3 and y1 - 3 <= y <= y2 + 3:
        return h
    return None

  def set_hover(h):
    if h is mouse["hover"]:
      return
    if mouse["hover"] is not None:
      mouse["hover"].set_hover(False)
    mouse["hover"] = h
    if h is not None:
      h.set_hover(True)
    canvas.config(cursor="hand2" if h is not None else "")

  def on_motion(e):
    set_hover(find_hit(e))

  def on_press(e):
    h = find_hit(e)
    set_hover(h)
    mouse["down"] = h
    if h is not None:
      h.press()

  def on_release(e):
    h = mouse["down"]
    mouse["down"] = None
    if h is not None:
      h.release()

  canvas.bind("<Motion>", on_motion)
  canvas.bind("<Leave>", lambda e: set_hover(None))
  canvas.bind("<ButtonPress-1>", on_press)
  canvas.bind("<ButtonRelease-1>", on_release)

  def _on_mousewheel(event):
    if getattr(event, "num", None) == 4:
      canvas.yview_scroll(-1, "units")
    elif getattr(event, "num", None) == 5:
      canvas.yview_scroll(1, "units")
    else:
      canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")

  stu_win.bind("<MouseWheel>", _on_mousewheel)
  stu_win.bind("<Button-4>", _on_mousewheel)  # Linux
  stu_win.bind("<Button-5>", _on_mousewheel)  # Linux

  # --- Чайки ---------------------------------------------------------------
  birds = {"job": None, "list": []}
  frame_ms = 40

  def stop_birds(event=None):
    if event is not None and event.widget is not stu_win:
      return
    if birds["job"] is not None:
      try:
        root.after_cancel(birds["job"])
      except tk.TclError:
        pass
      birds["job"] = None
    birds["list"] = []

  def schedule_birds(first=False):
    delay = random.randint(4000, 9000) if first else random.randint(
        15000, 35000
    )
    birds["job"] = root.after(delay, launch_flock)

  def launch_flock():
    birds["job"] = None
    try:
      if not stu_win.winfo_exists():
        return
      w = max(canvas.winfo_width(), 400)
      h = max(canvas.winfo_height(), 300)
    except tk.TclError:
      return
    # чаще одна чайка, иногда стайка из 2–4
    n = random.choices((1, 2, 3, 4), weights=(55, 22, 15, 8))[0]
    d = random.choice((1, -1))
    speed0 = random.uniform(4.5, 7.0)
    base0 = random.uniform(0.12, 0.70) * h
    lead = 0.0
    for i in range(n):
      if i:
        lead += random.uniform(60, 140)
      birds["list"].append({
          "d": d,
          "x": (-60.0 - lead) if d == 1 else (w + 60.0 + lead),
          "base": max(30.0, min(h - 30.0, base0 + random.uniform(-50, 50))),
          "speed": speed0 + random.uniform(-0.6, 0.6),
          "scale": random.uniform(0.75, 1.0),
          "phase": random.uniform(0, 6.28),
          "t": random.randint(0, 100),
      })
    animate_birds()

  def animate_birds():
    try:
      if not stu_win.winfo_exists():
        return
      canvas.delete("bird")
      w = max(canvas.winfo_width(), 1)
      top = canvas.canvasy(0)
      alive = []
      for b in birds["list"]:
        b["x"] += b["d"] * b["speed"]
        b["phase"] += 0.4  # чайка машет крыльями неторопливо
        b["t"] += 1
        if (b["d"] == 1 and b["x"] > w + 130) or (
            b["d"] == -1 and b["x"] < -130
        ):
          continue
        y = top + b["base"] + math.sin(b["t"] * 0.06) * 14
        draw_bird(
            canvas, b["x"], y, b["d"], b["scale"], math.sin(b["phase"])
        )
        alive.append(b)
      birds["list"] = alive
      canvas.tag_raise("bird")
      if alive:
        birds["job"] = root.after(frame_ms, animate_birds)
      else:
        birds["job"] = None
        schedule_birds()
    except tk.TclError:
      return

  stu_win.bind("<Destroy>", stop_birds)
  schedule_birds(first=True)

  # --- Список --------------------------------------------------------------
  def fit_text(text, font, max_w):
    if font.measure(text) <= max_w:
      return text
    while text and font.measure(text + "…") > max_w:
      text = text[:-1]
    return text + "…"

  def draw_list():
    canvas.delete("ui")
    canvas.config(cursor="")
    grade_items.clear()
    hits.clear()
    mouse["hover"] = None
    mouse["down"] = None

    W = canvas.winfo_width()
    if W < 300:
      W = 1000
    x1, x2 = PAD, W - PAD
    y = 6

    # ---- Блок «Никто» (жёлтый) ----
    nh = row_h + 14
    cy = y + nh / 2
    canvas.create_rectangle(
        x1, y, x2, y + nh, fill=AMBER_BG, outline=ORANGE, width=2, tags="ui"
    )
    canvas.create_text(
        x1 + 18, cy - lh * 0.45, text="Никто", anchor="w", fill=TEXT,
        font=F(14, "bold"), tags="ui",
    )  # fmt: skip
    canvas.create_text(
        x1 + 18, cy + lh * 0.55, text="шанс, что никого не вызовут",
        anchor="w", fill=AMBER_TEXT, font=F(10), tags="ui",
    )  # fmt: skip

    tw = m_tog.measure("Не использовать") + 36
    rx = x2 - 16
    tog = CBtn(
        canvas, hits, rx - tw, cy - bh / 2, rx, cy + bh / 2,
        "Не использовать" if nobody_cfg["enabled"] else "Использовать",
        lambda: toggle_nobody(),
        "danger" if nobody_cfg["enabled"] else "success", f_tog,
    )  # fmt: skip
    rx -= tw + 16
    CBtn(
        canvas, hits, rx - bw, cy - bh / 2, rx, cy + bh / 2, "+",
        lambda: adjust_prob(5), "success", f_pm,
    )  # fmt: skip
    rx -= bw + 6
    CBtn(
        canvas, hits, rx - bw, cy - bh / 2, rx, cy + bh / 2, "−",
        lambda: adjust_prob(-5), "minus", f_pm,
    )  # fmt: skip
    rx -= bw + 14
    prob_id = canvas.create_text(
        rx, cy, text=f"{nobody_cfg['prob']}%", anchor="e", fill=AMBER_TEXT,
        font=F(15, "bold"), tags="ui",
    )  # fmt: skip

    def adjust_prob(delta):
      nobody_cfg["prob"] = max(0, min(100, nobody_cfg["prob"] + delta))
      canvas.itemconfig(prob_id, text=f"{nobody_cfg['prob']}%")
      save_data(app_data)

    def toggle_nobody():
      nobody_cfg["enabled"] = not nobody_cfg["enabled"]
      tog.restyle(
          "Не использовать" if nobody_cfg["enabled"] else "Использовать",
          "danger" if nobody_cfg["enabled"] else "success",
      )
      save_data(app_data)

    y += nh + 10

    # ---- Ученики ----
    students.sort(key=lambda s: s["name"])

    if not students:
      canvas.create_text(
          W / 2, y + 70,
          text="В классе пока нет учеников.\nНажмите «Добавить ученика».",
          fill=MUTED, font=F(13), justify="center", tags="ui",
      )  # fmt: skip
      y += 140

    chip_w = m_chip.measure("оценок: 000") + 30
    chip_h = int(bh * 0.85)

    for i, stu in enumerate(students, 1):
      cy = y + row_h / 2
      rid = canvas.create_rectangle(
          x1, y, x2, y + row_h, fill=CARD,
          outline=PRIMARY if stu["selected"] else BORDER, width=2, tags="ui",
      )  # fmt: skip

      # 1. Порядковый номер
      canvas.create_text(
          x1 + 52, cy, text=f"{i}.", anchor="e", fill=MUTED, font=f_num,
          tags="ui",
      )  # fmt: skip

      # 2. Чекбокс
      def toggle_sel(val, s=stu, r=rid):
        s["selected"] = val
        canvas.itemconfig(r, outline=PRIMARY if val else BORDER)
        save_data(app_data)
        update_count()

      CCheck(canvas, hits, x1 + 70, cy - 15, 30, stu["selected"], toggle_sel)

      # Правая часть (справа налево): ✕, +, −, плашка с оценками
      rx = x2 - 14
      xb = (rx - bw, rx)
      rx -= bw + 8
      pb = (rx - bw, rx)
      rx -= bw + 6
      mb = (rx - bw, rx)
      rx -= bw + 14
      chip = (rx - chip_w, rx)

      # плашка «оценок: N» (светлая — это не кнопка)
      round_rect(
          canvas, chip[0], cy - chip_h / 2, chip[1], cy + chip_h / 2, 8,
          fill=VIOLET_BG, outline=VIOLET, width=2, tags="ui",
      )  # fmt: skip
      grade_tid = canvas.create_text(
          (chip[0] + chip[1]) / 2, cy, text=f"оценок: {stu['grades']}",
          fill=VIOLET, font=f_chip, tags="ui",
      )  # fmt: skip
      grade_items.append((stu, grade_tid))

      # 3. Имя ученика
      canvas.create_text(
          x1 + 116, cy,
          text=fit_text(stu["name"], m_name, chip[0] - 12 - (x1 + 116)),
          anchor="w", fill=TEXT, font=f_name, tags="ui",
      )  # fmt: skip

      def minus_grade(s=stu, tid=grade_tid):
        if s["grades"] > 0:
          s["grades"] -= 1
          canvas.itemconfig(tid, text=f"оценок: {s['grades']}")
          save_data(app_data)

      def add_grade(s=stu, tid=grade_tid):
        s["grades"] += 1
        canvas.itemconfig(tid, text=f"оценок: {s['grades']}")
        save_data(app_data)

      def delete_student(s=stu):
        if messagebox.askyesno(
            "Подтверждение удаления",
            f"Удалить ученика «{s['name']}» из класса?",
            parent=stu_win,
        ):
          students.remove(s)
          save_data(app_data)
          draw_list()

      # 4. «−» оранжевая, «+» зелёная, «✕» красная
      CBtn(
          canvas, hits, mb[0], cy - bh / 2, mb[1], cy + bh / 2, "−", minus_grade,
          "minus", f_pm,
      )  # fmt: skip
      CBtn(
          canvas, hits, pb[0], cy - bh / 2, pb[1], cy + bh / 2, "+", add_grade,
          "success", f_pm,
      )  # fmt: skip
      CBtn(
          canvas, hits, xb[0], cy - bh / 2, xb[1], cy + bh / 2, "✕", delete_student,
          "danger", f_x,
      )  # fmt: skip

      y += row_h + 6

    layout["h"] = y + 16
    update_region()
    canvas.tag_raise("bird")
    update_count()

  def do_select_all():
    if not students:
      return
    new_state = not all(s["selected"] for s in students)
    for s in students:
      s["selected"] = new_state
    save_data(app_data)
    draw_list()

  def do_reset_grades():
    if not students:
      return
    if messagebox.askyesno(
        "Обнуление оценок",
        "Вы уверены, что хотите обнулить количество оценок у всех учеников в"
        " этом классе?",
        parent=stu_win,
    ):
      for s in students:
        s["grades"] = 0
      save_data(app_data)
      # Обновляем подписи на месте, список не пересоздаём
      for s, tid in grade_items:
        canvas.itemconfig(tid, text=f"оценок: {s['grades']}")
      messagebox.showinfo(
          "Готово",
          "Количество оценок у всех учеников сброшено до 0.",
          parent=stu_win,
      )

  def open_add_student_dialog():
    dkey = ("add", id(stu_win))
    if reuse_window(dkey):
      return
    add_win = new_window("Добавить ученика", stu_win)
    _single[dkey] = add_win

    card = card_frame(add_win)
    card.pack(fill="both", expand=True, padx=24, pady=24)
    accent_bar(card, TEAL)
    inner = tk.Frame(card, bg=CARD)
    inner.pack(expand=True, fill="x", padx=36)

    tk.Label(
        inner, text="Новый ученик", bg=CARD, fg=TEXT, font=F(18, "bold")
    ).pack(pady=(0, 16))
    field_label(inner, "Фамилия").pack(fill="x", pady=(0, 4))
    ent_last = make_entry(inner, size=14)
    ent_last.pack(fill="x", ipady=8, pady=(0, 12))
    field_label(inner, "Имя").pack(fill="x", pady=(0, 4))
    ent_first = make_entry(inner, size=14)
    ent_first.pack(fill="x", ipady=8, pady=(0, 18))

    def do_add():
      last = ent_last.get().strip()
      first = ent_first.get().strip()
      if not last or not first:
        messagebox.showwarning(
            "Внимание", "Заполните оба поля!", parent=add_win
        )
        return
      full = f"{last} {first}"
      if any(s["name"] == full for s in students):
        messagebox.showwarning(
            "Внимание", "Такой ученик уже есть!", parent=add_win
        )
        return
      students.append(
          {"name": full, "grades": 0, "selected": False, "last_round": 0}
      )
      save_data(app_data)
      add_win.destroy()
      draw_list()

    Btn(inner, "Добавить", do_add, theme="add", size=13).pack(fill="x")

    ent_last.bind("<Return>", lambda e: ent_first.focus_set())
    ent_first.bind("<Return>", lambda e: do_add())

    center_win(add_win, 580, 560)
    add_win.resizable(True, True)
    reveal(add_win)
    ent_last.focus_set()

  def open_ready_window():
    selected = [s for s in students if s["selected"]]
    if not selected and not nobody_cfg["enabled"]:
      messagebox.showwarning(
          "Внимание",
          "Отметьте галочками хотя бы одного ученика!",
          parent=stu_win,
      )
      return
    rkey = ("ready", id(stu_win))
    if reuse_window(rkey):
      return
    confirm_win = new_window("Подтверждение", stu_win)
    _single[rkey] = confirm_win

    card = card_frame(confirm_win)
    card.pack(fill="both", expand=True, padx=24, pady=24)
    accent_bar(card, PRIMARY)

    tk.Label(
        card,
        text=f"Выбрано {len(selected)} учеников",
        bg=CARD,
        fg=TEXT,
        font=F(18, "bold"),
    ).pack(pady=(32, 24), padx=40)

    def start_selection():
      confirm_win.destroy()
      show_result(selected)

    Btn(card, "Поехали", start_selection, theme="primary", size=14).pack(
        pady=(0, 32), ipadx=14
    )

    center_win(confirm_win, 680, 400)
    confirm_win.resizable(True, True)
    reveal(confirm_win)

  def show_teacher_result():
    res_win = new_window("Результат")
    replace_single(("result", id(stu_win)), res_win)

    card = card_frame(res_win)
    card.pack(fill="both", expand=True, padx=24, pady=24)
    accent_bar(card, ORANGE)

    tk.Label(
        card, text="Сегодня объясняет:", bg=CARD, fg=MUTED,
        font=F(18, "bold"),
    ).pack(pady=(28, 6), padx=40)  # fmt: skip
    tk.Label(
        card, text="УЧИТЕЛЬ", bg=CARD, fg=ORANGE, font=F(54, "bold")
    ).pack(pady=10)
    tk.Label(
        card,
        text="Никто из учеников не вызван.",
        bg=CARD,
        fg=MUTED,
        font=F(15),
    ).pack(pady=(4, 20))
    Btn(card, "Закрыть", res_win.destroy, theme="neutral", size=13).pack(
        pady=(0, 28)
    )

    show_centered(res_win, 800, 520, 40, 20)

  def show_result(candidates):
    current_round = user_data.get("round_counter", 0) + 1
    if not candidates or (
        nobody_cfg["enabled"] and random.randint(1, 100) <= nobody_cfg["prob"]
    ):
      user_data["round_counter"] = current_round
      save_data(app_data)
      show_teacher_result()
      return

    intervals = []
    current_bound = 0
    is_equalized = equal_chances_var.get()
    cand_count = len(candidates)

    for s in candidates:
      eff_grades = 0 if is_equalized else s["grades"]
      base_weight = int(1000 / (eff_grades + 1))
      rounds_since = current_round - s.get("last_round", 0)
      if rounds_since <= 1:
        history_coef = 0.2
      elif rounds_since == 2:
        history_coef = 0.5
      elif rounds_since == 3:
        history_coef = 0.8
      else:
        history_coef = 1.0

      custom_coef = 1.0
      if s["name"] == "Тайнов Алексей":
        if 2 <= cand_count <= 4:
          custom_coef = 1.3
        else:
          custom_coef = 0.2

      final_weight = max(1, int(base_weight * history_coef * custom_coef))
      start = current_bound + 1
      end = current_bound + final_weight
      intervals.append((start, end, s, final_weight))
      current_bound = end

    total_range = current_bound
    roll = random.randint(1, total_range)
    chosen = None
    c_start = c_end = c_weight = 0
    for start, end, student, weight in intervals:
      if start <= roll <= end:
        chosen = student
        c_start, c_end, c_weight = start, end, weight
        break

    chosen["last_round"] = current_round
    user_data["round_counter"] = current_round
    save_data(app_data)

    res_win = new_window("Результат")
    replace_single(("result", id(stu_win)), res_win)

    card = card_frame(res_win)
    card.pack(fill="both", expand=True, padx=24, pady=24)
    accent_bar(card, PRIMARY)

    tk.Label(
        card, text="Сегодня отвечает:", bg=CARD, fg=MUTED,
        font=F(18, "bold"),
    ).pack(pady=(26, 4), padx=40)  # fmt: skip

    name_text = chosen["name"]
    if len(name_text) <= 12:
      f_size = 48
    elif len(name_text) <= 18:
      f_size = 36
    elif len(name_text) <= 25:
      f_size = 28
    else:
      f_size = 22

    tk.Label(
        card,
        text=name_text,
        font=F(f_size, "bold"),
        bg=CARD,
        fg=PRIMARY,
        wraplength=max(400, min(1000, res_win.winfo_screenwidth() - 160)),
    ).pack(pady=14, padx=30)

    grades_info = f"Оценок у ученика: {chosen['grades']}" + (
        " (приравнено к 0)" if is_equalized else ""
    )
    tk.Label(
        card, text=grades_info, bg=CARD, fg=VIOLET, font=F(15, "bold")
    ).pack(pady=(0, 12))

    chip = tk.Frame(
        card, bg=CHIP_BG, highlightbackground=BORDER, highlightthickness=2
    )
    chip.pack(pady=(0, 16), padx=30)
    tk.Label(
        chip,
        text=f"Вес: {c_weight} | Диапазон: [{c_start}-{c_end}]",
        font=FM(12),
        bg=CHIP_BG,
        fg=TEAL,
    ).pack(padx=18, pady=(10, 2))
    tk.Label(
        chip,
        text=f"Всего: 1-{total_range} | Выпало: {roll}",
        font=FM(12),
        bg=CHIP_BG,
        fg=SLATE_DARK,
    ).pack(padx=18, pady=(2, 10))

    Btn(card, "Закрыть", res_win.destroy, theme="neutral", size=13).pack(
        pady=(0, 26)
    )

    show_centered(res_win, 800, 520, 40, 20)

  # Слева: «Выбрать всех» (голубая — кнопка выбора)
  Btn(
      bottom_frame, "Выбрать всех", do_select_all, theme="info", size=11,
      padx=14,
  ).pack(side=tk.LEFT, padx=5)  # fmt: skip

  # Справа: основное действие — самое правое
  Btn(
      bottom_frame, "Готово", open_ready_window, theme="primary", size=11,
      padx=18,
  ).pack(side=tk.RIGHT, padx=5)  # fmt: skip
  Btn(
      bottom_frame, "Обнулить оценки", do_reset_grades, theme="danger",
      size=11, padx=14,
  ).pack(side=tk.RIGHT, padx=5)  # fmt: skip
  CheckBox(
      bottom_frame, equal_chances_var, text="Уравнять шансы", bg=CARD,
      font_size=11,
  ).pack(side=tk.RIGHT, padx=12)  # fmt: skip
  Btn(
      bottom_frame, "Добавить ученика", open_add_student_dialog,
      theme="add", size=11, padx=14,
  ).pack(side=tk.RIGHT, padx=5)  # fmt: skip

  stu_win.minsize(min(1000, stu_win.winfo_screenwidth() - 40), 460)
  center_win(stu_win, 1240, 780)
  stu_win.resizable(True, True)
  reveal(stu_win)
  stu_win.update_idletasks()
  layout["w"] = canvas.winfo_width()
  draw_list()


root.mainloop()
