# src/app.py
import tkinter as tk
from gui import PasswordApp

def main():
    root = tk.Tk()
    app = PasswordApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
