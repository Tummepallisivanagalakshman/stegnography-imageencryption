import streamlit as st
from PIL import Image
from cryptography.fernet import Fernet
import io

st.set_page_config(page_title="Secure Image Messenger", layout="centered")

st.title("🔐 Secure Image Messenger")
st.markdown("Hide secret messages within images using LSB steganography and Fernet encryption.")

tab1, tab2 = st.tabs(["Encode Message", "Decode Message"])

# --- ENCODE TAB ---
with tab1:
    st.header("Encode a Secret Message")
    encode_upload = st.file_uploader("Upload an Image to Hide Message", type=["png", "jpg", "jpeg", "bmp"], key="encode_upload")
    secret_message = st.text_area("Enter Secret Message")
    
    if st.button("Encode & Generate Image"):
        if not encode_upload:
            st.error("Please upload an image first.")
        elif not secret_message.strip():
            st.error("Message cannot be empty.")
        else:
            try:
                # Encrypt the message
                key = Fernet.generate_key()
                f = Fernet(key)
                encrypted_message = f.encrypt(secret_message.strip().encode())

                # Append delimiter
                delimiter = b"###END###"
                data_to_hide = encrypted_message + delimiter

                # Convert to binary
                binary_data = ''.join(format(byte, '08b') for byte in data_to_hide)
                data_len = len(binary_data)

                # Process image
                image = Image.open(encode_upload)
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                pixels = image.load()
                width, height = image.size
                
                if data_len > width * height * 3:
                    st.error("Image is too small to hold this much data.")
                else:
                    data_index = 0
                    for y in range(height):
                        for x in range(width):
                            if data_index < data_len:
                                r, g, b = pixels[x, y]

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

                    st.success("Image encoded successfully!")
                    st.info(f"**Your Encryption Key:** `{key.decode()}`\n\n*(Save this key! You need it to decode the message)*")
                    
                    # Convert to bytes for download
                    buf = io.BytesIO()
                    image.save(buf, format="PNG")
                    byte_im = buf.getvalue()
                    
                    st.download_button(
                        label="Download Encoded Image",
                        data=byte_im,
                        file_name="encoded_image.png",
                        mime="image/png"
                    )
            except Exception as e:
                st.error(f"Error encoding message: {str(e)}")

# --- DECODE TAB ---
with tab2:
    st.header("Decode a Secret Message")
    decode_upload = st.file_uploader("Upload an Encoded Image", type=["png", "bmp"], key="decode_upload")
    decryption_key = st.text_input("Enter Encryption Key", type="password")
    
    if st.button("Decode & Reveal Message"):
        if not decode_upload:
            st.error("Please upload an encoded image.")
        elif not decryption_key.strip():
            st.error("Encryption key is required.")
        else:
            try:
                image = Image.open(decode_upload)
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
                    st.error("No hidden message found in this image, or it is corrupted.")
                else:
                    try:
                        f = Fernet(decryption_key.strip().encode())
                        decrypted_message = f.decrypt(bytes(decoded_data)).decode()
                        st.success("Message decoded successfully:")
                        st.text_area("Hidden Message", decrypted_message, height=150)
                    except Exception:
                        st.error("Invalid key or corrupted data. Decryption failed.")
            except Exception as e:
                st.error(f"Error decoding message: {str(e)}")
