import sqlite3
import os
from backend.core.logger import log

# Database file location
DB_PATH = "data/investigations.db"


def get_connection():
    """
    Creates and returns a database connection.
    Like opening a file but for a database!
    """
    # Create data directory if not exists
    os.makedirs("data", exist_ok=True)

    conn = sqlite3.connect(DB_PATH)

    # Return rows as dictionaries
    # So we can access by column name!
    conn.row_factory = sqlite3.Row

    return conn


def init_database():
    """
    Creates database tables if they don't exist.
    Like setting up a new filing cabinet!
    """
    log.info("Initialising database...")

    conn = get_connection()
    cursor = conn.cursor()

    # Create investigations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS investigations (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            namespace TEXT NOT NULL,
            status TEXT NOT NULL,
            total_pods INTEGER DEFAULT 0,
            problematic_pods INTEGER DEFAULT 0,
            critical_events INTEGER DEFAULT 0,
            network_issues INTEGER DEFAULT 0,
            cluster_healthy BOOLEAN DEFAULT FALSE,
            root_cause TEXT,
            confidence INTEGER,
            suggested_fix TEXT,
            raw_diagnosis TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create actions table
    # Tracks every action approved/rejected
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            investigation_id TEXT NOT NULL,
            action_type TEXT NOT NULL,
            reason TEXT,
            command TEXT,
            risk TEXT,
            approved BOOLEAN DEFAULT FALSE,
            executed BOOLEAN DEFAULT FALSE,
            result TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (investigation_id)
                REFERENCES investigations(id)
        )
    """)

    conn.commit()
    conn.close()

    log.info("Database initialised successfully!")


def save_investigation(
    pipeline_id: str,
    namespace: str,
    pipeline_result: dict
) -> bool:
    """
    Saves an investigation to the database.
    Called after every investigation completes!
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        summary = pipeline_result.get(
            "investigation", {}
        ).get("summary", {})

        diagnosis = pipeline_result.get("diagnosis", {})

        cursor.execute("""
            INSERT OR REPLACE INTO investigations (
                id,
                timestamp,
                namespace,
                status,
                total_pods,
                problematic_pods,
                critical_events,
                network_issues,
                cluster_healthy,
                root_cause,
                confidence,
                suggested_fix,
                raw_diagnosis
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pipeline_id,
            pipeline_result.get("timestamp", ""),
            namespace,
            pipeline_result.get("status", ""),
            summary.get("total_pods", 0),
            summary.get("problematic_pods", 0),
            summary.get("critical_events", 0),
            summary.get("network_issues", 0),
            summary.get("cluster_healthy", False),
            diagnosis.get("root_cause", ""),
            diagnosis.get("confidence", 0),
            diagnosis.get("suggested_fix", ""),
            str(diagnosis)
        ))

        conn.commit()
        conn.close()

        log.info(f"Investigation {pipeline_id} saved!")
        return True

    except Exception as e:
        log.error(f"Failed to save investigation: {str(e)}")
        return False


def save_action(
    investigation_id: str,
    action: dict,
    approved: bool,
    result: dict = None
) -> bool:
    """
    Saves an action to the database.
    Called when user approves or rejects!
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO actions (
                investigation_id,
                action_type,
                reason,
                command,
                risk,
                approved,
                executed,
                result
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            investigation_id,
            action.get("action_type", ""),
            action.get("reason", ""),
            action.get("command", ""),
            action.get("risk", ""),
            approved,
            True if result else False,
            str(result) if result else None
        ))

        conn.commit()
        conn.close()

        log.info(
            f"Action saved for "
            f"investigation {investigation_id}"
        )
        return True

    except Exception as e:
        log.error(f"Failed to save action: {str(e)}")
        return False


def get_recent_investigations(limit: int = 10) -> list:
    """
    Returns recent investigations from database.
    Used to show history in dashboard!
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                timestamp,
                namespace,
                status,
                total_pods,
                problematic_pods,
                critical_events,
                cluster_healthy,
                root_cause,
                confidence,
                created_at
            FROM investigations
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    except Exception as e:
        log.error(
            f"Failed to get investigations: {str(e)}"
        )
        return []


def get_investigation_stats() -> dict:
    """
    Returns statistics about all investigations.
    Great for dashboard overview!
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN cluster_healthy = 0
                    THEN 1 ELSE 0 END) as unhealthy,
                AVG(confidence) as avg_confidence,
                MAX(created_at) as last_investigation
            FROM investigations
        """)

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else {}

    except Exception as e:
        log.error(f"Failed to get stats: {str(e)}")
        return {}