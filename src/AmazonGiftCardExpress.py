import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import tkinter as tk
from tkinter import filedialog, messagebox
import webbrowser

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def read_gift_card_codes(file_path):
    logging.info(f"Reading gift card codes from {file_path}")
    df = pd.read_excel(file_path, sheet_name=0)

    if 'Gift Card Codes' not in df.columns:
        logging.error('The Excel file does not contain a "Gift Card Codes" column.')
        raise ValueError('The Excel file does not contain a "Gift Card Codes" column.')

    gift_card_codes = df['Gift Card Codes'].dropna().tolist()
    logging.info(f"Found {len(gift_card_codes)} gift card codes")

    return gift_card_codes

class AmazonAdder:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.driver = webdriver.Chrome()  
        self.wait = WebDriverWait(self.driver, 20)

    def login(self):
        logging.info("Navigating to Amazon sign-in page")
        self.driver.get("https://amazon.in/addgiftcard")
        email_elem = self.wait.until(EC.element_to_be_clickable((By.ID, "ap_email")))
        email_elem.send_keys(self.email)
        email_elem.send_keys(Keys.RETURN)
        logging.info("Entered email and submitted")
        
        password_elem = self.wait.until(EC.element_to_be_clickable((By.ID, "ap_password")))
        password_elem.send_keys(self.password)
        password_elem.send_keys(Keys.RETURN)
        logging.info("Entered password and submitted")

    def handle_captcha(self):
        try:
            captcha_elem = self.wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='gc-captcha-image-container']")))
            if captcha_elem:
                logging.info("CAPTCHA detected. Please solve it manually.")
                top = tk.Toplevel()
                top.attributes("-topmost", True)
                top.withdraw()
                messagebox.showinfo("Amazon Gift Card Express", "CAPTCHA detected!\nPlease solve the CAPTCHA manually and then click OK to continue.", parent=top)
                top.destroy()
                logging.info("User clicked OK after solving CAPTCHA.")
        except Exception as e:
            logging.info("No CAPTCHA detected.")

    def add_gift_card(self, code):
        logging.info(f"Adding gift card code: {code}")
        self.driver.get("https://amazon.in/addgiftcard")
        try:
            self.handle_captcha()  # Handle CAPTCHA before entering the gift card code
            code_elem = self.wait.until(EC.presence_of_element_located((By.ID, "claim-Code-input-box")))
            code_elem.click()
            code_elem.send_keys(code)
            logging.info("Entered the gift card code")
            
            self.driver.execute_script("document.getElementsByTagName('tux-button')[0].click();")
            logging.info(f"Submitted gift card code: {code}")
            
            self.wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Gift card applied')]")))
            logging.info(f"Gift card code {code} applied successfully")
            return "Success"
        except Exception as e:
            logging.error(f"Failed to add gift card code: {code}. Error: {e}")
            return "Failed"

    def close(self):
        logging.info("Closing the browser")
        self.driver.quit()

def start_adding_gift_cards(email, password, file_path):
    if not email or not password or not file_path:
        messagebox.showerror("Amazon Gift Card Express", "All fields are mandatory.")
        return
    
    try:
        gift_card_codes = read_gift_card_codes(file_path)
        
        amazon_adder = AmazonAdder(email, password)
        amazon_adder.login()
        
        for code in gift_card_codes:
            logging.info(f"Processing gift card code: {code}")
            print(f"Processing gift card code: {code}")
            status = amazon_adder.add_gift_card(code)
            logging.info(f"Status: {status}")
        
        amazon_adder.close()
        messagebox.showinfo("Success", "All gift cards have been processed.")
        root.destroy()
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        messagebox.showerror("Error", f"An error occurred: {e}")
        root.destroy()

def browse_file():
    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
    if file_path:
        file_path_entry.delete(0, tk.END)
        file_path_entry.insert(0, file_path)

def open_support_link(event):
    webbrowser.open_new("https://buymeacoffee.com/kedargmnv")

# GUI
root = tk.Tk()
root.title("Amazon Gift Card Express")
root.config(bg="white")  
root.geometry("600x162")
root.resizable(False, False)  

tk.Label(root, text="Amazon Login Email:", bg="white").grid(row=0, column=0, padx=10, pady=5)
email_entry = tk.Entry(root, width=50, bd=2, highlightthickness=2, highlightbackground="white", highlightcolor="#ff9900")
email_entry.grid(row=0, column=1, padx=10, pady=5)

tk.Label(root, text="Amazon Password:", bg="white").grid(row=1, column=0, padx=10, pady=5)
password_entry = tk.Entry(root, show="*", width=50, bd=2, highlightthickness=2, highlightbackground="white", highlightcolor="#ff9900")
password_entry.grid(row=1, column=1, padx=10, pady=5)

tk.Label(root, text="Gift card excel File Path:", bg="white").grid(row=2, column=0, padx=10, pady=5)
file_path_entry = tk.Entry(root, width=50, bd=2, highlightthickness=2, highlightbackground="white", highlightcolor="#ff9900")
file_path_entry.grid(row=2, column=1, padx=10, pady=5)

tk.Button(root, text="Browse", command=browse_file, bg="#ff9900", fg="black", padx=20).grid(row=2, column=2, padx=20, pady=5)

tk.Button(root, text="Redeem!", command=lambda: start_adding_gift_cards(email_entry.get(), password_entry.get(), file_path_entry.get()), bg="#ff9900", fg="black", padx=20).grid(row=3, column=1, padx=20, pady=20)

support_label = tk.Label(root, text="Support me", fg="blue", cursor="hand2", bg="white")
support_label.grid(row=3, column=2, padx=10, pady=10, sticky="se")
support_label.bind("<Button-1>", open_support_link)

root.mainloop()