
from pathlib import Path
import duckdb

root = Path(__file__).resolve().parent
csv_path = root / "data" / "electronics.csv"
sql_path = root / "sql" / "analysis_queries.sql"

con = duckdb.connect(":memory:")

try:
    # Load the CSV as a SQL view; no duplicate dataset is created.
    csv_file = str(csv_path).replace("'", "''")
    con.execute(f"""
        CREATE VIEW electronics_reviews AS
        SELECT * FROM read_csv_auto('{csv_file}')
    """)

    sql_text = sql_path.read_text(encoding="utf-8")
    statements = [
        statement.strip()
        for statement in sql_text.split(";")
        if statement.strip()
    ]

    passed = 0
    for number, statement in enumerate(statements, start=1):
        try:
            result = con.execute(statement)
            rows = result.fetchall()
            columns = [item[0] for item in result.description]
            print(f"\nQUERY {number}: PASS")
            print("Columns:", columns)
            print("Rows returned:", len(rows))
            for row in rows[:5]:
                print(row)
            passed += 1
        except Exception as exc:
            print(f"\nQUERY {number}: FAIL")
            print(exc)

    print(f"\nSUMMARY: {passed}/{len(statements)} queries passed.")

finally:
    con.close()
