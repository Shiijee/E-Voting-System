def sync_election_statuses(conn, college_id=None):
    """Update election statuses based on their scheduled start and end times.

    Excludes 'paused' and 'completed' elections so that admin-set statuses
    (manual pause or early close) are never overwritten by the time-based sync.
    Only 'upcoming' and 'active' elections are eligible for auto-transition.
    """
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
            WHERE (college_id=%s OR college_id IS NULL)
              AND status NOT IN ('paused', 'completed', 'draft')
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
            WHERE status NOT IN ('paused', 'completed', 'draft')
            """
        )
    conn.commit()
    cursor.close()