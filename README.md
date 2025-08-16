# plex-debrid | ElfHosted

## What is this?

This is an [ElfHosted](https://elfhosted.com) maintenance-and-features fork of the deprecated-and-archived https://github.com/itsToggle/plex_debrid with the following improvements:

## How does it work?

Here's a [detailed guide / walkthrough](https://elfhosted.com/guides/media/stream-from-real-debrid-with-plex/)

## Can I use it without ElfHosted?

Yes, of course :) You can use it just like the original, but you're "on your own", support-wise!

One variation to note is that you'll need to set the ENV vars `CLIENT_ID` and `CLIENT_SECRET` to your own Trakt auth credentials. The ones in the original itstoggle repo expired and have not been refreshed. If you don't care to use Trackt, just set them to something non-null so that the script won't error out.

## Improvements

* ✅ Support [ElfHosted internal URLs](https://elfhosted.com/how-to/connect-apps/) for [Plex](https://elfhosted.com/app/plex/), [Jellyfin](https://elfhosted.com/app/jellyfin/), [Overseerr](https://elfhosted.com/app/overseerr/), [Jackett](https://elfhosted.com/app/jackett/), [Prowlarr](https://elfhosted.com/app/prowlarr/) by default.
* ✅ Trakt OAuth [fixed](https://github.com/elfhosted/plex_debrid/commit/c678fa1e5974a5c666b2fe70d65228c6fdfb4047) (*by passing your own client ID / secret in ENV vars*).
* ✅ Integrated with [Zilean](https://github.com/iPromKnight/zilean/) for scraping [DebridMediaManager](https://debridmediamanager.com/) (DMM) public hashes, defaults to ElfHosted internal Zilean service.
* ✅ Parametize watchlist loop interval (*defaults to 30s instead of hard-coded 30 min*)
* ✅ Single episode downloads [fixed](https://github.com/elfhosted/plex_debrid/pull/1)

## Thanks to these contributors!

<!-- readme: collaborators,contributors -start -->
<table>
	<tbody>
		<tr>
            <td align="center">
                <a href="https://github.com/itsToggle">
                    <img src="https://avatars.githubusercontent.com/u/71379623?v=4" width="64;" alt="itsToggle"/>
                    <br />
                    <sub><b>itsToggle</b></sub>
                </a>
            </td>
            <td align="center">
                <a href="https://github.com/funkypenguin">
                    <img src="https://avatars.githubusercontent.com/u/1524686?v=4" width="64;" alt="funkypenguin"/>
                    <br />
                    <sub><b>funkypenguin</b></sub>
                </a>
            </td>
            <td align="center">
                <a href="https://github.com/sirstudly">
                    <img src="https://avatars.githubusercontent.com/u/12377354?v=4" width="64;" alt="sirstudly"/>
                    <br />
                    <sub><b>sirstudly</b></sub>
                </a>
            </td>
            <td align="center">
                <a href="https://github.com/themegaphoenix">
                    <img src="https://avatars.githubusercontent.com/u/9766462?v=4" width="64;" alt="themegaphoenix"/>
                    <br />
                    <sub><b>themegaphoenix</b></sub>
                </a>
            </td>
            <td align="center">
                <a href="https://github.com/KaceCottam">
                    <img src="https://avatars.githubusercontent.com/u/28381193?v=4" width="64;" alt="KaceCottam"/>
                    <br />
                    <sub><b>KaceCottam</b></sub>
                </a>
            </td>
            <td align="center">
                <a href="https://github.com/KamalF">
                    <img src="https://avatars.githubusercontent.com/u/8170277?v=4" width="64;" alt="KamalF"/>
                    <br />
                    <sub><b>KamalF</b></sub>
                </a>
            </td>
		</tr>
		<tr>
            <td align="center">
                <a href="https://github.com/maspuce">
                    <img src="https://avatars.githubusercontent.com/u/688714?v=4" width="64;" alt="maspuce"/>
                    <br />
                    <sub><b>maspuce</b></sub>
                </a>
            </td>
            <td align="center">
                <a href="https://github.com/Murmiration">
                    <img src="https://avatars.githubusercontent.com/u/26490372?v=4" width="64;" alt="Murmiration"/>
                    <br />
                    <sub><b>Murmiration</b></sub>
                </a>
            </td>
            <td align="center">
                <a href="https://github.com/codevski">
                    <img src="https://avatars.githubusercontent.com/u/1435321?v=4" width="64;" alt="codevski"/>
                    <br />
                    <sub><b>codevski</b></sub>
                </a>
            </td>
            <td align="center">
                <a href="https://github.com/kana2001">
                    <img src="https://avatars.githubusercontent.com/u/71416354?v=4" width="64;" alt="kana2001"/>
                    <br />
                    <sub><b>kana2001</b></sub>
                </a>
            </td>
            <td align="center">
                <a href="https://github.com/master131">
                    <img src="https://avatars.githubusercontent.com/u/1592009?v=4" width="64;" alt="master131"/>
                    <br />
                    <sub><b>master131</b></sub>
                </a>
            </td>
            <td align="center">
                <a href="https://github.com/mcorcoran">
                    <img src="https://avatars.githubusercontent.com/u/1950615?v=4" width="64;" alt="mcorcoran"/>
                    <br />
                    <sub><b>mcorcoran</b></sub>
                </a>
            </td>
		</tr>
		<tr>
            <td align="center">
                <a href="https://github.com/piratsch">
                    <img src="https://avatars.githubusercontent.com/u/106690882?v=4" width="64;" alt="piratsch"/>
                    <br />
                    <sub><b>piratsch</b></sub>
                </a>
            </td>
		</tr>
	<tbody>
</table>
<!-- readme: collaborators,contributors -end -->