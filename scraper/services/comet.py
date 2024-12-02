# import modules
from ui.ui_print import *
import releases
import base64
import json
name = "comet"

request_timeout_sec = "60"
rate_limit_sec = "10"  # minimum number of seconds between requests
manifest_json_url = ""  # this is mandatory otherwise non-cached searches will fail without a valid debrid account


def request(func, *args):
    try:
        response = func(*args)
        if hasattr(response, "status_code") and response.status_code != 200:
            ui_print(f'[comet] error {str(response.status_code)}: failed response from comet. {response.content.decode("utf-8")}')
            return []

    except requests.exceptions.Timeout:
        ui_print('[comet] error: request timed out.')
        return []
    except Exception as e:
        ui_print('[comet] error: ' + str(e))
        return []

    try:
        json_response = json.loads(response.content, object_hook=lambda d: SimpleNamespace(**d))
    except Exception as e:
        if hasattr(response, "content"):
            ui_print('[comet] error: unable to parse response:' + response.content.decode("utf-8"))
        else:
            ui_print('[comet] error: unable to parse response.')
        ui_print('[comet] ' + str(e), ui_settings.debug)
        return []
    return json_response


def get(session: requests.Session, url: str) -> requests.Response:
    ui_print(f"[comet] GET url: {url} ...", ui_settings.debug)
    response = session.get(url, timeout=int(request_timeout_sec))
    ui_print("done", ui_settings.debug)
    return response


def setup(cls, new=False):
    from settings import settings_list
    from scraper.services import active
    settings = []
    for category, allsettings in settings_list:
        for setting in allsettings:
            if setting.cls == cls:
                settings += [setting]
    if settings == []:
        if not cls.name in active:
            active += [cls.name]
    back = False
    if not new:
        while not back:
            print("0) Back")
            indices = []
            for index, setting in enumerate(settings):
                print(str(index + 1) + ') ' + setting.name)
                indices += [str(index + 1)]
            print()
            if settings == []:
                print("Nothing to edit!")
                print()
                time.sleep(3)
                return
            choice = input("Choose an action: ")
            if choice in indices:
                settings[int(choice) - 1].input()
                if not cls.name in active:
                    active += [cls.name]
                back = True
            elif choice == '0':
                back = True
    else:
        for setting in settings:
            if setting.name == "Comet Scraper Parameters":
                setting.setup()
        if cls.name not in active:
            active += [cls.name]


def scrape(query, altquery):
    from scraper.services import active
    if 'comet' not in active:
        return []

    url_search = regex.search(r"(https?:\/\/[^\/]+).*manifest.json", manifest_json_url, regex.I)
    if not url_search:
        ui_print('[comet] error: the scraper parameters URL is not configured correctly: ' + manifest_json_url)
        return []
    base_url = url_search.group(1)

    if altquery == "(.*)":
        altquery = query
    type = ("show" if regex.search(
        r'(S[0-9]|complete|S\?[0-9])', altquery, regex.I) else "movie")

    if type == "show":
        s = (regex.search(r'(?<=S)([0-9]+)', altquery, regex.I).group()
             if regex.search(r'(?<=S)([0-9]+)', altquery, regex.I) else None)
        e = (regex.search(r'(?<=E)([0-9]+)', altquery, regex.I).group()
             if regex.search(r'(?<=E)([0-9]+)', altquery, regex.I) else None)
        if s is None or int(s) == 0:
            s = 1
        if e is None or int(e) == 0:
            e = 1

    if regex.search(r'(tt[0-9]+)', altquery, regex.I):
        imdb_id = regex.search(r'(tt[0-9]+)', altquery, regex.I).group()
    else:
        ui_print('[comet] error: search missing IMDB ID for query: ' + query)
        return []

    ui_print(f'[comet]: searching for {type}s with ID={imdb_id}', ui_settings.debug)
    session = custom_session(get_rate_limit=float(rate_limit_sec), post_rate_limit=float(rate_limit_sec))
    if type == 'movie':
        return scrape_imdb_movie(session, base_url, _get_base64_config(), imdb_id)
    return scrape_imdb_series(session, base_url, _get_base64_config(), imdb_id, s, e)


def scrape_imdb_movie(session: requests.Session, base_url: str, base64_config: str, imdb_id: str) -> list:
    return collate_releases_from_response(request(get, session, f'{base_url}/{base64_config}/stream/movie/{imdb_id}.json'))


def scrape_imdb_series(session: requests.Session, base_url: str, base64_config: str, imdb_id: str, season: int = 1, episode: int = 1) -> list:
    return collate_releases_from_response(request(get, session, f'{base_url}/{base64_config}/stream/series/{imdb_id}:{str(season)}:{str(episode)}.json'))


def collate_releases_from_response(response: requests.Response) -> list:
    scraped_releases = []
    if not hasattr(response, "streams"):
        if response is not None:
            ui_print('[comet] error: ' + repr(response))
        return scraped_releases

    ui_print(f"[comet] found {str(len(response.streams))} streams", ui_settings.debug)
    for result in response.streams:

        if hasattr(result, "description") and (result.description == "Invalid Comet config." or regex.search(r'(?<=Invalid )(.*)(?= account)', result.description)):
            ui_print(f'[comet] error: {result.description}')
            return scraped_releases
        elif not hasattr(result, "description"):
            ui_print(f'[comet] error: Missing description in result')
            continue
        elif not hasattr(result, "url") and not hasattr(result, "infoHash"):
            ui_print(f'[comet] error: Missing url/infoHash in result {result.description}')
            continue

        try:
            title = result.description.split("\n")[0]
            infohash = False
            if hasattr(result, "infoHash"):
                infohash = result.infoHash
            else:
                infohash_pattern = regex.compile(r"(?!.*playback\/)[a-fA-F0-9]{40}")
                infohash = infohash_pattern.search(result.url).group()

            if not infohash:
                ui_print(f'[comet]: error: infohash not found for title: {title}')
                continue

            size = int(result.torrentSize) / 1000000000 if hasattr(result, "torrentSize") else 0
            links = ['magnet:?xt=urn:btih:' + infohash + '&dn=&tr=']
            seeds = 0  # not available
            source = regex.search(r'(?<=🔎 )(.*)(?=\n|$)', result.description).group() \
                if regex.search(r'(?<=🔎 )(.*)(?=\n|$)', result.description) else "unknown"
            scraped_releases += [releases.release(
                '[comet: '+source+']', 'torrent', title, [], size, links, seeds)]
        except Exception as e:
            ui_print('[comet] stream parsing error: ' + str(e))
            continue
    return scraped_releases


# Retrieves the base64 configuration parameters from manifest_json_url
# If it isn't defined, then create a default profile without a debrid key
def _get_base64_config() -> str:

    if manifest_json_url.endswith("manifest.json"):
        return manifest_json_url.split("/")[-2]

    return base64.b64encode(json.dumps({
        "indexers": ["bitsearch","eztv","thepiratebay","therarbg","yts"],
        "maxResults": 0,
        "resolutions": ["All"],
        "languages": ["All"],
        "debridService": "realdebrid",
        "debridApiKey": "",
        "debridStreamProxyPassword": ""
    }).encode("utf-8")).decode("utf-8")
