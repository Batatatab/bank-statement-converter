import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from converter_engine import (
    StatementConverter,
    clean_float,
    export_to_excel_styled,
)


class App:

    def __init__(self, root):
        self.root = root
        self.root.title("Bank Statement to Standard Excel Converter")
        self.root.geometry("820x760")
        self.root.minsize(760, 680)

        self.account_name = tk.StringVar()
        self.account_no = tk.StringVar()
        self.pdf_path = tk.StringVar()
        self.out_path = tk.StringVar()
        self.pdf_password = tk.StringVar()
        self.first_tx_date = tk.StringVar()
        self.opening_bal = tk.StringVar()
        self.closing_bal = tk.StringVar()

        self._apply_theme()
        self._build_ui()

    def _apply_theme(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 9))
        style.configure("TLabelframe", background="#ffffff", relief="solid", borderwidth=1)
        style.configure("TLabelframe.Label", font=("Segoe UI", 9, "bold"), foreground="#1F497D", background="#ffffff")
        style.configure("TButton", font=("Segoe UI", 9, "bold"), padding=5)
        style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), background="#1F497D", foreground="#ffffff")
        style.map("Action.TButton", background=[("active", "#16365C")])

    def _build_ui(self):
        canvas_bg = ttk.Frame(self.root, padding=14)
        canvas_bg.pack(fill=tk.BOTH, expand=True)

        # 1. Statement File Picker
        file_frame = ttk.LabelFrame(canvas_bg, text=" 1. Bank Statement File ", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(file_frame, text="Select PDF Statement:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(file_frame, textvariable=self.pdf_path, width=65).grid(row=1, column=0, padx=(0, 8), sticky=tk.EW)
        ttk.Button(file_frame, text="Browse...", command=self._browse_pdf).grid(row=1, column=1)

        pw_row = ttk.Frame(file_frame)
        pw_row.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(6, 0))
        ttk.Label(pw_row, text="PDF Password (if protected):").pack(side=tk.LEFT)
        ttk.Entry(pw_row, textvariable=self.pdf_password, show="*", width=16).pack(side=tk.LEFT, padx=8)

        file_frame.columnconfigure(0, weight=1)

        # 2. Calibration Anchors with In-GUI Definitions
        anchor_frame = ttk.LabelFrame(canvas_bg, text=" 2. Calibration & Verification Anchors ", padding=10)
        anchor_frame.pack(fill=tk.X, pady=(0, 8))

        # Anchor Inputs Grid
        inputs_grid = ttk.Frame(anchor_frame)
        inputs_grid.pack(fill=tk.X)

        # First Tx Date
        f_box1 = ttk.Frame(inputs_grid)
        f_box1.grid(row=0, column=0, sticky=tk.W, padx=(0, 16))
        ttk.Label(f_box1, text="First Tx Date *", font=("Segoe UI", 9, "bold"), foreground="#1F497D").pack(anchor=tk.W)
        ttk.Entry(f_box1, textvariable=self.first_tx_date, width=20, font=("Segoe UI", 10)).pack(anchor=tk.W, pady=(2, 0))

        # Opening Balance
        f_box2 = ttk.Frame(inputs_grid)
        f_box2.grid(row=0, column=1, sticky=tk.W, padx=(0, 16))
        ttk.Label(f_box2, text="Opening Balance (Optional)", font=("Segoe UI", 9, "bold"), foreground="#1F497D").pack(anchor=tk.W)
        ttk.Entry(f_box2, textvariable=self.opening_bal, width=22, font=("Segoe UI", 10)).pack(anchor=tk.W, pady=(2, 0))

        # Expected Closing Balance
        f_box3 = ttk.Frame(inputs_grid)
        f_box3.grid(row=0, column=2, sticky=tk.W)
        ttk.Label(f_box3, text="Expected Closing Balance *", font=("Segoe UI", 9, "bold"), foreground="#1F497D").pack(anchor=tk.W)
        ttk.Entry(f_box3, textvariable=self.closing_bal, width=22, font=("Segoe UI", 10)).pack(anchor=tk.W, pady=(2, 0))

        # Inline Field Definitions
        guide_box = tk.Text(anchor_frame, height=4, bg="#F2F4F7", relief="flat", font=("Segoe UI", 8), fg="#333333", padx=8, pady=6)
        guide_box.pack(fill=tk.X, pady=(8, 0))
        guide_text = (
            "• First Tx Date: Date on the top-most transaction in the statement (e.g. 07/12/2023 or 2023-12-07). Locks table columns.\n"
            "• Opening Balance: Balance before first transaction. (Optional — if blank, auto-calculated from first transaction).\n"
            "• Expected Closing Balance: Ending balance printed on statement. Verifies 100% ledger accuracy against your bank."
        )
        guide_box.insert(tk.END, guide_text)
        guide_box.config(state=tk.DISABLED)

        # 3. Output Excel File Destination
        out_frame = ttk.LabelFrame(canvas_bg, text=" 3. Excel Output Destination ", padding=10)
        out_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(out_frame, text="Save Standardized Excel As:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(out_frame, textvariable=self.out_path, width=65).grid(row=1, column=0, padx=(0, 8), sticky=tk.EW)
        ttk.Button(out_frame, text="Save As...", command=self._browse_output).grid(row=1, column=1)
        out_frame.columnconfigure(0, weight=1)

        # Optional Metadata
        meta_row = ttk.Frame(out_frame)
        meta_row.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(8, 0))
        ttk.Label(meta_row, text="Account Holder (Opt):").pack(side=tk.LEFT)
        ttk.Entry(meta_row, textvariable=self.account_name, width=20).pack(side=tk.LEFT, padx=(4, 16))
        ttk.Label(meta_row, text="Account No (Opt):").pack(side=tk.LEFT)
        ttk.Entry(meta_row, textvariable=self.account_no, width=20).pack(side=tk.LEFT, padx=4)

        # Convert Button
        self.btn = ttk.Button(canvas_bg, text="▶  Convert, Reconcile & Verify Closing Balance", style="Action.TButton", command=self._start)
        self.btn.pack(fill=tk.X, pady=(2, 8))

        # 4. Closing Balance Verification Result Card
        self.card_frame = tk.Frame(canvas_bg, bg="#E9ECEF", bd=1, relief="solid", padx=10, pady=8)
        self.card_frame.pack(fill=tk.X, pady=(0, 8))

        self.card_title = tk.Label(self.card_frame, text="RECONCILIATION VERDICT: WAITING TO RUN", font=("Segoe UI", 10, "bold"), bg="#E9ECEF", fg="#495057")
        self.card_title.pack(anchor=tk.W)

        self.card_details = tk.Label(
            self.card_frame,
            text="Calculated Balance: --  |  Expected Balance: --  |  Variance: --",
            font=("Segoe UI", 9),
            bg="#E9ECEF",
            fg="#495057"
        )
        self.card_details.pack(anchor=tk.W, pady=(2, 0))

        # 5. Execution Log Console
        log_frame = ttk.LabelFrame(canvas_bg, text=" Audit & Execution Log ", padding=8)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_box = tk.Text(log_frame, height=7, font=("Consolas", 9), bg="#f8f9fa", relief="solid", borderwidth=1)
        self.log_box.pack(fill=tk.BOTH, expand=True)

        self.progress = ttk.Progressbar(canvas_bg, mode="indeterminate")
        self.progress.pack(fill=tk.X, pady=(4, 0))

    def _log(self, text):
        self.log_box.insert(tk.END, text + "\n")
        self.log_box.see(tk.END)

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
            messagebox.showerror("Missing PDF", "Please select a valid bank statement PDF file.")
            return
        if not date_input:
            messagebox.showerror("Missing Anchor Date", "Please enter the First Transaction Date (e.g. 07/12/2023 or 2023-12-07).")
            return
        if not out:
            messagebox.showerror("Missing Destination", "Please choose where to save the Excel file.")
            return

        op_bal = clean_float(op_bal_input) if op_bal_input else None
        expected_cl_bal = clean_float(cl_bal_input) if cl_bal_input else None

        self.btn.config(state=tk.DISABLED)
        self.progress.start(10)
        self.log_box.delete("1.0", tk.END)

        # Reset Result Card
        self.card_frame.config(bg="#E9ECEF")
        self.card_title.config(text="PROCESSING RECONCILIATION...", fg="#495057", bg="#E9ECEF")
        self.card_details.config(text="Parsing transactions and calculating double-entry running balances...", fg="#495057", bg="#E9ECEF")

        threading.Thread(
            target=self._run,
            args=(pdf, out, pw, date_input, op_bal, expected_cl_bal, acc_name, acc_no),
            daemon=True
        ).start()

    def _run(self, pdf, out, pw, date_input, op_bal, expected_cl_bal, acc_name, acc_no):
        try:
            converter = StatementConverter(log_fn=self._log)
            df, v_info = converter.parse_pdf(
                pdf,
                password=pw,
                first_tx_date=date_input,
                opening_bal=op_bal,
                expected_closing_bal=expected_cl_bal
            )

            if df.empty:
                self._log("0 transactions parsed.")
                self.card_frame.config(bg="#FFF3CD")
                self.card_title.config(text="WARNING: 0 TRANSACTIONS DETECTED", fg="#856404", bg="#FFF3CD")
                self.card_details.config(text="Please verify the First Transaction Date matches your PDF.", fg="#856404", bg="#FFF3CD")
                messagebox.showwarning("Warning", "No transactions detected.")
                return

            export_to_excel_styled(df, out, account_name=acc_name, account_no=acc_no)
            self._log(f"Exported {len(df)} rows to: {out}")

            final_bal = v_info["final_bal"]
            diff = v_info["diff"]
            matches = v_info["closing_matches"]
            tx_count = v_info["tx_count"]

            if expected_cl_bal is not None:
                if matches:
                    # Closing Balance Matches
                    self.card_frame.config(bg="#D4EDDA")
                    self.card_title.config(
                        text=f"✔  SUCCESS: CLOSING BALANCE MATCHES (100% RECONCILED)",
                        fg="#155724",
                        bg="#D4EDDA"
                    )
                    self.card_details.config(
                        text=f"Calculated: ₹{final_bal:,.2f}  |  Expected: ₹{expected_cl_bal:,.2f}  |  Variance: ₹{diff:,.2f} (EXACT MATCH)  |  Transactions: {tx_count}",
                        fg="#155724",
                        bg="#D4EDDA"
                    )
                    self._log(f"VERDICT: Closing Balance matches exactly (₹{final_bal:,.2f}). 0.00 discrepancy.")
                    messagebox.showinfo(
                        "Reconciliation Success",
                        f"SUCCESS: Statement 100% Reconciled!\n\n"
                        f"• Calculated Closing Balance: ₹{final_bal:,.2f}\n"
                        f"• Expected Closing Balance:   ₹{expected_cl_bal:,.2f}\n"
                        f"• Variance / Difference:     ₹{diff:,.2f} (MATCH)\n"
                        f"• Total Transactions:        {tx_count}"
                    )
                else:
                    # Closing Balance Mismatch
                    self.card_frame.config(bg="#F8D7DA")
                    self.card_title.config(
                        text=f"✖  MISMATCH DETECTED: CLOSING BALANCE DOES NOT MATCH",
                        fg="#721C24",
                        bg="#F8D7DA"
                    )
                    self.card_details.config(
                        text=f"Calculated: ₹{final_bal:,.2f}  |  Expected: ₹{expected_cl_bal:,.2f}  |  Difference: ₹{diff:,.2f}  |  Transactions: {tx_count}",
                        fg="#721C24",
                        bg="#F8D7DA"
                    )
                    self._log(f"VERDICT: MISMATCH DETECTED! Expected ₹{expected_cl_bal:,.2f}, Calculated ₹{final_bal:,.2f} (Diff: ₹{diff:,.2f})")
                    messagebox.showwarning(
                        "Closing Balance Mismatch",
                        f"ATTENTION: Closing Balance Mismatch!\n\n"
                        f"• Calculated Final Balance: ₹{final_bal:,.2f}\n"
                        f"• Expected Closing Balance: ₹{expected_cl_bal:,.2f}\n"
                        f"• Discrepancy / Difference: ₹{diff:,.2f}\n\n"
                        "Check for potential typos in the Opening Balance or individual transaction amounts."
                    )
            else:
                self.card_frame.config(bg="#D1ECF1")
                self.card_title.config(text=f"COMPLETED (No Expected Closing Balance Provided)", fg="#0C5460", bg="#D1ECF1")
                self.card_details.config(text=f"Final Ledger Balance: ₹{final_bal:,.2f}  |  Transactions: {tx_count}", fg="#0C5460", bg="#D1ECF1")
                self._log(f"Completed. Final calculated balance is ₹{final_bal:,.2f}.")
                messagebox.showinfo("Export Complete", f"Exported {tx_count} transactions.\nFinal Balance: ₹{final_bal:,.2f}")

        except Exception as e:
            self._log(f"ERROR: {str(e)}")
            self.card_frame.config(bg="#F8D7DA")
            self.card_title.config(text=f"EXECUTION ERROR", fg="#721C24", bg="#F8D7DA")
            self.card_details.config(text=str(e), fg="#721C24", bg="#F8D7DA")
            messagebox.showerror("Execution Error", str(e))
        finally:
            self.progress.stop()
            self.btn.config(state=tk.NORMAL)


if __name__ == "__main__":
    tk_root = tk.Tk()
    app = App(tk_root)
    tk_root.mainloop()