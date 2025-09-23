import streamlit as st
import requests
import feedparser
import re

# === Constants ===
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Referer": "https://www.mcxindia.com",
    "Accept-Language": "en-US,en;q=0.9",
}

NSE_FEED = "https://nsearchives.nseindia.com/content/RSS/Circulars.xml"
SEBI_FEED = "https://www.sebi.gov.in/sebirss.xml"
BSE_FEED = "https://www.bseindia.com/data/xml/notices.xml"
MCX_FEEDS = "https://www.mcxindia.com/en/rssfeed/circulars/tech"
KEYWORDS = [
    "MOCK", "ALGO", "colocation","colo","otr","Revision","Futures","Quantity","BEFS",
    "ip","Monitoring", "userid", "Connectivity", "Messages","audit","Expiry","Derivatives",
    "timeline","Penalty","Investor","software","sebi","session","Muhurat","Technology","Market"
]
MCxX_FEEDS = [
    "https://www.mcxindia.com/en/rssfeed/circulars/membership-and-compliance",
    "https://www.mcxindia.com/en/rssfeed/circulars/ctcl",
    "https://www.mcxindia.com/en/rssfeed/circulars/legal",
    "https://www.mcxindia.com/en/rssfeed/circulars/tech",
    "https://www.mcxindia.com/en/rssfeed/circulars/t-s"
]
IGNORE_DEPARTMENTS = ["SLBS", "CD", "NMF", "CML", "DS", "IPO"]
MANDATE_DEPARTMENTS = ["MSD","INSP"]

# === Helper Functions ===
def keyword_match(title):
    return any(
        re.search(rf'\b{k}\b', title, re.IGNORECASE)
        for k in KEYWORDS if k.strip()
    )

def extract_department_code(link):
    file = link.split("/")[-1]
    match = re.match(r'^([A-Z]+)', file)
    return match.group(1) if match else "UNKNOWN"

# === NSE Tab ===
def display_nse():
    st.subheader(" NSE Circulars")
    try:
        response = requests.get(NSE_FEED, headers=HEADERS)
        feed = feedparser.parse(response.text)
        found = False

        for entry in feed.entries:
            title = entry.title
            link = entry.link
            dept = extract_department_code(link)
            match = keyword_match(title)

            show = False
            if match and dept not in IGNORE_DEPARTMENTS:
                show = True
            elif not match and dept in MANDATE_DEPARTMENTS:
                show = True

            if show:
                found = True
                st.markdown(f"### {title}")
                st.markdown(f"[Read Circular]({link})")
                st.markdown(f"Published: {entry.get('published', 'N/A')}")
                st.markdown(f"Department Code: `{dept}`")
                st.markdown("---")

        if not found:
            st.info("No relevant NSE circulars found.")
    except Exception as e:
        st.error(f"Failed to load NSE circulars: {e}")

# === SEBI Tab ===
def display_sebi():
    st.subheader("SEBI Circulars")
    try:
        response = requests.get(SEBI_FEED, headers=HEADERS)
        feed = feedparser.parse(response.text)
        found = False

        for entry in feed.entries:
            title = entry.title
            link = entry.link
            if keyword_match(title):
                found = True
                st.markdown(f"{title}")
                st.markdown(f"[ Read Circular]({link})")
                st.markdown(f"Published: {entry.get('published', 'N/A')}")
                st.markdown("---")

        if not found:
            st.info("No relevant SEBI circulars found.")
    except Exception as e:
        st.error(f"Failed to load SEBI circulars: {e}")

# === BSE Tab ===
def display_bse():
    st.subheader("BSE Circulars")
    try:
        response = requests.get(BSE_FEED, headers=HEADERS)
        feed = feedparser.parse(response.text)
        found = False

        for entry in feed.entries:
            title = entry.title
            link = entry.link
            if keyword_match(title):
                found = True
                st.markdown(f"{title}")
                st.markdown(f"[ Read Circular]({link})")
                st.markdown(f"Published: {entry.get('published', 'N/A')}")
                st.markdown("---")

        if not found:
            st.info("No relevant BSE circulars found.")
    except Exception as e:
        st.error(f"Failed to load BSE circulars: {e}")
# === MCX Tab ===
def display_mcx():
    st.subheader("MCX Circulars")
    found = False

    for feed_url in MCX_FEEDS:
        # Extract department from URL, e.g., "general" from ".../circulars/general"
        department = feed_url.strip("/").split("/")[-1].replace("-", " ").title()

        try:
            response = requests.get(feed_url, headers=HEADERS)
            feed = feedparser.parse(response.text)

            for entry in feed.entries:
                title = entry.title
                link = entry.link

                if keyword_match(title):
                    found = True
                    st.markdown(f"{title}")
                    st.markdown(f"[Read Circular]({link})")
                    st.markdown(f"Published: {entry.get('published', 'N/A')}")
                    st.markdown(f"Department: `{department}`")
                    st.markdown("---")

        except Exception as e:
            st.error(f"Failed to load MCX feed: {feed_url} — {e}")

    if not found:
        st.info("No relevant MCX circulars found.")


# === Streamlit Layout ===
st.set_page_config(page_title="NSE | SEBI | BSE Circular Alerts", layout="wide")
st.title("Circular Alert Bot")

tab1, tab2, tab3, tab4 = st.tabs(["NSE", "SEBI", "BSE", "MCX"])




with tab1:
    display_nse()
with tab2:
    display_sebi()
with tab3:
    display_bse()
with tab4:
    display_mcx()


# streamlit run nse_circular.py
