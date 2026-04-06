from langchain.messages import AIMessage
from langchain_core.documents import Document
from playwright.async_api import async_playwright
from utils.logger import getLogger
from ..state import State
from .common import DOWNLOADED_FILES
import requests
import re
import os


_logger = getLogger(__name__)


def is_valid_link(href: str, valid_extensions: list[str], valid_content_types: list[str]) -> bool:
    if not href or not any(ext in href.lower() for ext in valid_extensions):
        return False
    response = requests.head(href, allow_redirects=True)
    content_type = response.headers.get('Content-Type', '')
    length = response.headers.get('Content-Length', 'unknown')
    length = int(length) / 1024 / 1024 if length != 'unknown' else 'unknown'  # Convert to MB
    if content_type in valid_content_types:
        _logger.info(f"size: {length:.2f} MB, url: {href}")
        return True
    return False


def parse_file_links(link: str, extensions: list[str]) -> str:
    lower_link = link.lower()
    for ext in extensions:
        if ext in lower_link:
            url = link.split(ext)[0] + ext
            match = re.split(r'http[s]?://', url)
            if len(match) > 1:
                if "http://" + match[1] in url:
                    return "http://" + match[1]
                elif "https://" + match[1] in url:
                    return "https://" + match[1]
    return ""


def download_file(url: str, save_path: str):
    if os.path.exists(save_path):
        _logger.info(f"File already exists: {save_path}")
        return True
    try:
        _logger.info(f"Downloading {url}")
        with requests.get(url, stream=True, timeout=15) as r:
            r.raise_for_status()
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return True
    except Exception as e:
        _logger.error(f"Error downloading {url}: {e}")
        return False

async def scrape_sources(state: State):
  """Scrape web source links to get more accurate details"""
  urls=state["citations"] or []
  async with async_playwright() as p:
      browser = await p.chromium.launch(headless=True)
      page = await browser.new_page()
      valid_content_types = [
          "application/pdf", 
          "text/csv"
      ]
      valid_extensions = [".pdf", ".csv"]
      file_urls = []
      documents: list[Document] = []

      for url in urls:
        if "facebook" in url or re.match(f".*({'|'.join(valid_extensions)}$)", url):
           _logger.info(f"skipped: {url}")
           continue
           
        try:
            # Navigate to link
          _logger.info(f"Navigating to {url}")
          await page.goto(url, timeout=5000)

          # Wait for the file table to load
          await page.wait_for_selector("table", timeout=5000)
          
          # Extract all links that contain valid file extensions
          links = await page.query_selector_all("a")
          _logger.info(f"Scanning {len(links)} links on the page.")

          # extract all tables
          table_handles = await page.query_selector_all("table")
          for handle in table_handles:
            text_content = await handle.inner_text()
            if text_content.strip():
              chunks = [Document(page_content=f"Scraped HTML Table Data:\n{text_content}", metadata={"source": url})] #text_splitter.create_documents([text_content], metadatas=[{"source": url}])
              documents.extend(chunks)

          for link in links:
              href = await link.get_attribute("href")
              # _logger.info(f"Checking link: {href}")
              if href:
                  if is_valid_link(href, valid_extensions, valid_content_types):
                      file_urls.append(href)
                  else:
                      query_param_url=parse_file_links(href, extensions=valid_extensions)
                      if is_valid_link(query_param_url, valid_extensions, valid_content_types):
                          file_urls.append(query_param_url)
        except Exception as e:
           _logger.error(e)
           pass

      _logger.info(f"Found {len(file_urls)} data files with valid content-type.")
          
      await browser.close()
      DOWNLOADED_FILES.mkdir(parents=True, exist_ok=True)

      # for url in file_urls:
      #     download_file(url, f"{DOWNLOADED_FILES}/{url.split('/')[-1]}")

      all_docs = state["documents"] or []
      for doc in documents:
        for item in all_docs:
          #  _logger.info(f"{doc.metadata.get('source')} == {item['source']}")
           if doc.metadata.get("source") == item["source"]:
              item["page_content"] = f"${item['page_content']}\n{doc.page_content}"

      _logger.info(f"scraped html table: {len(documents)}")

      return {
        "documents": all_docs,
        "messages": [AIMessage(content="done scraping urls")]
      }

