from typing import Set
import json
import sqlite3
import argparse
import googlesearch as google
import os




def google_domain_search(domain: str) -> Set[str]:
    print(f"expanding {domain}")
    result = set((get_base_url(i) for i in google.search(
        f"site:{domain}", tld="no", lang="no", pause=5) if domain in i))
    return result


def get_base_url(url: str) -> str:
    return "/".join(url.split("/")[:3])


def init(args):
    con = sqlite3.connect("data.db")
    cur = con.cursor()
    cur.execute("""DROP TABLE IF EXISTS errors""")
    domains = google_domain_search("uia.no")
    print('\n'.join(domains))
    cur.executemany("INSERT INTO subdomains VALUES (?,?)",[(i, 1) for i in domains])


def add_subdomain(args):
    con = sqlite3.connect("data.db")
    cur = con.cursor()
    print("adding subdomain now")
    cur.executemany("""INSERT INTO subdomains VALUES (?, ?)""", (args.name, 1))
    con.commit()


def remove_subdomain(args):
    con = sqlite3.connect("data.db")
    cur = con.cursor()
    print("removing subdomain now")
    cur.executemany("""DELETE FROM subdomains WHERE domain=?""", (args.name))
    con.commit()


def enable_subdomain(args):
    con = sqlite3.connect("data.db")
    cur = con.cursor()
    print("enabling {name}")
    cur.executemany("""UPDATE subdomains SET should_search = 1 WHERE domain = ?;""", (args.name))
    con.commit()


def disable_subdomain(args):
    con = sqlite3.connect("data.db")
    cur = con.cursor()
    print("disabling {name}")
    cur.executemany("""UPDATE subdomains SET should_search = 0 WHERE domain = ?;""", (args.name))
    con.commit()


parser = argparse.ArgumentParser(description="The Arachomb link checker")
subparsers = parser.add_subparsers()

subcommand_add = subparsers.add_parser('add')
subcommand_add.add_argument('name', nargs="+", type=str)
subcommand_add.set_defaults(func=add_subdomain)

subcommand_remove = subparsers.add_parser('remove')
subcommand_remove.add_argument('name', nargs="+", type=str)
subcommand_remove.set_defaults(func=remove_subdomain)

subcommand_enable = subparsers.add_parser('enable')
subcommand_enable.add_argument('name', nargs="+", type=str)
subcommand_enable.set_defaults(func=enable_subdomain)

subcommand_disable = subparsers.add_parser('disable')
subcommand_disable.add_argument('name', nargs="+", type=str)
subcommand_disable.set_defaults(func=disable_subdomain)

subcommand_init = subparsers.add_parser('init')
subcommand_init.add_argument('name', nargs="?", type=str)
subcommand_init.set_defaults(func=init)

parser.add_argument("-c", "--code", type=int,
                    help="filter errors by the given error code")
parser.add_argument("-s", "--subdomain", type=str,
                    help="filter errors by the given subdomain")
parser.add_argument("--add_subdomain", nargs="+", type=str,
                    help="adds the specified subdomain to the database")


args = parser.parse_args()
if args.func:
    args.func(args)
    # something else?
#else?  There was another branch to this, but I forget what he did here

def suggestion(code):
    if code == "404":
        return "make sure the URL is spelled correctly, and that the resource exists."
    elif code == "403":
        return "make sure the resource is publically available.  If this is intentional, ignore this error."
    elif code == "405":
        return "double check that the URL is spelled correctly, as the page only allows certain non-GET requests, so it won't appear properly in a browser."
    elif code == "557":
        return "give the website an up-to-date SSL certificate, since it currently does not have one."
    elif code == "5":
        return "make sure you are using an up to date version of python. you are likely using python3.8 with a minor version 2 or lower while on windows, this has some bugs in async code that are fixed in the later releases"
    return "figure out what kind of error this is, because we do not know."



# await cur.execute("""DROP TABLE IF EXISTS subdomains""")  # Reset database for testing
cur.execute("""CREATE TABLE IF NOT EXISTS subdomains (
            domain TEXT NOT NULL, 
            should_search BOOLEAN NOT NULL CHECK (should_search IN (0,1)),
            PRIMARY KEY (domain) ON CONFLICT IGNORE
            ) """)


cur.execute("""CREATE TABLE IF NOT EXISTS errors 
            (source TEXT NOT NULL, 
            subdomain TEXT NOT NULL,
            target TEXT NOT NULL,
            error TEXT,
            updated_at TEXT,
            CONSTRAINT prim_key PRIMARY KEY (source, target) ON CONFLICT REPLACE
            )""")

if args.add_subdomain:
    cur.executemany("""INSERT INTO subdomains VALUES (?, 1)""",
                    (args.add_subdomain))
con.commit()


# os.system("crawler.py")
# Use subprocess.Popen instead?  Needs research

print("Fetching error logs from database...")


def error_output(error, source, target, timestamp):
    if error == "557":
        error = "fault with the site's SSL certificate"
    elif error == "5":
        error = "fault relating to your computer's OS"
    else:
        error += " error"
    return f"""*****************\nWe found an error in {source}, in the link to 
        {target}\n\n
        Getting the link returned a {error}. Try to {suggestion(error)}\n\n
        Last checked at {timestamp}"""


if args.code and args.subdomain:
    for error, source, target, timestamp in cur.execute(f"SELECT error, source, target, updated_at FROM errors WHERE error=\"{args.code}\" AND subdomain=\"{args.subdomain}\" ORDER BY subdomain").fetchall():
        print(error_output(error, source, target, timestamp))

elif args.code:
    for error, source, target, timestamp in cur.execute(f"SELECT error, source, target, updated_at FROM errors WHERE error=\"{args.code}\" ORDER BY subdomain").fetchall():
        print(error_output(error, source, target, timestamp))

elif args.subdomain:
    for error, source, target, timestamp in cur.execute(f"SELECT error, source, target, updated_at FROM errors WHERE subdomain=\"{args.subdomain}\" ORDER BY subdomain").fetchall():
        print(error_output(error, source, target, timestamp))

else:
    for error, source, target, timestamp in cur.execute("SELECT error, source, target, updated_at FROM errors ORDER BY subdomain").fetchall():
        print(error_output(error, source, target, timestamp))
