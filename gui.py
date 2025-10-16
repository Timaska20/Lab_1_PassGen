# src/gui.py
import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from generator import build_alphabet, generate_password
from presets import save_preset, load_preset, list_presets
from utils import estimate_entropy
from pathlib import Path

try:
    import pyperclip
    HAS_PYPERCLIP = True
except Exception:
    HAS_PYPERCLIP = False

# ==== ДОБАВЛЕНО: функции для расчёта по методичке (P, V, T, S*) ====
def _required_space(V_per_sec: float, T_seconds: float, P: float) -> float:
    """
    S* = (V * T) / P
    V_per_sec — попыток/сек, T_seconds — секунды, P — допустимая вероятность успеха.
    """
    if P <= 0 or V_per_sec < 0 or T_seconds <= 0:
        return 0.0
    return (V_per_sec * T_seconds) / P

def _compute_min_length(alphabet_size: int, P: float, V_attempts_per_min: float, T_value: float, T_unit: str) -> int:
    """
    Находит минимальное L: A^L >= S*, где S* = (V*T)/P.
    V — попыток/мин, T — в выбранных единицах.
    """
    if alphabet_size <= 1:
        return 0
    units = {
        "min": 60.0,
        "hour": 3600.0,
        "day": 86400.0,
        "week": 7 * 86400.0,
        "month": 30 * 86400.0,
    }
    unit_sec = units.get(T_unit, 86400.0)
    V_per_sec = V_attempts_per_min / 60.0
    S_star = _required_space(V_per_sec, T_value * unit_sec, P)
    if S_star <= 1:
        return 1
    import math
    return int(math.ceil(math.log(S_star, alphabet_size)))
# ====================================================================

DEFAULT_LEN = 16

class PasswordApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Password Generator")
        root.geometry("860x620")  # чуть выше из-за новых блоков

        # ttkbootstrap theme
        self.style = tb.Style(theme="cyborg")  # можно "darkly", "flatly", "cosmo"
        frame = tb.Frame(root, padding=12)
        frame.pack(fill="both", expand=True)

        # Left panel
        left = tb.Frame(frame)
        left.pack(side=LEFT, fill=BOTH, expand=True, padx=6, pady=6)

        # Длина пароля — ТЕКСТОВОЕ ПОЛЕ
        length_frame = tb.Frame(left)
        length_frame.pack(fill="x", pady=6)
        tb.Label(length_frame, text="Длина пароля:").pack(side=LEFT)

        self.length_var = tk.IntVar(value=DEFAULT_LEN)
        self.length_entry = tb.Entry(length_frame, textvariable=self.length_var, width=6)
        self.length_entry.pack(side=LEFT, padx=6)

        # ограничения на длину
        def validate_length(event=None):
            try:
                val = int(self.length_var.get())
                if val < 4: val = 4
                if val > 128: val = 128
                self.length_var.set(val)
            except Exception:
                self.length_var.set(DEFAULT_LEN)
            self.update_stats()

        self.length_entry.bind("<FocusOut>", validate_length)
        self.length_entry.bind("<Return>", validate_length)

        # Группы символов
        groups = tb.Labelframe(left, text="Группы символов")
        groups.pack(fill="x", pady=6)
        self.use_upper = tk.BooleanVar(value=True)
        self.use_lower = tk.BooleanVar(value=True)
        self.use_digits = tk.BooleanVar(value=True)
        self.use_symbols = tk.BooleanVar(value=False)
        tb.Checkbutton(groups, text="A–Z (заглавные)", variable=self.use_upper).pack(anchor="w")
        tb.Checkbutton(groups, text="a–z (строчные)", variable=self.use_lower).pack(anchor="w")
        tb.Checkbutton(groups, text="0–9 (цифры)", variable=self.use_digits).pack(anchor="w")
        tb.Checkbutton(groups, text="Символы (!@#...)", variable=self.use_symbols).pack(anchor="w")

        # Пользовательский алфавит
        custom_frame = tb.Labelframe(left, text="Пользовательский алфавит")
        custom_frame.pack(fill=BOTH, expand=True, pady=6)
        self.custom_text = tk.Text(custom_frame, height=6, wrap="word")
        self.custom_text.pack(fill="both", expand=True, padx=6, pady=6)
        self.replace_only = tk.BooleanVar(value=False)
        tb.Checkbutton(left, text="Использовать ТОЛЬКО пользовательский алфавит",
                       variable=self.replace_only).pack(anchor="w")

        # === Блок P, V, T (методичка) ===
        lab_frame = tb.Labelframe(left, text="Параметры устойчивости (P, V, T)")
        lab_frame.pack(fill="x", pady=6)

        row1 = tb.Frame(lab_frame); row1.pack(fill="x", pady=2)
        tb.Label(row1, text="P (допустимая вероятность):").pack(side=LEFT)
        self.p_var = tk.StringVar(value="1e-9")
        tb.Entry(row1, textvariable=self.p_var, width=10).pack(side=LEFT, padx=6)

        row2 = tb.Frame(lab_frame); row2.pack(fill="x", pady=2)
        tb.Label(row2, text="V (попыток/мин):").pack(side=LEFT)
        self.v_var = tk.StringVar(value="10")
        tb.Entry(row2, textvariable=self.v_var, width=10).pack(side=LEFT, padx=6)

        row3 = tb.Frame(lab_frame); row3.pack(fill="x", pady=2)
        tb.Label(row3, text="T:").pack(side=LEFT)
        self.t_val_var = tk.StringVar(value="7")
        tb.Entry(row3, textvariable=self.t_val_var, width=6).pack(side=LEFT, padx=6)
        self.t_unit_var = tk.StringVar(value="day")
        tb.Combobox(row3, textvariable=self.t_unit_var,
                    values=["min","hour","day","week","month"],
                    width=7, state="readonly").pack(side=LEFT)

        var_frame = tb.Frame(lab_frame); var_frame.pack(fill="x", pady=4)
        tb.Label(var_frame, text="Варианты (табл. 1):").pack(side=LEFT)
        tb.Button(var_frame, text="1", command=lambda: self._apply_variant(1)).pack(side=LEFT, padx=2)
        tb.Button(var_frame, text="2", command=lambda: self._apply_variant(2)).pack(side=LEFT, padx=2)
        tb.Button(var_frame, text="3", command=lambda: self._apply_variant(3)).pack(side=LEFT, padx=2)
        tb.Button(var_frame, text="4", command=lambda: self._apply_variant(4)).pack(side=LEFT, padx=2)

        tb.Button(lab_frame, text="Рассчитать минимальную длину L",
                  bootstyle=INFO, command=self.on_compute_L).pack(fill="x", padx=4, pady=6)

        self.requirement_label = tb.Label(lab_frame, text="Требование: —")
        self.requirement_label.pack(fill="x", padx=4, pady=(0,4))

        # Right panel
        right = tb.Frame(frame)
        right.pack(side=RIGHT, fill=BOTH, expand=True, padx=6, pady=6)

        out_frame = tb.Labelframe(right, text="Сгенерированный пароль")
        out_frame.pack(fill=BOTH, expand=True)
        self.password_var = tk.StringVar()
        self.password_entry = tb.Entry(out_frame, textvariable=self.password_var, font=("Consolas", 14))
        self.password_entry.pack(fill="x", padx=8, pady=(8,6))

        stats = tb.Frame(out_frame)
        stats.pack(fill="x", padx=8, pady=(0,8))
        self.alphabet_label = tb.Label(stats, text="Алфавит: —")
        self.alphabet_label.pack(side=LEFT)
        self.entropy_label = tb.Label(stats, text="Энтропия: — бит")
        self.entropy_label.pack(side=RIGHT)

        btns = tb.Frame(right)
        btns.pack(fill="x", pady=6, padx=8)
        tb.Button(btns, text="Generate", bootstyle=PRIMARY, command=self.on_generate).pack(side=LEFT, padx=6)
        tb.Button(btns, text="Copy", command=self.on_copy).pack(side=LEFT, padx=6)
        tb.Button(btns, text="Clear", bootstyle=WARNING, command=self.on_clear).pack(side=LEFT, padx=6)
        tb.Button(btns, text="Export...", command=self.on_export).pack(side=RIGHT, padx=6)

        # key bindings
        root.bind("<Return>", lambda e: self.on_generate())

        self.update_stats()

    def build_alphabet_local(self):
        custom = self.custom_text.get("1.0", tk.END).rstrip("\n")
        return build_alphabet(self.use_upper.get(), self.use_lower.get(), self.use_digits.get(),
                              self.use_symbols.get(), custom=custom, replace_only=self.replace_only.get())

    def update_stats(self):
        alphabet = self.build_alphabet_local()
        size = len(alphabet)
        try:
            length = int(self.length_var.get())
        except Exception:
            length = DEFAULT_LEN
            self.length_var.set(length)

        ent = estimate_entropy(size, length)
        self.alphabet_label.config(text=f"Алфавит: {size} символов")
        self.entropy_label.config(text=f"Энтропия: {ent:.1f} бит")

        # расчёт S* и статус требования
        try:
            P = float(str(self.p_var.get()).replace(",", "."))
            V = float(str(self.v_var.get()).replace(",", "."))
            T_val = float(str(self.t_val_var.get()).replace(",", "."))
            T_unit = self.t_unit_var.get() or "day"

            units = {"min":60, "hour":3600, "day":86400, "week":7*86400, "month":30*86400}
            unit_sec = units.get(T_unit, 86400)
            V_per_sec = V / 60.0
            S_star = _required_space(V_per_sec, T_val * unit_sec, P) if (P>0 and V>=0 and T_val>0) else 0.0

            meets = (size ** length) >= S_star if (size > 1 and S_star > 0) else False
            if S_star <= 0:
                text = "Требование: —"
            else:
                text = f"Требование: A^L {'≥' if meets else '<'} S* ≈ {S_star:,.0f}".replace(",", " ")
            self.requirement_label.config(text=text)
        except Exception:
            self.requirement_label.config(text="Требование: —")

    def on_generate(self):
        self.update_stats()
        alphabet = self.build_alphabet_local()
        try:
            length = int(self.length_var.get())
            if length < 4: length = 4
            if length > 128: length = 128
            self.length_var.set(length)
        except Exception:
            length = DEFAULT_LEN
            self.length_var.set(length)

        if not alphabet:
            messagebox.showwarning("Пустой алфавит", "Выберите группы или введите пользовательский алфавит.")
            return
        try:
            pwd = generate_password(length, alphabet)
            self.password_var.set(pwd)
            self.password_entry.select_range(0, tk.END)
            self.password_entry.icursor(tk.END)
        finally:
            self.update_stats()

    def on_copy(self):
        pwd = self.password_var.get()
        if not pwd:
            return
        if HAS_PYPERCLIP:
            try:
                import pyperclip
                pyperclip.copy(pwd)
                messagebox.showinfo("Скопировано", "Пароль скопирован в буфер обмена")
                return
            except Exception:
                pass
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(pwd)
            messagebox.showinfo("Скопировано", "Пароль скопирован (tkinter clipboard)")
        except Exception as e:
            messagebox.showerror("Ошибка копирования", str(e))

    def on_clear(self):
        self.password_var.set("")

    def on_export(self):
        pwd = self.password_var.get()
        if not pwd:
            messagebox.showwarning("Пусто", "Сначала сгенерируйте пароль")
            return
        fname = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files","*.txt")])
        if fname:
            with open(fname, "w", encoding="utf-8") as f:
                f.write(pwd + "\n")
            messagebox.showinfo("Экспорт", f"Пароль сохранён в {fname}")

    def save_preset_dialog(self):
        default_dir = Path.cwd() / "presets"
        default_dir.mkdir(exist_ok=True)
        name = filedialog.asksaveasfilename(defaultextension=".json", initialdir=str(default_dir),
                                            filetypes=[("JSON","*.json")], title="Сохранить пресет как...")
        if not name:
            return
        settings = {
            "length": self.length_var.get(),
            "use_upper": self.use_upper.get(),
            "use_lower": self.use_lower.get(),
            "use_digits": self.use_digits.get(),
            "use_symbols": self.use_symbols.get(),
            "custom": self.custom_text.get("1.0", tk.END),
            "replace_only": self.replace_only.get(),
        }
        try:
            p = Path(name)
            save_preset(p.stem, settings)
            messagebox.showinfo("Сохранено", f"Пресет сохранён в {p.with_suffix('.json')}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def load_preset_dialog(self):
        files = list_presets()
        default_dir = Path.cwd() / "presets"
        default_dir.mkdir(exist_ok=True)
        if not files:
            messagebox.showwarning("Нет пресетов", f"Папка {default_dir} пуста")
            return
        fname = filedialog.askopenfilename(initialdir=str(default_dir), filetypes=[("JSON","*.json")])
        if not fname:
            return
        try:
            s = load_preset(fname)
            self.length_var.set(s.get("length", DEFAULT_LEN))
            self.use_upper.set(s.get("use_upper", True))
            self.use_lower.set(s.get("use_lower", True))
            self.use_digits.set(s.get("use_digits", True))
            self.use_symbols.set(s.get("use_symbols", False))
            self.custom_text.delete("1.0", tk.END)
            self.custom_text.insert("1.0", s.get("custom",""))
            self.replace_only.set(s.get("replace_only", False))
            self.update_stats()
            messagebox.showinfo("Загружено", "Пресет загружен")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    # Варианты из таблицы (подгони под свою методичку, если нужно)
    def _apply_variant(self, n: int):
        if n == 1:
            self.p_var.set("1e-9");  self.v_var.set("50");  self.t_val_var.set("5"); self.t_unit_var.set("day")
        elif n == 2:
            self.p_var.set("1e-9");  self.v_var.set("100"); self.t_val_var.set("1"); self.t_unit_var.set("month")
        elif n == 3:
            self.p_var.set("1e-12"); self.v_var.set("15");  self.t_val_var.set("2"); self.t_unit_var.set("week")
        elif n == 4:
            self.p_var.set("1e-8");  self.v_var.set("200"); self.t_val_var.set("1"); self.t_unit_var.set("week")
        self.update_stats()

    def on_compute_L(self):
        # читаем ввод
        try:
            P = float(str(self.p_var.get()).replace(",", "."))
        except Exception:
            P = 1e-9
        try:
            V = float(str(self.v_var.get()).replace(",", "."))
        except Exception:
            V = 10.0
        try:
            T_val = float(str(self.t_val_var.get()).replace(",", "."))
        except Exception:
            T_val = 7.0
        T_unit = self.t_unit_var.get() or "day"

        # текущий алфавит
        A = len(self.build_alphabet_local())
        if A <= 1:
            messagebox.showwarning("Алфавит слишком мал", "Расширьте алфавит (выберите группы/добавьте символы).")
            return

        # вычислить минимальную длину
        L = _compute_min_length(A, P, V, T_val, T_unit)
        self.length_var.set(L)
        self.update_stats()
        messagebox.showinfo("Расчёт длины", f"Минимальная длина L при A={A}:\nL = {L}")
