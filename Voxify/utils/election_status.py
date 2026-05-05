def sync_election_statuses(conn, college_id=None):
    """Update election statuses based on their scheduled start and end times.

    Rules:
    - 'upcoming' elections auto-transition to 'active' or 'completed' based on time.
    - 'active' elections auto-transition to 'completed' only when end_date has passed.
      Active elections are NOT flipped back to 'upcoming' even if start_date is in the future
      (to preserve manual admin activation).
    - 'paused', 'completed', and 'draft' elections are never touched by the sync.
    """
    cursor = conn.cursor()

    # Auto-close active elections whose end_date has passed
    if college_id is not None:
        cursor.execute(
            """
            UPDATE elections
            SET status = 'completed'
            WHERE status = 'active'
              AND end_date < NOW()
              AND (college_id=%s OR college_id IS NULL)
            """,
            (college_id,)
        )
    else:
        cursor.execute(
            """
            UPDATE elections
            SET status = 'completed'
            WHERE status = 'active'
              AND end_date < NOW()
            """
        )

    # Auto-transition upcoming elections based on schedule
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
              AND status = 'upcoming'
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
            WHERE status = 'upcoming'
            """
        )

    conn.commit()
    cursor.close()