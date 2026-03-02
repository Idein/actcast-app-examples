import tkinter as tk
from tkinter import font

def on_submit():
    text = entry.get()
    result_label.config(text=f"入力: {text}")

root = tk.Tk()
root.title("テキスト入力GUI")

font_candidates = [
    "Noto Sans CJK JP",
    "Noto Sans JP",
]
available = set(font.families())
chosen_font = next((f for f in font_candidates if f in available), None)

ui_font = (chosen_font, 12) if chosen_font else ("TkDefaultFont", 12)

label = tk.Label(root, text="日本語も表示できます。入力してください:", font=ui_font)
label.pack(padx=10, pady=(10, 5), anchor="w")

entry = tk.Entry(root, width=30, font=ui_font)
entry.pack(padx=10, pady=5, fill="x")
entry.focus_set()

btn = tk.Button(root, text="決定", command=on_submit, font=ui_font)
btn.pack(padx=10, pady=5, anchor="e")

result_label = tk.Label(root, text="入力:", font=ui_font)
result_label.pack(padx=10, pady=(5, 10), anchor="w")

root.mainloop()
