from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import logging
import tkinter as tk
from tkinter import messagebox
import webbrowser
from concurrent.futures import ThreadPoolExecutor, as_completed


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def parse_gift_card_codes(text):
    """Parse one gift card code per line from the input box."""
    codes = [line.strip() for line in text.splitlines() if line.strip()]
    if not codes:
        raise ValueError("At least one gift card code is required.")
    return codes


class AmazonAdder:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 20)

    def login(self):
        logging.info("Opening Amazon sign-in page")
        self.driver.get("https://www.amazon.in/ap/signin")
        try:
            email_elem = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#ap_email, input[name='email']")
                )
            )
            email_elem.send_keys(self.email)
            email_elem.send_keys(Keys.RETURN)

            password_elem = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "#ap_password, input[name='password']")
                )
            )
            password_elem.send_keys(self.password)
            password_elem.send_keys(Keys.RETURN)
            logging.info("Amazon login submitted")
        except TimeoutException:
            logging.info(
                "Amazon did not show the standard login form; "
                "waiting for manual login or an existing session"
            )

        messagebox.showinfo(
            "Amazon login",
            "Chrome window mein Amazon login, CAPTCHA ya OTP complete karo, "
            "phir yahan OK click karo. Session isi browser mein connected rahega.",
        )
        self.driver.get("https://www.amazon.in/addgiftcard")
        logging.info("Amazon browser session accepted by user")

    def handle_captcha(self):
        try:
            captcha_elem = WebDriverWait(self.driver, 1).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[@id='gc-captcha-image-container']")
                )
            )
            if captcha_elem:
                logging.info("CAPTCHA detected. Waiting for manual completion.")
                top = tk.Toplevel()
                top.attributes("-topmost", True)
                top.withdraw()
                messagebox.showinfo(
                    "Amazon Gift Card Express",
                    "CAPTCHA detected. Solve it in the Amazon browser, then click OK.",
                    parent=top,
                )
                top.destroy()
        except Exception:
            pass

    def add_gift_card(self, code):
        return self._add_gift_card_with_driver(self.driver, code)

    def _add_gift_card_with_driver(self, driver, code):
        try:
            selector = (
                "#claim-Code-input-box:not([disabled]):not([type='hidden']), "
                "#gc-redemption-input:not([disabled]):not([type='hidden']), "
                "input[name='claimCode']:not([disabled]):not([type='hidden']), "
                "input[name='claim-code']:not([disabled]):not([type='hidden'])"
            )
            try:
                code_elem = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
            except TimeoutException:
                driver.get("https://www.amazon.in/addgiftcard")
                code_elem = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
            code_elem.click()
            code_elem.send_keys(Keys.CONTROL, "a")
            code_elem.send_keys(Keys.BACKSPACE)
            code_elem.send_keys(code)
            driver.execute_script(
                "document.getElementsByTagName('tux-button')[0].click();"
            )
            status = self._read_claim_status(driver)
            print(f"{code} -> {status}", flush=True)
            return status
        except Exception as exc:
            status = f"ERROR: {exc}"
            print(f"{code} -> {status}", flush=True)
            logging.error("Failed to process gift card code: %s", exc)
            return "Failed"

    def _read_claim_status(self, driver):
        """Read Amazon's result text and map it to a concise terminal status."""
        def result_is_visible(driver):
            text = driver.find_element(By.TAG_NAME, "body").text.lower()
            status_words = (
                "gift card applied",
                "already claimed",
                "already redeemed",
                "invalid",
                "not valid",
                "cannot be redeemed",
                "couldn't be redeemed",
            )
            return text if any(word in text for word in status_words) else False

        try:
            page_text = WebDriverWait(driver, 15, poll_frequency=0.1).until(
                result_is_visible
            )
        except TimeoutException:
            return "UNKNOWN (Amazon response timeout)"

        if "gift card applied" in page_text:
            return "CLAIMED"
        if "already claimed" in page_text or "already redeemed" in page_text:
            return "ALREADY CLAIMED"
        if "invalid" in page_text or "not valid" in page_text:
            return "INVALID"
        if "cannot be redeemed" in page_text or "couldn't be redeemed" in page_text:
            return "NOT REDEEMABLE"
        return "UNKNOWN"

    def add_gift_cards_parallel(self, codes):
        """Process up to six codes concurrently in copied authenticated sessions."""
        cookies = self.driver.get_cookies()

        def process(code):
            driver = webdriver.Chrome()
            try:
                driver.get("https://www.amazon.in/")
                for cookie in cookies:
                    try:
                        driver.add_cookie(cookie)
                    except Exception:
                        logging.debug("Could not copy one Amazon cookie", exc_info=True)
                driver.get("https://www.amazon.in/addgiftcard")
                return self._add_gift_card_with_driver(driver, code)
            finally:
                driver.quit()

        results = [None] * len(codes)
        with ThreadPoolExecutor(max_workers=6) as executor:
            pending = {
                executor.submit(process, code): index
                for index, code in enumerate(codes)
            }
            for future in as_completed(pending):
                results[pending[future]] = future.result()
        return results

    def close(self):
        logging.info("Closing the browser")
        self.driver.quit()


