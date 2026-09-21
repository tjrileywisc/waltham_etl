import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from bs4 import BeautifulSoup
from curl_cffi.requests import Session
from tqdm import tqdm

from connect_db import get_db

logger = logging.getLogger("scraper")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)-8s %(message)s", "%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)
logger.addHandler(handler)

ROOT = "https://waltham.patriotproperties.com"
TIMEOUT = 15  # seconds
PROPERTY_DELAY = 15  # seconds between properties
BACKOFF_BASE = 10  # seconds; doubles each pause: 10, 20, 40, …
IMPERSONATE = "chrome124"
QUERY_LIMIT = 100

_pause_count = 0  # resets to 0 on a successful (non-403) request

SUB_PAGES = {
    "summary": "/summary.asp",
    # TODO: this always seems to be empty
    #"condo_info": "/g_condo.asp",
    "sales_info": "/g_sales.asp",
    "zoning_info": "/g_zoning.asp",
    # TODO: this always seems to be empty
    #"comments_info": "/g_comments.asp",
    "interior_info": "/interior.asp",
    "rooms_and_bedrooms": "/g_rooms.asp",
    "building_sqft": "/g_area.asp",
    "exterior_info": "/exterior.asp",
    "yard_items": "/g_yard.asp",
    "permits": "/g_permits.asp",
    # TODO: this always seems to be empty
    #"similar_properties": "/sales.asp",
}


def _direct_rows(table):
    for child in table.children:
        if not hasattr(child, "name"):
            continue
        if child.name == "tr":
            yield child
        elif child.name in ("tbody", "thead", "tfoot"):
            for grandchild in child.children:
                if hasattr(grandchild, "name") and grandchild.name == "tr":
                    yield grandchild


def _is_value_cell(td) -> bool:
    for tag in td.find_all(True):
        if tag.get("color", "").upper() == "#0000FF":
            return True
    return False


def _row_cells(tr) -> list[str]:
    cells = []
    for td in tr.find_all(["td", "th"], recursive=False):
        if td.find("table"):
            continue
        cells.append(" ".join(td.get_text().split()))
    return cells


def extract_tables(html: str) -> dict:
    """For g_ pages: parse as HTML tables with optional caption, header row, and data rows."""
    soup = BeautifulSoup(html, "html.parser")
    result = {}
    unnamed = 0
    for table in soup.find_all("table"):
        caption_el = table.find("caption")
        caption = " ".join(caption_el.get_text().split()) if caption_el else None

        raw_rows = list(_direct_rows(table))
        if not raw_rows:
            continue

        headers = _row_cells(raw_rows[0])
        if not any(headers):
            continue

        rows = []
        for tr in raw_rows[1:]:
            cells = _row_cells(tr)
            if any(cells):
                rows.append(dict(zip(headers, cells)))

        if not rows:
            continue

        unnamed += 1
        key = caption if caption else f"table_{unnamed}"
        result[key] = rows

    return result


def extract_kv(html: str) -> dict:
    """For non-g_ pages: pair non-blue (key) cells with following blue (value) cells."""
    soup = BeautifulSoup(html, "html.parser")
    result = {}
    pending_key = None
    for table in soup.find_all("table"):
        for tr in _direct_rows(table):
            for td in tr.find_all(["td", "th"], recursive=False):
                if td.find("table"):
                    continue
                text = " ".join(td.get_text().split())
                if not text:
                    continue
                if _is_value_cell(td):
                    if pending_key is not None:
                        result[pending_key] = text
                        pending_key = None
                else:
                    pending_key = text
    return result


def fetch_text(session: Session, url: str) -> str:
    global _pause_count
    while True:
        resp = session.get(url, timeout=TIMEOUT)
        if resp.status_code != 403:
            _pause_count = 0
            return resp.text
        _pause_count += 1
        wait = BACKOFF_BASE * (2 ** (_pause_count - 1))
        logger.warning(f"403 on {url} — pausing for {wait}s (backoff #{_pause_count})")
        time.sleep(wait)


def fetch_page(session: Session, url: str, use_kv: bool = False) -> dict:
    html = fetch_text(session, url)
    soup = BeautifulSoup(html, "html.parser")
    frames = soup.find_all("frame")
    extract = extract_kv if use_kv else extract_tables

    if not frames:
        return extract(html)

    base = url.split("?")[0].rsplit("/", 1)[0] + "/"
    frame_urls = [
        src if (src := frame.get("src", "")).startswith("http") else base + src
        for frame in frames
        if (src := frame.get("src", ""))
        and not src.lower().endswith(".htm")
        and "-middle.asp" not in src.lower()
    ]

    result = {}
    for fu in frame_urls:
        fhtml = fetch_text(session, fu)
        result.update(extract(fhtml))
    return result


def scrape_property(prop_id: str, cama_id: str) -> dict:
    with Session(impersonate=IMPERSONATE) as session:
        fetch_text(session, ROOT)
        html = fetch_text(session, f"{ROOT}/search-middle-ns.asp")
        soup = BeautifulSoup(html, "html.parser")
        form = soup.find("form")

        if not form:
            return {"prop_id": prop_id, "cama_id": cama_id, "error": "search form not found"}

        form_data = {}
        for inp in form.find_all("input"):
            name = inp.get("name")
            if name:
                form_data[name] = inp.get("value", "")
        for sel in form.find_all("select"):
            name = sel.get("name")
            if name:
                selected = sel.find("option", selected=True)
                form_data[name] = selected["value"] if selected else ""

        # ASP.NET hides __VIEWSTATE / __EVENTVALIDATION etc. — sometimes outside <form>
        for inp in soup.find_all("input", attrs={"name": True}):
            name = inp["name"]
            if "__" in name and name not in form_data:
                form_data[name] = inp.get("value", "")

        parcel_field = next(
            (k for k in form_data if "parcel" in k.lower() or "pid" in k.lower()), None
        )
        if parcel_field:
            form_data[parcel_field] = prop_id

        action = form.get("action", "/SearchResults.asp")
        if not action.startswith("http"):
            action = f"{ROOT}/{action.lstrip('/')}"

        method = form.get("method", "post").lower()
        if method == "post":
            session.post(action, data=form_data, timeout=TIMEOUT)
        else:
            session.get(action, params=form_data, timeout=TIMEOUT)

        data: dict = {"prop_id": prop_id, "cama_id": cama_id}
        for key, path in SUB_PAGES.items():
            url = f"{ROOT}{path}?AccountNumber={cama_id}"
            use_kv = not path.lstrip("/").startswith("g_")
            try:
                data[key] = fetch_page(session, url, use_kv=use_kv)
            except Exception as exc:
                data[key] = {"error": str(exc)}

        return data


def main() -> None:
    con = get_db()
    query = f"""
    select "PROP_ID", "CAMA_ID"
    from "M308Assess_CY26_FY26"
    limit {QUERY_LIMIT}
    """
    df = pd.read_sql(query, con)

    start = time.time()
    results = []

    bar = tqdm(total=len(df), desc="scraping")
    for i, row in enumerate(df.itertuples(index=False)):
        results.append(scrape_property(str(row.PROP_ID), str(row.CAMA_ID)))
        bar.update(1)
        if i < len(df) - 1:
            time.sleep(PROPERTY_DELAY)
    bar.close()

    out_path = "assessments/output.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Done. Written to {out_path}. Total time {time.time() - start:.2f}s")


if __name__ == "__main__":
    main()
