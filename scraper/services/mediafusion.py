# import modules
from ui.ui_print import *
import releases
import urllib.parse
name = "mediafusion"

base_url = "https://mediafusion.elfhosted.com"
api_password = ""
request_timeout_sec = "60"
rate_limit_sec = "10"  # minimum number of seconds between requests
manifest_json_url = ""
mediafusion_encrypted_str = ""


def request(func, *args):
    try:
        response = func(*args)
        if hasattr(response, "status_code") and response.status_code != 200:
            ui_print(f'[mediafusion] error {str(response.status_code)}: failed response from mediafusion. {response.content.decode("utf-8")}')
            return []

    except requests.exceptions.Timeout:
        ui_print('[mediafusion] error: request timed out.')
        return []
    except Exception as e:
        ui_print('[mediafusion] error: ' + str(e))
        return []

    try:
        json_response = json.loads(response.content, object_hook=lambda d: SimpleNamespace(**d))
    except Exception as e:
        ui_print('[mediafusion] error: unable to parse response:' + response.content.decode("utf-8") + " " + str(e))
        return []
    return json_response


def get(session: requests.Session, url: str) -> requests.Response:
    ui_print(f"[mediafusion] GET url: {url} ...", ui_settings.debug)
    response = session.get(url, timeout=int(request_timeout_sec))
    ui_print("done", ui_settings.debug)
    return response


def post(session: requests.Session, url: str, body: dict) -> requests.Response:
    ui_print(f"[mediafusion] POST url: {url} with {repr(body)} ...", ui_settings.debug)
    response = session.post(url, json=body, timeout=int(request_timeout_sec))
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
        if not cls.name in active:
            active += [cls.name]


def scrape(query, altquery):
    from scraper.services import active
    if 'mediafusion' not in active:
        return []

    global base_url
    if base_url.endswith('/'):
        base_url = base_url[:-1]

    manual_search = False
    if altquery == "(.*)":
        altquery = query
        manual_search = True
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

    plain_text = ""
    imdb_ids = []
    session = custom_session(get_rate_limit=float(rate_limit_sec), post_rate_limit=float(rate_limit_sec))
    if regex.search(r'(tt[0-9]+)', altquery, regex.I):
        imdb_ids += [regex.search(r'(tt[0-9]+)', altquery, regex.I).group()]
    elif manual_search:
        plain_text = urllib.parse.quote(query)
        try:
            if type == "show":
                url = f"{base_url}/catalog/series/mediafusion_search_series/search={plain_text}.json"
                meta = request(get, session, url)
            else:
                url = f"{base_url}/catalog/movie/mediafusion_search_movies/search={plain_text}.json"
                meta = request(get, session, url)
            # collate all matched IMDB IDs
            imdb_ids += [m.id for m in meta.metas if regex.search(r'(tt[0-9]+)', m.id, regex.I)]
        except:
            try:
                if type == "movie":
                    type = "show"
                    s = 1
                    e = 1
                    url = f"{base_url}/catalog/series/mediafusion_search_series/search={plain_text}.json"
                    meta = request(get, session, url)
                else:
                    type = "movie"
                    url = f"{base_url}/catalog/movie/mediafusion_search_movies/search={plain_text}.json"
                    meta = request(get, session, url)
                # collate all matched IMDB IDs
                imdb_ids += [m.id for m in meta.metas]
            except Exception as e:
                ui_print('[mediafusion] error: could not find IMDB ID. ' + str(e))
                return []
    else:
        ui_print('[mediafusion] error: search missing IMDB ID for query: ' + query)
        return []

    global mediafusion_encrypted_str
    if mediafusion_encrypted_str == "":
        try:
            mediafusion_encrypted_str = _get_encrypted_string(session)
        except Exception as e:
            ui_print('[mediafusion] error: Failed to compute encrypted string. ' + str(e))
            return []

    ui_print(f'[mediafusion]: searching for {type}s with IDs [{str(imdb_ids)}]', ui_settings.debug)
    if type == 'movie':
        return flatten_list([scrape_imdb_movie(session, imdb_id, plain_text) for imdb_id in imdb_ids])
    return flatten_list([scrape_imdb_series(session, imdb_id, s, e) for imdb_id in imdb_ids])


def scrape_imdb_movie(session: requests.Session, imdb_id: str, query_text: str = None) -> list:
    url = f'{base_url}/{mediafusion_encrypted_str}/stream/movie/{imdb_id}.json'
    response = request(get, session, url)

    # fallback to TV series search if we don't get any results
    if not hasattr(response, "streams") or len(response.streams) == 0:
        if query_text is not None and query_text != "":
            try:
                url = f"{base_url}/catalog/series/mediafusion_search_series/search={query_text}.json"
                meta = request(get, session, url)
                return [scrape_imdb_series(session, m.id) for m in meta.metas if regex.search(r'(tt[0-9]+)', m.id, regex.I)]
            except Exception as e:
                ui_print(f'[mediafusion] error: could not find IMDB ID for {query_text}. ' + str(e))
                return []
    return collate_releases_from_response(response)


