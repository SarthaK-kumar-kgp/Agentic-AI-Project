import json
import sqlite3
from pathlib import Path


DEFAULT_DB_PATH = Path(__file__).resolve().parent / "harness.sqlite3"


def create_tables(db_path=DEFAULT_DB_PATH):
    conn = sqlite3.connect(db_path)

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal TEXT NOT NULL,
            status TEXT NOT NULL,
            final_result TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS steps (
            step_id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            iteration_number INTEGER NOT NULL,
            agent_id TEXT NOT NULL,
            thought TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (task_id) REFERENCES tasks (task_id)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tool_calls (
            tool_call_id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            step_id INTEGER,
            tool_name TEXT NOT NULL,
            tool_input_json TEXT,
            tool_output_json TEXT,
            error_json TEXT,
            successful_flag INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (task_id) REFERENCES tasks (task_id),
            FOREIGN KEY (step_id) REFERENCES steps (step_id)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS file_changes (
            file_change_id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            tool_call_id INTEGER NOT NULL,
            file_name TEXT NOT NULL,
            file_start_text TEXT,
            file_end_text TEXT,
            file_difference TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (task_id) REFERENCES tasks (task_id),
            FOREIGN KEY (tool_call_id) REFERENCES tool_calls (tool_call_id)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            payload_json TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (task_id) REFERENCES tasks (task_id)
        )
        """
    )

    conn.commit()
    conn.close()


class SQLStore:
    def __init__(self, db_path=DEFAULT_DB_PATH):
        self.db_path = db_path
        create_tables(self.db_path)

    def read_query(self, query, params=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        results = cursor.fetchall()
        conn.close()
        return results

    def write_query(self, query, params=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return new_id

    def to_json(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return json.dumps(value)

    def create_task(self, goal, status="PENDING", final_result=None):
        query = """
        INSERT INTO tasks (goal, status, final_result, created_at, updated_at)
        VALUES (?, ?, ?, datetime('now'), datetime('now'))
        """
        return self.write_query(query, (goal, status, final_result))

    def update_task_status(self, task_id, status, final_result=None):
        if final_result is None:
            query = """
            UPDATE tasks
            SET status = ?, updated_at = datetime('now')
            WHERE task_id = ?
            """
            self.write_query(query, (status, task_id))
        else:
            query = """
            UPDATE tasks
            SET status = ?, final_result = ?, updated_at = datetime('now')
            WHERE task_id = ?
            """
            self.write_query(query, (status, final_result, task_id))

    def create_step(self, task_id, iteration_number, agent_id, thought=None):
        query = """
        INSERT INTO steps (task_id, iteration_number, agent_id, thought, created_at)
        VALUES (?, ?, ?, ?, datetime('now'))
        """
        return self.write_query(query, (task_id, iteration_number, agent_id, thought))

    def create_tool_call(self, task_id, step_id, tool_name, tool_input_json, tool_output_json, error_json, successful_flag):
        query = """
        INSERT INTO tool_calls (task_id, step_id, tool_name, tool_input_json, tool_output_json, error_json, successful_flag, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """
        return self.write_query(
            query,
            (
                task_id,
                step_id,
                tool_name,
                self.to_json(tool_input_json),
                self.to_json(tool_output_json),
                self.to_json(error_json),
                successful_flag,
            ),
        )

    def create_file_change(self, task_id, tool_call_id, file_name, file_start_text, file_end_text, file_difference):
        query = """
        INSERT INTO file_changes (task_id, tool_call_id, file_name, file_start_text, file_end_text, file_difference, created_at)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """
        return self.write_query(query, (task_id, tool_call_id, file_name, file_start_text, file_end_text, file_difference))

    def create_event(self, task_id, event_type, payload_json):
        query = """
        INSERT INTO events (task_id, event_type, payload_json, created_at)
        VALUES (?, ?, ?, datetime('now'))
        """
        return self.write_query(query, (task_id, event_type, self.to_json(payload_json)))

    def get_task(self, task_id):
        query = "SELECT * FROM tasks WHERE task_id = ?"
        rows = self.read_query(query, (task_id,))
        if not rows:
            return None
        return rows[0]

    def get_steps(self, task_id):
        query = "SELECT * FROM steps WHERE task_id = ? ORDER BY iteration_number"
        return self.read_query(query, (task_id,))

    def get_task_events(self, task_id):
        query = "SELECT * FROM events WHERE task_id = ? ORDER BY created_at"
        return self.read_query(query, (task_id,))

    def get_task_tool_calls(self, task_id):
        query = "SELECT * FROM tool_calls WHERE task_id = ? ORDER BY created_at"
        return self.read_query(query, (task_id,))
