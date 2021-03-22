import json
import sqlite3

#with open("config.json") as file:
#    data = json.loads(file.read())
#domains = set(filter(lambda x: data[x], data.keys()))

def suggestion(code):
    #TODO: do somethign with this?
    return code

con = sqlite3.connect("data.db")
cur = con.cursor()
print("finding stuff")
for error, source, target, timestamp in cur.execute(f"SELECT error_code,source,target,updated_at FROM errors ORDER BY source").fetchall():
    print(f"""*****************\nWe found an error in {source}, in the link to 
        {target}:\n\nhot diggity code here\n\n
        Getting the link returned a {error} error, suggesting you should 
        {suggestion(error)}.\n\n
        Last checked at {timestamp}""")