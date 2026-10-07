import tkinter as tk
from tkinter import ttk
import random
import time
import threading

class CancerResearchTool(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Система поиска и анализа способов лечения (Прототип/Исследования)")
        self.geometry("800x600")
        self.configure(bg="#f0f5f9")

        self.style = ttk.Style(self)
        self.style.theme_use('clam')

        # Header
        header = ttk.Frame(self)
        header.pack(fill="x", pady=10)
        ttk.Label(header, text="Анализатор биоинформатических данных", font=("Helvetica", 18, "bold")).pack()
        ttk.Label(header, text="Внимание: Только для исследовательских и образовательных целей. Не для клинического применения.", foreground="red").pack()

        # Main content
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Controls
        controls = ttk.Frame(main_frame)
        controls.pack(fill="x", pady=10)

        ttk.Label(controls, text="Тип данных:").pack(side="left", padx=5)
        self.data_type = ttk.Combobox(controls, values=["Геномные профили", "Экспрессия белков", "Клинические испытания (публичные)"])
        self.data_type.current(0)
        self.data_type.pack(side="left", padx=5)

        ttk.Button(controls, text="Запустить анализ", command=self.start_analysis).pack(side="left", padx=20)

        # Progress
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(fill="x", pady=20)

        self.status_label = ttk.Label(main_frame, text="Готов к работе...")
        self.status_label.pack()

        # Results
        results_frame = ttk.LabelFrame(main_frame, text="Результаты симуляции")
        results_frame.pack(fill="both", expand=True, pady=10)

        self.results_text = tk.Text(results_frame, height=15, state="disabled", bg="#ffffff")
        self.results_text.pack(fill="both", expand=True, padx=5, pady=5)

    def log_result(self, message):
        def _log():
            self.results_text.config(state="normal")
            self.results_text.insert("end", message + "\n")
            self.results_text.see("end")
            self.results_text.config(state="disabled")
        self.after(0, _log)

    def start_analysis(self):
        self.progress_var.set(0)
        self.results_text.config(state="normal")
        self.results_text.delete(1.0, "end")
        self.results_text.config(state="disabled")
        self.status_label.config(text="Загрузка данных...")

        # Запускаем в отдельном потоке, чтобы не зависал интерфейс
        threading.Thread(target=self._run_mock_analysis, daemon=True).start()

    def update_progress(self, value, step_text):
        self.progress_var.set(value)
        self.status_label.config(text=step_text)

    def finish_analysis(self):
        self.status_label.config(text="Анализ завершен.")

    def _run_mock_analysis(self):
        dtype = self.data_type.get()
        self.log_result(f"Инициализация анализа для: {dtype}")

        steps = [
            "Парсинг публичных датасетов...",
            "Нормализация данных...",
            "Поиск биомаркеров...",
            "Применение алгоритмов машинного обучения...",
            "Кросс-валидация результатов...",
            "Генерация отчета..."
        ]

        for i, step in enumerate(steps):
            time.sleep(1.5)  # Симуляция работы
            self.after(0, self.update_progress, (i + 1) * (100 / len(steps)), step)
            self.log_result(f"[+] {step} Успешно.")

        time.sleep(1)
        self.after(0, self.finish_analysis)
        self.log_result("\n=== ВЫВОДЫ (СИМУЛЯЦИЯ) ===")

        mock_findings = [
            "Выявлена корреляция между геном XYZ и ответом на препарат А (p < 0.05).",
            "Потенциальная мишень: белок ABC1. Требуются дальнейшие in vitro тесты.",
            "Анализ выживаемости: группы с мутацией DEF показывают лучшую динамику при терапии B.",
            "Обнаружена аномальная экспрессия в путях метаболизма глюкозы."
        ]

        self.log_result(random.choice(mock_findings))
        self.log_result("\nНапоминание: Это симуляция на основе публичных алгоритмов.")

if __name__ == "__main__":
    app = CancerResearchTool()
    app.mainloop()