def scrape_imdb_series(session: requests.Session, imdb_id: str, season: int = 1, episode: int = 1) -> list:
    try:
        url = f'{base_url}/{mediafusion_encrypted_str}/stream/series/{imdb_id}:{str(season)}:{str(episode)}.json'
        return collate_releases_from_response(request(get, session, url))
    except Exception as e:
        ui_print('[mediafusion] error: ' + str(e))
        return []


def collate_releases_from_response(response: requests.Response) -> list:
    scraped_releases = []
    if not hasattr(response, "streams"):
        if response is not None:
            ui_print('[mediafusion] error: ' + repr(response))
        return scraped_releases

    ui_print(f"[mediafusion] found {str(len(response.streams))} streams", ui_settings.debug)
    for result in response.streams:
        if (hasattr(result, "url") and "?info_hash=" in result.url) or hasattr(result, "infoHash"):
            try:
                title = result.description.split("\n💾")[0].replace("📂 ", "")
                info_hash = result.infoHash if hasattr(result, "infoHash") else result.url.split("?info_hash=")[1]
                size = result.behaviorHints.videoSize / 1000000000 \
                    if hasattr(result, "behaviorHints") and hasattr(result.behaviorHints, "videoSize") else 0
                links = ['magnet:?xt=urn:btih:' + info_hash + '&dn=&tr=']
                seeds = int(regex.search(r'(?<=👤 )([0-9]+)', result.description).group()) \
                    if regex.search(r'(?<=👤 )([1-9]+)', result.description) else 0
                source = (regex.search(r'(?<=🔗 )(.*)(?=\n|$)', result.description).group()) \
                    if regex.search(r'(?<=🔗 )(.*)(?=\n|$)', result.description) else "unknown"
                scraped_releases += [releases.release(
                    '[mediafusion: '+source+']', 'torrent', title, [], size, links, seeds)]
            except Exception as e:
                ui_print('[mediafusion] stream parsing error: ' + str(e))
                continue
    return scraped_releases


# gets the mediafusion configuration by looking for a defined manifest.json, otherwise generate one using the standard defaults
def _get_encrypted_string(session: requests.Session) -> str:

    if manifest_json_url.endswith("manifest.json"):
        return manifest_json_url.split("/")[-2]

    # apply standard defaults if no configuration exists
    payload = {
        "streaming_provider": None,
        "selected_catalogs": [],
        "selected_resolutions": ["4k","2160p","1440p","1080p","720p","576p","480p","360p","240p",None],
        "enable_catalogs": False,
        "enable_imdb_metadata": True,
        "max_size": "inf",
        "show_full_torrent_name": True,
        "max_streams_per_resolution": 50,
        "torrent_sorting_priority": [
            {
                "key": "language",
                "direction": "desc"
            },
            {
                "key": "cached",
                "direction": "desc"
            },
            {
                "key": "resolution",
                "direction": "desc"
            },
            {
                "key": "quality",
                "direction": "desc"
            },
            {
                "key": "size",
                "direction": "desc"
            },
            {
                "key": "seeders",
                "direction": "desc"
            },
            {
                "key": "created_at",
                "direction": "desc"
            }
        ],
        "show_language_country_flag": False,
        "nudity_filter": ["Disable"],
        "certification_filter": ["Disable"],
        "language_sorting": [
            "English",
            "Tamil",
            "Hindi",
            "Malayalam",
            "Kannada",
            "Telugu",
            "Chinese",
            "Russian",
            "Arabic",
            "Japanese",
            "Korean",
            "Taiwanese",
            "Latino",
            "French",
            "Spanish",
            "Portuguese",
            "Italian",
            "German",
            "Ukrainian",
            "Polish",
            "Czech",
            "Thai",
            "Indonesian",
            "Vietnamese",
            "Dutch",
            "Bengali",
            "Turkish",
            "Greek",
            "Swedish",
            None
        ],
        "quality_filter": [
            "BluRay/UHD",
            "WEB/HD",
            "DVD/TV/SAT",
            "CAM/Screener",
            "Unknown"
        ],
        "mediaflow_config": None,
        "rpdb_config": None,
        "live_search_streams": False,
        "contribution_streams": False
    }

    if api_password != "":
        payload |= {"api_password": api_password}

    response = request(post,session, f"{base_url}/encrypt-user-data", payload)
    if not hasattr(response, "encrypted_str"):
        raise Exception("[mediafusion] Unable to retrieve encrypted string")
    return response.encrypted_str


def flatten_list(nested_list):
    return [item for sublist in nested_list for item in sublist]