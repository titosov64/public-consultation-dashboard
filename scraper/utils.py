import re
from bs4 import BeautifulSoup
from typing import List, Dict


def parse_comments(soup: BeautifulSoup) -> List[Dict]:
    """Extract comment entries from the consultation page.
    The portal lists comments in a table where each row (<tr>) contains:
      - an ID cell (first column) with a link to the comment details
      - author, timestamp, and the comment text.
    This function is tolerant to minor HTML changes – it looks for the
    first <table> that contains a header with the word "Comentario".
    Returns a list of dicts with keys: id, text, author, timestamp, source_url.
    """
    comments: List[Dict] = []
    tables = soup.find_all("table")
    target_table = None
    for tbl in tables:
        header = tbl.find("th")
        if header and "comentario" in header.get_text(strip=True).lower():
            target_table = tbl
            break
    if not target_table:
        return comments
    for row in target_table.find_all("tr")[1:]:  # skip header row
        cols = row.find_all("td")
        if len(cols) < 4:
            continue
        # Column 0: ID with link
        link = cols[0].find("a")
        comment_id = link.get_text(strip=True) if link else cols[0].get_text(strip=True)
        source_url = link["href"] if link and link.has_attr("href") else ""
        # Column 1: Author
        author = cols[1].get_text(strip=True)
        # Column 2: Timestamp (format like 'dd/mm/yyyy hh:mm')
        timestamp_raw = cols[2].get_text(strip=True)
        # Convert to ISO format if possible
        timestamp = timestamp_raw
        # Column 3: Comment text (may contain HTML)
        text = cols[3].get_text(separator=" ", strip=True)
        comments.append({
            "id": comment_id,
            "text": text,
            "author": author,
            "timestamp": timestamp,
            "source_url": source_url,
        })
    return comments


def detection_misattribution(text: str) -> bool:
    """Detect if a comment likely belongs to the closed consultation (ID 15).
    Simple heuristic: look for mentions of the number "15" together with
    keywords such as "consulta", "cierre", "15" in the context of the
    portal. This can be refined later with more sophisticated NLP.
    """
    patterns = [
        r"\bconsulta\s*15\b",
        r"\bconsulta\s*#?15\b",
        r"\b15\s*\-\s*consulta",
        r"\b15\b",
    ]
    for pat in patterns:
        if re.search(pat, text, flags=re.IGNORECASE):
            return True
    return False
