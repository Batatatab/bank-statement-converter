import os
import shutil
import sys
from typing import Any, Dict, List
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract

TESSERACT_CANDIDATE_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.join(
        os.environ.get("LOCALAPPDATA", ""),
        r"Programs\Tesseract-OCR\tesseract.exe",
    ),
]


def resolve_tesseract_cmd() -> str:
  """Detects bundled Tesseract in PyInstaller/local folder with fallback to system paths."""
  # 1. Check bundled runtime directory first (PyInstaller _MEIPASS or local repo)
  base_dir = (
      sys._MEIPASS
      if hasattr(sys, "_MEIPASS")
      else os.path.dirname(os.path.abspath(__file__))
  )
  bundled_dir = os.path.join(base_dir, "Tesseract-OCR")
  bundled_exe = os.path.join(bundled_dir, "tesseract.exe")

  if os.path.exists(bundled_exe):
    tessdata_dir = os.path.join(bundled_dir, "tessdata")
    if os.path.exists(tessdata_dir):
      os.environ["TESSDATA_PREFIX"] = tessdata_dir
    return bundled_exe

  # 2. Check standard system install paths on Windows
  for path in TESSERACT_CANDIDATE_PATHS:
    if os.path.exists(path):
      parent_dir = os.path.dirname(path)
      tessdata_candidate = os.path.join(parent_dir, "tessdata")
      if os.path.exists(tessdata_candidate) and "TESSDATA_PREFIX" not in os.environ:
        os.environ["TESSDATA_PREFIX"] = tessdata_candidate
      return path

  # 3. Check system environment PATH
  which_path = shutil.which("tesseract")
  if which_path:
    return which_path

  raise FileNotFoundError(
      "Tesseract OCR executable not found. Ensure the bundled 'Tesseract-OCR' folder "
      "exists or install Tesseract-OCR to standard Windows paths."
  )


class OCRPageWrapper:
  """Mock pdfplumber Page object returning OCR tokens in standard PDF coordinate space."""

  def __init__(
      self,
      page_number: int,
      width: float,
      height: float,
      words: List[Dict[str, Any]],
  ):
    self.page_number = page_number
    self.width = width
    self.height = height
    self._words = words

  def extract_words(
      self, x_tolerance: float = 2, y_tolerance: float = 2
  ) -> List[Dict[str, Any]]:
    return list(self._words)

  def extract_text(self) -> str:
    return " ".join(w["text"] for w in self._words)


class ScannedPDFProcessor:
  """Renders scanned PDF pages, runs OCR, and normalizes word bounding boxes."""

  def __init__(self, dpi: int = 300, log_fn=None):
    self.dpi = dpi
    self.log = log_fn or (lambda x: None)
    pytesseract.pytesseract.tesseract_cmd = resolve_tesseract_cmd()

  def _preprocess_image(self, img: Image.Image) -> Image.Image:
    """Enhances contrast, sharpens digits, and normalizes DPI artifacts."""
    gray = img.convert("L")
    enhancer = ImageEnhance.Contrast(gray)
    contrasted = enhancer.enhance(2.0)
    sharpened = contrasted.filter(ImageFilter.SHARPEN)
    return sharpened

  def process_page(self, pdf_page) -> OCRPageWrapper:
    pdf_w = float(pdf_page.width)
    pdf_h = float(pdf_page.height)

    # Render raster image from vector page canvas
    page_img_obj = pdf_page.to_image(resolution=self.dpi)
    raw_img = page_img_obj.original

    proc_img = self._preprocess_image(raw_img)
    img_w, img_h = proc_img.size

    scale_x = pdf_w / img_w
    scale_y = pdf_h / img_h

    # PSM 6 enforces single uniform block assumption (preserves ledger grid alignment)
    custom_config = r"--oem 3 --psm 6"
    ocr_data = pytesseract.image_to_data(
        proc_img, config=custom_config, output_type=pytesseract.Output.DICT
    )

    words = []
    n_boxes = len(ocr_data["text"])

    for i in range(n_boxes):
      txt = ocr_data["text"][i].strip()
      try:
        conf = int(ocr_data["conf"][i])
      except (ValueError, TypeError):
        conf = -1

      # Eliminate empty tokens and low-confidence visual noise
      if not txt or conf < 30:
        continue

      left = ocr_data["left"][i]
      top = ocr_data["top"][i]
      width = ocr_data["width"][i]
      height = ocr_data["height"][i]

      # Rescale image pixels back to PDF points
      x0 = round(left * scale_x, 2)
      x1 = round((left + width) * scale_x, 2)
      y0 = round(top * scale_y, 2)
      y1 = round((top + height) * scale_y, 2)

      words.append({
          "text": txt,
          "x0": x0,
          "x1": x1,
          "top": y0,
          "bottom": y1,
          "confidence": conf,
      })

    return OCRPageWrapper(
        page_number=pdf_page.page_number,
        width=pdf_w,
        height=pdf_h,
        words=words,
    )