import json
import sqlite3
import argparse
import os


def add_subdomain(name):
    print("adding subdomain now")
    cur.execute("""INSERT INTO subdomains VALUES (?, ?)""", (name, 1))
    con.commit()


def remove_subdomain(name):
    print("removing subdomain now")
    cur.execute("""DELETE FROM subdomains WHERE domain=?""", (name))
    con.commit()

parser = argparse.ArgumentParser(description="The Arachomb link checker")
subparsers = parser.add_subparsers()

subcommand_add = subparsers.add_parser('add')
subcommand_add.add_argument('name', type=str)
subcommand_add.set_defaults(func=add_subdomain)

subcommand_remove = subparsers.add_parser('remove')
subcommand_remove.add_argument('name', type=str)
subcommand_remove.set_defaults(func=remove_subdomain)

parser.add_argument("-c", "--code", type=int,
        help="filter errors by the given error code")
parser.add_argument("-s", "--subdomain", type=str,
        help="filter errors by the given subdomain")
parser.add_argument("--add_subdomain", nargs="+", type=str,
        help="adds the specified subdomain to the database")
parser.add_argument("-i", "--init", action="store_true", default=False,
        help="reset the database")

args = parser.parse_args()
print(args.code, args.subdomain, args.add_subdomain, args.init)


def suggestion(code):
    if code == "404":
        return "make sure the URL is spelled correctly, and that the resource exists."
    elif code == "403":
        return "make sure the resource is publically available.  If this is intentional, ignore this error."
    elif code == "405":
        return "double check that the URL is spelled correctly, as the page only allows certain non-GET requests, so it won't appear properly in a browser."
    return "tell us where you got this error, because that should not happen."


con = sqlite3.connect("data.db")
cur = con.cursor()

#await cur.execute("""DROP TABLE IF EXISTS subdomains""")  # Reset database for testing
cur.execute("""CREATE TABLE IF NOT EXISTS subdomains (
            domain TEXT NOT NULL, 
            should_search BOOLEAN NOT NULL CHECK (should_search IN (0,1)),
            PRIMARY KEY (domain) ON CONFLICT IGNORE
            ) """)

if args.init:
    cur.execute("""DROP TABLE IF EXISTS errors""")  # Reset database for testing
cur.execute("""CREATE TABLE IF NOT EXISTS errors 
            (source TEXT NOT NULL, 
            target TEXT NOT NULL,
            error TEXT,
            updated_at TEXT,
            CONSTRAINT prim_key PRIMARY KEY (source, target) ON CONFLICT REPLACE
            )""")

if args.add_subdomain:
    for subdomain in args.add_subdomain:
        cur.execute("""INSERT INTO subdomains VALUES (?, 1)""", (subdomain))
con.commit()


# os.system("crawler.py")
# Use subprocess.Popen instead?  Needs research

print("Fetching error logs from database...")

either_filter = bool(args.code or args.subdomain)
both_filters = bool(args.code and args.subdomain)
#if args.code or args.subdomain:
#    for error, source, target, timestamp in cur.execute(f"SELECT error, source, target, updated_at FROM errors WHERE error='{args.code}'"):
for error, source, target, timestamp in cur.execute("SELECT error, source, target, updated_at FROM errors " + "WHERE "*either_filter + f"error=\"{args.code}\" "*bool(args.code) + "AND "*both_filters + f"source=\"{args.subdomain}\" "*bool(args.subdomain) + "ORDER BY source").fetchall():
# for error, source, target, timestamp in cur.execute(f"SELECT error, source, target, updated_at FROM errors ORDER BY source").fetchall():
    print(f"""*****************\nWe found an error in {source}, in the link to 
        {target}\n\n
        Getting the link returned a {error} error. Try {suggestion(error)}\n\n
        Last checked at {timestamp}""")
