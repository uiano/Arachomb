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
    elif code == "557":
        return "give the website an up-to-date SSL certificate, since it currently does not have one."
    return "figure out what kind of error this is, because we do not know."


con = sqlite3.connect("data.db")
cur = con.cursor()

# await cur.execute("""DROP TABLE IF EXISTS subdomains""")  # Reset database for testing
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
    cur.executemany("""INSERT INTO subdomains VALUES (?, 1)""",
                    (args.add_subdomain))
con.commit()


# os.system("crawler.py")
# Use subprocess.Popen instead?  Needs research

print("Fetching error logs from database...")


def error_output(error, source, target, timestamp):
    return f"""*****************\nWe found an error in {source}, in the link to 
        {target}\n\n
        Getting the link returned a {error} error. Try {suggestion(error)}\n\n
        Last checked at {timestamp}"""


if args.code and args.subdomain:
    for error, source, target, timestamp in cur.execute(f"SELECT error, source, target, updated_at FROM errors WHERE error=\"{args.code}\" AND source=\"{args.subdomain}\" ORDER BY source").fetchall():
        print(error_output(error, source, target, timestamp))

elif args.code:
    for error, source, target, timestamp in cur.execute(f"SELECT error, source, target, updated_at FROM errors WHERE error=\"{args.code}\" ORDER BY source").fetchall():
        print(error_output(error, source, target, timestamp))

elif args.subdomain:
    for error, source, target, timestamp in cur.execute(f"SELECT error, source, target, updated_at FROM errors WHERE source=\"{args.subdomain}\" ORDER BY source").fetchall():
    for error, source, target, timestamp in cur.execute(""):
        print(error_output(error, source, target, timestamp))

else:
    for error, source, target, timestamp in cur.execute("SELECT error, source, target, updated_at FROM errors ORDER BY source").fetchall():
        print(error_output(error, source, target, timestamp))
