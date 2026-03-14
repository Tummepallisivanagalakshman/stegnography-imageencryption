import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image
from cryptography.fernet import Fernet
import pyperclip
import os

class SteganographyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Secure Image Messenger")
        self.root.geometry("600x500")

        self.tab_control = ttk.Notebook(root)

        self.encode_tab = ttk.Frame(self.tab_control)
        self.decode_tab = ttk.Frame(self.tab_control)

        self.tab_control.add(self.encode_tab, text="Encode")
        self.tab_control.add(self.decode_tab, text="Decode")
        self.tab_control.pack(expand=1, fill="both")

        self.encode_image_path: str = ""
        self.decode_image_path: str = ""

        # Declare UI elements
        self.btn_select_encode_img: tk.Button
        self.lbl_encode_img_path: tk.Label
        self.txt_message: tk.Text
        self.btn_encode: tk.Button
        
        self.btn_select_decode_img: tk.Button
        self.lbl_decode_img_path: tk.Label
        self.entry_key: tk.Entry
        self.btn_decode: tk.Button
        self.txt_decoded: tk.Text

        self.setup_encode_tab()
        self.setup_decode_tab()

    # --- ENCODE TAB ---
    def setup_encode_tab(self):
        tk.Label(self.encode_tab, text="Select Image to Hide Message:", font=("Arial", 12)).pack(pady=10)

        self.btn_select_encode_img = tk.Button(self.encode_tab, text="Select Image", command=self.select_encode_image)
        self.btn_select_encode_img.pack()

        self.lbl_encode_img_path = tk.Label(self.encode_tab, text="No image selected", fg="gray")
        self.lbl_encode_img_path.pack()

        tk.Label(self.encode_tab, text="Enter Secret Message:", font=("Arial", 12)).pack(pady=10)
        self.txt_message = tk.Text(self.encode_tab, height=5, width=50)
        self.txt_message.pack()

        self.btn_encode = tk.Button(self.encode_tab, text="Encode & Save Image", command=self.encode_message, bg="lightgreen", font=("Arial", 12, "bold"))
        self.btn_encode.pack(pady=20)

    def select_encode_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")])
        if file_path:
            self.encode_image_path = file_path
            self.lbl_encode_img_path.config(text=os.path.basename(file_path))

    def encode_message(self):
        if not self.encode_image_path:
            messagebox.showerror("Error", "Please select an image first.")
            return

        message = self.txt_message.get("1.0", tk.END).strip()
        if not message:
            messagebox.showerror("Error", "Message cannot be empty.")
            return

        # Encrypt the message
        key = Fernet.generate_key()
        f = Fernet(key)
        encrypted_message = f.encrypt(message.encode())

        # Append a delimiter so we know when to stop decoding
        delimiter = b"###END###"
        data_to_hide = encrypted_message + delimiter

        # Convert to binary
        binary_data = ''.join(format(byte, '08b') for byte in data_to_hide)

        # Hide via LSB
        try:
            image = Image.open(self.encode_image_path)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            pixels = image.load()

            width, height = image.size
            data_index = 0
            data_len = len(binary_data)

            for y in range(height):
                for x in range(width):
                    if data_index < data_len:
                        r, g, b = pixels[x, y]

                        # Modify the LSB of R, G, B
                        if data_index < data_len:
                            r = (r & ~1) | int(binary_data[data_index])
                            data_index += 1
                        if data_index < data_len:
                            g = (g & ~1) | int(binary_data[data_index])
                            data_index += 1
                        if data_index < data_len:
                            b = (b & ~1) | int(binary_data[data_index])
                            data_index += 1

                        pixels[x, y] = (r, g, b)
                    else:
                        break
                if data_index >= data_len:
                    break

            if data_index < data_len:
                messagebox.showerror("Error", "Image is too small to hold this much data.")
                return

            save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Files", "*.png")])
            if save_path:
                image.save(save_path)
                key_str = key.decode()
                pyperclip.copy(key_str)
                messagebox.showinfo("Success", f"Image successfully encoded and saved!\n\nEncryption Key (Copied to Clipboard):\n{key_str}")
                self.txt_message.delete("1.0", tk.END)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to encode message: {str(e)}")

    # --- DECODE TAB ---
    def setup_decode_tab(self):
        tk.Label(self.decode_tab, text="Select Encoded Image:", font=("Arial", 12)).pack(pady=10)

        self.btn_select_decode_img = tk.Button(self.decode_tab, text="Select Image", command=self.select_decode_image)
        self.btn_select_decode_img.pack()

        self.lbl_decode_img_path = tk.Label(self.decode_tab, text="No image selected", fg="gray")
        self.lbl_decode_img_path.pack()

        tk.Label(self.decode_tab, text="Enter Encryption Key:", font=("Arial", 12)).pack(pady=10)
        self.entry_key = tk.Entry(self.decode_tab, width=50)
        self.entry_key.pack()

        self.btn_decode = tk.Button(self.decode_tab, text="Decode & Reveal", command=self.decode_message, bg="lightblue", font=("Arial", 12, "bold"))
        self.btn_decode.pack(pady=20)

        tk.Label(self.decode_tab, text="Decoded Message:", font=("Arial", 12)).pack(pady=10)
        self.txt_decoded = tk.Text(self.decode_tab, height=5, width=50, state=tk.DISABLED)
        self.txt_decoded.pack()

    def select_decode_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.bmp")])
        if file_path:
            self.decode_image_path = file_path
            self.lbl_decode_img_path.config(text=os.path.basename(file_path))

    def decode_message(self):
        if not self.decode_image_path:
            messagebox.showerror("Error", "Please select an image first.")
            return

        key = self.entry_key.get().strip()
        if not key:
            messagebox.showerror("Error", "Encryption key is required.")
            return

        try:
            image = Image.open(self.decode_image_path)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            pixels = image.load()
            width, height = image.size

            decoded_data = bytearray()
            delimiter = b"###END###"
            delimiter_found = False
            
            binary_buffer = ""

            for y in range(height):
                if delimiter_found:
                    break
                for x in range(width):
                    if delimiter_found:
                        break
                    
                    r, g, b = pixels[x, y]
                    binary_buffer += str(r & 1) + str(g & 1) + str(b & 1)
                    
                    while len(binary_buffer) >= 8:
                        byte_str = binary_buffer[:8]
                        binary_buffer = binary_buffer[8:]
                        decoded_data.append(int(byte_str, 2))
                        
                        if len(decoded_data) >= len(delimiter):
                            if bytes(decoded_data[-len(delimiter):]) == delimiter:
                                delimiter_found = True
                                decoded_data = decoded_data[:-len(delimiter)]
                                break
            
            if not delimiter_found:
                messagebox.showerror("Error", "No hidden message found in this image, or it is corrupted.")
                return

            f = Fernet(key.encode())
            try:
                decrypted_message = f.decrypt(bytes(decoded_data)).decode()
                self.txt_decoded.config(state=tk.NORMAL)
                self.txt_decoded.delete("1.0", tk.END)
                self.txt_decoded.insert("1.0", decrypted_message)
                self.txt_decoded.config(state=tk.DISABLED)
            except Exception as e:
                messagebox.showerror("Error", "Invalid key or corrupted data.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to decode message: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SteganographyApp(root)
    root.mainloop()
