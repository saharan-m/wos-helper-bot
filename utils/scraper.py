import aiohttp
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger("discord-bot.scraper")

async def scrape_active_codes():
    """
    Scrapes active WOS gift codes from https://www.wosgiftcodes.com/
    Returns a list of code strings.
    """
    url = "https://www.wosgiftcodes.com/"
    codes = []

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    logger.warning(f"Failed to fetch codes page, status: {resp.status}")
                    return codes

                html = await resp.text()
                soup = BeautifulSoup(html, "html.parser")

                # parse the active codes table
                table = soup.find("table")
                if not table:
                    logger.warning("No table found on page for codes")
                    return codes

                tbody = table.find("tbody")
                if not tbody:
                    logger.warning("No table body found on page")
                    return codes

                for row in tbody.find_all("tr"):
                    code_cell = row.find("td")
                    if code_cell:
                        code_text = code_cell.get_text(strip=True)
                        if code_text:
                            codes.append(code_text)

    except Exception as e:
        logger.error(f"Error scraping codes: {e}")

    return codes
