from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any

import requests
from tools._shared import TIMEOUT, err

ARXIV_API_URL = "https://export.arxiv.org/api/query"


def _arxiv_id(value: str) -> str:
    match = re.search(r"(\d{4}\.\d{4,5}(?:v\d+)?)", value or "")
    if not match:
        raise ValueError("Invalid arXiv ID or URL")
    return match.group(1)


def get_arxiv_bibtex(arxiv_url: str = "") -> dict[str, Any]:
    """Tự động lấy thông tin bài báo arXiv và tạo chuỗi trích dẫn BibTeX chuẩn."""
    try:
        arxiv_id = _arxiv_id(arxiv_url)
        params = {"id_list": arxiv_id}
        response = requests.get(ARXIV_API_URL, params=params, timeout=TIMEOUT)
        response.raise_for_status()

        root = ET.fromstring(response.text)
        namespaces = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom",
        }

        entry = root.find(".//atom:entry", namespaces)
        if entry is None:
            return err("paper_bibtex", ValueError(f"Paper {arxiv_id} not found"))

        title = entry.find("./atom:title", namespaces)
        title_text = " ".join((title.text or "").split()) if title is not None else ""

        authors = [
            (author.find("./atom:name", namespaces).text or "").strip()
            for author in entry.findall("./atom:author", namespaces)
            if author.find("./atom:name", namespaces) is not None
        ]

        published = entry.find("./atom:published", namespaces)
        year = published.text[:4] if published is not None and published.text else "2024"

        first_author_last_name = authors[0].split()[-1].lower() if authors else "unknown"
        cite_key = f"{first_author_last_name}{year}arxiv{arxiv_id.replace('.', '')}"
        authors_str = " and ".join(authors)

        bibtex = (
            f"@article{{{cite_key},\n"
            f"  title={{{title_text}}},\n"
            f"  author={{{authors_str}}},\n"
            f"  journal={{arXiv preprint arXiv:{arxiv_id}}},\n"
            f"  year={{{year}}},\n"
            f"  url={{https://arxiv.org/abs/{arxiv_id}}}\n"
            f"}}"
        )

        return {
            "tool": "paper_bibtex",
            "arxiv_id": arxiv_id,
            "bibtex": bibtex,
            "items": [{
                "title": title_text,
                "url": f"https://arxiv.org/abs/{arxiv_id}",
                "source": "arxiv.org",
                "summary": bibtex,
            }],
        }
    except Exception as exc:
        return err("paper_bibtex", exc)