amazon_adder = None


def connect_to_amazon():
    global amazon_adder
    email = email_entry.get().strip()
    password = password_entry.get()
    if not email or not password:
        messagebox.showerror(
            "Amazon Gift Card Express", "Email and password are required."
        )
        return

    try:
        amazon_adder = AmazonAdder(email, password)
        amazon_adder.login()
        connect_button.config(state=tk.DISABLED, text="Connected")
        email_entry.config(state=tk.DISABLED)
        password_entry.config(state=tk.DISABLED)
        messagebox.showinfo(
            "Amazon Gift Card Express",
            "Amazon account connected. You can now redeem codes without logging in again.",
        )
    except Exception as exc:
        logging.error("Could not connect to Amazon: %s", exc)
        if amazon_adder is not None:
            amazon_adder.close()
            amazon_adder = None
        messagebox.showerror("Connection error", str(exc))


def redeem_gift_cards():
    if amazon_adder is None:
        messagebox.showerror(
            "Amazon Gift Card Express", "Connect to Amazon before redeeming codes."
        )
        return

    try:
        codes = parse_gift_card_codes(codes_text.get("1.0", tk.END))
        logging.info("Processing %d gift card code(s) in batches of 6", len(codes))
        results = []
        for start in range(0, len(codes), 6):
            batch = codes[start:start + 6]
            logging.info("Processing batch %d-%d", start + 1, start + len(batch))
            results.extend(amazon_adder.add_gift_cards_parallel(batch))

        successful = results.count("CLAIMED")
        already_claimed = results.count("ALREADY CLAIMED")
        invalid = results.count("INVALID")
        messagebox.showinfo(
            "Redeem complete",
            f"Processed {len(results)} code(s):\n"
            f"Claimed: {successful}\n"
            f"Already claimed: {already_claimed}\n"
            f"Invalid: {invalid}\n"
            f"Other/failed: {len(results) - successful - already_claimed - invalid}",
        )
    except Exception as exc:
        logging.error("Redeem failed: %s", exc)
        messagebox.showerror("Redeem error", str(exc))


def open_support_link(_event):
    webbrowser.open_new("https://buymeacoffee.com/kedargmnv")


def close_application():
    if amazon_adder is not None:
        amazon_adder.close()
    root.destroy()


root = tk.Tk()
root.title("Amazon Gift Card Express")
root.config(bg="white")
root.geometry("700x430")
root.resizable(False, False)
root.protocol("WM_DELETE_WINDOW", close_application)

tk.Label(root, text="Amazon Login Email:", bg="white").grid(
    row=0, column=0, padx=10, pady=5
)
email_entry = tk.Entry(
    root, width=45, bd=2, highlightthickness=2,
    highlightbackground="white", highlightcolor="#ff9900",
)
email_entry.grid(row=0, column=1, columnspan=2, padx=10, pady=5)

tk.Label(root, text="Amazon Password:", bg="white").grid(
    row=1, column=0, padx=10, pady=5
)
password_entry = tk.Entry(
    root, show="*", width=45, bd=2, highlightthickness=2,
    highlightbackground="white", highlightcolor="#ff9900",
)
password_entry.grid(row=1, column=1, columnspan=2, padx=10, pady=5)

connect_button = tk.Button(
    root, text="Connect Amazon", command=connect_to_amazon,
    bg="#ff9900", fg="black", padx=20,
)
connect_button.grid(row=2, column=1, padx=20, pady=10)

tk.Label(root, text="Gift card codes (one per line):", bg="white").grid(
    row=3, column=0, padx=10, pady=5, sticky="n"
)
codes_text = tk.Text(
    root, width=52, height=12, bd=2, highlightthickness=2,
    highlightbackground="white", highlightcolor="#ff9900",
)
codes_text.grid(row=3, column=1, columnspan=2, padx=10, pady=5)

tk.Button(
    root, text="Redeem!", command=redeem_gift_cards,
    bg="#ff9900", fg="black", padx=20,
).grid(row=4, column=1, padx=20, pady=15)

support_label = tk.Label(root, text="Support me", fg="blue", cursor="hand2", bg="white")
support_label.grid(row=4, column=2, padx=10, pady=10, sticky="se")
support_label.bind("<Button-1>", open_support_link)

root.mainloop()
