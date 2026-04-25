import os
import psycopg2

# Database connection details from docker-compose.yml
DB_NAME = "jadslink"
DB_USER = "jads"
DB_PASS = "jadspass"
DB_HOST = "db"
DB_PORT = "5432"

conn = None
cur = None

try:
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()

    # 1. Find duplicate plans and identify the golden record for each group
    cur.execute("""
        SELECT name, tenant_id, array_agg(id::text) as ids, array_agg(updated_at) as updated_ats
        FROM plans
        GROUP BY name, tenant_id
        HAVING count(*) > 1
    """)
    duplicates = cur.fetchall()

    for duplicate in duplicates:
        name, tenant_id, ids, updated_ats = duplicate
        
        # Find the golden record (most recent updated_at)
        golden_id = ids[updated_ats.index(max(updated_ats))]
        
        # Get the list of duplicate ids to be deleted
        duplicate_ids = [id for id in ids if id != golden_id]

        print(f"Found duplicates for plan '{name}' in tenant '{tenant_id}'")
        print(f"  Golden plan id: {golden_id}")
        print(f"  Duplicate plan ids: {duplicate_ids}")

        # 2. Update tickets to point to the golden plan
        cur.execute(
            "UPDATE tickets SET plan_id = %s::uuid WHERE plan_id = ANY(%s::uuid[])",
            (golden_id, duplicate_ids)
        )
        print(f"  Updated {cur.rowcount} tickets")

        # 3. Delete duplicate plans
        cur.execute(
            "DELETE FROM plans WHERE id = ANY(%s::uuid[])",
            (duplicate_ids,)
        )
        print(f"  Deleted {cur.rowcount} duplicate plans")

    conn.commit()
    print()
    print("Cleanup complete!")

except psycopg2.Error as e:
    print(f"Database error: {e}")
    if conn:
        conn.rollback()

finally:
    if cur:
        cur.close()
    if conn:
        conn.close()
