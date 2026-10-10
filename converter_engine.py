from datetime import date, datetime
import re
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
import pandas as pd
import pdfplumber

# ----------------- OCR HEALING & DATE MAPS -----------------
MONTH_NAME_TO_NUM = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}

DECIMAL_REGEX = re.compile(r"^[-+]?[\d,]+\.\d{2}$")
CHEQUE_6DIGIT_REGEX = re.compile(r"^\d{6}$")

FOOTER_AND_TOTAL_PATTERNS = [
    r"\bTOTAL\b",
    r"\bGRAND\s*TOTAL\b",
    r"\bSUB\s*TOTAL\b",
    r"\bTOTAL\s*DEBIT\b",
    r"\bTOTAL\s*CREDIT\b",
    r"\bSTATEMENT\s*PERIOD\b",
    r"\bSTATEMENT\s*OF\s*ACCOUNT\b",
    r"\bCUSTOMER\s*ID\b",
    r"\bACCOUNT\s*NO\b",
    r"\bREGISTERED\s*OFFICE\b",
    r"\bSTATEMENT\s*FOR\s*\(TILL\b",
    r"\bSCHEME\s*OPENING\s*POINTS\b",
    r"\bPOINTS\s*ADJUSTMENT\b",
    r"\bREWARD\s*POINTS\b",
    r"\bPAGE\s*(?:NO)?\.?\s*\d+\s*(?:OF\s*\d+)?",
    r"\bCOMPUTER\s*GENERATED\b",
    r"\bEND\s*OF\s*STATEMENT\b",
    r"\bUNLESS\s*A\s*CONSTITUENT\b",
    r"\bPLEASE\s*DO\s*NOT\s*SHARE\s*YOUR\s*ATM\b",
]

HEADER_KEYWORDS = {
    "serial_no": [
        "serial no",
        "serial number",
        "sl no",
        "sr no",
        "s.no",
        "sr.no",
        "sl.no",
        "s no",
        "sl",
        "sr",
    ],
    "val_date": [
        "value date",
        "value dt",
        "val date",
        "val dt",
        "value_date",
        "v.date",
    ],
    "date": [
        "transaction date",
        "txn date",
        "tran date",
        "trans date",
        "date",
        "post date",
    ],
    "chq_ref": [
        "reference no",
        "reference number",
        "ref no",
        "ref. no.",
        "reference",
        "cheque/reference#",
        "cheque/reference",
        "cheque number",
        "chq no",
        "cheque no",
        "cheque",
        "chq / ref",
        "chq./ref.no.",
        "ref/cheque",
    ],
    "particulars": [
        "description",
        "particulars",
        "narration",
        "transaction details",
        "remarks",
        "details",
    ],
    "dr": [
        "debited amount",
        "debited",
        "debit",
        "withdrawal",
        "dr",
        "dr amount",
        "withdrawal amt",
        "withdrawals",
    ],
    "cr": [
        "credited amount",
        "credited",
        "credit",
        "deposit",
        "cr",
        "cr amount",
        "deposit amt",
        "deposits",
    ],
    "bal": ["balance", "bal", "closing balance", "running balance"],
}


def _match_keyword(text: str, keywords: list[str]) -> bool:
    if not text:
        return False
    t_clean = text.lower().strip()
    for kw in keywords:
        pattern = r"\b" + re.escape(kw.lower()) + r"\b"
        if re.search(pattern, t_clean):
            return True
    return False


def _heal_ocr_date(s: str) -> str:
    s = re.sub(r"\b2[oO](\d{2})\b", r"20\1", s)
    s = re.sub(r"\b(\d{2})2[oO]\b", r"\g<1>20", s)
    s = re.sub(r"(?<=[/\.\-\s])[oO](\d)", r"0\1", s)
    s = re.sub(r"(\d)[oO](?=[/\.\-\s])", r"\g<1>0", s)
    s = re.sub(r"\b[oO](\d)(?=[/\.\-\s])", r"0\1", s)
    s = re.sub(r"(?<=[/\.\-\s])[oO]\b", r"0", s)
    return s


