import httpx
import trio
import bs4 as soup
import googlesearch as google
from typing import Set
import sys
import logging

logging.basicConfig(level=logging.DEBUG, format="%(levelname)-8s %(message)s",handlers=[logging.StreamHandler(sys.stdout),logging.FileHandler("debug.log")])

def get_base_url(url: str)->str:
    return "/".join(url.split("/")[:3])

async def google_domain_search(domain: str) -> Set[str]:
    print(f"expanding {domain}")
    result = set((get_base_url(i) for i in google.search(
        f"site:{domain}", tld="no", lang="no", pause=5) if domain in i))
    print(result)
    return result

async def main() -> None:
    visited = set()
    domains = set(['https://www.uia.no', 'https://cair.uia.no', 'https://home.uia.no', 'https://kompetansetorget.uia.no', 'https://icnp.uia.no', 'http://friluft.uia.no', 'https://passord.uia.no', 'https://windplan.uia.no', 'https://appsanywhere.uia.no', 'https://shift.uia.no', 'https://insitu.uia.no', 'https://lyingpen.uia.no', 'https://platinum.uia.no', 'https://dekomp.uia.no', 'https://naturblogg.uia.no', 'https://enters.uia.no', 'https://wisenet.uia.no', 'https://libguides.uia.no', 'http://ciem.uia.no']) #await google_domain_search("uia.no")

    #TODO: make more async with trio.nursery
    while domains:
        async with httpx.AsyncClient(timeout=20) as client:
            current = domains.pop()
            if current.startswith("mailto:") or current.startswith("#"):  continue
            logging.log(0,f"##################\nsearching {current}")
            try:
                req = await client.get(current)
                await trio.sleep(1)
            except Exception as e:
                logging.error(f"{current},{e}")
                continue
        visited.add(current)
        status = req.status_code

        if 'uia.no' not in current and status in [200, 304]:
            logging.log(0,"#####################")
            continue

        if status in [200, 304]:  #Other "success"-return codes?  All of 2xx?
            text = soup.BeautifulSoup(req.text, 'html.parser')
            
            hrefs = set(map(lambda x: x.get('href'), filter(lambda x: x not in visited, text.find_all(href=True))))
            srcs  = set(map(lambda x: x.get('src'),  filter(lambda x: x not in visited, text.find_all(src=True))))

            try:
                domains |= set(i if i.startswith("http") else get_base_url(current)+i for i in (hrefs | srcs))
            except:
                logging.critical("Bad URL found,", hrefs|srcs, "\n######################")

        else:
            logging.error(f"HTTP {status} in {current}\n#######################")

trio.run(main)
