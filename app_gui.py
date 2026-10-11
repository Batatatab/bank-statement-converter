import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from converter_engine import (
    StatementConverter,
    clean_float,
    export_to_excel_styled,
)
from optimizer import (
    dispatch_to_main_thread,
    get_asset_path,
    setup_windows_environment,
)

# Apply Windows XP high-DPI scaling and AppUserModelID before window creation
setup_windows_environment("sharva.bankstatementconverter.1.0")

# Classic Windows XP Palette
XP_BG = "#ECE9D8"
XP_BORDER = "#7F9DB9"
XP_TEXT = "#000000"
XP_FONT = ("Tahoma", 8)
XP_FONT_BOLD = ("Tahoma", 8, "bold")
XP_FONT_TITLE = ("Tahoma", 9, "bold")
XP_FONT_HINT = ("Tahoma", 7)


class App:

    def __init__(self, root):
        self.root = root
        self.root.title("Bank Statement to Excel Converter")
        self.root.geometry("690x650")
        self.root.minsize(650, 590)
        self.root.configure(bg=XP_BG)

        # Apply custom icon via asset path resolver
        self._icon_img = None
        self._set_icon()

        self.account_name = tk.StringVar()
        self.account_no = tk.StringVar()
        self.pdf_path = tk.StringVar()
        self.out_path = tk.StringVar()
        self.pdf_password = tk.StringVar()
        self.first_tx_date = tk.StringVar()
        self.opening_bal = tk.StringVar()
        self.closing_bal = tk.StringVar()

        self._build_ui()

    def _set_icon(self):
        for candidate in ["app_icon.ico", "app_icon.png", "icon.ico", "icon.png"]:
            full_path = get_asset_path(candidate)
            if os.path.exists(full_path):
                try:
                    if candidate.endswith(".ico"):
                        self.root.iconbitmap(full_path)
                    else:
                        self._icon_img = tk.PhotoImage(file=full_path)
                        self.root.iconphoto(True, self._icon_img)
                    break
                except Exception:
                    pass

    def _make_entry(self, parent, textvariable, width=20, show=None):
        return tk.Entry(
            parent,
            textvariable=textvariable,
            width=width,
            show=show,
            font=XP_FONT,
            bg="#FFFFFF",
            fg=XP_TEXT,
            relief="sunken",
            bd=1,
            highlightthickness=1,
            highlightcolor=XP_BORDER,
            highlightbackground=XP_BORDER,
        )

    def _make_button(self, parent, text, command, width=None):
        return tk.Button(
            parent,
            text=text,
            command=command,
            width=width,
            font=XP_FONT,
            bg=XP_BG,
            fg=XP_TEXT,
            relief="raised",
            bd=2,
            activebackground="#DFDCC9",
            padx=6,
            pady=2,
        )

    def _build_ui(self):
        main = tk.Frame(self.root, bg=XP_BG, padx=8, pady=8)
        main.pack(fill=tk.BOTH, expand=True)

        # 1. Statement File Group
        f_group = tk.LabelFrame(
            main, text=" Statement File ", font=XP_FONT_BOLD, bg=XP_BG, fg=XP_TEXT, bd=2, relief="groove"
        )
        f_group.pack(fill=tk.X, pady=(0, 6), padx=2, ipadx=4, ipady=4)

        tk.Label(f_group, text="PDF File:", font=XP_FONT, bg=XP_BG).grid(row=0, column=0, sticky="w", padx=6, pady=2)
        e_pdf = self._make_entry(f_group, self.pdf_path, width=54)
        e_pdf.grid(row=0, column=1, sticky="ew", padx=4, pady=2)
        self._make_button(f_group, "Browse...", self._browse_pdf, width=10).grid(row=0, column=2, padx=6, pady=2)

        tk.Label(f_group, text="Password:", font=XP_FONT, bg=XP_BG).grid(row=1, column=0, sticky="w", padx=6, pady=2)
        self._make_entry(f_group, self.pdf_password, width=16, show="*").grid(row=1, column=1, sticky="w", padx=4, pady=2)
        f_group.columnconfigure(1, weight=1)

        # 2. Calibration Anchors Group
        a_group = tk.LabelFrame(
            main, text=" Calibration Anchors ", font=XP_FONT_BOLD, bg=XP_BG, fg=XP_TEXT, bd=2, relief="groove"
        )
        a_group.pack(fill=tk.X, pady=(0, 6), padx=2, ipadx=4, ipady=4)

        anchor_grid = tk.Frame(a_group, bg=XP_BG)
        anchor_grid.pack(fill=tk.X, padx=4, pady=2)

        # Field 1: First Transaction Date
        tk.Label(anchor_grid, text="First Tx Date:", font=XP_FONT_BOLD, bg=XP_BG).grid(row=0, column=0, sticky="w", padx=4)
        tk.Label(anchor_grid, text="e.g. 01-05-2024 or 01/05/2024", font=XP_FONT_HINT, fg="#555555", bg=XP_BG).grid(row=1, column=0, sticky="w", padx=4)
        self._make_entry(anchor_grid, self.first_tx_date, width=22).grid(row=2, column=0, sticky="w", padx=4, pady=(2, 4))

        # Field 2: Opening Balance
        tk.Label(anchor_grid, text="Opening Bal (Opt):", font=XP_FONT, bg=XP_BG).grid(row=0, column=1, sticky="w", padx=8)
        tk.Label(anchor_grid, text="e.g. 10000.00 (or leave blank)", font=XP_FONT_HINT, fg="#555555", bg=XP_BG).grid(row=1, column=1, sticky="w", padx=8)
        self._make_entry(anchor_grid, self.opening_bal, width=20).grid(row=2, column=1, sticky="w", padx=8, pady=(2, 4))

        # Field 3: Expected Closing Balance
        tk.Label(anchor_grid, text="Expected Closing Bal:", font=XP_FONT_BOLD, bg=XP_BG).grid(row=0, column=2, sticky="w", padx=4)
        tk.Label(anchor_grid, text="e.g. 24500.75", font=XP_FONT_HINT, fg="#555555", bg=XP_BG).grid(row=1, column=2, sticky="w", padx=4)
        self._make_entry(anchor_grid, self.closing_bal, width=20).grid(row=2, column=2, sticky="w", padx=4, pady=(2, 4))

        # 3. Output Destination Group
        o_group = tk.LabelFrame(
            main, text=" Destination & Metadata ", font=XP_FONT_BOLD, bg=XP_BG, fg=XP_TEXT, bd=2, relief="groove"
        )
        o_group.pack(fill=tk.X, pady=(0, 6), padx=2, ipadx=4, ipady=4)

        tk.Label(o_group, text="Save As:", font=XP_FONT, bg=XP_BG).grid(row=0, column=0, sticky="w", padx=6, pady=2)
        e_out = self._make_entry(o_group, self.out_path, width=54)
        e_out.grid(row=0, column=1, sticky="ew", padx=4, pady=2)
        self._make_button(o_group, "Save As...", self._browse_output, width=10).grid(row=0, column=2, padx=6, pady=2)

        meta_frame = tk.Frame(o_group, bg=XP_BG)
        meta_frame.grid(row=1, column=0, columnspan=3, sticky="w", padx=6, pady=(4, 0))
        tk.Label(meta_frame, text="Account Name (Opt):", font=XP_FONT, bg=XP_BG).pack(side="left")
        self._make_entry(meta_frame, self.account_name, width=18).pack(side="left", padx=(4, 12))
        tk.Label(meta_frame, text="Account No (Opt):", font=XP_FONT, bg=XP_BG).pack(side="left")
        self._make_entry(meta_frame, self.account_no, width=18).pack(side="left", padx=4)
        o_group.columnconfigure(1, weight=1)

        # Action Button
        self.btn = tk.Button(
            main,
            text="Convert and Reconcile",
            command=self._start,
            font=XP_FONT_TITLE,
            bg=XP_BG,
            fg=XP_TEXT,
            relief="raised",
            bd=2,
            activebackground="#DFDCC9",
            pady=4,
        )
        self.btn.pack(fill=tk.X, pady=(2, 6), padx=2)

        # 4. Reconciliation Verdict Card
        self.verdict_frame = tk.Frame(main, bg="#FFFFFF", bd=2, relief="sunken", padx=6, pady=4)
        self.verdict_frame.pack(fill=tk.X, pady=(0, 6), padx=2)

        self.verdict_label = tk.Label(
            self.verdict_frame,
            text="Reconciliation Verdict: Ready",
            font=XP_FONT_BOLD,
            bg="#FFFFFF",
            fg="#444444",
            anchor="w",
        )
        self.verdict_label.pack(fill=tk.X)

        self.verdict_sub = tk.Label(
            self.verdict_frame,
            text="Calculated: --   |   Expected: --   |   Difference: --",
            font=XP_FONT,
            bg="#FFFFFF",
            fg="#666666",
            anchor="w",
        )
        self.verdict_sub.pack(fill=tk.X)

        # 5. Activity Log
        log_group = tk.LabelFrame(
            main, text=" Activity Log ", font=XP_FONT_BOLD, bg=XP_BG, fg=XP_TEXT, bd=2, relief="groove"
        )
        log_group.pack(fill=tk.BOTH, expand=True, padx=2, pady=(0, 4))

        self.log_box = tk.Text(
            log_group,
            height=7,
            font=("Lucida Console", 8),
            bg="#FFFFFF",
            fg="#000000",
            relief="sunken",
            bd=1,
            highlightthickness=0,
        )
        self.log_box.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # 6. Status Bar (No static green box; progress bar only appears while working)
        status_bar = tk.Frame(main, bg=XP_BG, bd=1, relief="sunken")
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(2, 0))

        self.status_text = tk.Label(
            status_bar,
            text="Ready",
            font=XP_FONT,
            bg=XP_BG,
            fg=XP_TEXT,
            anchor="w",
            padx=4,
        )
        self.status_text.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.progress = ttk.Progressbar(status_bar, mode="indeterminate", length=130)

    def _log(self, text):
        def _append():
            self.log_box.insert(tk.END, text + "\n")
            self.log_box.see(tk.END)
        dispatch_to_main_thread(self.root, _append)

    def _browse_pdf(self):
        f = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")])
        if f:
            self.pdf_path.set(f)
            self.out_path.set(os.path.splitext(f)[0] + "_Standardized.xlsx")

    def _browse_output(self):
        f = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx"), ("All files", "*.*")])
        if f:
            self.out_path.set(f)

    def _start(self):
        pdf = self.pdf_path.get().strip()
        out = self.out_path.get().strip()
        date_input = self.first_tx_date.get().strip()
        op_bal_input = self.opening_bal.get().strip()
        cl_bal_input = self.closing_bal.get().strip()
        pw = self.pdf_password.get().strip() or None
        acc_name = self.account_name.get().strip()
        acc_no = self.account_no.get().strip()

        if not pdf or not os.path.exists(pdf):
            messagebox.showerror("Error", "Please select a valid PDF file.")
            return
        if not date_input:
            messagebox.showerror("Input Required", "Please enter the First Transaction Date.")
            return
        if not out:
            messagebox.showerror("Error", "Please select an output destination.")
            return

        op_bal = clean_float(op_bal_input) if op_bal_input else None
        expected_cl_bal = clean_float(cl_bal_input) if cl_bal_input else None

        self.btn.config(state=tk.DISABLED)
        self.status_text.config(text="Processing statement...")
        self.progress.pack(side=tk.RIGHT, padx=2, pady=1)
        self.progress.start(10)
        self.log_box.delete("1.0", tk.END)

        self.verdict_label.config(text="Processing...", fg="#000080")
        self.verdict_sub.config(text="Parsing PDF tables and reconciling running balances...")

        threading.Thread(
            target=self._run,
            args=(pdf, out, pw, date_input, op_bal, expected_cl_bal, acc_name, acc_no),
            daemon=True,
        ).start()

    def _run(self, pdf, out, pw, date_input, op_bal, expected_cl_bal, acc_name, acc_no):
        try:
            converter = StatementConverter(log_fn=self._log)
            df, v_info = converter.parse_pdf(
                pdf,
                password=pw,
                first_tx_date=date_input,
                opening_bal=op_bal,
                expected_closing_bal=expected_cl_bal,
            )

            if df.empty:
                self._log("0 transactions parsed.")
                def _on_zero():
                    self.verdict_label.config(text="Verdict: 0 Transactions Found", fg="#800000")
                    self.verdict_sub.config(text="Verify that the First Transaction Date matches the statement.")
                    messagebox.showwarning("Warning", "No transactions detected.")
                dispatch_to_main_thread(self.root, _on_zero)
                return

            export_to_excel_styled(df, out, account_name=acc_name, account_no=acc_no)
            self._log(f"Exported {len(df)} rows to: {out}")

            final_bal = v_info["final_bal"]
            diff = v_info["diff"]
            matches = v_info["closing_matches"]
            tx_count = v_info.get("tx_count", len(df) - 1)

            def _update_ui_success():
                if expected_cl_bal is not None:
                    if matches:
                        self.verdict_label.config(
                            text=f"Verdict: MATCH (100% Reconciled - {tx_count} Transactions)",
                            fg="#006600",
                        )
                        self.verdict_sub.config(
                            text=f"Calculated: {final_bal:,.2f}   |   Expected: {expected_cl_bal:,.2f}   |   Difference: {diff:,.2f}"
                        )
                        messagebox.showinfo(
                            "Reconciliation Success",
                            f"Closing Balance Matches!\n\n"
                            f"Calculated:  {final_bal:,.2f}\n"
                            f"Expected:    {expected_cl_bal:,.2f}\n"
                            f"Difference:  {diff:,.2f}",
                        )
                    else:
                        self.verdict_label.config(
                            text=f"Verdict: MISMATCH (Difference: {diff:,.2f})",
                            fg="#A00000",
                        )
                        self.verdict_sub.config(
                            text=f"Calculated: {final_bal:,.2f}   |   Expected: {expected_cl_bal:,.2f}   |   Difference: {diff:,.2f}"
                        )
                        messagebox.showwarning(
                            "Balance Mismatch",
                            f"Closing Balance Mismatch!\n\n"
                            f"Calculated:  {final_bal:,.2f}\n"
                            f"Expected:    {expected_cl_bal:,.2f}\n"
                            f"Difference:  {diff:,.2f}",
                        )
                else:
                    self.verdict_label.config(
                        text=f"Verdict: Complete ({tx_count} Transactions)", fg="#000080"
                    )
                    self.verdict_sub.config(
                        text=f"Final Balance: {final_bal:,.2f}   |   Expected: Not Provided"
                    )
                    messagebox.showinfo(
                        "Complete", f"Exported {tx_count} transactions.\nFinal Balance: {final_bal:,.2f}"
                    )

            dispatch_to_main_thread(self.root, _update_ui_success)

        except Exception as e:
            err_msg = str(e)
            self._log(f"ERROR: {err_msg}")
            def _on_error():
                self.verdict_label.config(text="Verdict: Execution Error", fg="#A00000")
                self.verdict_sub.config(text=err_msg)
                messagebox.showerror("Execution Error", err_msg)
            dispatch_to_main_thread(self.root, _on_error)

        finally:
            def _cleanup():
                self.progress.stop()
                self.progress.pack_forget()
                self.status_text.config(text="Ready")
                self.btn.config(state=tk.NORMAL)
            dispatch_to_main_thread(self.root, _cleanup)


if __name__ == "__main__":
    tk_root = tk.Tk()
    app = App(tk_root)
    tk_root.mainloop()