def parse_date_flexible(val, default_year: int = None) -> date | None:
    if not val:
        return None
    if isinstance(val, (datetime, date)):
        return val.date() if isinstance(val, datetime) else val

    s = str(val).strip()
    if not s:
        return None

    s = re.sub(
        r"[T\s]\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?.*$", "", s, flags=re.IGNORECASE
    )
    s = re.sub(r"\s+\d{1,2}$", "", s)
    s = s.strip().rstrip(",")
    s_clean = _heal_ocr_date(s)

    def make_date(y, m, d):
        if y < 70:
            y += 2000
        elif y < 100:
            y += 1900
        try:
            return date(y, m, d)
        except (ValueError, TypeError):
            return None

    if re.fullmatch(r"\d{8}", s_clean):
        y_cand = int(s_clean[:4])
        if 1970 <= y_cand <= 2099:
            d = make_date(y_cand, int(s_clean[4:6]), int(s_clean[6:8]))
            if d:
                return d
        d = make_date(int(s_clean[4:8]), int(s_clean[2:4]), int(s_clean[:2]))
        if d:
            return d

    if re.fullmatch(r"\d{6}", s_clean):
        d = make_date(int(s_clean[4:6]), int(s_clean[2:4]), int(s_clean[:2]))
        if d:
            return d

    m_match = re.search(
        r"\b(\d{1,2})[/\.\- ]([A-Za-z]+)[/\.\- ](\d{2,4})\b", s_clean
    )
    if m_match:
        d_val = int(m_match.group(1))
        m_name = m_match.group(2).lower()
        y_val = int(m_match.group(3))
        if m_name in MONTH_NAME_TO_NUM:
            res = make_date(y_val, MONTH_NAME_TO_NUM[m_name], d_val)
            if res:
                return res

    m_first = re.search(
        r"\b([A-Za-z]+)[/\.\- ](\d{1,2})(?:,[ ]*|[/\.\- ])(\d{2,4})\b",
        s_clean,
    )
    if m_first:
        m_name = m_first.group(1).lower()
        d_val = int(m_first.group(2))
        y_val = int(m_first.group(3))
        if m_name in MONTH_NAME_TO_NUM:
            res = make_date(y_val, MONTH_NAME_TO_NUM[m_name], d_val)
            if res:
                return res

    y_m_first = re.search(
        r"\b(\d{4})[/\.\- ]([A-Za-z]+)[/\.\- ](\d{1,2})\b", s_clean
    )
    if y_m_first:
        y_val = int(y_m_first.group(1))
        m_name = y_m_first.group(2).lower()
        d_val = int(y_m_first.group(3))
        if m_name in MONTH_NAME_TO_NUM:
            res = make_date(y_val, MONTH_NAME_TO_NUM[m_name], d_val)
            if res:
                return res

    y_dash = re.search(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", s_clean)
    if y_dash:
        res = make_date(int(y_dash.group(1)), int(y_dash.group(2)), int(y_dash.group(3)))
        if res:
            return res

    y_slash = re.search(r"\b(\d{4})/(\d{1,2})/(\d{1,2})\b", s_clean)
    if y_slash:
        res = make_date(int(y_slash.group(1)), int(y_slash.group(2)), int(y_slash.group(3)))
        if res:
            return res

    d_dash = re.search(r"\b(\d{1,2})-(\d{1,2})-(\d{2,4})\b", s_clean)
    if d_dash:
        res = make_date(int(d_dash.group(3)), int(d_dash.group(2)), int(d_dash.group(1)))
        if res:
            return res

    d_slash = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b", s_clean)
    if d_slash:
        res = make_date(int(d_slash.group(3)), int(d_slash.group(2)), int(d_slash.group(1)))
        if res:
            return res

    d_dot = re.search(r"\b(\d{1,2})\.(\d{1,2})\.(\d{2,4})\b", s_clean)
    if d_dot:
        res = make_date(int(d_dot.group(3)), int(d_dot.group(2)), int(d_dot.group(1)))
        if res:
            return res

    d_space = re.search(r"\b([0-3]?\d) ([0-1]?\d) (\d{4})\b", s_clean)
    if d_space:
        res = make_date(int(d_space.group(3)), int(d_space.group(2)), int(d_space.group(1)))
        if res:
            return res

    if default_year is not None:
        no_y_text = re.search(r"\b(\d{1,2})[/\.\- ]([A-Za-z]+)\b", s_clean)
        if no_y_text and no_y_text.group(2).lower() in MONTH_NAME_TO_NUM:
            return make_date(
                default_year,
                MONTH_NAME_TO_NUM[no_y_text.group(2).lower()],
                int(no_y_text.group(1)),
            )

        no_y_dash = re.search(r"\b(\d{1,2})-(\d{1,2})\b", s_clean)
        if no_y_dash:
            return make_date(default_year, int(no_y_dash.group(2)), int(no_y_dash.group(1)))

        no_y_slash = re.search(r"\b(\d{1,2})/(\d{1,2})\b", s_clean)
        if no_y_slash:
            return make_date(default_year, int(no_y_slash.group(2)), int(no_y_slash.group(1)))

    return None


def clean_float(val) -> float:
    if val is None:
        return 0.0
    s = str(val).strip()
    if not s or s == "-":
        return 0.0

    match = re.search(r"[-+]?[\d,]+\.\d{2,3}(?:\s*(?:CR|DR))?", s, re.IGNORECASE)
    if not match:
        return 0.0

    target = match.group(0).replace(",", "").strip()
    is_negative = target.startswith("-") or "(DR)" in target.upper() or "OD" in target.upper()
    s_clean = re.sub(r"[^\d\.]", "", target)
    try:
        f = float(s_clean)
        return -f if is_negative else f
    except ValueError:
        return 0.0


def extract_strict_decimal(tokens: list[str]) -> float:
    for t in tokens:
        c = (
            t.replace(",", "")
            .replace("+", "")
            .replace("₹", "")
            .replace("Rs.", "")
            .strip()
        )
        c = re.sub(r"(?:CR|DR)$", "", c, flags=re.IGNORECASE).strip()
        if re.match(r"^[-+]?\d+\.\d{2,3}$", c):
            try:
                return abs(round(float(c), 2))
            except ValueError:
                continue
    return 0.0


def _is_footer_or_total_text(text: str) -> bool:
    if not text:
        return False
    t_clean = text.strip()
    return any(
        re.search(pat, t_clean, re.IGNORECASE) for pat in FOOTER_AND_TOTAL_PATTERNS
    )


# ----------------- PARSING ENGINE -----------------
class AnchorStatementParser:

    def __init__(self, log_fn=None):
        self.log = log_fn or (lambda x: None)

    def parse(
        self,
        pdf_path: str,
        password: str = None,
        first_tx_date_str: str = "",
        opening_bal: float = None,
        expected_closing_bal: float = None,
    ) -> tuple[pd.DataFrame, dict]:
        target_date = parse_date_flexible(first_tx_date_str)
        if not target_date:
            raise ValueError(
                f"Could not parse First Transaction Date: '{first_tx_date_str}'."
            )

        with pdfplumber.open(pdf_path, password=password if password else None) as pdf:
            self.log(
                f"Opened PDF: {len(pdf.pages)} pages. Locating anchor date: {target_date.strftime('%d-%m-%Y')}..."
            )

            grid_detected, grid_col_map, anchor_page_idx = self._detect_grid_structure(
                pdf, target_date
            )

            raw_txs = []
            in_table_op_bal = None

            if grid_detected:
                self.log(
                    f"Locked {len(grid_col_map)} table columns from Page {anchor_page_idx}. Extracting rows using verified column mappings..."
                )
                raw_txs, in_table_op_bal = self._extract_all_grid_pages(
                    pdf, anchor_page_idx, grid_col_map, target_date
                )
            else:
                self.log("Document is borderless. Using horizontal coordinate engine...")
                anchor_found, anchor_page_idx, header_cols, anchor_y = (
                    self._locate_anchor_and_headers(pdf, target_date)
                )
                if not anchor_found:
                    raise ValueError(
                        f"Could not find transaction on '{first_tx_date_str}' containing amounts. "
                        "Verify the exact first transaction date in your PDF."
                    )
                raw_txs, in_table_op_bal = self._extract_all_transactions_borderless(
                    pdf, anchor_page_idx, anchor_y, header_cols, target_date.year
                )

        self.log(f"Extracted {len(raw_txs)} transaction rows.")

        effective_op_bal = opening_bal
        if effective_op_bal is None and in_table_op_bal is not None:
            effective_op_bal = in_table_op_bal
            self.log(f"Adopted in-table Opening Balance: ₹{effective_op_bal:,.2f}")

        # Check for reverse chronological order (newest to oldest) and normalize
        parsed_dates = [tx["date_obj"] for tx in raw_txs if tx.get("date_obj")]
        if len(parsed_dates) >= 2:
            descending_count = sum(
                1 for i in range(len(parsed_dates) - 1) if parsed_dates[i] > parsed_dates[i + 1]
            )
            ascending_count = sum(
                1 for i in range(len(parsed_dates) - 1) if parsed_dates[i] < parsed_dates[i + 1]
            )
            if descending_count > ascending_count:
                self.log(
                    "Detected reverse chronological order (newest to oldest). "
                    "Normalizing into chronological sequence for ledger reconciliation..."
                )
                raw_txs.reverse()

        reconciled_rows, calculated_op_bal = self._reconcile(raw_txs, effective_op_bal)

        final_bal = (
            reconciled_rows[-1]["Bal"] if reconciled_rows else calculated_op_bal
        )
        total_dr = sum(r["Dr"] for r in reconciled_rows[1:])
        total_cr = sum(r["Cr"] for r in reconciled_rows[1:])

        verification_info = {
            "opening_bal": calculated_op_bal,
            "final_bal": final_bal,
            "total_dr": total_dr,
            "total_cr": total_cr,
            "tx_count": len(reconciled_rows) - 1,
            "expected_closing_bal": expected_closing_bal,
            "closing_matches": True,
            "diff": 0.0,
        }

        if expected_closing_bal is not None:
            diff = round(final_bal - expected_closing_bal, 2)
            verification_info["diff"] = diff
            verification_info["closing_matches"] = abs(diff) <= 0.05

        return pd.DataFrame(reconciled_rows), verification_info

    def _detect_grid_structure(self, pdf, target_date):
        for page_idx, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            if not tables:
                continue

            for table in tables:
                if len(table) < 2 or len(table[0]) < 4:
                    continue

                header_row = [str(c).lower().replace("\n", " ").strip() for c in table[0]]
                col_indices = {}
                assigned = set()

                for col_name in [
                    "serial_no",
                    "val_date",
                    "chq_ref",
                    "particulars",
                    "dr",
                    "cr",
                    "bal",
                    "date",
                ]:
                    keywords = HEADER_KEYWORDS[col_name]
                    for idx, cell_text in enumerate(header_row):
                        if idx in assigned:
                            continue
                        if _match_keyword(cell_text, keywords):
                            col_indices[col_name] = idx
                            assigned.add(idx)
                            break

                if (
                    "date" in col_indices
                    and "particulars" in col_indices
                    and ("dr" in col_indices or "cr" in col_indices or "bal" in col_indices)
                ):
                    return True, col_indices, page_idx

        return False, {}, 0

    def _extract_all_grid_pages(
        self, pdf, start_page, col_map, target_date
    ):
        raw_txs = []
        started = False
        in_table_op_bal = None

        for page_idx in range(start_page - 1, len(pdf.pages)):
            page = pdf.pages[page_idx]
            tables = page.extract_tables()
            if not tables:
                continue

            for table in tables:
                if len(table) < 1 or len(table[0]) < 4:
                    continue

                for row in table:
                    if not row or not any(row):
                        continue

                    row_str = " ".join([str(c) for c in row if c]).lower()
                    if "transaction details" in row_str or "particulars" in row_str or "credited amount" in row_str:
                        continue
                    if _is_footer_or_total_text(row_str):
                        continue

                    def get_cell(key):
                        idx = col_map.get(key)
                        if idx is not None and idx < len(row) and row[idx] is not None:
                            return str(row[idx]).strip()
                        return ""

                    raw_date = get_cell("date")
                    date_obj = parse_date_flexible(
                        raw_date, default_year=target_date.year
                    )
                    desc = get_cell("particulars").replace("\n", " ")
                    ref = get_cell("chq_ref").replace("\n", "")
                    dr_val = clean_float(get_cell("dr"))
                    cr_val = clean_float(get_cell("cr"))
                    bal_val = clean_float(get_cell("bal"))

                    if "bal" in col_map and col_map["bal"] >= len(row):
                        bal_val = clean_float(row[-1])
                    if "particulars" in col_map and col_map["particulars"] >= len(row):
                        desc = str(row[1]).replace("\n", " ") if len(row) > 1 else ""

                    is_op = (
                        "opening balance" in desc.lower()
                        or "brought forward" in desc.lower()
                        or "balance forward" in desc.lower()
                    )
                    if is_op:
                        op_cand = (
                            abs(bal_val)
                            if abs(bal_val) > 0.0
                            else (abs(cr_val) if abs(cr_val) > 0.0 else abs(dr_val))
                        )
                        if op_cand > 0.0 and in_table_op_bal is None:
                            in_table_op_bal = op_cand
                        if date_obj and date_obj == target_date:
                            started = True
                        continue

                    has_movement = (
                        abs(dr_val) > 0.0 or abs(cr_val) > 0.0 or abs(bal_val) > 0.0
                    )

                    if not started:
                        if date_obj and date_obj == target_date and has_movement:
                            started = True
                        else:
                            continue

                    if not date_obj and not has_movement:
                        continue

                    cheque_val = ""
                    ref_final = ref
                    if ref in ("000000", "0", "-", ""):
                        upi_m = re.search(r"UPI/(?:DR|CR)/(\d{12})", desc)
                        neft_m = re.search(r"(?:CMS|NEFT)[A-Za-z0-9]+", desc)
                        if upi_m:
                            ref_final = upi_m.group(1)
                        elif neft_m:
                            ref_final = neft_m.group(0)
                        else:
                            ref_final = ""
                    elif CHEQUE_6DIGIT_REGEX.match(ref):
                        cheque_val = ref

                    raw_txs.append(
                        {
                            "date_obj": date_obj,
                            "raw_date": raw_date,
                            "ref_no": ref_final,
                            "cheque_no": cheque_val,
                            "particulars_parts": [desc],
                            "dr": abs(dr_val),
                            "cr": abs(cr_val),
                            "bal": bal_val if bal_val != 0.0 else 0.0,
                        }
                    )

        return raw_txs, in_table_op_bal

    def _locate_anchor_and_headers(self, pdf, target_date):
        for page_idx, page in enumerate(pdf.pages, start=1):
            words = page.extract_words(x_tolerance=2, y_tolerance=2)
            if not words:
                continue

            lines = self._group_words_by_line(words)

            for line_idx, line in enumerate(lines):
                detected_date = None
                for i in range(min(5, len(line))):
                    w_text = line[i]["text"].strip()
                    if w_text.isdigit() and len(w_text) <= 4:
                        continue

                    d = parse_date_flexible(w_text)
                    if d:
                        detected_date = d
                        break

                    if i + 1 < len(line):
                        d2 = parse_date_flexible(w_text + " " + line[i + 1]["text"])
                        if d2:
                            detected_date = d2
                            break

                    if i + 2 < len(line):
                        d3 = parse_date_flexible(
                            w_text + " " + line[i + 1]["text"] + " " + line[i + 2]["text"]
                        )
                        if d3:
                            detected_date = d3
                            break

                has_amounts = any(
                    re.search(r"\d+\.\d{2}", w["text"]) for w in line[1:]
                )

                if detected_date and detected_date == target_date and has_amounts:
                    anchor_y = line[0]["top"]

                    header_line = None
                    for prev_idx in range(line_idx - 1, max(-1, line_idx - 8), -1):
                        prev_str = " ".join([w["text"].lower() for w in lines[prev_idx]])
                        if "date" in prev_str and any(
                            _match_keyword(prev_str, HEADER_KEYWORDS[k])
                            for k in ["particulars", "chq_ref", "cr", "dr", "serial_no"]
                        ):
                            header_line = lines[prev_idx]
                            break

                    header_cols = self._build_header_intervals(
                        header_line, page.width
                    )
                    return True, page_idx, header_cols, anchor_y

        return False, 0, {}, 0.0

    def _build_header_intervals(self, header_line, page_width):
        if not header_line:
            return {
                "serial_no": (0, 45),
                "date": (45, 110),
                "val_date": (110, 175),
                "particulars": (175, 380),
                "chq_ref": (380, 430),
                "dr": (430, 495),
                "cr": (495, 555),
                "bal": (555, page_width),
            }

        col_positions = {}
        used_words = set()

        for key in [
            "serial_no",
            "val_date",
            "chq_ref",
            "particulars",
            "dr",
            "cr",
            "bal",
            "date",
        ]:
            for w in header_line:
                if id(w) in used_words:
                    continue
                if _match_keyword(w["text"], HEADER_KEYWORDS[key]):
                    col_positions[key] = w
                    used_words.add(id(w))
                    break

        sorted_cols = sorted(col_positions.items(), key=lambda item: item[1]["x0"])
        intervals = {}
        for i in range(len(sorted_cols)):
            col_name = sorted_cols[i][0]
            curr_w = sorted_cols[i][1]
            x_left = 0 if i == 0 else (sorted_cols[i - 1][1]["x1"] + curr_w["x0"]) / 2
            x_right = (
                page_width
                if i == len(sorted_cols) - 1
                else (curr_w["x1"] + sorted_cols[i + 1][1]["x0"]) / 2
            )
            intervals[col_name] = (x_left, x_right)

        for req in ["date", "particulars"]:
            if req not in intervals:
                intervals[req] = (0, page_width)

        return intervals

    def _bin_words(self, line, intervals):
        data = {k: [] for k in intervals}
        for w in line:
            mid = (w["x0"] + w["x1"]) / 2
            for col_name, (x_left, x_right) in intervals.items():
                if x_left <= mid < x_right:
                    data[col_name].append(w["text"])
                    break
        return data

    def _group_words_by_line(self, words):
        words_sorted = sorted(words, key=lambda w: (round(w["top"], 1), w["x0"]))
        lines = []
        curr = []
        last_top = None

        for w in words_sorted:
            if last_top is None or abs(w["top"] - last_top) <= 3.2:
                curr.append(w)
                last_top = w["top"]
            else:
                lines.append(sorted(curr, key=lambda item: item["x0"]))
                curr = [w]
                last_top = w["top"]
        if curr:
            lines.append(sorted(curr, key=lambda item: item["x0"]))
        return lines

    def _extract_all_transactions_borderless(
        self, pdf, start_page_idx, start_y, header_cols, default_year
    ):
        raw_txs = []
        current_tx = None
        last_seen_date = None
        last_seen_raw_date = ""
        in_table_op_bal = None

        for page_idx in range(start_page_idx - 1, len(pdf.pages)):
            page = pdf.pages[page_idx]
            words = page.extract_words(x_tolerance=2, y_tolerance=2)
            if not words:
                continue

            lines = self._group_words_by_line(words)

            for line in lines:
                if page_idx == start_page_idx - 1 and line[0]["top"] < start_y - 2:
                    continue

                line_full_text = " ".join([w["text"] for w in line]).strip()
                if _is_footer_or_total_text(line_full_text):
                    continue

                binned = self._bin_words(line, header_cols)

                date_tokens = binned.get("date", [])
                line_date = parse_date_flexible(
                    " ".join(date_tokens), default_year=default_year
                )
                if not line_date:
                    for t in line[:4]:
                        if not (t["text"].isdigit() and len(t["text"]) <= 4):
                            cand = parse_date_flexible(t["text"], default_year=default_year)
                            if cand:
                                line_date = cand
                                break

                dr_val = extract_strict_decimal(binned.get("dr", []))
                cr_val = extract_strict_decimal(binned.get("cr", []))
                bal_val = extract_strict_decimal(binned.get("bal", []))

                if bal_val == 0.0 and len(line) >= 2:
                    decimals_on_line = [
                        extract_strict_decimal([w["text"]])
                        for w in line
                        if extract_strict_decimal([w["text"]]) > 0.0
                    ]
                    if len(decimals_on_line) >= 2:
                        bal_val = decimals_on_line[-1]
                        if dr_val == 0.0 and cr_val == 0.0:
                            dr_val = decimals_on_line[-2]

                chq_ref_str = " ".join(binned.get("chq_ref", [])).strip()
                particulars_str = " ".join(binned.get("particulars", [])).strip()

                if _is_footer_or_total_text(particulars_str):
                    continue

                if (
                    "balance forward" in particulars_str.lower()
                    or "brought forward" in particulars_str.lower()
                    or "opening balance" in particulars_str.lower()
                ):
                    op_amt = (
                        bal_val if bal_val > 0.0 else (cr_val if cr_val > 0.0 else dr_val)
                    )
                    if op_amt > 0.0 and in_table_op_bal is None:
                        in_table_op_bal = op_amt
                    if line_date:
                        last_seen_date = line_date
                        last_seen_raw_date = " ".join(date_tokens)
                    continue

                if line_date:
                    last_seen_date = line_date
                    last_seen_raw_date = " ".join(date_tokens)

                has_movement = dr_val > 0.0 or cr_val > 0.0 or bal_val > 0.0

                is_new_tx = False
                tx_date_to_use = None
                raw_date_to_use = ""

                if line_date and (has_movement or chq_ref_str):
                    is_new_tx = True
                    tx_date_to_use = line_date
                    raw_date_to_use = " ".join(date_tokens)
                elif (not line_date) and has_movement and (last_seen_date is not None):
                    is_new_tx = True
                    tx_date_to_use = last_seen_date
                    raw_date_to_use = last_seen_raw_date

                if is_new_tx:
                    if current_tx:
                        raw_txs.append(current_tx)

                    cheque_val = (
                        chq_ref_str if CHEQUE_6DIGIT_REGEX.match(chq_ref_str) else ""
                    )

                    current_tx = {
                        "date_obj": tx_date_to_use,
                        "raw_date": raw_date_to_use,
                        "ref_no": chq_ref_str,
                        "cheque_no": cheque_val,
                        "particulars_parts": (
                            [particulars_str] if particulars_str else []
                        ),
                        "dr": dr_val,
                        "cr": cr_val,
                        "bal": bal_val,
                    }
                elif current_tx:
                    narration_part = particulars_str
                    if (
                        not narration_part
                        and dr_val == 0.0
                        and cr_val == 0.0
                        and bal_val == 0.0
                    ):
                        narration_part = line_full_text

                    if narration_part and not _is_footer_or_total_text(narration_part):
                        current_tx["particulars_parts"].append(narration_part)

        if current_tx:
            raw_txs.append(current_tx)

        return raw_txs, in_table_op_bal

    def _reconcile(
        self,
        raw_txs: list[dict],
        opening_bal: float | None,
        tol: float = 0.05,
    ) -> tuple[list[dict], float]:
        output = []

        if not raw_txs:
            op = float(opening_bal) if opening_bal is not None else 0.0
            return output, op

        if opening_bal is None:
            first_tx = raw_txs[0]
            first_bal = first_tx["bal"]
            first_dr = first_tx["dr"]
            first_cr = first_tx["cr"]

            if first_bal != 0.0:
                if first_dr > 0.0:
                    opening_bal = round(first_bal + first_dr, 2)
                elif first_cr > 0.0:
                    opening_bal = round(first_bal - first_cr, 2)
                else:
                    opening_bal = first_bal
            else:
                opening_bal = 0.0

            self.log(f"Auto-calculated Opening Balance from Tx #1: ₹{opening_bal:,.2f}")

        prev_bal = float(opening_bal)

        first_date = raw_txs[0]["date_obj"] if raw_txs else None
        output.append(
            {
                "Date": first_date,
                "Ref No": "",
                "Cheque No": "",
                "Particulars": "OPENING BALANCE",
                "Dr": 0.0,
                "Cr": 0.0,
                "Bal": prev_bal,
                "PDF Bal": prev_bal,
                "Status": "VERIFIED",
                "Warning": "",
            }
        )

        for tx in raw_txs:
            dr = tx["dr"]
            cr = tx["cr"]
            pdf_bal = tx["bal"]

            if pdf_bal != 0.0 and prev_bal != 0.0:
                delta = round(pdf_bal - prev_bal, 2)
                if (dr > 0.0 and cr == 0.0) or (cr > 0.0 and dr == 0.0):
                    amt = max(dr, cr)
                    if delta < -tol:
                        dr = amt
                        cr = 0.0
                    elif delta > tol:
                        cr = amt
                        dr = 0.0
                elif dr > 0.0 and cr > 0.0:
                    if delta < 0:
                        cr = 0.0
                    elif delta > 0:
                        dr = 0.0

            computed_bal = round(prev_bal - dr + cr, 2)

            if pdf_bal != 0.0:
                if (
                    abs(round(prev_bal - cr + dr, 2) - pdf_bal) <= tol
                    and dr != cr
                ):
                    dr, cr = cr, dr
                    computed_bal = round(prev_bal - dr + cr, 2)

            adj_bal = computed_bal

            output.append(
                {
                    "Date": tx["date_obj"],
                    "Ref No": tx["ref_no"],
                    "Cheque No": tx["cheque_no"],
                    "Particulars": " ".join(tx["particulars_parts"]).strip(),
                    "Dr": dr,
                    "Cr": cr,
                    "Bal": adj_bal,
                    "PDF Bal": pdf_bal,
                    "Status": "VERIFIED",
                    "Warning": "",
                }
            )
            prev_bal = adj_bal

        return output, float(opening_bal)


def export_to_excel_styled(
    df: pd.DataFrame,
    out_path: str,
    account_name: str = "",
    account_no: str = "",
):
    with pd.ExcelWriter(
        out_path,
        engine="openpyxl",
        date_format="DD-MM-YYYY",
        datetime_format="DD-MM-YYYY",
    ) as writer:
        start_row = 1
        if account_name or account_no:
            start_row = 4

        df.to_excel(
            writer, index=False, sheet_name="Ledger", startrow=start_row - 1
        )
        ws = writer.sheets["Ledger"]

        if account_name or account_no:
            ws["A1"] = "Account Holder Name:"
            ws["B1"] = account_name
            ws["A2"] = "Account Number:"
            ws["B2"] = str(account_no)

            label_font = Font(name="Segoe UI", size=10, bold=True, color="1F497D")
            val_font = Font(name="Segoe UI", size=10, bold=True)
            ws["A1"].font = label_font
            ws["A2"].font = label_font
            ws["B1"].font = val_font
            ws["B2"].font = val_font

        header_fill = PatternFill(
            start_color="1F497D", end_color="1F497D", fill_type="solid"
        )
        header_font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
        thin_border = Border(
            left=Side(style="thin", color="D9D9D9"),
            right=Side(style="thin", color="D9D9D9"),
            top=Side(style="thin", color="D9D9D9"),
            bottom=Side(style="thin", color="D9D9D9"),
        )

        header_row_idx = start_row
        for col_idx in range(1, len(df.columns) + 1):
            cell = ws.cell(row=header_row_idx, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for row in ws.iter_rows(
            min_row=header_row_idx + 1,
            max_row=ws.max_row,
            min_col=1,
            max_col=ws.max_column,
        ):
            for cell in row:
                cell.border = thin_border
                col_name = df.columns[cell.column - 1]

                if col_name == "Date":
                    cell.number_format = "DD-MM-YYYY"
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                elif col_name in ["Dr", "Cr", "Bal", "PDF Bal"]:
                    cell.number_format = "#,##0.00"
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                elif col_name in ["Ref No", "Cheque No", "Status"]:
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                elif col_name == "Particulars":
                    cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

        for col_idx, col_name in enumerate(df.columns, 1):
            col_letter = get_column_letter(col_idx)

            if col_name == "Particulars":
                ws.column_dimensions[col_letter].width = 44
            elif col_name == "Date":
                ws.column_dimensions[col_letter].width = 14
            elif col_name in ["Dr", "Cr", "Bal", "PDF Bal"]:
                ws.column_dimensions[col_letter].width = 16
            elif col_name in ["Ref No", "Cheque No"]:
                ws.column_dimensions[col_letter].width = 18
            elif col_name == "Status":
                ws.column_dimensions[col_letter].width = 13
            elif col_name == "Warning":
                ws.column_dimensions[col_letter].width = 20
            else:
                ws.column_dimensions[col_letter].width = 15

        ws.freeze_panes = ws.cell(row=header_row_idx + 1, column=1)


class StatementConverter:

    def __init__(self, log_fn=None):
        self.log = log_fn or (lambda x: None)

    def parse_pdf(
        self,
        pdf_path: str,
        password: str = None,
        first_tx_date: str = "",
        opening_bal: float = None,
        expected_closing_bal: float = None,
    ) -> tuple[pd.DataFrame, dict]:
        parser = AnchorStatementParser(log_fn=self.log)
        return parser.parse(
            pdf_path,
            password=password,
            first_tx_date_str=first_tx_date,
            opening_bal=opening_bal,
            expected_closing_bal=expected_closing_bal,
        )