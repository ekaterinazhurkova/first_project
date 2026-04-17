import os
import customtkinter as ctk
from tkinter import filedialog
import segyio
import numpy as np
import gc  # <-- Добавлена библиотека для очистки памяти

# Настройка внешнего вида
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

class SeismicApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Сейсмокуб")
        self.geometry("600x650") # Немного увеличил окно для удобства
        
        # Переменные для хранения состояния
        self.current_file_path = None
        self.total_traces = 0
        self.samples_count = 0

        self.setup_ui()

    def setup_ui(self):
        # --- БЛОК 1: Загрузка файла ---
        self.frame_file = ctk.CTkFrame(self)
        self.frame_file.pack(pady=20, padx=20, fill="x")

        ctk.CTkLabel(self.frame_file, text="Загрузка файла", font=("Arial", 16, "bold")).pack(pady=10)

        self.btn_load = ctk.CTkButton(self.frame_file, text="Выбрать файл", command=self.load_file)
        self.btn_load.pack(pady=10)

        self.label_file_status = ctk.CTkLabel(self.frame_file, text="Файл не выбран", text_color="gray")
        self.label_file_status.pack(pady=(5, 2))
        
        self.label_file_info = ctk.CTkLabel(self.frame_file, text="")
        self.label_file_info.pack(pady=(0, 10))

        # --- БЛОК 2: Выбор трасс ---
        self.frame_data = ctk.CTkFrame(self)
        self.frame_data.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(self.frame_data, text="Выбор данных (пока что только для чтения)", font=("Arial", 16, "bold")).pack(pady=10)

        # Контейнер для трех полей ввода
        self.input_container = ctk.CTkFrame(self.frame_data, fg_color="transparent")
        self.input_container.pack(pady=10)

        # Поле ОТ
        ctk.CTkLabel(self.input_container, text="От:").grid(row=0, column=0, padx=5)
        self.entry_start = ctk.CTkEntry(self.input_container, placeholder_text="0", width=80, state="disabled")
        self.entry_start.grid(row=0, column=1, padx=10)

        # Поле ДО
        ctk.CTkLabel(self.input_container, text="До:").grid(row=0, column=2, padx=5)
        self.entry_end = ctk.CTkEntry(self.input_container, placeholder_text="Конец", width=80, state="disabled")
        self.entry_end.grid(row=0, column=3, padx=10)

        # Поле ШАГ
        ctk.CTkLabel(self.input_container, text="Шаг:").grid(row=0, column=4, padx=5)
        self.entry_step = ctk.CTkEntry(self.input_container, placeholder_text="1", width=60, state="disabled")
        self.entry_step.grid(row=0, column=5, padx=10)

        self.btn_read = ctk.CTkButton(
            self.frame_data, 
            text="Прочитать в память", 
            command=self.read_data, 
            state="disabled", 
            fg_color="#2ecc71", 
            hover_color="#27ae60"
        )
        self.btn_read.pack(pady=15)

        # --- БЛОК 3: Вывод результата ---
        self.label_result = ctk.CTkLabel(self, text="", font=("Arial", 14), text_color="#f1c40f")
        self.label_result.pack(pady=20)

    def load_file(self):
        file_path = filedialog.askopenfilename(
            title="Выберите SEGY файл",
            filetypes=(("SEGY files", "*.sgy *.segy"), ("All files", "*.*"))
        )

        if not file_path:
            return

        try:
            with segyio.open(file_path, "r", ignore_geometry=True) as f:
                self.total_traces = f.tracecount
                self.samples_count = len(f.samples)
            
            self.current_file_path = file_path
            name = os.path.basename(file_path)

            self.label_file_status.configure(text=f"Успешно: {name}", text_color="#2ecc71")
            self.label_file_info.configure(
                text=f"Всего трасс: {self.total_traces}\nКоличество строк: {self.samples_count}",
                text_color="white"
            )

            # Включаем все поля ввода
            self.entry_start.configure(state="normal")
            self.entry_end.configure(state="normal", placeholder_text=str(self.total_traces))
            self.entry_step.configure(state="normal")
            self.btn_read.configure(state="normal")
            
            self.label_result.configure(text="")

        except Exception as e:
            self.label_file_status.configure(text=f"Ошибка чтения: {e}", text_color="#e74c3c")

    def read_data(self):
        try:
            # Считываем значения или ставим дефолты
            start = int(self.entry_start.get()) if self.entry_start.get() else 0
            end = int(self.entry_end.get()) if self.entry_end.get() else self.total_traces
            step = int(self.entry_step.get()) if self.entry_step.get() else 1

            # Валидация
            if step <= 0:
                self.label_result.configure(text="Ошибка: Шаг должен быть больше 0", text_color="#e74c3c")
                return
            if start < 0 or end > self.total_traces or start >= end:
                self.label_result.configure(text="Ошибка: Неверный диапазон трасс", text_color="#e74c3c")
                return

            # --- ОЧИСТКА СТАРОЙ ПАМЯТИ ---
            if hasattr(self, 'matrix_data'):
                del self.matrix_data # Удаляем ссылку на старую матрицу
                gc.collect()         # Принудительно очищаем RAM

            # --- ЧТЕНИЕ НОВЫХ ДАННЫХ ---
            with segyio.open(self.current_file_path, "r", ignore_geometry=True) as f:
                self.label_result.configure(text="Чтение данных...", text_color="white")
                self.update()
                
                # Используем срез [от : до : шаг]
                self.matrix_data = f.trace.raw[start : end : step]

            shape = self.matrix_data.shape
            
            success_msg = (
                f"✅ Данные загружены!\n\n"
                f"Трасс выбрано: {shape[0]} (с шагом {step})\n"
                f"Точек в каждой: {shape[1]}\n"
                f"Размер матрицы: {shape[0]}x{shape[1]}"
            )
            self.label_result.configure(text=success_msg, text_color="#2ecc71")

        except ValueError:
            self.label_result.configure(text="Ошибка: Введите целые числа в поля", text_color="#e74c3c")

if __name__ == "__main__":
    app = SeismicApp()
    app.mainloop()
