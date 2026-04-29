import tkinter as tk
from tkinter import messagebox, simpledialog
import json
import os
import random

DATA_FILE = "school_data.json"

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
                        new_data["users"][name] = {"password": pwd, "classes": {}, "round_counter": 0}
                    return new_data
                return data
        except json.JSONDecodeError:
            pass
    return {
        "users": {
            "admin": {
                "password": "1234",
                "classes": {"10А": [{"name": "Смирнов Алексей", "grades": 0, "selected": False, "last_round": 0}]},
                "round_counter": 0
            }
        }
    }

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

app_data = load_data()

root = tk.Tk()
root.title("Авторизация")
root.geometry("320x280")

tk.Label(root, text="Здравствуйте!\nНеобходимо авторизоваться", font=("Arial", 12)).pack(pady=15)
tk.Label(root, text="Имя:").pack()
entry_name = tk.Entry(root, width=25)
entry_name.pack(pady=3)
tk.Label(root, text="Пароль:").pack()
entry_pass = tk.Entry(root, width=25, show="*")
entry_pass.pack(pady=3)

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
        if messagebox.askyesno("Пользователь не найден", "Ваше имя не найдено. Зарегистрироваться?"):
            app_data["users"][name] = {"password": password, "classes": {}, "round_counter": 0}
            save_data(app_data)
            messagebox.showinfo("Успех", "Регистрация прошла успешно!")
            open_main_window(name)

tk.Button(root, text="Войти", command=try_login).pack(pady=15)

def open_main_window(user_name):
    root.withdraw()
    win = tk.Toplevel()
    win.title("Главное меню")
    win.geometry("350x380")

    tk.Label(win, text=f"Добро пожаловать, {user_name}!", font=("Arial", 13, "bold")).pack(pady=10)
    tk.Label(win, text="выберите класс:", font=("Arial", 11)).pack(pady=5)

    user_classes = app_data["users"][user_name]["classes"]
    listbox = tk.Listbox(win, width=28, height=8, font=("Arial", 11))
    listbox.pack(pady=5)

    def refresh_classes():
        listbox.delete(0, tk.END)
        for cls in sorted(user_classes.keys()):
            listbox.insert(tk.END, cls)
    refresh_classes()

    def do_add_class():
        new_name = simpledialog.askstring("Новый класс", "Введите название (например, 9Б):")
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

    tk.Button(win, text="Добавить класс", command=do_add_class).pack(pady=5)
    tk.Button(win, text="Открыть класс", command=do_open_class).pack(pady=5)
    win.protocol("WM_DELETE_WINDOW", root.destroy)

