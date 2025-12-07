"""
Phase 1 scraper for the CSE T2I Manifesto (AY 2025/26).

- Fetch Manifest page once.
- Parse course rows (code, name, CFU, semester, language, group, detail URL).
- Skip TAB ENHANCE + ENHANCE Alliance rows and final exam.
- Keep only 1st-semester courses.
- For each course, fetch detail page and extract:
    * Course description
    * SSD codes
    * Last alphabetical group row (To == 'ZZZZ') with lecturer
- Write backend/data/courses.json.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import requests
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin


# Manifest URL for CSE (542), track T2I, AY 2025/26, EN, all semesters.
MANIFEST_URL = (
    "https://onlineservices.polimi.it/manifesti/manifesti/controller/"
    "ManifestoPublic.do?evn_default=EVENTO&aa=2025&k_cf=225&k_corso_la=542"
    "&ac_ins=0&k_indir=T2I&lang=EN&tipoCorso=ALL_TIPO_CORSO&semestre=ALL_SEMESTRI"
    "&sede=ALL_SEDI"
)


@dataclass
class CourseManifestEntry:
    code: str
    name: str
    cfu: float
    semester: int
    language: str
    group: str
    detail_url: str


def default_output_path() -> Path:
    """
    Default JSON output: backend/data/courses.json (relative to repo root).
    """
    scripts_dir = Path(__file__).resolve().parent
    backend_dir = scripts_dir.parent
    data_dir = backend_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "courses.json"


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape Polimi Manifesto for CSE T2I first-semester courses."
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=default_output_path(),
        help="Path to the JSON file to write (default: backend/data/courses.json).",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not hit the network, just print what would be done.",
    )

    return parser.parse_args(argv)


# ---------------------
# HTTP helpers
# ---------------------


def fetch_manifest_html(url: str = MANIFEST_URL, timeout: int = 30) -> str:
    """
    Fetch the Manifest HTML once.
    """
    headers = {
        "User-Agent": (
            "polimi-course-advisor/0.1 "
            "(personal academic PoC; polite single-shot scraping)"
        )
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def fetch_course_detail_html(url: str, timeout: int = 30) -> str:
    """
    Fetch a single course detail page.
    """
    headers = {
        "User-Agent": (
            "polimi-course-advisor/0.1 "
            "(personal academic PoC; polite single-shot scraping)"
        )
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text


# ---------------------
# Manifest parsing
# ---------------------


def _norm(text: str) -> str:
    return " ".join(text.split()).strip().lower()


def extract_group_for_row(row: Tag) -> str:
    """
    Look backwards for strings like:
      - 'Courses of the Group XXX'
      - 'Courses to be chosen from Group XXX'
    and return 'XXX'. If none is found, treat the course as MANDATORY.
    """
    for s in row.find_all_previous(string=True):
        if not s:
            continue
        st = s.strip()
        if not st:
            continue
        low = st.lower()
        if "courses of the group" in low or "courses to be chosen from group" in low:
            idx = low.find("group")
            if idx != -1:
                # Use original string slice for nicer casing
                group = st[idx + len("group") :].strip("- :")
            else:
                group = ""
            return group.upper() or "MANDATORY"
    return "MANDATORY"


def extract_language_from_cells(cells: List[Tag]) -> str:
    """
    Try to infer language by scanning cells for the language icon alt text.
    Fall back to 'UNKNOWN'.
    """
    for cell in cells:
        img = cell.find("img")
        if img is not None:
            alt = (img.get("alt") or "").strip().lower()
            if not alt:
                continue
            if "italian and english" in alt or "english and italian" in alt:
                return "EN/IT"
            if "english" in alt:
                return "EN"
            if "italian" in alt:
                return "IT"
    return "UNKNOWN"


def parse_manifest_courses(html: str) -> Tuple[List[CourseManifestEntry], Dict[str, int]]:
    """
    Parse the Manifest HTML and return:
      - a list of first-semester, non-ENHANCE CourseManifestEntry
      - a small stats dict for logging

    Row-based: iterate over <tr> that contain a 6-digit code and an anchor
    with 'codDescr=' in its href.
    """
    soup = BeautifulSoup(html, "html.parser")
    all_rows = soup.find_all("tr")

    courses_by_code: Dict[str, CourseManifestEntry] = {}

    total_rows_with_code = 0
    skipped_enhance_rows = 0
    skipped_no_anchor = 0
    skipped_no_sem = 0
    skipped_final_exam = 0

    for tr in all_rows:
        cells = tr.find_all("td")
        if not cells:
            continue

        row_text = " ".join(c.get_text(" ", strip=True) for c in cells)
        m_code = re.search(r"\b(\d{6})\b", row_text)
        if not m_code:
            continue

        total_rows_with_code += 1
        code = m_code.group(1)

        # Determine group (MANDATORY, APPLICATIONS, GROUNDINGS, METHODS, TAB ENHANCE, etc.)
        group_label = extract_group_for_row(tr)
        group_upper = group_label.upper()

        # Skip TAB ENHANCE block and obvious ENHANCE Alliance rows
        if "TAB ENHANCE" in group_upper:
            skipped_enhance_rows += 1
            continue
        if "course offered by a university of the enhance alliance" in row_text.lower():
            skipped_enhance_rows += 1
            continue

        # Course anchor: href containing 'codDescr=' and non-empty text.
        course_anchor: Optional[Tag] = None
        for a in tr.find_all("a"):
            href = a.get("href") or ""
            if "codDescr=" in href and a.get_text(strip=True):
                course_anchor = a
                break

        if course_anchor is None:
            skipped_no_anchor += 1
            continue

        name = course_anchor.get_text(" ", strip=True)
        href = course_anchor.get("href") or ""
        detail_url = urljoin(MANIFEST_URL, href)

        # Type cell: first cell whose text is one of typical type codes.
        type_index: Optional[int] = None
        for i, cell in enumerate(cells):
            txt = cell.get_text(" ", strip=True)
            if txt in {"M", "L", "I", "T", "V"}:
                type_index = i
                break

        if type_index is None:
            skipped_no_sem += 1
            continue

        type_text = cells[type_index].get_text(" ", strip=True).strip().upper()
        if type_text == "V":
            skipped_final_exam += 1
            continue

        # Semester cell: first cell after type_index whose text starts with a digit or 'A'.
        sem_index: Optional[int] = None
        sem_raw: Optional[str] = None
        for j in range(type_index + 1, len(cells)):
            txt = cells[j].get_text(" ", strip=True)
            if not txt:
                continue
            ch = txt[0]
            if ch.isdigit() or ch == "A":
                sem_index = j
                sem_raw = txt
                break

        if sem_index is None or sem_raw is None:
            skipped_no_sem += 1
            continue

        # Parse semester integer from first character if it's a digit.
        ch0 = sem_raw.strip()[0]
        if not ch0.isdigit():
            # We only keep numeric semesters (1, 2, ...).
            skipped_no_sem += 1
            continue
        semester = int(ch0)

        # CFU: first cell after sem_index whose text has digits.
        cfu: float = 0.0
        for k in range(sem_index + 1, len(cells)):
            txt = cells[k].get_text(" ", strip=True)
            if not txt:
                continue
            if re.search(r"\d", txt):
                try:
                    cfu = float(txt.replace(",", "."))
                except ValueError:
                    cfu = 0.0
                break

        # Language: scan cells for language icon.
        language = extract_language_from_cells(cells)

        entry = CourseManifestEntry(
            code=code,
            name=name,
            cfu=cfu,
            semester=semester,
            language=language,
            group=group_label or "MANDATORY",
            detail_url=detail_url,
        )

        # Dedupe by course code; prefer non-MANDATORY group over MANDATORY.
        existing = courses_by_code.get(code)
        if existing is None:
            courses_by_code[code] = entry
        else:
            if existing.group.upper() == "MANDATORY" and entry.group.upper() != "MANDATORY":
                existing.group = entry.group

    all_courses = list(courses_by_code.values())
    first_sem_courses = [c for c in all_courses if c.semester == 1]

    stats = {
        "total_rows_with_code": total_rows_with_code,
        "total_unique_courses_all_semesters": len(all_courses),
        "skipped_enhance_rows": skipped_enhance_rows,
        "skipped_no_anchor": skipped_no_anchor,
        "skipped_no_sem_or_type": skipped_no_sem,
        "skipped_final_exam": skipped_final_exam,
        "kept_first_semester": len(first_sem_courses),
    }

    return first_sem_courses, stats


# ---------------------
# Detail page parsing
# ---------------------


def extract_description(soup: BeautifulSoup) -> str:
    """
    Extract 'Course Description' text from the detail page.
    """
    label = soup.find(string=re.compile(r"Course Description", re.I))
    if not label:
        return ""

    # Typical structure: <tr><td>Course Description</td><td>long text...</td></tr>
    td = label.find_parent("td")
    if td:
        sib = td.find_next_sibling("td")
        if sib:
            return sib.get_text(" ", strip=True)

    # Fallback: take last <td> in the row.
    tr = label.find_parent("tr")
    if tr:
        tds = tr.find_all("td")
        if len(tds) >= 2:
            return tds[-1].get_text(" ", strip=True)

    return ""


def extract_ssd_codes(soup: BeautifulSoup) -> List[str]:
    """
    Extract SSD codes (e.g. 'MAT/09', 'ING-INF/05') from the SSD table.
    """
    codes: List[str] = []
    seen = set()

    label = soup.find(string=re.compile(r"Scientific-Disciplinary Sector", re.I))
    if not label:
        return codes

    table = label.find_parent("table")
    if not table:
        tr = label.find_parent("tr")
        if tr:
            table = tr.find_parent("table")
    if not table:
        return codes

    for td in table.find_all("td"):
        txt = td.get_text(" ", strip=True)
        for m in re.finditer(r"[A-Z]{2,4}-?[A-Z0-9]*/\d{2}", txt):
            code = m.group(0)
            if code not in seen:
                seen.add(code)
                codes.append(code)

    return codes


def extract_alpha_group_last(soup: BeautifulSoup) -> Optional[Dict[str, str]]:
    """
    Extract the last alphabetical group row (the one whose group cell ends with ZZZZ)
    from the 'Class schedule planning' table.

    We return:
      - 'from': letter before ZZZZ (e.g. 'Q' from '---Q ZZZZ')
      - 'to': 'ZZZZ'
      - 'lecturer': first lecturer name in that row.
    """
    # 1) Find the 'Class schedule planning' anchor
    anchor = soup.find("a", string=re.compile(r"Class schedule planning", re.I))
    if not anchor:
        return None

    # 2) Find the first table after that anchor that looks like the schedule table
    schedule_table: Optional[Tag] = None
    for table in anchor.find_all_next("table"):
        text = table.get_text(" ", strip=True)
        if "Alphabetical group" in text and "Lecturer" in text:
            schedule_table = table
            break

    if schedule_table is None:
        return None

    # 3) Within that table, find the row whose text contains 'ZZZZ'
    target_row: Optional[Tag] = None
    for tr in schedule_table.find_all("tr"):
        tds = tr.find_all("td")
        if not tds:
            continue
        row_text = " ".join(td.get_text(" ", strip=True) for td in tds)
        if "ZZZZ" in row_text:
            target_row = tr
            break

    if target_row is None:
        return None

    tds = target_row.find_all("td")
    group_text = tds[0].get_text(" ", strip=True) if tds else ""

    # Expect something like '---Q ZZZZ'
    m = re.search(r"([A-Z])[^A-Z]*ZZZZ", group_text)
    group_from = m.group(1) if m else ""
    group_to = "ZZZZ"

    # 4) Lecturer: first anchor in that row (these are the lecturer names)
    lecturer = ""
    for a in target_row.find_all("a"):
        name = a.get_text(" ", strip=True)
        if name and "Class schedule planning" not in name:
            lecturer = name
            break

    if not lecturer and not group_from:
        # Probably not a valid schedule row
        return None

    return {
        "from": group_from,
        "to": group_to,
        "lecturer": lecturer,
    }


def parse_course_detail(html: str) -> Tuple[str, List[str], Optional[Dict[str, str]]]:
    """
    Given a detail page HTML, return:
      - description
      - list of SSD codes
      - alpha_group_last dict or None
    """
    soup = BeautifulSoup(html, "html.parser")
    description = extract_description(soup)
    ssd_codes = extract_ssd_codes(soup)
    alpha_last = extract_alpha_group_last(soup)
    return description, ssd_codes, alpha_last


# ---------------------
# Main orchestration
# ---------------------


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)

    print("[scrape_manifest] Target manifest URL:")
    print(f"  {MANIFEST_URL}")
    print(f"[scrape_manifest] Output JSON will be: {args.output}")

    if args.dry_run:
        print("[scrape_manifest] Dry run: no HTTP requests, no parsing.")
        return 0

    print("[scrape_manifest] Fetching manifest HTML...")
    manifest_html = fetch_manifest_html()

    print("[scrape_manifest] Parsing manifest for course rows...")
    courses, stats = parse_manifest_courses(manifest_html)

    print("[scrape_manifest] Manifest parse stats:")
    for k, v in stats.items():
        print(f"  - {k}: {v}")

    print("[scrape_manifest] First-semester, non-ENHANCE courses (preview up to 10):")
    for c in sorted(courses, key=lambda c: (c.semester, c.code))[:10]:
        print(
            f"  {c.code} | {c.name} | sem={c.semester} | CFU={c.cfu} | "
            f"group={c.group} | lang={c.language}"
        )

    print("[scrape_manifest] Fetching and parsing course detail pages...")
    data = []
    detail_ok = 0
    detail_fail = 0

    for idx, entry in enumerate(courses, start=1):
        print(f"  [{idx}/{len(courses)}] {entry.code} -> {entry.detail_url}")
        try:
            html = fetch_course_detail_html(entry.detail_url)
            desc, ssd_codes, alpha_last = parse_course_detail(html)
            detail_ok += 1
        except Exception as e:
            print(f"    !! Error fetching/parsing details for {entry.code}: {e}")
            desc = ""
            ssd_codes = []
            alpha_last = None
            detail_fail += 1

        record = {
            "code": entry.code,
            "name": entry.name,
            "cfu": entry.cfu,
            "semester": entry.semester,
            "language": entry.language,
            "group": entry.group,
            "ssd": ssd_codes,
            "description": desc,
            "alpha_group_last": alpha_last,
        }
        data.append(record)

    print(f"[scrape_manifest] Detail pages parsed OK: {detail_ok}, failed: {detail_fail}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"[scrape_manifest] Wrote {len(data)} course records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
