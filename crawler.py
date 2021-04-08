import httpx
import bs4 as soup
import googlesearch as google
from typing import Set
import sys
import json
import logging
import aiosqlite
import datetime
import asyncio

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


def handle_url(url: str, current) -> str:
    https = 's' if "https" in str(current.url) else ''

    if url.startswith("http"):
        return url
    elif url.startswith("#"):
        return str(current.url) + url
    elif url.startswith("//"):
        return "http" + https + ":" + url
    elif url.startswith("/"):
        return "http" + https + "://" + current.url.host + url
    else:
        return "http" + https + "://" + current.url.host + "/" + url


async def search_domain(domain: str, visited: Set[str]) -> None:
    print(f"searching {domain}")
    async with httpx.AsyncClient(timeout=30) as client, aiosqlite.connect(DATABASE_NAME) as con:
        cur = await con.cursor()
        resp = await client.get(domain);
        to_search = set([resp])
        while to_search:
            current = to_search.pop()
            #print(f"searching {current if type(current)==str else current.url}")

            # Get all the URLs in the current page
            text = soup.BeautifulSoup(current.text, "html.parser")
            hrefs = {i.get("href") for i in text.find_all(
                href=True) if i.get("href") not in visited}
            srcs = {i.get("src") for i in text.find_all(
                src=True) if i.get("src") not in visited}
            
            # Loop over the URLs in the current page
            for url in hrefs | srcs:
                if any(url.startswith(i) for i in ["mailto:", "tel:", "javascript:", "#content-middle", "about:blank"]):
                    continue
                if url == "#" or "linkedin" in url: continue

                try:  # getting the content of the URL we're checking currently
                    full_url = handle_url(str(url), current)
                    resp = await client.get(full_url)
                    await asyncio.sleep(0.5)

                    if 200 <= resp.status_code < 300 or resp.status_code == 301 or resp.status_code == 302:
                        if not ".js" in full_url and resp.url.host.endswith("uia.no"):
                            to_search.add(resp)

                        logging.debug(f"******************\n   {full_url}\n   {url}\nIn {str(current.url)}\n{resp.status_code}")

                    else:  # Got an HTTP error
                        await cur.execute("""INSERT INTO errors VALUES (?,?,?,?)""", (str(current.url), full_url, str(resp.status_code), str(datetime.date.today())))
                        #await cur.commit()
                        await con.commit()
                        logging.error(f"******************\n   {full_url}\n   {url}\nIn {str(current.url)}\n{resp.status_code}")


                except httpx.ConnectError as e:  # "Tidsavbruddsperioden for semaforen har utløpt"
                    await cur.execute("""INSERT INTO errors VALUES (?,?,?,?)""", (str(current.url), full_url, str(e.args), str(datetime.date.today())))
                    #await cur.commit()
                    await con.commit()
                    logging.error(f"******************\n   {full_url}\n   {url}\nIn {str(current.url)}\n{e.args}")
                
                except aiosqlite.IntegrityError as e:  # Unique constraint failed
                    # Some page has the same faulty link to the same place??  Ignore
                    logging.error(f"******************\n   {full_url}\n   {url}\nIn {str(current.url)}\nThis error apparently already exists")
                    pass





DATABASE_NAME = "data.db"
async def main() -> None:
    visited = set()
    #domains = set(['https://www.uia.no', 'https://cair.uia.no', 'https://home.uia.no', 'https://kompetansetorget.uia.no', 'https://icnp.uia.no', 'http://friluft.uia.no', 'https://passord.uia.no', 'https://windplan.uia.no', 'https://appsanywhere.uia.no', 'https://shift.uia.no', 'https://insitu.uia.no', 'https://lyingpen.uia.no', 'https://platinum.uia.no', 'https://dekomp.uia.no', 'https://naturblogg.uia.no', 'https://enters.uia.no', 'https://wisenet.uia.no', 'https://libguides.uia.no', 'http://ciem.uia.no'])  # await google_domain_search("uia.no")
    #await cur.executemany("INSERT INTO subdomains VALUES (?,?)",[(i,True) for i in domains])
    con = await aiosqlite.connect(DATABASE_NAME)
    cur = await con.cursor()
    domains = set()
    try:
        for (i,) in await cur.execute("SELECT domain FROM subdomains where should_search=1"):
            print(i)
            domains.add(i)
    except:
        with open("config.json") as file:
            data = json.loads(file.read())
        domains = set(filter(lambda x: data[x], data.keys()))
    print("starting")
    print(domains)
    a,b = await asyncio.wait([search_domain(domain, visited) for domain in domains],return_when=asyncio.ALL_COMPLETED)

if __name__ == "__main__":
        #asyncio.run(main())
        asyncio.get_event_loop().run_until_complete(main())
