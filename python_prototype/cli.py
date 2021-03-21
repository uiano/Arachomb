import json
import sqlite3

with open("config.json") as file:
    data = json.loads(file.read())
domains = set(filter(lambda x: data[x], data.keys()))

con = sqlite3.connect('[NAME].db')
cur = con.cursor()

for error, source, target, timestamp in cur.execute(f"SELECT * FROM errors ORDER BY source"):
    print(f"""*****************\nWe found an error in {source}, in the link to 
        {target}:\n\nhot diggity code here\n\n
        Getting the link returned a {error} error, suggesting you should 
        {suggestion(error)}.\n\n
        Last checked at {timestamp}""")
