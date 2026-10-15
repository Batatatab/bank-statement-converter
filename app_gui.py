from datetime import datetime
import json
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
    self.root.geometry("1040x680")
    self.root.minsize(980, 620)
    self.root.configure(bg=XP_BG)

    self._icon_img = None
    self._set_icon()

    self.history_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "conversion_history.json"
    )

    self.account_name = tk.StringVar()
    self.account_no = tk.StringVar()
    self.pdf_path = tk.StringVar()
    self.out_path = tk.StringVar()
    self.pdf_password = tk.StringVar()
    self.first_tx_date = tk.StringVar()
    self.opening_bal = tk.StringVar()
    self.closing_bal = tk.StringVar()
    self.is_scanned = tk.BooleanVar(value=False)

    self._build_ui()
    self._load_history()

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

    # Split Panes: Converter Controls (Left), Recent Conversions (Right)
    left_pane = tk.Frame(main, bg=XP_BG)
    left_pane.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))

    right_pane = tk.Frame(main, bg=XP_BG, width=340)
    right_pane.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
    right_pane.pack_propagate(False)

    # ----------------------------------------------------
    # LEFT PANE: CONVERTER CONTROLS
    # ----------------------------------------------------
    # 1. Statement File Group
    f_group = tk.LabelFrame(
        left_pane,
        text=" Statement File ",
        font=XP_FONT_BOLD,
        bg=XP_BG,
        fg=XP_TEXT,
        bd=2,
        relief="groove",
    )
    f_group.pack(fill=tk.X, pady=(0, 6), padx=2, ipadx=4, ipady=4)

    tk.Label(f_group, text="PDF File:", font=XP_FONT, bg=XP_BG).grid(
        row=0, column=0, sticky="w", padx=6, pady=2
    )
    e_pdf = self._make_entry(f_group, self.pdf_path, width=42)
    e_pdf.grid(row=0, column=1, sticky="ew", padx=4, pady=2)
    self._make_button(
        f_group, "Browse...", self._browse_pdf, width=9
    ).grid(row=0, column=2, padx=6, pady=2)

    tk.Label(f_group, text="Password:", font=XP_FONT, bg=XP_BG).grid(
        row=1, column=0, sticky="w", padx=6, pady=2
    )
    self._make_entry(
        f_group, self.pdf_password, width=16, show="*"
    ).grid(row=1, column=1, sticky="w", padx=4, pady=2)

    chk_scan = tk.Checkbutton(
        f_group,
        text="Scanned / Image PDF (Enable OCR-BETA)",
        variable=self.is_scanned,
        font=XP_FONT_BOLD,
        bg=XP_BG,
        fg=XP_TEXT,
        activebackground=XP_BG,
        selectcolor="#FFFFFF",
    )
    chk_scan.grid(
        row=2, column=0, columnspan=2, sticky="w", padx=6, pady=(4, 2)
    )

    f_group.columnconfigure(1, weight=1)

    # 2. Calibration Anchors Group
    a_group = tk.LabelFrame(
        left_pane,
        text=" Calibration Anchors ",
        font=XP_FONT_BOLD,
        bg=XP_BG,
        fg=XP_TEXT,
        bd=2,
        relief="groove",
    )
    a_group.pack(fill=tk.X, pady=(0, 6), padx=2, ipadx=4, ipady=4)

    anchor_grid = tk.Frame(a_group, bg=XP_BG)
    anchor_grid.pack(fill=tk.X, padx=4, pady=2)

    tk.Label(
        anchor_grid, text="First Tx Date:", font=XP_FONT_BOLD, bg=XP_BG
    ).grid(row=0, column=0, sticky="w", padx=4)
    tk.Label(
        anchor_grid,
        text="e.g. 01-05-2024 or 01/05/2024",
        font=XP_FONT_HINT,
        fg="#555555",
        bg=XP_BG,
    ).grid(row=1, column=0, sticky="w", padx=4)
    self._make_entry(anchor_grid, self.first_tx_date, width=18).grid(
        row=2, column=0, sticky="w", padx=4, pady=(2, 4)
    )

    tk.Label(
        anchor_grid, text="Opening Bal (Opt):", font=XP_FONT, bg=XP_BG
    ).grid(row=0, column=1, sticky="w", padx=6)
    tk.Label(
        anchor_grid,
        text="e.g. 10000.00 (or blank)",
        font=XP_FONT_HINT,
        fg="#555555",
        bg=XP_BG,
    ).grid(row=1, column=1, sticky="w", padx=6)
    self._make_entry(anchor_grid, self.opening_bal, width=17).grid(
        row=2, column=1, sticky="w", padx=6, pady=(2, 4)
    )

    tk.Label(
        anchor_grid,
        text="Expected Closing Bal:",
        font=XP_FONT_BOLD,
        bg=XP_BG,
    ).grid(row=0, column=2, sticky="w", padx=4)
    tk.Label(
        anchor_grid,
        text="e.g. 24500.75",
        font=XP_FONT_HINT,
        fg="#555555",
        bg=XP_BG,
    ).grid(row=1, column=2, sticky="w", padx=4)
    self._make_entry(anchor_grid, self.closing_bal, width=17).grid(
        row=2, column=2, sticky="w", padx=4, pady=(2, 4)
    )

    # 3. Output Destination Group
    o_group = tk.LabelFrame(
        left_pane,
        text=" Destination & Metadata ",
        font=XP_FONT_BOLD,
        bg=XP_BG,
        fg=XP_TEXT,
        bd=2,
        relief="groove",
    )
    o_group.pack(fill=tk.X, pady=(0, 6), padx=2, ipadx=4, ipady=4)

    tk.Label(o_group, text="Save As:", font=XP_FONT, bg=XP_BG).grid(
        row=0, column=0, sticky="w", padx=6, pady=2
    )
    e_out = self._make_entry(o_group, self.out_path, width=42)
    e_out.grid(row=0, column=1, sticky="ew", padx=4, pady=2)
    self._make_button(
        o_group, "Save As...", self._browse_output, width=9
    ).grid(row=0, column=2, padx=6, pady=2)

    meta_frame = tk.Frame(o_group, bg=XP_BG)
    meta_frame.grid(
        row=1, column=0, columnspan=3, sticky="w", padx=6, pady=(4, 0)
    )
    tk.Label(
        meta_frame, text="Account Name (Opt):", font=XP_FONT, bg=XP_BG
    ).pack(side="left")
    self._make_entry(meta_frame, self.account_name, width=16).pack(
        side="left", padx=(4, 10)
    )
    tk.Label(
        meta_frame, text="Account No (Opt):", font=XP_FONT, bg=XP_BG
    ).pack(side="left")
    self._make_entry(meta_frame, self.account_no, width=16).pack(
        side="left", padx=4
    )
    o_group.columnconfigure(1, weight=1)

    # Action Row: Convert & Reconcile + Clear Button
    act_row = tk.Frame(left_pane, bg=XP_BG)
    act_row.pack(fill=tk.X, pady=(2, 6), padx=2)

    self.btn = tk.Button(
        act_row,
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
    self.btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

    self.btn_clear = tk.Button(
        act_row,
        text="Clear Form",
        command=self._clear_all,
        font=XP_FONT_BOLD,
        bg=XP_BG,
        fg="#600000",
        relief="raised",
        bd=2,
        activebackground="#DFDCC9",
        padx=10,
        pady=4,
    )
    self.btn_clear.pack(side=tk.RIGHT, fill=tk.Y)

    # 4. Reconciliation Verdict Card
    self.verdict_frame = tk.Frame(
        left_pane, bg="#FFFFFF", bd=2, relief="sunken", padx=6, pady=4
    )
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
        left_pane,
        text=" Activity Log ",
        font=XP_FONT_BOLD,
        bg=XP_BG,
        fg=XP_TEXT,
        bd=2,
        relief="groove",
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

    # ----------------------------------------------------
    # RIGHT PANE: RECENT CONVERSIONS / HISTORY
    # ----------------------------------------------------
    hist_group = tk.LabelFrame(
        right_pane,
        text=" Recent Conversions ",
        font=XP_FONT_BOLD,
        bg=XP_BG,
        fg=XP_TEXT,
        bd=2,
        relief="groove",
    )
    hist_group.pack(fill=tk.BOTH, expand=True, padx=2, pady=(0, 4))

    tree_frame = tk.Frame(hist_group, bg=XP_BG)
    tree_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    cols = ("time", "file", "status", "txs")
    self.hist_tree = ttk.Treeview(
        tree_frame, columns=cols, show="headings", selectmode="browse"
    )
    self.hist_tree.heading("time", text="Time")
    self.hist_tree.heading("file", text="Statement")
    self.hist_tree.heading("status", text="Status")
    self.hist_tree.heading("txs", text="Rows")

    self.hist_tree.column("time", width=62, anchor="center")
    self.hist_tree.column("file", width=120, anchor="w")
    self.hist_tree.column("status", width=70, anchor="center")
    self.hist_tree.column("txs", width=42, anchor="center")

    scroll_y = ttk.Scrollbar(
        tree_frame, orient=tk.VERTICAL, command=self.hist_tree.yview
    )
    self.hist_tree.configure(yscrollcommand=scroll_y.set)

    self.hist_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

    self.hist_tree.bind("<Double-1>", lambda e: self._open_selected_excel())

    # History Action Buttons
    hist_btn_bar = tk.Frame(hist_group, bg=XP_BG)
    hist_btn_bar.pack(fill=tk.X, padx=4, pady=(2, 4))

    self._make_button(
        hist_btn_bar, "Open Excel", self._open_selected_excel, width=10
    ).pack(side=tk.LEFT, padx=(0, 2))
    self._make_button(
        hist_btn_bar, "Open Folder", self._open_selected_folder, width=10
    ).pack(side=tk.LEFT, padx=2)
    self._make_button(
        hist_btn_bar, "Clear Log", self._clear_history, width=9
    ).pack(side=tk.RIGHT, padx=(2, 0))

    # 6. Status Bar
    status_bar = tk.Frame(self.root, bg=XP_BG, bd=1, relief="sunken")
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

  def _clear_all(self):
    self.pdf_path.set("")
    self.out_path.set("")
    self.pdf_password.set("")
    self.first_tx_date.set("")
    self.opening_bal.set("")
    self.closing_bal.set("")
    self.account_name.set("")
    self.account_no.set("")
    self.is_scanned.set(False)

    self.verdict_label.config(
        text="Reconciliation Verdict: Ready", fg="#444444"
    )
    self.verdict_sub.config(
        text="Calculated: --   |   Expected: --   |   Difference: --",
        fg="#666666",
    )

    self.log_box.delete("1.0", tk.END)
    self.status_text.config(text="Ready")

  def _load_history(self):
    for item in self.hist_tree.get_children():
      self.hist_tree.delete(item)

    if not os.path.exists(self.history_file):
      return

    try:
      with open(self.history_file, "r", encoding="utf-8") as f:
        data = json.load(f)
      for entry in data[-40:]:
        self.hist_tree.insert(
            "",
            0,
            values=(
                entry.get("time", ""),
                entry.get("file", ""),
                entry.get("status", ""),
                entry.get("txs", ""),
            ),
            tags=(entry.get("out_path", ""),),
        )
    except Exception:
      pass

  def _add_history_entry(self, file_name, status, txs, out_path):
    time_str = datetime.now().strftime("%H:%M:%S")
    entry = {
        "time": time_str,
        "file": file_name,
        "status": status,
        "txs": txs,
        "out_path": out_path,
    }

    records = []
    if os.path.exists(self.history_file):
      try:
        with open(self.history_file, "r", encoding="utf-8") as f:
          records = json.load(f)
      except Exception:
        records = []

    records.append(entry)
    records = records[-50:]

    try:
      with open(self.history_file, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    except Exception:
      pass

    dispatch_to_main_thread(self.root, self._load_history)

  def _open_selected_excel(self):
    sel = self.hist_tree.selection()
    if not sel:
      return
    tags = self.hist_tree.item(sel[0], "tags")
    if tags and os.path.exists(tags[0]):
      os.startfile(tags[0])
    else:
      messagebox.showwarning(
          "File Not Found", "The converted Excel file no longer exists."
      )

  def _open_selected_folder(self):
    sel = self.hist_tree.selection()
    if not sel:
      return
    tags = self.hist_tree.item(sel[0], "tags")
    if tags and os.path.exists(tags[0]):
      folder = os.path.dirname(tags[0])
      os.startfile(folder)
    else:
      messagebox.showwarning("Notice", "Output folder could not be found.")

  def _clear_history(self):
    if os.path.exists(self.history_file):
      try:
        os.remove(self.history_file)
      except Exception:
        pass
    for item in self.hist_tree.get_children():
      self.hist_tree.delete(item)

  def _log(self, text):
    def _append():
      self.log_box.insert(tk.END, text + "\n")
      self.log_box.see(tk.END)

    dispatch_to_main_thread(self.root, _append)

  def _browse_pdf(self):
    f = filedialog.askopenfilename(
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
    )
    if f:
      self.pdf_path.set(f)
      self.out_path.set(os.path.splitext(f)[0] + "_Standardized.xlsx")

  def _browse_output(self):
    f = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Excel", "*.xlsx"), ("All files", "*.*")],
    )
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
    scanned_flag = self.is_scanned.get()

    if not pdf or not os.path.exists(pdf):
      messagebox.showerror("Error", "Please select a valid PDF file.")
      return
    if not date_input:
      messagebox.showerror(
          "Input Required", "Please enter the First Transaction Date."
      )
      return
    if not out:
      messagebox.showerror("Error", "Please select an output destination.")
      return

    op_bal = clean_float(op_bal_input) if op_bal_input else None
    expected_cl_bal = clean_float(cl_bal_input) if cl_bal_input else None

    self.btn.config(state=tk.DISABLED)
    self.btn_clear.config(state=tk.DISABLED)
    self.status_text.config(
        text="Processing statement (OCR)..." if scanned_flag else "Processing statement..."
    )
    self.progress.pack(side=tk.RIGHT, padx=2, pady=1)
    self.progress.start(10)
    self.log_box.delete("1.0", tk.END)

    self.verdict_label.config(text="Processing...", fg="#000080")
    self.verdict_sub.config(
        text="Scanning pages with OCR..." if scanned_flag else "Parsing PDF tables and reconciling running balances..."
    )

    threading.Thread(
        target=self._run,
        args=(
            pdf,
            out,
            pw,
            date_input,
            op_bal,
            expected_cl_bal,
            acc_name,
            acc_no,
            scanned_flag,
        ),
        daemon=True,
    ).start()

  def _run(
      self,
      pdf,
      out,
      pw,
      date_input,
      op_bal,
      expected_cl_bal,
      acc_name,
      acc_no,
      scanned_flag,
  ):
    pdf_base = os.path.basename(pdf)
    try:
      converter = StatementConverter(log_fn=self._log)
      df, v_info = converter.parse_pdf(
          pdf,
          password=pw,
          first_tx_date=date_input,
          opening_bal=op_bal,
          expected_closing_bal=expected_cl_bal,
          is_scanned=scanned_flag,
      )

      if df.empty:
        self._log("0 transactions parsed.")
        self._add_history_entry(pdf_base, "0 ROWS", 0, out)

        def _on_zero():
          self.verdict_label.config(
              text="Verdict: 0 Transactions Found", fg="#800000"
          )
          self.verdict_sub.config(
              text="Verify that the First Transaction Date matches the statement."
          )
          messagebox.showwarning("Warning", "No transactions detected.")

        dispatch_to_main_thread(self.root, _on_zero)
        return

      is_od = v_info.get("is_od_account", False)
      try:
        export_to_excel_styled(
            df,
            out,
            account_name=acc_name,
            account_no=acc_no,
            is_od_account=is_od,
        )
      except TypeError:
        export_to_excel_styled(
            df,
            out,
            account_name=acc_name,
            account_no=acc_no,
        )

      self._log(f"Exported {len(df)} rows to: {out}")

      final_bal = v_info["final_bal"]
      diff = v_info["diff"]
      matches = v_info["closing_matches"]
      tx_count = v_info.get("tx_count", len(df) - 1)

      status_tag = "MATCH" if matches else "DIFF"
      if expected_cl_bal is None:
        status_tag = "COMPLETE"

      self._add_history_entry(pdf_base, status_tag, tx_count, out)

      def _update_ui_success():
        if expected_cl_bal is not None:
          if matches:
            self.verdict_label.config(
                text=(
                    f"Verdict: MATCH (100% Reconciled - {tx_count}"
                    " Transactions)"
                ),
                fg="#006600",
            )
            self.verdict_sub.config(
                text=(
                    f"Calculated: {final_bal:,.2f}   |   Expected:"
                    f" {expected_cl_bal:,.2f}   |   Difference: {diff:,.2f}"
                )
            )
            messagebox.showinfo(
                "Reconciliation Success",
                f"Closing Balance Matches!\n\nCalculated:  {final_bal:,.2f}\nExpected:"
                f"    {expected_cl_bal:,.2f}\nDifference:  {diff:,.2f}",
            )
          else:
            self.verdict_label.config(
                text=f"Verdict: MISMATCH (Difference: {diff:,.2f})",
                fg="#A00000",
            )
            self.verdict_sub.config(
                text=(
                    f"Calculated: {final_bal:,.2f}   |   Expected:"
                    f" {expected_cl_bal:,.2f}   |   Difference: {diff:,.2f}"
                )
            )
            messagebox.showwarning(
                "Balance Mismatch",
                f"Closing Balance Mismatch!\n\nCalculated:  {final_bal:,.2f}\nExpected:"
                f"    {expected_cl_bal:,.2f}\nDifference:  {diff:,.2f}",
            )
        else:
          self.verdict_label.config(
              text=f"Verdict: Complete ({tx_count} Transactions)", fg="#000080"
          )
          self.verdict_sub.config(
              text=(
                  f"Final Balance: {final_bal:,.2f}   |   Expected: Not"
                  " Provided"
              )
          )
          messagebox.showinfo(
              "Complete",
              f"Exported {tx_count} transactions.\nFinal Balance:"
              f" {final_bal:,.2f}",
          )

      dispatch_to_main_thread(self.root, _update_ui_success)

    except Exception as e:
      err_msg = str(e)
      self._log(f"ERROR: {err_msg}")
      self._add_history_entry(pdf_base, "ERROR", 0, out)

      def _on_error():
        self.verdict_label.config(
            text="Verdict: Execution Error", fg="#A00000"
        )
        self.verdict_sub.config(text=err_msg)
        messagebox.showerror("Execution Error", err_msg)

      dispatch_to_main_thread(self.root, _on_error)

    finally:

      def _cleanup():
        self.progress.stop()
        self.progress.pack_forget()
        self.status_text.config(text="Ready")
        self.btn.config(state=tk.NORMAL)
        self.btn_clear.config(state=tk.NORMAL)

      dispatch_to_main_thread(self.root, _cleanup)


if __name__ == "__main__":
  tk_root = tk.Tk()
  app = App(tk_root)
  tk_root.mainloop()