import httpx
import trio
import bs4 as soup
import googlesearch as google
from typing import Set
import sys
import logging
import aiosqlite
import datetime
import trio_asyncio
from trio_asyncio import aio_as_trio

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
    url = str(url)

    if url.startswith("http"):
        return url
    elif url.startswith("#"):
        return "http" + https + "://" + current.url + url
    elif url.startswith("//"):
        return "http" + https + "://" + current.url.host + url[1:]
    elif url.startswith("/"):
        return "http" + https + "://" + current.url.host + url
    else:
        return "http" + https + "://" + current.url.host + "/" + url


async def search_domain(domain: str, visited: Set[str]) -> None:
    async with httpx.AsyncClient(timeout=30) as client, aiosqlite.connect(DATABASE_NAME) as con:
        cur = await aio_as_trio(con.cursor)()
        resp = await client.get(domain);
        to_search = set([resp])
        while to_search:
            current = to_search.pop()
            if "uia.no" not in str(current.url): continue

            text = soup.BeautifulSoup(current.text, "html.parser")
            hrefs = {i.get("href") for i in text.find_all(
                href=True) if i.get("href") not in visited}
            srcs = {i.get("src") for i in text.find_all(
                src=True) if i.get("src") not in visited}
            
            for url in hrefs | srcs:
                for nothanks in ["mailto:", "tel:", "javascript:", "#content-middle"]:
                    if url.startswith(nothanks): 
                        continue
                try:
                    full_url = handle_url(url, current)
                    resp = await client.get(full_url)
                    await trio.sleep(0.5)
                    if 200 <= resp.status_code < 300 or resp.status_code == 301 or resp.status_code == 302:
                        to_search.add(resp)

                        logging.debug(f"******************\n   {url}\nIn {current.url}\n{resp.status_code}")
                    else:
                        await aio_as_trio(cur.execute)("""INSERT INTO errors VALUES (?,?,?,?,?)""",(str(current.url),str(url),resp.status_code,"error name",str(datetime.date.today())))
                        #logging.error(f"******************\n   {url}\nIn {current.url}\n{resp.status_code}")


                except Exception as e:
                    logging.error(f"******************\n   {url}\nIn {current.url}\n{e.args}")






DATABASE_NAME = "data.db"
async def main() -> None:
    #TODO: move this into the cli script/server, since the crawler should only insert data
    con = await aio_as_trio(aiosqlite.connect)(DATABASE_NAME)
    cur = await aio_as_trio(con.cursor)()
    #await aio_as_trio(cur.execute)("""DROP TABLE IF EXISTS subdomains""") #reset database for testing
    await aio_as_trio(cur.execute)("""CREATE TABLE IF NOT EXISTS subdomains (domain TEXT PRIMARY KEY NOT NULL, should_search BOOLEAN NOT NULL CHECK (should_search IN (0,1)))""")

    #await aio_as_trio(cur.execute)("""DROP TABLE IF EXISTS errors""") #reset database for testing
    await aio_as_trio(cur.execute)("""CREATE TABLE IF NOT EXISTS errors 
                (source TEXT PRIMARY KEY NOT NULL, 
                target TEXT PRIMARY KEY NOT NULL,
                error_code INTEGER,
                error_name TEXT,
                updated_at TEXT)""")
    visited = set()
    #domains = set(['https://www.uia.no', 'https://cair.uia.no', 'https://home.uia.no', 'https://kompetansetorget.uia.no', 'https://icnp.uia.no', 'http://friluft.uia.no', 'https://passord.uia.no', 'https://windplan.uia.no', 'https://appsanywhere.uia.no', 'https://shift.uia.no', 'https://insitu.uia.no', 'https://lyingpen.uia.no', 'https://platinum.uia.no', 'https://dekomp.uia.no', 'https://naturblogg.uia.no', 'https://enters.uia.no', 'https://wisenet.uia.no', 'https://libguides.uia.no', 'http://ciem.uia.no'])  # await google_domain_search("uia.no")
    #await cur.executemany("INSERT INTO subdomains VALUES (?,?)",[(i,True) for i in domains])
    await aio_as_trio(con.commit)()
    async for (i,) in await aio_as_trio(cur.execute)("SELECT domain FROM subdomains where should_search=1"):
        domais.add(i)
    async with trio.open_nursery() as nurse:
        for domain in domains:
            nurse.start_soon(search_domain, domain, visited)

if __name__ == "__main__":
        trio_asyncio.run(main)
