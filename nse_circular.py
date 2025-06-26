# import streamlit as st
# import requests
# import feedparser
# import re


# RSS_URL = "https://nsearchives.nseindia.com/content/RSS/Circulars.xml"
# KEYWORDS = [
#     "MOCK", "ALGO", "COMPLIANCE", "Additional", "colocation",
#     "ip", "userid", "Connectivity", "Messages"
# ]
# IGNORE_DEPARTMENTS = ["SLBS", "CD", "NMF", "CML", "DS", "CMTR", "IPO","COM"]
# MANDATE_DEPARTMENTS = ["MSD"]

# HEADERS = {"User-Agent": "Mozilla/5.0"}

# st.title("NSE Circular Alert Bot")
# # st.caption("Displays circulars based on keyword or mandatory department logic")


# response = requests.get(RSS_URL, headers=HEADERS)
# feed = feedparser.parse(response.text)

# st.subheader("Matching Circulars")
# found = False

# for entry in feed.entries:
#     title = entry.title
#     link = entry.link

#     file_name = link.split("/")[-1]  # e.g., COMP68671.pdf
#     match = re.match(r'^([A-Z]+)', file_name)
#     prefix = match.group(1) if match else "UNKNOWN"


#     keyword_match = any(
#         re.search(rf'\b{k}\b', title, re.IGNORECASE)
#         for k in KEYWORDS if k.strip()
#     )




#     show_this = False
#     #  #Debug info
#     # st.text(f"DEBUG: Title = {title}")
#     # st.text(f"DEBUG: Dept = {prefix}, Keyword Match = {keyword_match}")

#     if keyword_match:

#         if prefix not in IGNORE_DEPARTMENTS:
#             show_this = True
#     else:
   
#         if prefix in MANDATE_DEPARTMENTS:
#             show_this = True


#     if show_this:
#         found = True
#         st.markdown(f"{title}")
#         st.markdown(f"[Read Circular]({link})")
#         st.markdown(f"Published: {entry.get('published', 'N/A')}")
#         st.markdown(f"Department Code: `{prefix}`")
#         st.markdown("---")

# if not found:
#     st.info("No relevant circulars found based on your filters.")


# streamlit run nse_circular.py


import re
import time
import requests
import feedparser
import streamlit as st
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# ------------------- constants -------------------
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Referer": "https://www.mcxindia.com",
    "Accept-Language": "en-US,en;q=0.9",
}

NSE_FEED  = "https://nsearchives.nseindia.com/content/RSS/Circulars.xml"
SEBI_FEED = "https://www.sebi.gov.in/sebirss.xml"
BSE_FEED  = "https://www.bseindia.com/data/xml/notices.xml"
MCX_FEEDS = [
    "https://www.mcxindia.com/en/rssfeed/circulars/general",
    "https://www.mcxindia.com/en/rssfeed/circulars/membership-and-compliance",
    "https://www.mcxindia.com/en/rssfeed/circulars/ctcl",
    "https://www.mcxindia.com/en/rssfeed/circulars/legal",
    "https://www.mcxindia.com/en/rssfeed/circulars/t-s",
]

KEYWORDS = [
    "MOCK", "ALGO", "colocation", "colo", "otr", "Revision",
    "ip", "Monitoring", "userid", "Connectivity", "Messages",
    "audit", "Expiry", "Derivatives", "timeline", "penalty",
    "Investor", "software",
]

IGNORE_DEPARTMENTS  = ["SLBS", "CD", "NMF", "CML", "DS", "CMTR", "IPO"]
MANDATE_DEPARTMENTS = ["MSD", "INSP"]

# ------------------- helpers -------------------

def keyword_match(title: str) -> bool:
    """Return True if any keyword appears as a full word in title."""
    title_lower = title.lower()
    return any(re.search(fr"\b{re.escape(k.lower())}\b", title_lower) for k in KEYWORDS)

def extract_department_code(link: str) -> str:
    """For NSE/BSE PDF links return the leading alpha code, else UNKNOWN."""
    file_part = link.split("/")[-1]
    m = re.match(r"^([A-Z]+)", file_part)
    return m.group(1) if m else "UNKNOWN"

