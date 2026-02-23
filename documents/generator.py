"""
Document generation: fills the Word template with session data and
optionally converts it to PDF via LibreOffice (if available).
"""
import logging
import os
import subprocess
import tempfile
from datetime import datetime
from typing import Optional, Tuple

from docxtpl import DocxTemplate

from config import TEMPLATE_PATH, OUTPUT_DIR
from models import VisaSession

logger = logging.getLogger(__name__)


def _build_context(session: VisaSession) -> dict:
    """Convert a VisaSession into a Jinja2 context dict for docxtpl."""
    crew_list = []
    for idx, member in enumerate(session.crew, start=1):
        crew_list.append({
            "index": idx,
            "full_name": member.full_name,
            "passport_number": member.passport_number,
            "passport_expiry": member.passport_expiry,
            "cdc_number": member.cdc_number,
            "cdc_expiry": member.cdc_expiry,
            "gender": member.gender,
            "date_of_birth": member.date_of_birth,
            "rank": member.rank,
        })

    return {
        "issue_date": datetime.now().strftime("%Y/%m/%d"),
        "visa_type": session.visa_type,
        "ship_name": session.ship.name,
        "ship_owner": session.ship.owner,
        "ship_imo": session.ship.imo_number,
        "ship_reg_date": session.ship.registration_date,
        "origin": session.routing.origin,
        "destination": session.routing.destination,
        "crew": crew_list,
        "crew_count": len(crew_list),
    }


def _convert_to_pdf(docx_path: str) -> Optional[str]:
    """
    Try to convert the docx to PDF using LibreOffice CLI.
    Returns the PDF path on success, None otherwise.
    """
    try:
        result = subprocess.run(
            [
                "libreoffice",
                "--headless",
                "--convert-to", "pdf",
                "--outdir", OUTPUT_DIR,
                docx_path,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            pdf_name = os.path.splitext(os.path.basename(docx_path))[0] + ".pdf"
            return os.path.join(OUTPUT_DIR, pdf_name)
        logger.warning("LibreOffice conversion failed: %s", result.stderr)
    except FileNotFoundError:
        logger.info("LibreOffice not found; skipping PDF conversion.")
    except subprocess.TimeoutExpired:
        logger.warning("LibreOffice conversion timed out.")
    return None


def generate_documents(session: VisaSession, chat_id: int) -> Tuple[str, Optional[str]]:
    """
    Generate a Word document (and optionally a PDF) for the given session.

    Returns:
        (word_path, pdf_path)  — pdf_path is None if conversion failed.
    """
    if not os.path.exists(TEMPLATE_PATH):
        raise FileNotFoundError(
            f"Template not found at {TEMPLATE_PATH}. "
            "Run `python documents/create_template.py` to generate it."
        )

    tpl = DocxTemplate(TEMPLATE_PATH)
    context = _build_context(session)
    tpl.render(context)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"visa_letter_{chat_id}_{timestamp}.docx"
    word_path = os.path.join(OUTPUT_DIR, filename)
    tpl.save(word_path)
    logger.info("Word document saved: %s", word_path)

    pdf_path = _convert_to_pdf(word_path)
    return word_path, pdf_path
