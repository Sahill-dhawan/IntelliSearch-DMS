import os
import csv
import threading
from PyPDF2 import PdfReader
from docx import Document
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
import re
import traceback

# ---------- GLOBAL DATA ----------
results_data = []            
scanning = False             
stop_requested = False      

# ---------- FUNCTIONS ----------

def read_file_content(file_path):
    """Read text content from supported file types."""
    text = ""
    try:
        if file_path.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        elif file_path.endswith(".pdf"):
            reader = PdfReader(file_path)
            for page in reader.pages:
                extracted = page.extract_text() or ""
                text += extracted + "\n"
        elif file_path.endswith(".docx"):
            doc = Document(file_path)
            text = "\n".join(para.text for para in doc.paragraphs)
    except Exception:
        return text
    return text

def preview_file(file_path, matched_keywords):
    """Show full paragraphs containing keywords with occurrences highlighted."""
    try:
        text = read_file_content(file_path)
        if not text.strip():
            text = "[No readable text found in this file]"

        preview_win = tk.Toplevel(root)
        preview_win.title(f"Preview - {os.path.basename(file_path)}")
        preview_win.geometry("800x600")
        preview_win.config(bg="#1e1e1e")

        label = tk.Label(
            preview_win,
            text=f"🔍 Preview: {os.path.basename(file_path)}",
            bg="#1e1e1e", fg="#00FFAA", font=("Arial", 12, "bold")
        )
        label.pack(pady=10)

        text_box = scrolledtext.ScrolledText(
            preview_win, wrap="word", width=100, height=30,
            bg="#2e2e2e", fg="white", insertbackground="white"
        )
        text_box.pack(padx=10, pady=10, fill="both", expand=True)

        # Split text into paragraphs
        paragraphs = text.split("\n\n")
        display_text = ""
        for para in paragraphs:
            for kw in matched_keywords:
                if re.search(r"\b" + re.escape(kw) + r"\b", para, flags=re.IGNORECASE):
                    display_text += para.strip() + "\n\n"
                    break
        if not display_text:
            display_text = text[:1000]  # fallback

        text_box.insert(tk.END, display_text)

        # Highlight keywords and show occurrence count
        colors = ["#FF6347","#FFD700","#00FF00","#00BFFF","#FF69B4","#FFA500"]
        for idx, kw in enumerate(matched_keywords):
            start_index = "1.0"
            color = colors[idx % len(colors)]
            count = 0
            while True:
                idx_pos = text_box.search(kw, start_index, tk.END, nocase=1)
                if not idx_pos:
                    break
                end_idx = f"{idx_pos}+{len(kw)}c"
                tagname = f"{kw}_{idx_pos}"
                text_box.tag_add(tagname, idx_pos, end_idx)
                text_box.tag_config(tagname, background="#2e2e2e", foreground=color)
                start_index = end_idx
                count += 1
            # Show count of this keyword
            text_box.insert(tk.END, f"[{kw} occurs {count} times]\n", "bold")

        text_box.tag_config("bold", font=("Arial", 10, "bold"), foreground="#00FFAA")
        text_box.config(state=tk.DISABLED)

    except Exception as e:
        messagebox.showerror("❌ Preview Error", f"Cannot preview this file:\n{e}\n\n{traceback.format_exc()}")


        # Highlight keywords
        for kw in matched_keywords:
            start_index = "1.0"
            while True:
                idx = text_box.search(kw, start_index, tk.END, nocase=1)
                if not idx:
                    break
                end_idx = f"{idx}+{len(kw)}c"
                tagname = f"pv_kw_{kw}_{start_index}"
                text_box.tag_add(tagname, idx, end_idx)
                text_box.tag_config(tagname, background="#004D40", foreground="#FFFF00")
                start_index = end_idx

        text_box.config(state=tk.DISABLED)

    except Exception as e:
        messagebox.showerror("❌ Preview Error", f"Cannot preview this file:\n{e}\n\n{traceback.format_exc()}")

def run_search_thread():
    global scanning, stop_requested
    if scanning:
        messagebox.showinfo("⏳ Please Wait", "Scanning already in progress.")
        return
    stop_requested = False
    scanning = True
    threading.Thread(target=search_files, daemon=True).start()

def stop_search():
    global stop_requested
    if not scanning:
        messagebox.showinfo("ℹ️ Not running", "No scan is currently running.")
        return
    stop_requested = True
    messagebox.showinfo("⏸ Stop Requested", "Scan will stop shortly.")