def show_students_window(class_name, user_name):
    stu_win = tk.Toplevel()
    stu_win.title(f"Ученики класса {class_name}")
    stu_win.geometry("620x600")

    user_data = app_data["users"][user_name]
    students = user_data["classes"][class_name]

    canvas = tk.Canvas(stu_win, highlightthickness=0)
    scrollbar = tk.Scrollbar(stu_win, orient="vertical", command=canvas.yview)
    list_frame = tk.Frame(canvas)

    list_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=list_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    stu_win.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

    def draw_list():
        for w in list_frame.winfo_children():
            w.destroy()
        students.sort(key=lambda s: s["name"])
        for i, stu in enumerate(students, 1):
            row = tk.Frame(list_frame)
            row.pack(fill=tk.X, pady=3, padx=5)

            tk.Label(row, text=f"{i}.", width=3, font=("Arial", 10)).pack(side=tk.LEFT)
            tk.Label(row, text=stu["name"], width=25, anchor="w", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)

            grade_lbl = tk.Label(row, text=f"({stu['grades']})", width=4, font=("Arial", 10))
            grade_lbl.pack(side=tk.LEFT, padx=5)

            def minus_grade(s=stu, lbl=grade_lbl):
                if s['grades'] > 0:
                    s['grades'] -= 1
                    lbl.config(text=f"({s['grades']})")
                    save_data(app_data)
            def add_grade(s=stu, lbl=grade_lbl):
                s['grades'] += 1
                lbl.config(text=f"({s['grades']})")
                save_data(app_data)

            tk.Button(row, text="-", command=minus_grade, width=2).pack(side=tk.LEFT, padx=2)
            tk.Button(row, text="+", command=add_grade, width=2).pack(side=tk.LEFT, padx=2)

            var = tk.BooleanVar(value=stu["selected"])
            def toggle_sel(s=stu, v=var):
                s["selected"] = v.get()
                save_data(app_data)
            tk.Checkbutton(row, variable=var, command=toggle_sel).pack(side=tk.LEFT, padx=5)

    draw_list()

    bottom_frame = tk.Frame(stu_win)
    bottom_frame.pack(fill=tk.X, padx=10, pady=10)

    def do_select_all():
        if not students: return
        new_state = not all(s["selected"] for s in students)
        for s in students:
            s["selected"] = new_state
        save_data(app_data)
        draw_list()

    def open_add_student_dialog():
        add_win = tk.Toplevel(stu_win)
        add_win.title("Добавить ученика")
        add_win.geometry("280x220")
        add_win.transient(stu_win)

        tk.Label(add_win, text="Фамилия:").pack(pady=(15, 2))
        ent_last = tk.Entry(add_win, width=25)
        ent_last.pack()
        tk.Label(add_win, text="Имя:").pack(pady=(10, 2))
        ent_first = tk.Entry(add_win, width=25)
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
            students.append({"name": full, "grades": 0, "selected": False, "last_round": 0})
            save_data(app_data)
            add_win.destroy()
            draw_list()

        tk.Button(add_win, text="Добавить", command=do_add).pack(pady=15)

    def open_ready_window():
        selected = [s for s in students if s["selected"]]
        if not selected:
            messagebox.showwarning("Внимание", "Отметьте галочками хотя бы одного ученика!")
            return
        confirm_win = tk.Toplevel(stu_win)
        confirm_win.title("Подтверждение")
        confirm_win.geometry("320x200")
        confirm_win.transient(stu_win)
        tk.Label(confirm_win, text=f"Выбрано {len(selected)} учеников", font=("Arial", 13, "bold")).pack(pady=30)
        tk.Button(confirm_win, text="Поехали", command=lambda: (confirm_win.destroy(), show_result(selected)), font=("Arial", 11, "bold")).pack(pady=15)

    def show_result(candidates):
        current_round = user_data.get("round_counter", 0) + 1
        intervals = []
        current_bound = 0
        for s in candidates:
            base_weight = int(1000 / (s["grades"] + 1))
            rounds_since = current_round - s.get("last_round", 0)
            if rounds_since <= 1: history_coef = 0.2
            elif rounds_since == 2: history_coef = 0.5
            elif rounds_since == 3: history_coef = 0.8
            else: history_coef = 1.0

            custom_coef = 1.0
            if s["name"] == "Тайнов Алексей":
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
        res_win.title("Результат")
        res_win.geometry("400x350")
        res_win.resizable(False, False)
        tk.Label(res_win, text="Сегодня отвечает:", font=("Arial", 14)).pack(pady=20)
        tk.Label(res_win, text=chosen["name"], font=("Arial", 24, "bold"), fg="#2196F3").pack(pady=10)
        tk.Label(res_win, text=f"Оценок у ученика: {chosen['grades']}", font=("Arial", 12), fg="gray").pack(pady=5)
        tk.Label(res_win, text=f"Вес: {c_weight} | Диапазон: [{c_start}-{c_end}]", font=("Courier", 10), fg="#555").pack(pady=5)
        tk.Label(res_win, text=f"Всего: 1-{total_range} | Выпало: {roll}", font=("Courier", 10), fg="#555").pack(pady=15)
        tk.Button(res_win, text="Закрыть", command=res_win.destroy, font=("Arial", 11)).pack(pady=20)

    tk.Button(bottom_frame, text="Выбрать всех", command=do_select_all).pack(side=tk.LEFT, padx=5)
    tk.Button(bottom_frame, text="Добавить ученика", command=open_add_student_dialog).pack(side=tk.LEFT, padx=5)
    tk.Button(bottom_frame, text="Готово", command=open_ready_window, width=12).pack(side=tk.RIGHT, padx=5)

root.mainloop()



