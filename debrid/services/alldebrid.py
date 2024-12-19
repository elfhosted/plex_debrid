#import modules
from base import *
from ui.ui_print import *
import releases

# (required) Name of the Debrid service
name = "All Debrid"
short = "AD"
# (required) Authentification of the Debrid service, can be oauth aswell. Create a setting for the required variables in the ui.settings_list. For an oauth example check the trakt authentification.
api_key = ""
# Define Variables
rate_limit_sec = 1 / 12  # minimum number of seconds between requests
session = custom_session(get_rate_limit=rate_limit_sec, post_rate_limit=rate_limit_sec)

def setup(cls, new=False):
    from debrid.services import setup
    setup(cls,new)

# Error Log
def logerror(response):
    if not response.status_code == 200:
        ui_print("[alldebrid] error "+str(response.status_code)+": " + str(response.content), debug=ui_settings.debug)
    if 'error' in str(response.content):
        try:
            response2 = json.loads(response.content, object_hook=lambda d: SimpleNamespace(**d))
            ui_print("[alldebrid] error "+str(response.status_code)+": " + response2.data[0].error.message)
        except:
            try:
                response2 = json.loads(response.content, object_hook=lambda d: SimpleNamespace(**d))
                ui_print("[alldebrid] error "+str(response.status_code)+": " + response2.error.message)
            except:
                ui_print("[alldebrid] error "+str(response.status_code)+": unknown error")
    if response.status_code == 401:
        ui_print("[alldebrid] error: 401: alldebrid api key does not seem to work. check your alldebrid settings.")

# Get Function
def get(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
        'authorization': 'Bearer ' + api_key}
    try:
        ui_print("[alldebrid] (get): " + url, debug=ui_settings.debug)
        response = session.get(url + '&agent=plex_debrid', headers=headers)
        logerror(response)
        response = json.loads(response.content, object_hook=lambda d: SimpleNamespace(**d))
    except Exception as e:
        ui_print("[alldebrid] error: (json exception): " + str(e), debug=ui_settings.debug)
        response = None
    return response

# Post Function
def post(url, data):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
        'authorization': 'Bearer ' + api_key}
    try:
        ui_print("[alldebrid] (post): " + url + " with data " + repr(data), debug=ui_settings.debug)
        response = session.post(url, headers=headers, data=data)
        logerror(response)
        response = json.loads(response.content, object_hook=lambda d: SimpleNamespace(**d))
    except Exception as e:
        ui_print("[alldebrid] error: (json exception): " + str(e), debug=ui_settings.debug)
        response = None
    return response

# (required) Download Function.
def download(element, stream=True, query='', force=False):
    cached = element.Releases
    if query == '':
        query = element.deviation()
    for release in cached[:]:
        # if release matches query
        if regex.match(r'(' + query + ')', release.title, regex.I) or force:
            debrid_uncached = True
            for i, rule in enumerate(element.version.rules):
                if rule[0] == "cache status" and rule[1] in ['requirement', 'preference'] and rule[2] == "cached":
                    debrid_uncached = False
                    break
            if not debrid_uncached:  # Cached Download Method for AllDebrid
                torrent_id = None
                try:
                    url = 'https://api.alldebrid.com/v4/magnet/upload?magnets[]=' + release.download[0]
                    response = get(url)
                    if not hasattr(response, "status") or response.status != "success":
                        ui_print(f"[alldebrid] failed to add release {release.title}.")
                        continue
                    if not hasattr(response, "data") or not hasattr(response.data.magnets[0], "id"):
                        ui_print(f"[alldebrid] failed to add release {release.title}.")
                        if hasattr(response.data.magnets[0], "error"):
                            ui_print(f"[alldebrid] error: {response.data.magnets[0].error.message}.")
                        continue

                    # check if release is instantly available
                    torrent_id = response.data.magnets[0].id
                    url = 'https://api.alldebrid.com/v4.1/magnet/status?id=' + str(torrent_id)
                    response = get(url)
                    if response.status != "success" or response.data.magnets.status != "Ready":
                        raise Exception(f"{release.title} is in status '{response.data.magnets.status}' (not cached).")

                    saved_links = []
                    for link in get_all_links_from_files(response.data.magnets.files):
                        url = 'https://api.alldebrid.com/v4/link/unlock?link=' + requests.utils.quote(link)
                        response = get(url)
                        if response.status != 'success':
                            raise Exception(f"{response.status} response on unlock link for {release.title}.")
                        saved_links += [requests.utils.quote(link)]

                    if len(saved_links) > 0:
                        saved_links = '&links[]='.join(saved_links)
                        url = 'https://api.alldebrid.com/v4/user/links/save?links[]=' + saved_links
                        response = get(url)
                        if response.status != "success":
                            raise Exception(f"failed to save links for {release.title}.")
                        ui_print(f"[alldebrid] adding cached release: {release.title}")
                        return True
                    else:
                        raise Exception(f"no files found for {release.title}")
                except Exception as e:
                    ui_print("[alldebrid] " + str(e) + " Looking for another release.")
                    if torrent_id is not None:
                        get('https://api.alldebrid.com/v4/magnet/delete?id=' + str(torrent_id))
            else:
                # Uncached Download Method for AllDebrid
                url = 'https://api.alldebrid.com/v4/magnet/upload?magnets[]=' + release.download[0]
                response = get(url)
                if not hasattr(response, "status") or response.status != "success":
                    ui_print(f"[alldebrid] failed to add release {release.title}.")
                    continue
                ui_print('[alldebrid] adding uncached release: ' + release.title)
                return True
    return False
    # (required) Check Function

def check(element, force=False):
    if force:
        wanted = ['.*']
    else:
        wanted = element.files()
    unwanted = releases.sort.unwanted
    wanted_patterns = list(zip(wanted, [regex.compile(r'(' + key + ')', regex.IGNORECASE) for key in wanted]))
    unwanted_patterns = list(zip(unwanted, [regex.compile(r'(' + key + ')', regex.IGNORECASE) for key in unwanted]))
    for release in element.Releases[:]:
        release.wanted_patterns = wanted_patterns
        release.unwanted_patterns = unwanted_patterns
        release.maybe_cached += ['AD']  # we won't know if it's cached until we attempt to download it


def get_all_links_from_files(files):
    links = []
    for file in files:
        if hasattr(file, "e"):  # is folder
            links += get_all_links_from_files(file.e)
        elif hasattr(file, "l"):  # is a file
            links += [file.l]
    return links
