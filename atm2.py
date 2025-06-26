import json
import os
from datetime import datetime
import hashlib
import random
import sqlite3
import tkinter as tk
from tkinter import messagebox, simpledialog

# Database setup
def init_db():
    conn = sqlite3.connect('atm.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            account_number TEXT PRIMARY KEY,
            pin_hash TEXT,
            name TEXT,
            phone_no TEXT,
            balance REAL,
            withdrawn_today REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_number TEXT,
            type TEXT,
            amount REAL,
            date TEXT
        )
    ''')
    conn.commit()
    conn.close()

class Account:
    def __init__(self, account_number, pin_hash, name, phone_no, balance=0.0, withdrawn_today=0.0):
        self.account_number = account_number
        self.pin_hash = pin_hash
        self.name = name
        self.phone_no = phone_no
        self.balance = balance
        self.withdrawn_today = withdrawn_today
        self.daily_withdrawal_limit = 1000.0

    def check_pin(self, pin):
        return hashlib.sha256(pin.encode()).hexdigest() == self.pin_hash

    def deposit(self, amount):
        if amount > 0:
            self.balance += amount
            self.record_transaction("Deposit", amount)
            return True
        return False

    def withdraw(self, amount):
        if amount > 0 and amount <= self.balance and self.withdrawn_today + amount <= self.daily_withdrawal_limit:
            self.balance -= amount
            self.withdrawn_today += amount
            self.record_transaction("Withdrawal", amount)
            return True
        return False

    def transfer(self, target_account, amount):
        if amount > 0 and amount <= self.balance:
            self.balance -= amount
            target_account.balance += amount
            self.record_transaction("Transfer Out", amount)
            target_account.record_transaction("Transfer In", amount)
            return True
        return False

    def record_transaction(self, transaction_type, amount):
        conn = sqlite3.connect('atm.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO transactions (account_number, type, amount, date)
            VALUES (?, ?, ?, ?)
        ''', (self.account_number, transaction_type, amount, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()

    def get_transaction_history(self):
        conn = sqlite3.connect('atm.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT type, amount, date FROM transactions WHERE account_number = ? ORDER BY date DESC LIMIT 10
        ''', (self.account_number,))
        history = cursor.fetchall()
        conn.close()
        return history

class ATM:
    def __init__(self):
        self.current_account = None
        self.logged_in = False
        self.root = tk.Tk()
        self.root.title("ATM Interface")
        self.root.configure(bg="#F5F5F5")  # Light gray background
        self.create_welcome_screen()

    def create_welcome_screen(self):
        self.clear_screen()
        tk.Label(self.root, text="Welcome to ATM", font=("Arial", 20, "bold"), bg="#4CAF50", fg="white").pack(pady=20)
        tk.Button(self.root, text="Login", command=self.create_login_screen, bg="#2196F3", fg="white", font=("Arial", 12)).pack(pady=10)
        tk.Button(self.root, text="Exit", command=self.root.quit, bg="#F44336", fg="white", font=("Arial", 12)).pack(pady=10)

    def create_login_screen(self):
        self.clear_screen()
        login_frame = tk.Frame(self.root, bg="#F5F5F5")
        login_frame.pack(pady=10)
        tk.Label(login_frame, text="ATM Login", font=("Arial", 16, "bold"), bg="#4CAF50", fg="white").pack(pady=10)
        tk.Label(login_frame, text="Account Number:").pack()
        self.acc_entry = tk.Entry(login_frame)
        self.acc_entry.pack()
        tk.Label(login_frame, text="PIN:").pack()
        self.pin_entry = tk.Entry(login_frame, show="*")
        self.pin_entry.pack()
        tk.Button(login_frame, text="Login", command=self.login, bg="#2196F3", fg="white", font=("Arial", 10, "bold")).pack(pady=10)

    def login(self):
        acc_num = self.acc_entry.get()
        pin = self.pin_entry.get()
        conn = sqlite3.connect('atm.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT pin_hash, balance, withdrawn_today, name, phone_no FROM accounts WHERE account_number = ?
        ''', (acc_num,))
        account_data = cursor.fetchone()
        conn.close()
        
        if account_data and hashlib.sha256(pin.encode()).hexdigest() == account_data[0]:
            otp = random.randint(100000, 999999)
            print(f"Simulated OTP sent: {otp}")  # For simulation
            entered_otp = simpledialog.askstring("OTP Verification", "Enter the OTP sent to your email:", parent=self.root)
            if entered_otp and entered_otp == str(otp):
                self.current_account = Account(acc_num, account_data[0], account_data[3], account_data[4], account_data[1], account_data[2])
                self.logged_in = True
                self.create_main_screen()
            else:
                messagebox.showerror("Error", "Invalid OTP", parent=self.root)
        else:
            messagebox.showerror("Error", "Invalid account number or PIN", parent=self.root)

    def create_main_screen(self):
        self.clear_screen()
        main_frame = tk.Frame(self.root, bg="#F5F5F5")
        main_frame.pack(pady=10)
        tk.Label(main_frame, text=f"Welcome, {self.current_account.name} (Account {self.current_account.account_number})", font=("Arial", 16, "bold")).pack(pady=10)
        tk.Button(main_frame, text="Check Balance", command=self.check_balance, bg="#2196F3", fg="white").pack(pady=5)
        tk.Button(main_frame, text="Deposit", command=self.deposit, bg="#4CAF50", fg="white").pack(pady=5)
        tk.Button(main_frame, text="Withdraw", command=self.withdraw, bg="#FF9800", fg="white").pack(pady=5)
        tk.Button(main_frame, text="Transfer", command=self.transfer, bg="#9C27B0", fg="white").pack(pady=5)
        tk.Button(main_frame, text="Change PIN", command=self.change_pin, bg="#9E9E9E", fg="white").pack(pady=5)
        tk.Button(main_frame, text="Transaction History", command=self.transaction_history, bg="#607D8B", fg="white").pack(pady=5)
        tk.Button(main_frame, text="Logout", command=self.logout, bg="#F44336", fg="white").pack(pady=5)
        tk.Button(main_frame, text="Exit", command=self.root.quit, bg="#757575", fg="white").pack(pady=5)

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def logout(self):
        self.logged_in = False
        self.current_account = None
        self.create_welcome_screen()

    def check_balance(self):
        messagebox.showinfo("Balance", f"Current Balance: ₹{self.current_account.balance:.2f}")

    def deposit(self):
        self.clear_screen()
        deposit_frame = tk.Frame(self.root, bg="#F5F5F5")
        deposit_frame.pack(pady=10)
        tk.Label(deposit_frame, text="Deposit Amount (in ₹)", font=("Arial", 14, "bold")).pack(pady=10)
        amount_entry = tk.Entry(deposit_frame)
        amount_entry.pack()
        tk.Button(deposit_frame, text="Confirm", command=lambda: self.process_deposit(amount_entry.get()), bg="#4CAF50", fg="white").pack(pady=5)
        tk.Button(deposit_frame, text="Back", command=self.create_main_screen, bg="#757575", fg="white").pack(pady=5)

    def process_deposit(self, amount):
        try:
            amount = float(amount)
            if self.current_account.deposit(amount):
                self.update_account()
                messagebox.showinfo("Deposit", f"Deposited ₹{amount:.2f}. New balance: ₹{self.current_account.balance:.2f}")
            else:
                messagebox.showerror("Error", "Invalid amount")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")
        self.create_main_screen()

    def withdraw(self):
        self.clear_screen()
        withdraw_frame = tk.Frame(self.root, bg="#F5F5F5")
        withdraw_frame.pack(pady=10)
        tk.Label(withdraw_frame, text="Withdraw Amount (in ₹)", font=("Arial", 14, "bold")).pack(pady=10)
        amount_entry = tk.Entry(withdraw_frame)
        amount_entry.pack()
        tk.Button(withdraw_frame, text="Confirm", command=lambda: self.process_withdraw(amount_entry.get()), bg="#FF9800", fg="white").pack(pady=5)
        tk.Button(withdraw_frame, text="Back", command=self.create_main_screen, bg="#757575", fg="white").pack(pady=5)

    def process_withdraw(self, amount):
        try:
            amount = float(amount)
            if self.current_account.withdraw(amount):
                self.update_account()
                messagebox.showinfo("Withdraw", "Withdrawal successful")
            else:
                messagebox.showerror("Error", "Invalid amount or insufficient funds")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")
        self.create_main_screen()

    def transfer(self):
        self.clear_screen()
        transfer_frame = tk.Frame(self.root, bg="#F5F5F5")
        transfer_frame.pack(pady=10)
        tk.Label(transfer_frame, text="Transfer Amount (in ₹)", font=("Arial", 14, "bold")).pack(pady=10)
        amount_entry = tk.Entry(transfer_frame)
        amount_entry.pack()
        tk.Label(transfer_frame, text="Target Account Number").pack(pady=5)
        target_entry = tk.Entry(transfer_frame)
        target_entry.pack()
        tk.Button(transfer_frame, text="Confirm", command=lambda: self.process_transfer(amount_entry.get(), target_entry.get()), bg="#9C27B0", fg="white").pack(pady=5)
        tk.Button(transfer_frame, text="Back", command=self.create_main_screen, bg="#757575", fg="white").pack(pady=5)

    def process_transfer(self, amount, target_acc):
        try:
            amount = float(amount)
            conn = sqlite3.connect('atm.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT balance FROM accounts WHERE account_number = ?
            ''', (target_acc,))
            target_data = cursor.fetchone()
            if target_data:
                target_account = Account(target_acc, "", target_data[0])
                if self.current_account.transfer(target_account, amount):
                    self.update_account()
                    conn.execute('''
                        UPDATE accounts SET balance = ? WHERE account_number = ?
                    ''', (target_account.balance, target_acc))
                    conn.commit()
                    messagebox.showinfo("Transfer", "Transfer successful")
                else:
                    messagebox.showerror("Error", "Invalid amount or insufficient funds")
            else:
                messagebox.showerror("Error", "Target account not found")
            conn.close()
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")
        self.create_main_screen()

    def transaction_history(self):
        history = self.current_account.get_transaction_history()
        history_str = "\n".join([f"{trans[2]} - {trans[0]}: ₹{trans[1]:.2f}" for trans in history])
        messagebox.showinfo("Transaction History", history_str if history else "No transactions yet")

    def update_account(self):
        conn = sqlite3.connect('atm.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE accounts SET balance = ?, withdrawn_today = ? WHERE account_number = ?
        ''', (self.current_account.balance, self.current_account.withdrawn_today, self.current_account.account_number))
        conn.commit()
        conn.close()

    def change_pin(self):
        self.clear_screen()
        change_pin_frame = tk.Frame(self.root, bg="#F5F5F5")
        change_pin_frame.pack(pady=10)
        tk.Label(change_pin_frame, text="Change PIN", font=("Arial", 16, "bold"), bg="#9E9E9E", fg="white").pack(pady=10)
        tk.Label(change_pin_frame, text="Current PIN:").pack()
        current_pin_entry = tk.Entry(change_pin_frame, show="*")
        current_pin_entry.pack()
        tk.Label(change_pin_frame, text="New PIN:").pack()
        new_pin_entry = tk.Entry(change_pin_frame, show="*")
        new_pin_entry.pack()
        tk.Button(change_pin_frame, text="Confirm", command=lambda: self.process_change_pin(current_pin_entry.get(), new_pin_entry.get()), bg="#9E9E9E", fg="white").pack(pady=5)
        tk.Button(change_pin_frame, text="Back", command=self.create_main_screen, bg="#757575", fg="white").pack(pady=5)

    def process_change_pin(self, current_pin, new_pin):
        if self.current_account.check_pin(current_pin):
            otp = random.randint(100000, 999999)
            print(f"Simulated OTP sent: {otp}")  # For simulation
            entered_otp = simpledialog.askstring("OTP Verification", "Enter the OTP sent to your email:", parent=self.root)
            if entered_otp and entered_otp == str(otp):
                if len(new_pin) >= 4:  # Minimum 4 digits for security
                    new_pin_hash = hashlib.sha256(new_pin.encode()).hexdigest()
                    conn = sqlite3.connect('atm.db')
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE accounts SET pin_hash = ? WHERE account_number = ?
                    ''', (new_pin_hash, self.current_account.account_number))
                    conn.commit()
                    conn.close()
                    self.current_account.pin_hash = new_pin_hash
                    messagebox.showinfo("Success", "PIN changed successfully")
                else:
                    messagebox.showerror("Error", "New PIN must be at least 4 digits")
            else:
                messagebox.showerror("Error", "Invalid OTP")
        else:
            messagebox.showerror("Error", "Incorrect current PIN")
        self.create_main_screen()

if __name__ == "__main__":
    init_db()
    # Create sample account if not exists
    conn = sqlite3.connect('atm.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO accounts (account_number, pin_hash, name, phone_no, balance, withdrawn_today)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ("123456", hashlib.sha256("7890".encode()).hexdigest(), "John Doe", "1234567890", 1000.0, 0.0))
    conn.commit()
    conn.close()
    atm = ATM()
    atm.root.mainloop()