import sqlite3

class Database:
    def __init__(self, db_name: str = "bot_database.db"):
        self.db_name = db_name
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_name)
    
    def _init_db(self):
        with self._connect() as conn:
            cur = conn.cursor()

            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tg_id INTEGER UNIQUE NOT NULL
                )
            ''')

            cur.execute('''
                CREATE TABLE IF NOT EXISTS pics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    is_private BOOL NOT NULL,
                    storage TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            cur.execute('''
                CREATE TABLE IF NOT EXISTS fav_pics (
                    user_id INTEGER NOT NULL,
                    pic_id INTEGER NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (pic_id) REFERENCES pics (id),
                    PRIMARY KEY (user_id, pic_id)
                )
            ''')

            cur.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tag_str TEXT UNIQUE NOT NULL
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS pics_tags (
                    pic_id INTEGER NOT NULL,
                    tag_id INTEGER NOT NULL,
                    FOREIGN KEY (pic_id) REFERENCES pics (id),
                    FOREIGN KEY (tag_id) REFERENCES tags (id),
                    PRIMARY KEY (pic_id, tag_id)
                )
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_pics_tags_pic_id ON pics_tags(pic_id)
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_pics_tags_tag_id ON pics_tags(tag_id)
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS tags_match (
                    tag_a INTEGER NOT NULL REFERENCES tags(id),
                    tag_b INTEGER NOT NULL REFERENCES tags(id),
                    match FLOAT DEFAULT 0,
                    PRIMARY KEY (tag_a, tag_b),
                    CHECK (tag_a < tag_b)
                );
            """)

            conn.commit()


    def _get_user_id(self, tg_id: int, conn: sqlite3.Connection) -> int:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE tg_id = ?", (tg_id,))
        row = cur.fetchone()
        if row:
            return row[0]
        
        cur.execute("INSERT INTO users (tg_id) VALUES (?)", (tg_id,))
        conn.commit()    
        return cur.lastrowid
        
        
    def _tag_exists(self, tag: str, conn: sqlite3.Connection) -> bool:
        cur = conn.cursor()
        cur.execute("SELECT id FROM tags WHERE tag_str = ?", (tag,))
        return cur.fetchone() is not None
        
        
    def _get_tag_id(self, tag: str, conn: sqlite3.Connection) -> int:
        cur = conn.cursor()
        cur.execute("SELECT id FROM tags WHERE tag_str = ?", (tag,))
        row = cur.fetchone()
        if row:
            return row[0]
        
        cur.execute("INSERT INTO tags (tag_str) VALUES (?)", (tag,))
        conn.commit()    
        return cur.lastrowid


    def _add_to_table(self, tg_id: int, is_private: bool, storage: str, tags: list[str], conn: sqlite3.Connection):
        cur = conn.cursor()
        
        user_id = self._get_user_id(tg_id=tg_id, conn=conn)

        cur.execute(
            "INSERT INTO pics (user_id, is_private, storage) VALUES (?, ?, ?)",
            (user_id, is_private, storage)
        )
        pic_id = cur.lastrowid

        for tag in tags:
            tag_id = self._get_tag_id(tag, conn)
            cur.execute(
                "INSERT INTO pics_tags (pic_id, tag_id) VALUES (?, ?)",
                (pic_id, tag_id)
            )

        conn.commit()

    
    def _rewrite_tags(self, tags: list[str], conn: sqlite3.Connection):
        #with self._connect() as conn:
        #    cur = conn.cursor()

        #    for tag_str in tags:
        #        tag_a = self._get_tag_id(tag=tag_str)

        #        cur.execute("""
        #            SELECT pt2.tag_id, COUNT(*) as tcount
        #            FROM pics_tags pt1
        #            JOIN pics_tags pt2 ON pt1.pic_id = pt2.pic_id
        #            WHERE pt1.tag_id = ? AND pt2.tag_id != ?
        #            GROUP BY pt2.tag_id
        #            ORDER BY ghosts DESC
        #            LIMIT 10
        #        """, (tag_a, tag_a))

        #        ghosts = cur.fetchall()

        #    conn.commit()
        pass
    

    def add_to(self, tg_id: int, is_private: bool, storage: str, tags: list[str]):
        with self._connect() as conn:
            self._add_to_table(tg_id, is_private, storage, tags, conn)
            self._rewrite_tags(tags, conn)


    def add_from(self, tg_id: int, pic_id: int):
        with self._connect() as conn:
            cur = conn.cursor()

            user_id = self._get_user_id(tg_id=tg_id, conn=conn)

            cur.execute(
                "INSERT INTO fav_pics (user_id, pic_id) VALUES (?, ?)",
                (user_id, pic_id)
            )

            conn.commit()


    def find(self, tg_id: int, tags: list[str]) -> []:
        with self._connect() as conn:
            cur = conn.cursor()

            user_id = self._get_user_id(tg_id=tg_id, conn=conn)

            tag_ids = [self._get_tag_id(tag, conn) if self._tag_exists(tag, conn) else -1 for tag in tags]

            q_marks = ','.join('?' for _ in tag_ids)
            cur.execute(f"""
                SELECT fp.pic_id
                FROM fav_pics fp
                JOIN pics_tags pt ON fp.pic_id = pt.pic_id
                WHERE fp.user_id = ?
                AND pt.tag_id IN ({q_marks})
                GROUP BY fp.pic_id
                HAVING COUNT(DISTINCT pt.tag_id) = ?
            """, (user_id, *tag_ids, len(tag_ids)))

            return [row[0] for row in cur.fetchall()]