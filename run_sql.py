import sqlite3, sys
con = sqlite3.connect('collections.db')
cur = con.cursor()
path = sys.argv[1]
sql = open(path).read()
cur.executescript(sql)
con.commit()
# if last statement was a SELECT, executescript won't return rows; so re-run selects individually for display
con.close()
print(f"OK: executed {path}")
