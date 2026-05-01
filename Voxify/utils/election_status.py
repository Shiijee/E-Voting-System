def sync_election_statuses(conn, college_id=None):
    """Update election statuses based on their scheduled start and end times."""
    cursor = conn.cursor()
    if college_id is not None:
        cursor.execute(
            """
            UPDATE elections
            SET status = CASE
                WHEN end_date < NOW() THEN 'completed'
                WHEN start_date <= NOW() AND end_date >= NOW() THEN 'active'
                WHEN start_date > NOW() THEN 'upcoming'
                ELSE status
            END
            WHERE college_id=%s OR college_id IS NULL
            """,
            (college_id,)
        )
    else:
        cursor.execute(
            """
            UPDATE elections
            SET status = CASE
                WHEN end_date < NOW() THEN 'completed'
                WHEN start_date <= NOW() AND end_date >= NOW() THEN 'active'
                WHEN start_date > NOW() THEN 'upcoming'
                ELSE status
            END
            """
        )
    conn.commit()
    cursor.close()
