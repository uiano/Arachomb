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


async def search_domain(domain: str, visited: Set[str], database_queue) -> None:
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(domain)
        except httpx.ConnectError as e:
            print(f"got an ssl error in {domain}")
            return
        to_search = set([resp])
        while to_search:
            current = to_search.pop()
            print(f"searching {current.url}")

            # Get all the URLs in the current page
            text = soup.BeautifulSoup(current.text, "html.parser")
            hrefs = {i.get("href") for i in text.find_all(
                href=True) if i.get("href") not in visited}
            srcs = {i.get("src") for i in text.find_all(
                src=True) if i.get("src") not in visited}

            # Loop over the URLs in the current page
            for url in hrefs | srcs:
                print(f"checking {url}")
                if any(url.startswith(i) for i in ["mailto:", "tel:", "javascript:", "#content-middle", "about:blank"]):
                    continue
                if url == "#" or "linkedin" in url:
                    continue

                try:  # getting the content of the URL we're checking currently
                    full_url = handle_url(str(url), current)
                    resp = await client.get(full_url)
                    await asyncio.sleep(0.5)
                    if 200 <= resp.status_code < 300 or resp.status_code == 301 or resp.status_code == 302:
                        if ".js" not in full_url and "uia.no" in resp.url.host:
                            to_search.add(resp)

                        logging.debug(
                            f"******************\n   {full_url}\n   {url}\nIn {str(current.url)}\n{resp.status_code}")

                    else:  # Got an HTTP error
                        await database_queue.put((str(current.url), full_url, str(resp.status_code), str(datetime.datetime.today())))
                        # await cur.execute("""INSERT INTO errors VALUES (?,?,?,?)""", (str(current.url), full_url, str(resp.status_code), str(datetime.date.today())))
                        # await cur.commit()
                        # await con.commit()
                        logging.error(
                            f"******************\n   {full_url}\n   {url}\nIn {str(current.url)}\n{resp.status_code}")

                except httpx.ConnectError as e:  # "Tidsavbruddsperioden for semaforen har utløpt"
                    await database_queue.put((str(current.url), full_url, str(resp.status_code), str(datetime.datetime.today())))
                    # await cur.execute("""INSERT INTO errors VALUES (?,?,?,?)""", (str(current.url), full_url, str(e.args), str(datetime.date.today())))
                    # await cur.commit()
                    # await con.commit()
                    logging.error(f"******************\n   {full_url}\n   {url}\nIn {str(current.url)}\n{e.args}")

async def database_worker(data_queue, insert_length) -> None:
    print("starting database worker")
    async with aiosqlite.connect(DATABASE_NAME) as con:
        cursor = await con.cursor()
        stored_data = []
        try:
            while True:
                print("waiting for data")
                await asyncio.sleep(1)
                # (source,target,code,timestamp) = await data_queue.get()
                data = await data_queue.get()
                print(f"data={data}")
                stored_data.append(data)
                if len(stored_data) >= insert_length:
                    await cursor.executemany(
                        "INSERT INTO errors VALUES (?,?,?,?)", stored_data)
                    print("stored data")
                    stored_data = []
                    await con.commit()
                data_queue.task_done()
        except asyncio.CancelledError:
            if len(stored_data)!=0:
                    await cursor.executemany(
                        "INSERT INTO errors VALUES (?,?,?,?)", stored_data)
        finally:
            await cursor.close()


DATABASE_NAME = "data.db"


async def main() -> None:
    visited = set()
    domains = set(['https://www.uia.no', 'https://cair.uia.no', 'https://home.uia.no', 'https://kompetansetorget.uia.no', 'https://icnp.uia.no', 'http://friluft.uia.no', 'https://passord.uia.no', 'https://windplan.uia.no', 'https://appsanywhere.uia.no', 'https://shift.uia.no',
                   'https://insitu.uia.no', 'https://lyingpen.uia.no', 'https://platinum.uia.no', 'https://dekomp.uia.no', 'https://naturblogg.uia.no', 'https://enters.uia.no', 'https://wisenet.uia.no', 'https://libguides.uia.no', 'http://ciem.uia.no'])  # await google_domain_search("uia.no")
    # await cur.executemany("INSERT INTO subdomains VALUES (?,?)",[(i,True) for i in domains])
    con = await aiosqlite.connect(DATABASE_NAME)
    cur = await con.cursor()
    # domains = set()
    try:
        for (i,) in await cur.execute("SELECT domain FROM subdomains where should_search=1"):
            print(i)
            domains.add(i)
    except:
        with open("config.json") as file:
            data = json.loads(file.read())
        domains = set(filter(lambda x: data[x], data.keys()))
    await cur.close()
    # _ = await asyncio.wait([search_domain(domain, visited) for domain in domains],return_when=asyncio.ALL_COMPLETED)
    # worker_amount = 6
    # task_queue = asyncio.Queue()
    insert_length = 1
    database_queue = asyncio.Queue()
    # result_queue = asyncio.Queue()
    data_worker = asyncio.create_task(
        database_worker(database_queue, insert_length))
    workers = []

    for domain in domains:
        workers.append(asyncio.create_task(search_domain(domain,visited,database_queue),name=domain))
    #await asyncio.gather(*workers, return_exceptions=True)
    (done, running) = await asyncio.wait(workers,return_when=asyncio.FIRST_COMPLETED) 
    print(f"{done=}")
    print(f"{running=}")
    while running:
        (done_new, running_new) = await asyncio.wait(workers,return_when=asyncio.FIRST_COMPLETED) 
        if done_new!=done:
            print(f"{len(done)}/{len(done)+len(running)} workers done")
        done,running=done_new,running_new
        await asyncio.sleep(1)
    await database_queue.join()
    data_worker.cancel()


if __name__ == "__main__":
    asyncio.run(main())
    # asyncio.get_event_loop().run_until_complete(main())