# ---------- selenium helpers for MCX ------------

@st.cache_data(show_spinner=False)
def fetch_mcx_html(url: str) -> str:
    """Fetch page source via headless Chrome to bypass Akamai block."""
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    driver.get(url)
    time.sleep(3)  # allow Akamai redirect + load
    html = driver.page_source
    driver.quit()
    return html

@st.cache_data(show_spinner=False)
def parse_rss_items_from_html(html: str):
    soup = BeautifulSoup(html, "xml")
    items = []
    for item in soup.find_all("item"):
        items.append({
            "title": item.title.text,
            "link": item.link.text,
            "published": item.pubDate.text if item.pubDate else "N/A",
        })
    return items

# ------------------- UI builders -------------------

def section_header(label: str):
    st.markdown(f"## {label}")

# NSE
def display_nse():
    section_header("NSE Circulars")
    try:
        feed = feedparser.parse(requests.get(NSE_FEED, headers=HEADERS).text)
        show_any = False
        for e in feed.entries:
            title, link = e.title, e.link
            dept = extract_department_code(link)
            kw  = keyword_match(title)
            if (kw and dept not in IGNORE_DEPARTMENTS) or (not kw and dept in MANDATE_DEPARTMENTS):
                show_any = True
                st.markdown(f"**{title}**")
                st.markdown(f"[Read Circular]({link})  ")
                st.markdown(f"Published: {e.get('published', 'N/A')} | Dept: `{dept}`")
                st.markdown("---")
        if not show_any:
            st.info("No relevant NSE circulars found.")
    except Exception as err:
        st.error(f"NSE feed failed → {err}")

# SEBI
def display_sebi():
    section_header("SEBI Circulars")
    try:
        feed = feedparser.parse(requests.get(SEBI_FEED, headers=HEADERS).text)
        show_any = False
        for e in feed.entries:
            if keyword_match(e.title):
                show_any = True
                st.markdown(f"**{e.title}**")
                st.markdown(f"[Read Circular]({e.link})")
                st.markdown(f"Published: {e.get('published', 'N/A')}")
                st.markdown("---")
        if not show_any:
            st.info("No relevant SEBI circulars found.")
    except Exception as err:
        st.error(f"SEBI feed failed → {err}")

# BSE
def display_bse():
    section_header("BSE Circulars")
    try:
        feed = feedparser.parse(requests.get(BSE_FEED, headers=HEADERS).text)
        show_any = False
        for e in feed.entries:
            if keyword_match(e.title):
                show_any = True
                st.markdown(f"**{e.title}**")
                st.markdown(f"[Read Circular]({e.link})")
                st.markdown(f"Published: {e.get('published', 'N/A')}")
                st.markdown("---")
        if not show_any:
            st.info("No relevant BSE circulars found.")
    except Exception as err:
        st.error(f"BSE feed failed → {err}")

# MCX
def display_mcx():
    section_header("MCX Circulars (via Selenium)")
    show_any = False
    for url in MCX_FEEDS:
        dept_name = url.rstrip("/").split("/")[-1].replace("-", " ").title()
        try:
            html = fetch_mcx_html(url)
            for item in parse_rss_items_from_html(html):
                title = item["title"]
                if keyword_match(title):
                    show_any = True
                    st.markdown(f"**{title}**")
                    st.markdown(f"[Read Circular]({item['link']})")
                    st.markdown(f"Published: {item['published']} | Dept: `{dept_name}`")
                    st.markdown("---")
        except Exception as err:
            st.error(f"{dept_name} feed failed → {err}")
    if not show_any:
        st.info("No relevant MCX circulars found.")

# ------------------- main layout -------------------

st.set_page_config(page_title="NSE | SEBI | BSE | MCX Circular Alert", layout="wide")

st.title("📰 Market Circular Alert Bot")

nse_tab, sebi_tab, bse_tab, mcx_tab = st.tabs(["NSE", "SEBI", "BSE", "MCX"])

with nse_tab:
    display_nse()
with sebi_tab:
    display_sebi()
with bse_tab:
    display_bse()
with mcx_tab:
    display_mcx()




# streamlit run nse_circular.py
