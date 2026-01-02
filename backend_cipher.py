import tkinter as tk
from tkinter import messagebox

class CipherBackend:
    b = 5

    def __init__(self):
        self.alfabet = "абвгґдеєжзиіїйклмнопрстуфхцчшщьюя"
        self.keyplus = 5
        self.keyminus = self.find_inverse(self.keyplus, len(self.alfabet))

    def find_inverse(self, key, mod):
        for i in range(1, mod):
            if (key * i) % mod == 1:
                return i
        return None

    def process_text(self, text, mode):
        result = ""
        mod = len(self.alfabet)
        for char in text:
            if char in self.alfabet:
                idx = self.alfabet.index(char)
                if mode == "encode":
                    new_idx = ((idx * self.keyplus) + self.b) % mod
                else:
                    if not self.keyminus:
                        return "❌ Цей keyplus не має оберненого числа!"
                    new_idx = ((idx - self.b) * self.keyminus) % mod
                result += self.alfabet[new_idx]
            else:
                result += char
        return result

    def recover_cipher(self, data):
        if len(data) != 4:
            return "Помилка: Потрібно ввести рівно 4 числа через пробіл!"

        try:
            l = [int(i) for i in data]
        except ValueError:
            return "Помилка: Введення має містити лише числа!"

        if l[0] < l[1]:
            a = l[1] - l[0]
            b = l[3] - l[2]
        else:
            a = l[0] - l[1]
            b = l[2] - l[3]

        k = None
        for i in range(1, 33):
            if (a * i) % 33 == b % 33:
                k = i
                break

        t = None
        if k is not None:
            for i in range(1, 33):
                if (l[0] * k + i) % 33 == l[2] % 33:
                    t = i
                    break

        if k is not None and t is not None:
            return f"Відновлений шифр:\na = b*{k} + {t} (mod 33)"
        else:
            return "Не вдалося знайти параметри шифру."