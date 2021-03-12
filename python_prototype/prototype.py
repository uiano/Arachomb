import httpx
import trio
import bs4 as soup
import googlesearch as google
from typing import Set
import sys
import logging

logging.basicConfig(level=logging.WARN, format="%(levelname)-8s %(message)s", handlers=[
    logging.StreamHandler(sys.stdout),
    logging.FileHandler("debug.log")])


def get_base_url(url: str) -> str:
    return "/".join(url.split("/")[:3])


async def google_domain_search(domain: str) -> Set[str]:
    print(f"expanding {domain}")
    result = set((get_base_url(i) for i in google.search(
        f"site:{domain}", tld="no", lang="no", pause=5) if domain in i))
    return result


async def search_domain(domain: str, visited: Set[str]) -> None:
    to_search = set([domain])
    while to_search:
        async with httpx.AsyncClient(timeout=20) as client:
            current = to_search.pop()
            if current.startswith("mailto:") or current.startswith("phone:") or current.startswith("#"):
                continue
            logging.debug(f"searching {current}")
            try:
                req = await client.get(current)
                await trio.sleep(1)
            except Exception as e:
                logging.error(f"{current},  {e.args}")
                continue
            visited.add(current)
            status = req.status_code
            if "uia.no" not in current and (200 <= status < 300 or status == 304):
                continue
            if 200 <= status < 300 or status == 304:
                text = soup.BeautifulSoup(req.text, "html.parser")
                hrefs = {i.get("href") for i in text.find_all(
                    href=True) if i.get("href") not in visited}
                srcs = {i.get("href") for i in text.find_all(
                    href=True) if i.get("href") not in visited}
                try:
                    to_search |= set(i if i.startswith("http") else get_base_url(
                        current)+i for i in (hrefs | srcs))
                except:
                    logging.critical("Bad URL found,", hrefs | srcs)
            else:
                logging.error(f"Status code {status} from {current}")


async def main() -> None:
    visited = set()
    domains = set(['https://www.uia.no', 'https://cair.uia.no', 'https://home.uia.no', 'https://kompetansetorget.uia.no', 'https://icnp.uia.no', 'http://friluft.uia.no', 'https://passord.uia.no', 'https://windplan.uia.no', 'https://appsanywhere.uia.no', 'https://shift.uia.no',
                   'https://insitu.uia.no', 'https://lyingpen.uia.no', 'https://platinum.uia.no', 'https://dekomp.uia.no', 'https://naturblogg.uia.no', 'https://enters.uia.no', 'https://wisenet.uia.no', 'https://libguides.uia.no', 'http://ciem.uia.no'])  # await google_domain_search("uia.no")

    async with trio.open_nursery() as nurse:
        for domain in domains:
            nurse.start_soon(search_domain, domain, visited)

if __name__ == "__main__":
    trio.run(main)
