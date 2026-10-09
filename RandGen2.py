import json
import os
import random
import sys
import tkinter as tk
from tkinter import messagebox, simpledialog


DATA_FILE = "school_data.json"


# Автоматический выбор системного шрифта (Segoe UI на Windows, Arial на macOS/Linux)
FONT_FAMILY = "Segoe UI" if sys.platform.startswith("win") else "Arial"




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
                      "name": "Смирнов Алексей",
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


try:
  icon = tk.PhotoImage(file="icon.png")
  root.iconphoto(True, icon)
except Exception:
  pass




def center_win(win, w, h):
  win.update_idletasks()
  sw = win.winfo_screenwidth()
  sh = win.winfo_screenheight()
  x = (sw // 2) - (w // 2)
  y = (sh // 2) - (h // 2)
  win.geometry(f"{w}x{h}+{x}+{y}")




center_win(root, 480, 420)
root.resizable(True, True)
root.deiconify()


tk.Label(
    root,
    text="Здравствуйте!\nНеобходимо авторизоваться",
    font=(FONT_FAMILY, 16),
).pack(pady=20)
tk.Label(root, text="Имя:", font=(FONT_FAMILY, 13)).pack()
entry_name = tk.Entry(root, width=28, font=(FONT_FAMILY, 13))
entry_name.pack(pady=5)
entry_name.focus_set()


tk.Label(root, text="Пароль:", font=(FONT_FAMILY, 13)).pack()
entry_pass = tk.Entry(root, width=28, show="*", font=(FONT_FAMILY, 13))
entry_pass.pack(pady=5)




def try_login():
  name = entry_name.get().strip()
  password = entry_pass.get().strip()
  if not name or not password:
    messagebox.showwarning("Внимание", "Заполните все поля!")
    return
  if name in app_data["users"]:
    if app_data["users"][name]["password"] == password:
      open_main_window(name)
    else:
      messagebox.showerror("Ошибка", "Неверный пароль!")
  else:
    if messagebox.askyesno(
        "Пользователь не найден", "Ваше имя не найдено. Зарегистрироваться?"
    ):
      app_data["users"][name] = {
          "password": password,
          "classes": {},
          "round_counter": 0,
      }
      save_data(app_data)
      messagebox.showinfo("Успех", "Регистрация прошла успешно!")
      open_main_window(name)




def open_guest_window():
  guest_win = tk.Toplevel(root)
  guest_win.withdraw()
  guest_win.title("Гостевой режим")
  guest_win.transient(root)


  tk.Label(
      guest_win, text="Диапазон чисел", font=(FONT_FAMILY, 16, "bold")
  ).pack(pady=15)
  tk.Label(guest_win, text="ОТ:", font=(FONT_FAMILY, 14)).pack()
  ent_from = tk.Entry(
      guest_win, width=18, font=(FONT_FAMILY, 16), justify="center"
  )
  ent_from.pack(pady=5)
  ent_from.focus_set()


  tk.Label(guest_win, text="ДО:", font=(FONT_FAMILY, 14)).pack()
  ent_to = tk.Entry(
      guest_win, width=18, font=(FONT_FAMILY, 16), justify="center"
  )
  ent_to.pack(pady=5)


  def generate():
    try:
      start_val = int(ent_from.get())
      end_val = int(ent_to.get())
      if start_val > end_val:
        messagebox.showwarning("Ошибка", "'ОТ' не может быть больше 'ДО'!")
        return
    except ValueError:
      messagebox.showwarning("Ошибка", "Введите целые числа!")
      return
    chosen = random.randint(start_val, end_val)
    res_win = tk.Toplevel(guest_win)
    res_win.withdraw()
    res_win.title("Результат")
    res_win.transient(guest_win)


    tk.Label(res_win, text="Выпало число:", font=(FONT_FAMILY, 18)).pack(
        pady=15
    )
    tk.Label(
        res_win, text=str(chosen), font=(FONT_FAMILY, 64, "bold"), fg="#2196F3"
    ).pack(pady=10)
    tk.Button(
        res_win,
        text="Закрыть",
        command=res_win.destroy,
        font=(FONT_FAMILY, 13),
    ).pack(pady=15)


    res_win.update_idletasks()
    w = max(500, res_win.winfo_reqwidth() + 40)
    h = max(300, res_win.winfo_reqheight() + 20)
    center_win(res_win, w, h)
    res_win.resizable(True, True)
    res_win.deiconify()


  tk.Button(
      guest_win,
      text="Сгенерировать",
      command=generate,
      font=(FONT_FAMILY, 14),
      width=16,
  ).pack(pady=20)


  center_win(guest_win, 500, 400)
  guest_win.resizable(True, True)
  guest_win.deiconify()




tk.Button(
    root, text="Войти", command=try_login, font=(FONT_FAMILY, 12), width=15
).pack(pady=15)
tk.Button(
    root,
    text="Войти как гость",
    command=open_guest_window,
    font=(FONT_FAMILY, 12),
    width=18,
).pack(pady=5)




def open_main_window(user_name):
  root.withdraw()
  win = tk.Toplevel()
  win.withdraw()
  win.title("Главное меню")


  tk.Label(
      win,
      text=f"Добро пожаловать, {user_name}!",
      font=(FONT_FAMILY, 18, "bold"),
  ).pack(pady=15)
  tk.Label(win, text="Выберите класс:", font=(FONT_FAMILY, 15)).pack(pady=5)
  user_classes = app_data["users"][user_name]["classes"]
  listbox = tk.Listbox(win, width=32, height=10, font=(FONT_FAMILY, 14))
  listbox.pack(pady=8)


  def refresh_classes():
    listbox.delete(0, tk.END)
    for cls in sorted(user_classes.keys()):
      listbox.insert(tk.END, cls)


  refresh_classes()


  def do_add_class():
    new_name = simpledialog.askstring(
        "Новый класс", "Введите название (например, 10А):"
    )
    if new_name and new_name.strip():
      name = new_name.strip()
      if name in user_classes:
        messagebox.showwarning("Внимание", "Такой класс уже существует!")
      else:
        user_classes[name] = []
        save_data(app_data)
        refresh_classes()


  def do_open_class():
    sel = listbox.curselection()
    if not sel:
      messagebox.showwarning("Внимание", "Сначала выберите класс!")
      return
    show_students_window(listbox.get(sel[0]), user_name)


  def do_delete_class():
    sel = listbox.curselection()
    if not sel:
      messagebox.showwarning(
          "Внимание", "Сначала выберите класс для удаления!"
      )
      return
    class_to_del = listbox.get(sel[0])
    if messagebox.askyesno(
        "Подтверждение удаления",
        f"Удалить класс «{class_to_del}»?\nВсе ученики и данные будут"
        " потеряны.",
    ):
      del user_classes[class_to_del]
      save_data(app_data)
      refresh_classes()
      messagebox.showinfo("Готово", f"Класс {class_to_del} успешно удалён.")


  tk.Button(
      win,
      text="Добавить класс",
      command=do_add_class,
      font=(FONT_FAMILY, 12),
      width=15,
  ).pack(pady=6)
  tk.Button(
      win,
      text="Открыть класс",
      command=do_open_class,
      font=(FONT_FAMILY, 12),
      width=15,
  ).pack(pady=6)
  tk.Button(
      win,
      text="Удалить класс",
      command=do_delete_class,
      fg="red",
      font=(FONT_FAMILY, 12),
      width=15,
  ).pack(pady=6)
  win.protocol("WM_DELETE_WINDOW", root.destroy)


  center_win(win, 650, 600)
  win.resizable(True, True)
  win.deiconify()




def show_students_window(class_name, user_name):
  stu_win = tk.Toplevel()
  stu_win.withdraw()
  stu_win.title(f"Ученики класса {class_name}")


  user_data = app_data["users"][user_name]
  students = user_data["classes"][class_name]
  nobody_cfg = app_data["nobody_configs"].setdefault(
      class_name, {"prob": 10, "enabled": True}
  )


  equal_chances_var = tk.BooleanVar(value=False)


  # Нижняя панель управления
  bottom_frame = tk.Frame(stu_win)
  bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=15)


  scrollbar = tk.Scrollbar(stu_win, orient="vertical")
  canvas = tk.Canvas(stu_win, highlightthickness=0)
  scrollbar.config(command=canvas.yview)


  list_frame = tk.Frame(canvas)


  list_frame.bind(
      "<Configure>",
      lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
  )
  canvas_frame_id = canvas.create_window((0, 0), window=list_frame, anchor="nw")


  def _on_canvas_configure(e):
    canvas.itemconfig(canvas_frame_id, width=e.width)


  canvas.bind("<Configure>", _on_canvas_configure)
  canvas.configure(yscrollcommand=scrollbar.set)


  scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
  canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)


  # Универсальная обработка прокрутки под все ОС (Win / Mac / Linux)
  def _on_mousewheel(event):
    if sys.platform.startswith("win"):
      canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    elif sys.platform == "darwin":
      canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
    else:  # Linux (X11)
      if event.num == 4:
        canvas.yview_scroll(-1, "units")
      elif event.num == 5:
        canvas.yview_scroll(1, "units")


  stu_win.bind("<MouseWheel>", _on_mousewheel)
  stu_win.bind("<Button-4>", _on_mousewheel)
  stu_win.bind("<Button-5>", _on_mousewheel)


  def draw_list():
    for w in list_frame.winfo_children():
      w.destroy()


    list_frame.vars = []


    # Строка управления "Никто"
    nobody_row = tk.Frame(list_frame)
    nobody_row.pack(fill=tk.X, pady=8, padx=15)


    tk.Label(
        nobody_row, text="Никто", anchor="w", font=(FONT_FAMILY, 14, "bold")
    ).grid(row=0, column=0, padx=(0, 5), sticky="w")
    prob_lbl = tk.Label(
        nobody_row,
        text=f"({nobody_cfg['prob']}%)",
        width=6,
        font=(FONT_FAMILY, 14),
    )
    prob_lbl.grid(row=0, column=1, padx=5)


    def adjust_prob(delta):
      nobody_cfg["prob"] = max(0, min(100, nobody_cfg["prob"] + delta))
      prob_lbl.config(text=f"({nobody_cfg['prob']}%)")
      save_data(app_data)


    tk.Button(
        nobody_row,
        text="-",
        command=lambda: adjust_prob(-5),
        width=3,
        font=(FONT_FAMILY, 11),
    ).grid(row=0, column=2, padx=2)
    tk.Button(
        nobody_row,
        text="+",
        command=lambda: adjust_prob(5),
        width=3,
        font=(FONT_FAMILY, 11),
    ).grid(row=0, column=3, padx=2)


    def toggle_nobody():
      nobody_cfg["enabled"] = not nobody_cfg["enabled"]
      toggle_btn.config(
          text="Не использовать" if nobody_cfg["enabled"] else "Использовать",
          fg="red" if nobody_cfg["enabled"] else "green",
      )
      save_data(app_data)


    toggle_btn = tk.Button(
        nobody_row,
        text="Не использовать" if nobody_cfg["enabled"] else "Использовать",
        fg="red" if nobody_cfg["enabled"] else "green",
        width=15,
        font=(FONT_FAMILY, 11),
        command=toggle_nobody,
    )
    toggle_btn.grid(row=0, column=4, padx=10)


    # Разделительная черта
    sep = tk.Frame(list_frame, height=1, bg="#DDDDDD")
    sep.pack(fill=tk.X, padx=15, pady=5)


    students.sort(key=lambda s: s["name"])
    for i, stu in enumerate(students, 1):
      row = tk.Frame(list_frame)
      row.pack(fill=tk.X, pady=3, padx=15)


      var = tk.BooleanVar(value=stu["selected"])
      list_frame.vars.append(var)


      def toggle_sel(s=stu, v=var):
        s["selected"] = v.get()
        save_data(app_data)


      # 1. Порядковый номер
      tk.Label(
          row, text=f"{i}.", width=3, font=(FONT_FAMILY, 13), anchor="e"
      ).grid(row=0, column=0, padx=(0, 5), sticky="e")


      # 2. Галочка выбора
      cb = tk.Checkbutton(row, variable=var, command=toggle_sel)
      cb.var = var
      cb.grid(row=0, column=1, padx=5)


      # 3. Имя ученика
      tk.Label(
          row, text=stu["name"], width=30, anchor="w", font=(FONT_FAMILY, 13)
      ).grid(row=0, column=2, padx=5, sticky="w")


      # 4. Количество оценок
      grade_lbl = tk.Label(
          row, text=f"({stu['grades']})", width=5, font=(FONT_FAMILY, 13)
      )
      grade_lbl.grid(row=0, column=3, padx=5)


      def minus_grade(s=stu, lbl=grade_lbl):
        if s["grades"] > 0:
          s["grades"] -= 1
          lbl.config(text=f"({s['grades']})")
          save_data(app_data)


      def add_grade(s=stu, lbl=grade_lbl):
        s["grades"] += 1
        lbl.config(text=f"({s['grades']})")
        save_data(app_data)


      def delete_student(s=stu):
        if messagebox.askyesno(
            "Подтверждение удаления",
            f"Удалить ученика «{s['name']}» из класса?",
        ):
          students.remove(s)
          save_data(app_data)
          draw_list()


      # 5. Кнопки управления
      tk.Button(
          row, text="-", command=minus_grade, width=3, font=(FONT_FAMILY, 11)
      ).grid(row=0, column=4, padx=2)
      tk.Button(
          row, text="+", command=add_grade, width=3, font=(FONT_FAMILY, 11)
      ).grid(row=0, column=5, padx=2)
      tk.Button(
          row,
          text="✕",
          command=delete_student,
          width=3,
          font=(FONT_FAMILY, 10, "bold"),
          fg="red",
      ).grid(row=0, column=6, padx=(5, 10))


  draw_list()


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
    ):
      for s in students:
        s["grades"] = 0
      save_data(app_data)
      draw_list()
      messagebox.showinfo(
          "Готово", "Количество оценок у всех учеников сброшено до 0."
      )


  def open_add_student_dialog():
    add_win = tk.Toplevel(stu_win)
    add_win.withdraw()
    add_win.title("Добавить ученика")
    add_win.transient(stu_win)


    tk.Label(add_win, text="Фамилия:", font=(FONT_FAMILY, 14)).pack(
        pady=(15, 2)
    )
    ent_last = tk.Entry(add_win, width=25, font=(FONT_FAMILY, 14))
    ent_last.pack()
    ent_last.focus_set()


    tk.Label(add_win, text="Имя:", font=(FONT_FAMILY, 14)).pack(pady=(10, 2))
    ent_first = tk.Entry(add_win, width=25, font=(FONT_FAMILY, 14))
    ent_first.pack()


    def do_add():
      last = ent_last.get().strip()
      first = ent_first.get().strip()
      if not last or not first:
        messagebox.showwarning("Внимание", "Заполните оба поля!")
        return
      full = f"{last} {first}"
      if any(s["name"] == full for s in students):
        messagebox.showwarning("Внимание", "Такой ученик уже есть!")
        return
      students.append(
          {"name": full, "grades": 0, "selected": False, "last_round": 0}
      )
      save_data(app_data)
      add_win.destroy()
      draw_list()


    tk.Button(
        add_win,
        text="Добавить",
        command=do_add,
        font=(FONT_FAMILY, 13),
        width=12,
    ).pack(pady=20)


    center_win(add_win, 450, 350)
    add_win.resizable(True, True)
    add_win.deiconify()


  def open_ready_window():
    selected = [s for s in students if s["selected"]]
    # Исправление критического бага: обязательно требуем выбор учеников
    if not selected:
      messagebox.showwarning(
          "Внимание", "Отметьте галочками хотя бы одного ученика!"
      )
      return
    confirm_win = tk.Toplevel(stu_win)
    confirm_win.withdraw()
    confirm_win.title("Подтверждение")
    confirm_win.transient(stu_win)


    tk.Label(
        confirm_win,
        text=f"Выбрано {len(selected)} учеников",
        font=(FONT_FAMILY, 16, "bold"),
    ).pack(pady=30)


    def start_selection():
      confirm_win.destroy()
      show_result(selected)


    tk.Button(
        confirm_win,
        text="Поехали",
        command=start_selection,
        font=(FONT_FAMILY, 14),
        width=12,
    ).pack(pady=15)


    center_win(confirm_win, 550, 320)
    confirm_win.resizable(True, True)
    confirm_win.deiconify()


  def show_result(candidates):
    current_round = user_data.get("round_counter", 0) + 1
    if nobody_cfg["enabled"] and random.randint(1, 100) <= nobody_cfg["prob"]:
      user_data["round_counter"] = current_round
      save_data(app_data)
      res_win = tk.Toplevel()
      res_win.withdraw()
      res_win.title("Результат")


      tk.Label(
          res_win, text="Сегодня объясняет:", font=(FONT_FAMILY, 20)
      ).pack(pady=20)
      tk.Label(
          res_win, text="УЧИТЕЛЬ", font=(FONT_FAMILY, 56, "bold"), fg="#FF9800"
      ).pack(pady=15)
      tk.Label(
          res_win,
          text="Никто из учеников не вызван.",
          font=(FONT_FAMILY, 16),
          fg="gray",
      ).pack(pady=10)
      tk.Button(
          res_win,
          text="Закрыть",
          command=res_win.destroy,
          font=(FONT_FAMILY, 13),
      ).pack(pady=20)


      res_win.update_idletasks()
      w = max(650, res_win.winfo_reqwidth() + 60)
      h = max(450, res_win.winfo_reqheight() + 40)
      center_win(res_win, w, h)
      res_win.resizable(True, True)
      res_win.deiconify()
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


    res_win = tk.Toplevel()
    res_win.withdraw()
    res_win.title("Результат")


    tk.Label(
        res_win, text="Сегодня отвечает:", font=(FONT_FAMILY, 20)
    ).pack(pady=15)


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
        res_win,
        text=name_text,
        font=(FONT_FAMILY, f_size, "bold"),
        fg="#2196F3",
        wraplength=1000,
    ).pack(pady=15, padx=20)


    grades_info = f"Оценок у ученика: {chosen['grades']}" + (
        " (приравнено к 0)" if is_equalized else ""
    )
    tk.Label(
        res_win, text=grades_info, font=(FONT_FAMILY, 16), fg="gray"
    ).pack(pady=8)
    tk.Label(
        res_win,
        text=f"Вес: {c_weight} | Диапазон: [{c_start}-{c_end}]",
        font=("Courier", 12),
        fg="#555",
    ).pack(pady=5)
    tk.Label(
        res_win,
        text=f"Всего: 1-{total_range} | Выпало: {roll}",
        font=("Courier", 12),
        fg="#555",
    ).pack(pady=10)
    tk.Button(
        res_win,
        text="Закрыть",
        command=res_win.destroy,
        font=(FONT_FAMILY, 13),
    ).pack(pady=20)


    res_win.update_idletasks()
    w = max(650, res_win.winfo_reqwidth() + 60)
    h = max(450, res_win.winfo_reqheight() + 40)
    center_win(res_win, w, h)
    res_win.resizable(True, True)
    res_win.deiconify()


  # Панель управления снизу
  tk.Button(
      bottom_frame,
      text="Выбрать всех",
      command=do_select_all,
      font=(FONT_FAMILY, 12),
      width=13,
  ).pack(side=tk.LEFT, padx=5)


  tk.Button(
      bottom_frame,
      text="Готово",
      command=open_ready_window,
      width=12,
      font=(FONT_FAMILY, 12, "bold"),
  ).pack(side=tk.RIGHT, padx=5)


  tk.Button(
      bottom_frame,
      text="Обнулить оценки",
      command=do_reset_grades,
      font=(FONT_FAMILY, 12),
      fg="red",
      width=15,
  ).pack(side=tk.RIGHT, padx=5)


  tk.Checkbutton(
      bottom_frame,
      text="Уравнять шансы",
      variable=equal_chances_var,
      font=(FONT_FAMILY, 12),
  ).pack(side=tk.RIGHT, padx=10)


  tk.Button(
      bottom_frame,
      text="Добавить ученика",
      command=open_add_student_dialog,
      font=(FONT_FAMILY, 12),
      width=16,
  ).pack(side=tk.RIGHT, padx=5)


  center_win(stu_win, 950, 650)
  stu_win.resizable(True, True)
  stu_win.deiconify()




root.mainloop()

