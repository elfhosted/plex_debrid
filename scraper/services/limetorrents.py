import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
from ui.ui_print import *
import releases

name = "limetorrents"
session = urllib.request.build_opener()


def setup(cls, new=False):
    from scraper.services import setup
    setup(cls, new)


def scrape(query, altquery):
    from scraper.services import active
    scraped_releases = []
    if 'limetorrents' in active:
        ui_print("[limetorrents] using extended query: " + query, ui_settings.debug)

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'}

        url = f'https://www.limetorrents.lol/search/all/' + urllib.parse.quote(query, safe=':/') + '/'
        response = None
        try:
            ui_print("[limetorrents] Sending GET request to URL: " + url, ui_settings.debug)
            request = urllib.request.Request(url, headers=headers)
            response = session.open(request)
            status_code = response.getcode()

            if status_code == 200:
                content = response.read().decode('utf-8', errors='ignore')
                soup = BeautifulSoup(content, 'html.parser')
                torrentList = soup.select('tr:has(td.tdleft)')[4::1]
                if torrentList:
                    ui_print(f"[limetorrents] Found {len(torrentList)} torrent(s)", ui_settings.debug)
                    for count, torrent in enumerate(torrentList):
                        title_element = torrent.select_one('div.tt-name a:nth-of-type(2)')
                        title = title_element.get_text() if title_element else 'Unknown Title'
                        title = regex.sub(r'[^\w\s\.\-]', '', title)  # a good place for this is in the classes.py during the regex bits that checks for matches
                        title = title.replace(" ", '.')
                        title = regex.sub(r'\.+', ".", title)
                        if regex.match(r'(' + altquery.replace('.', r'\.').replace(r"\.*", ".*") + ')', title, regex.I):
                            download_element = torrent.select_one('td.item-icons a[href^="magnet"]')
                            download = download_element['href'] if download_element else '#'

                            link_element = torrent.select_one('div.tt-name a:nth-of-type(1)')
                            link = link_element['href'] if link_element else '#'
                            download = link.replace("http://itorrents.org/torrent/", "magnet:?xt=urn:btih:").replace(".torrent?title=", "&dn=")

                            size_element = torrent.select_one('td.tdnormal:nth-of-type(3)')
                            size = size_element.get_text().strip() if size_element else '0 GB'
                            size_match = regex.search(r'([0-9]*\.?[0-9]+)\s*(KB|MB|GB)', size, regex.I)

                            seeders_element = torrent.select_one('td.tdseed')
                            seeders = int(seeders_element.get_text().strip().replace(",", "")) if seeders_element else 0

                            if size_match:
                                size_value = float(size_match.group(1))
                                size_unit = size_match.group(2).upper()

                                if size_unit == 'KB':
                                    size = size_value / (1024 * 1024)
                                elif size_unit == 'MB':
                                    size = size_value / 1024
                                elif size_unit == 'GB':
                                    size = size_value
                            else:
                                size = float(size_value)

                            scraped_releases += [releases.release('[limetorrents]', 'torrent', title, [], size, [download], seeders=seeders)]
                            ui_print(f"[limetorrents] Scraped release: title={title}, size={size:.2f} GB, seeders={seeders}", ui_settings.debug)
                else:
                    ui_print("[limetorrents] No torrents found", ui_settings.debug)
            else:
                ui_print("[limetorrents] Failed to retrieve the page. Status code: " + str(status_code), ui_settings.debug)

        except Exception as e:
            if hasattr(response, "status_code") and not str(response.status_code).startswith("2"):
                ui_print('[limetorrents] error ' + str(response.status_code) + ': limetorrents is temporarily not reachable')
            else:
                ui_print('[limetorrents] error: unknown error. turn on debug printing for more information.')
            response = None
            ui_print('[limetorrents] error: exception: ' + str(e), ui_settings.debug)
    return scraped_releases