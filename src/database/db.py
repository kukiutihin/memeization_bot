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
                    is_private INTEGER NOT NULL,
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
                CREATE TABLE IF NOT EXISTS ghosts (
                    tag INTEGER NOT NULL REFERENCES tags(id),
                    his_ghost INTEGER NOT NULL REFERENCES tags(id),
                    PRIMARY KEY (tag, his_ghost)
                );
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_ghosts_tag ON ghosts(tag)
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_ghosts_ghost ON ghosts(his_ghost)
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
    

    def _get_pic_tags(self, pic_id: int, conn: sqlite3.Connection) -> list[str]:
        cur = conn.cursor()
        cur.execute("""
                SELECT tag_id
                FROM pics_tags
                WHERE pic_id = ?
            """, (pic_id,))
        
        return [row[0] for row in cur.fetchall()]
        

    def _add_to_table(self, tg_id: int, is_private: bool, storage: str, tags: list[str], conn: sqlite3.Connection) -> int:
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
        return pic_id


    def _get_ghosts_for_tag(self, tag_id: int, limit: int, conn: sqlite3.Connection) -> list[int]:
        cur = conn.cursor()

        cur.execute("""
            SELECT pt2.tag_id, COUNT(*) as tcount
            FROM pics_tags pt1
            JOIN pics_tags pt2 ON pt1.pic_id = pt2.pic_id
            WHERE pt1.tag_id = ? AND pt2.tag_id != ?
            GROUP BY pt2.tag_id
            ORDER BY tcount DESC
            LIMIT ?
        """, (tag_id, tag_id, limit))

        return [row[0] for row in cur.fetchall()] + [tag_id]


    def _rewrite_ghosts_for_tag(self, tag_id: int, ghosts: list[int], conn: sqlite3.Connection):
        cur = conn.cursor()
        cur.execute("DELETE FROM ghosts WHERE tag = ?", (tag_id,))

        for ghost_id in ghosts:
            cur.execute("INSERT OR IGNORE INTO ghosts(tag, his_ghost) VALUES (?, ?)", (tag_id, ghost_id))
    
    
    def _update_tags_ghosts(self, tags: list[str], limit: int, conn: sqlite3.Connection):
        for tag_str in tags:
            tag_id = self._get_tag_id(tag_str, conn)
            ghosts = self._get_ghosts_for_tag(tag_id, limit, conn)
            self._rewrite_ghosts_for_tag(tag_id, ghosts, conn)

        conn.commit()


    def add_to(self, tg_id: int, is_private: bool, storage: str, tags: list[str], limit: int):
        with self._connect() as conn:
            pic_id = self._add_to_table(tg_id, is_private, storage, tags, conn)
            self._update_tags_ghosts(pic_id, tags, limit, conn)


    def add_from(self, tg_id: int, pic_id: int):
        with self._connect() as conn:
            cur = conn.cursor()

            user_id = self._get_user_id(tg_id=tg_id, conn=conn)

            cur.execute("""
                    INSERT INTO fav_pics (user_id, pic_id)
                    SELECT ?, ?
                    FROM pics
                    WHERE id = ?
                    AND (is_private = 0 OR user_id = ?);
                """, (user_id, pic_id, pic_id, user_id))

            conn.commit()


    def transfer(self, tg_id_from: int, tg_id_to: int):
        with self._connect() as conn:
            cur = conn.cursor()

            from_uid = self._get_user_id(tg_id=tg_id_from, conn=conn)
            to_uid = self._get_user_id(tg_id=tg_id_to, conn=conn)

            cur.execute("""
                UPDATE fav_pic
                SET user_id = ?
                WHERE user_id = ?
            """, (to_uid, from_uid))


    def is_private(self, pid: int) -> bool:
        with self._connect() as conn:
            cur = conn.cursor()

            cur.execute("""
                SELECT is_private
                FROM pics
                WHERE id = ?
            """, (pid, ))
  
            return bool(cur.fetchone()[0])


    def _find_favs(self, user_id: int, tags: list[int], conn: sqlite3.Connection) -> list[int]:
        cur = conn.cursor()
        if not tags:
            cur.execute(f"""
                    SELECT fp.pic_id
                    FROM fav_pics fp
                    WHERE fp.user_id = ?
                """, (user_id,))
            
            return [row[0] for row in cur.fetchall()]

        cur.execute(f"""
            SELECT pt.pic_id, COUNT(*) as matches
            FROM fav_pics fp
            JOIN pics_tags pt ON fp.pic_id = pt.pic_id
            WHERE fp.user_id = ?
            AND pt.tag_id IN ({','.join('?'*len(tags))})
            GROUP BY pt.pic_id
            ORDER BY matches DESC
        """, (user_id, *tags))

        return [row[0] for row in cur.fetchall()]
    

    def _jaccard_similarity(self, ghost_a: list[int], ghost_b: set[int]) -> float:
        set_a = set(ghost_a)
        set_b = set(ghost_b)

        if not set_a and not set_b:
            return 0.0
        intersection = set_a & set_b
        union = set_a | set_b

        return len(intersection) / len(union)


    def _get_pic_ghosts(self, pic_id: int, limit: int, conn: sqlite3.Connection) -> set[int]:
        all_ghosts = []
        tags = self._get_pic_tags(pic_id, conn)
        for tag in tags:
            ghosts = self._get_ghosts_for_tag(tag, limit, conn)
            all_ghosts += ghosts

        return all_ghosts


    def _find_global(self, tags: list[int], threshold: float, recommendations_len: int, limit:int, conn: sqlite3.Connection) -> list[int]:
        if not tags:
            return []

        cur = conn.cursor()

        result = []
        cur.execute("SELECT id FROM pics ORDER BY RANDOM()")
        all_pics = [r[0] for r in cur.fetchall()]

        for pic_id in all_pics:
            pic_tags = self._get_pic_ghosts(pic_id, limit, conn)
            score = self._jaccard_similarity(tags, pic_tags)
            if score >= threshold:
                result.append(pic_id)
                if len(result) >= recommendations_len:
                    break

        return result


    def find(self, tg_id: int, tags: list[str], threshold: float, recommendations_len: int, limit: int) -> list[int]:
        with self._connect() as conn:
            user_id = self._get_user_id(tg_id, conn)

            tag_ids = []
            for tag in tags:
                if not self._tag_exists(tag, conn):
                    return []
                
                tag_ids.append(self._get_tag_id(tag, conn))

            favs = self._find_favs(user_id, tag_ids, conn)
            global_sim = self._find_global(tag_ids, threshold, recommendations_len, limit, conn)

        return favs + global_sim