def search_files():
    global results_data, scanning, stop_requested
    try:
        results_data = []

        folder_path = folder_entry.get().strip()
        keywords = [k.strip() for k in keywords_entry.get().split(",") if k.strip()]

        if not folder_path or not keywords:
            messagebox.showwarning("⚠️ Input Error", "Please enter folder path (or select a file) and keywords!")
            return

        result_box.config(state=tk.NORMAL)
        result_box.delete(1.0, tk.END)
        progress_bar["value"] = 0
        root.update_idletasks()

        all_files = []
        if os.path.isfile(folder_path):
            if folder_path.lower().endswith((".txt", ".pdf", ".docx")):
                all_files.append(folder_path)
        else:
            for root_dir, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith((".txt", ".pdf", ".docx")):
                        all_files.append(os.path.join(root_dir, file))

        total_files = len(all_files)
        if total_files == 0:
            messagebox.showinfo("No Files", "No supported files found!")
            return

        for i, file_path in enumerate(all_files, start=1):
            if stop_requested:
                result_box.insert(tk.END, "\n⛔ Scan stopped by user.\n", "error")
                break

            try:
                text = read_file_content(file_path)
                matched_keywords = [kw for kw in keywords if re.search(r"\b" + re.escape(kw) + r"\b", text, flags=re.IGNORECASE)]

                results_data.append({
                    "file_name": os.path.basename(file_path),
                    "file_path": file_path,
                    "matched_keywords": ", ".join(matched_keywords) if matched_keywords else ""
                })

                result_box.insert(tk.END, f"{os.path.basename(file_path)}\n", "file")

                if matched_keywords:
                    result_box.insert(tk.END, "Matched keywords: ", "bold")
                    for k in matched_keywords:
                        result_box.insert(tk.END, f"{k} ", "keyword")
                    tag_name = f"link_{i}"
                    result_box.insert(tk.END, "\n[Click to Preview]\n\n", tag_name)
                    result_box.tag_config(tag_name, foreground="#4FC3F7", underline=1)
                    def make_callback(path=file_path, mk=matched_keywords):
                        return lambda event: preview_file(path, mk)
                    result_box.tag_bind(tag_name, "<Button-1>", make_callback())
                else:
                    result_box.insert(tk.END, "No keywords matched\n\n", "notfound")

            except Exception as e:
                result_box.insert(tk.END, f"⚠️ Error reading {os.path.basename(file_path)}: {e}\n", "error")
                result_box.insert(tk.END, traceback.format_exc() + "\n\n", "error")

            progress_bar["value"] = (i / total_files) * 100
            root.update_idletasks()

    finally:
        scanning = False
        stop_requested = False
        result_box.config(state=tk.NORMAL)

def browse_folder():
    folder = filedialog.askdirectory()
    if folder:
        folder_entry.delete(0, tk.END)
        folder_entry.insert(0, folder)

def browse_file():
    file_path = filedialog.askopenfilename(filetypes=[("Supported Files", "*.pdf *.docx *.txt")])
    if file_path:
        folder_entry.delete(0, tk.END)
        folder_entry.insert(0, file_path)

def save_csv():
    if not results_data:
        messagebox.showwarning("⚠️ No Data", "No results to save!")
        return
    save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if save_path:
        try:
            with open(save_path, "w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=["file_name","file_path","matched_keywords"])
                writer.writeheader()
                writer.writerows(results_data)
            messagebox.showinfo("✅ Success", f"Results saved to:\n{save_path}")
        except Exception as e:
            messagebox.showerror("❌ Error", f"Failed to save CSV:\n{e}")

# ---------- MAIN UI ----------
root = tk.Tk()
root.title("Resume Scanner")
root.geometry("900x800")
root.config(bg="#1e1e1e")

tk.Label(root, text="IntelliSearch DMS", font=("Helvetica", 20, "bold"), bg="#1e1e1e", fg="#00FFAA").pack(pady=12)


tk.Label(root, text="📁 Folder or File Path:", bg="#1e1e1e", fg="white", font=("Arial", 11)).pack()
folder_entry = tk.Entry(root, width=90, font=("Arial", 10))
folder_entry.pack(pady=5)

btn_frame = tk.Frame(root, bg="#1e1e1e")
btn_frame.pack()
tk.Button(btn_frame, text="Browse Folder", command=browse_folder, bg="#00bcd4", fg="white", font=("Arial", 11, "bold"), relief="flat").pack(side=tk.LEFT, padx=6)
tk.Button(btn_frame, text="Select Single File", command=browse_file, bg="#2196F3", fg="white", font=("Arial", 11, "bold"), relief="flat").pack(side=tk.LEFT, padx=6)

tk.Label(root, text="🔍 Keywords (comma separated):", bg="#1e1e1e", fg="white", font=("Arial", 11)).pack(pady=6)
keywords_entry = tk.Entry(root, width=90, font=("Arial", 10))
keywords_entry.pack(pady=5)

actions_frame = tk.Frame(root, bg="#1e1e1e")
actions_frame.pack(pady=8)
tk.Button(actions_frame, text="🚀 Start Search", command=run_search_thread, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), relief="flat", padx=12).pack(side=tk.LEFT, padx=6)
tk.Button(actions_frame, text="⏹ Stop Search", command=stop_search, bg="#f44336", fg="white", font=("Arial", 12, "bold"), relief="flat", padx=12).pack(side=tk.LEFT, padx=6)
tk.Button(actions_frame, text="💾 Save Results to CSV", command=save_csv, bg="#FF9800", fg="white", font=("Arial", 12, "bold"), relief="flat", padx=12).pack(side=tk.LEFT, padx=6)

progress_bar = ttk.Progressbar(root, orient="horizontal", length=700, mode="determinate")
progress_bar.pack(pady=12)

result_box = scrolledtext.ScrolledText(root, width=115, height=20, bg="#2e2e2e", fg="white", insertbackground="white")
result_box.tag_config("notfound", foreground="#FF6666")
result_box.tag_config("error", foreground="#FFA500")
result_box.tag_config("keyword", foreground="#00FF00", font=("Arial", 10, "bold"))
result_box.tag_config("bold", font=("Arial", 10, "bold"))
result_box.tag_config("file", font=("Arial", 11, "bold"))
result_box.pack(pady=10, fill="both", expand=True)

summary_label = tk.Label(root, text="", bg="#1e1e1e", fg="#00FFAA", font=("Arial", 12, "bold"))
summary_label.pack(pady=6)

root.mainloop()
