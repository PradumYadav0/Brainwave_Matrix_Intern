import sqlite3
import tkinter as tk
from tkinter import messagebox
import hashlib

# Database setup with table recreation
def init_db():
    conn = sqlite3.connect('atm.db')
    cursor = conn.cursor()
    try:
        # Drop the existing table if it exists to recreate with new schema
        cursor.execute("DROP TABLE IF EXISTS accounts")
        cursor.execute('''
            CREATE TABLE accounts (
                account_number TEXT PRIMARY KEY,
                pin_hash TEXT,
                name TEXT,
                phone_no TEXT,
                balance REAL,
                withdrawn_today REAL
            )
        ''')
        # Optional: Add a sample account
        cursor.execute('''
            INSERT INTO accounts (account_number, pin_hash, name, phone_no, balance, withdrawn_today)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ("123456", hashlib.sha256("7890".encode()).hexdigest(), "John Doe", "1234567890", 0.0, 0.0))
        conn.commit()
        print("Database table 'accounts' recreated successfully with new columns.")
    except sqlite3.Error as e:
        print(f"Error creating/updating table: {e}")
    finally:
        conn.close()

class UserManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Add User Details")
        self.root.configure(bg="#F5F5F5")
        self.create_add_user_screen()

    def create_add_user_screen(self):
        self.clear_screen()
        add_frame = tk.Frame(self.root, bg="#F5F5F5")
        add_frame.pack(pady=10)
        tk.Label(add_frame, text="Add New User", font=("Arial", 16, "bold"), bg="#4CAF50", fg="white").pack(pady=10)
        tk.Label(add_frame, text="Account Number:").pack()
        self.acc_entry = tk.Entry(add_frame)
        self.acc_entry.pack()
        tk.Label(add_frame, text="Name:").pack()
        self.name_entry = tk.Entry(add_frame)
        self.name_entry.pack()
        tk.Label(add_frame, text="Phone No:").pack()
        self.phone_entry = tk.Entry(add_frame)
        self.phone_entry.pack()
        tk.Label(add_frame, text="PIN:").pack()
        self.pin_entry = tk.Entry(add_frame, show="*")
        self.pin_entry.pack()
        tk.Button(add_frame, text="Submit", command=self.process_add_user, bg="#4CAF50", fg="white").pack(pady=10)
        tk.Button(add_frame, text="Exit", command=self.root.quit, bg="#F44336", fg="white").pack(pady=10)

    def process_add_user(self):
        acc_num = self.acc_entry.get()
        name = self.name_entry.get()
        phone_no = self.phone_entry.get()
        pin = self.pin_entry.get()

        if acc_num and name and phone_no and pin:
            conn = sqlite3.connect('atm.db')
            cursor = conn.cursor()
            try:
                # Check if account already exists
                cursor.execute('SELECT account_number, name, phone_no, balance FROM accounts WHERE account_number = ?', (acc_num,))
                existing_account = cursor.fetchone()
                if existing_account:
                    existing_acc_num, existing_name, existing_phone, existing_balance = existing_account
                    if name != existing_name or phone_no != existing_phone or pin != hashlib.sha256(self.pin_entry.get().encode()).hexdigest():
                        messagebox.showerror("Error", f"Account {existing_acc_num} already exists with different details. Update not allowed.")
                    else:
                        message = f"Account {existing_acc_num} already exists.\nDetails: Name: {existing_name}, Phone: {existing_phone}, Balance: ₹{existing_balance:.2f}"
                        messagebox.showinfo("Info", message)
                else:
                    cursor.execute('''
                        INSERT INTO accounts (account_number, pin_hash, name, phone_no, balance, withdrawn_today)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (acc_num, hashlib.sha256(pin.encode()).hexdigest(), name, phone_no, 0.0, 0.0))
                    conn.commit()
                    messagebox.showinfo("Success", "User account created successfully!")
                    self.clear_entries()
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Database error: {e}")
            finally:
                conn.close()
        else:
            messagebox.showerror("Error", "All fields are required")

    def clear_entries(self):
        self.acc_entry.delete(0, tk.END)
        self.name_entry.delete(0, tk.END)
        self.phone_entry.delete(0, tk.END)
        self.pin_entry.delete(0, tk.END)

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = UserManager(root)
    root.mainloop()