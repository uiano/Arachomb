import json
import sqlite3

#with open("config.json") as file:
#    data = json.loads(file.read())
#domains = set(filter(lambda x: data[x], data.keys()))

def suggestion(code):
    if code == "404":
        return "make sure the URL is spelled correctly, and that the resource exists."
    elif code == "403":
        return "make sure the resource is publically available.  If this is intentional, ignore this error."
    elif code == "405":
        return "double check that the URL is spelled correctly, as the page only allows certain non-GET requests, so it won't appear properly in a browser."
    return "figure out what kind of error this is, because we do not know."

con = sqlite3.connect("data.db")
cur = con.cursor()
print("finding stuff")
for error, source, target, timestamp in cur.execute(f"SELECT error, source, target, updated_at FROM errors ORDER BY source").fetchall():
    print(f"""*****************\nWe found an error in {source}, in the link to 
        {target}\n\n
        Getting the link returned a {error} error, suggesting you should 
        {suggestion(error)}\n\n
        Last checked at {timestamp}""")
