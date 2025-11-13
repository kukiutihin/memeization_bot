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
                CREATE TABLE IF NOT EXISTS tags_match (
                    tag_a INTEGER NOT NULL REFERENCES tags(id),
                    tag_b INTEGER NOT NULL REFERENCES tags(id),
                    match FLOAT DEFAULT 0,
                    PRIMARY KEY (tag_a, tag_b),
                    CHECK (tag_a < tag_b)
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS ghosts (
                    tag INTEGER NOT NULL REFERENCES tags(id),
                    his_ghost INTEGER NOT NULL REFERENCES tags(id),
                    PRIMARY KEY (tag, his_ghost),
                    CHECK (tag < his_ghost)
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


    def _update_tags_match(self, ghosts_a: list[int], ghosts_b: list[int], conn: sqlite3.Connection):
        cur = conn.cursor()

        set_a = set(ghosts_a)
        set_b = set(ghosts_b)

        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        similarity = intersection / union if union != 0 else 0.0

        for tag_a in set_a:
            for tag_b in set_b:
                if tag_a == tag_b:
                    continue

                t1, t2 = sorted([tag_a, tag_b])

                cur.execute("""
                    INSERT INTO tags_match (tag_a, tag_b, match)
                    VALUES (?, ?, ?)
                """, (t1, t2, similarity))


    def _get_ghosts_for_tag(self, tag_id: int, conn: sqlite3.Connection, limit: int) -> list[int]:
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

        return [row[0] for row in cur.fetchall()]


    def _rewrite_ghosts_for_tag(self, tag_id: int, ghosts: list[int], conn: sqlite3.Connection):
        cur = conn.cursor()
        cur.execute("DELETE FROM ghosts WHERE tag = ? OR his_ghost = ?", (tag_id, tag_id))

        for ghost_id in ghosts:
            a, b = sorted([tag_id, ghost_id])
            cur.execute("INSERT OR IGNORE INTO ghosts(tag, his_ghost) VALUES (?, ?)", (a, b))

    
    def _rewrite_tags(self, tags: list[str], conn: sqlite3.Connection, limit: int):
        ghost_cache = {}

        for tag_str in tags:
            tag_id = self._get_tag_id(tag=tag_str, conn=conn)
            ghosts = self._get_ghosts_for_tag(tag_id, conn, limit)
            ghost_cache[tag_id] = ghosts

            self._rewrite_ghosts_for_tag(tag_id, ghosts, conn)

        for a, ghosts_a in ghost_cache.items():
            for b, ghosts_b in ghost_cache.items():
                if a >= b:
                    continue
                
                self._update_tags_match(ghosts_a, ghosts_b, conn)

        conn.commit()


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

            entry = cur.fetchone()          

            return bool(entry[0])


    def _get_pic_tags(self, pic_id: int, conn: sqlite3.Connection) -> set[int]:
        cur = conn.cursor()
        cur.execute("SELECT tag_id FROM pics_tags WHERE pic_id = ?", (pic_id,))

        return {row[0] for row in cur.fetchall()}


    def _expand_tags_with_ghosts(self, tags: set[int], conn: sqlite3.Connection) -> set[int]:
        if not tags:
            return set()
        
        cur = conn.cursor()
        cur.execute(f"""
            SELECT tag, his_ghost FROM ghosts
            WHERE tag IN ({','.join('?'*len(tags))}) 
            OR his_ghost IN ({','.join('?'*len(tags))})
        """, tuple(tags)*2)
        ghost_rows = cur.fetchall()

        expanded = set(tags)
        for a, b in ghost_rows:
            if a in expanded or b in expanded:
                expanded.update([a, b])

        return expanded


    def _jaccard_similarity(self, set1: set[int], set2: set[int]) -> float:
        if not set1 and not set2:
            return 0.0
        intersection = set1 & set2
        union = set1 | set2

        return len(intersection) / len(union)


    def _match_tags_pic(self, pic_id: int, tags: list[int]) -> float:
        with self._connect() as conn:
            if not tags:
                return 0.0

            pic_tags = self._get_pic_tags(pic_id)
            if not pic_tags:
                return 0.0

            pic_tags_expanded = self._expand_tags_with_ghosts(pic_tags, conn)
            tags_expanded = self._expand_tags_with_ghosts(set(tags), conn)

            return self._jaccard_similarity(pic_tags_expanded, tags_expanded)


    def _find_favs(self, user_id: int, tags: list[int]) -> list[int]:
        if not tags:
            return []

        with self._connect() as conn:
            cur = conn.cursor()
            q_marks = ",".join("?" for _ in tags)

            cur.execute(f"""
                SELECT pt.pic_id, COUNT(*) as matches
                FROM fav_pics fp
                JOIN pics_tags pt ON fp.pic_id = pt.pic_id
                WHERE fp.user_id = ?
                AND pt.tag_id IN ({q_marks})
                GROUP BY pt.pic_id
                ORDER BY matches DESC
            """, (user_id, *tags))

            return cur.fetchall()


    def _find_global(self, tags: list[int], threshold: float, need: int, batch_size: int) -> list[int]: # TODO threshold, need, batch_size in config
        if not tags:
            return []

        with self._connect() as conn:
            cur = conn.cursor()

            result = []

            while len(result) < need:
                cur.execute("""
                    SELECT id
                    FROM pics
                    ORDER BY RANDOM()
                    LIMIT ?
                """, (batch_size,))

                batch = [r[0] for r in cur.fetchall()]
                if not batch:
                    break  

                for pic_id in batch:
                    score = self._match_tags_pic(pic_id, tags)
                    if score >= threshold:
                        result.append(pic_id)
                        if len(result) >= need:
                            break

            return result


    def find(self, tg_id: int, tags: list[str]):
        with self._connect() as conn:
            user_id = self._get_user_id(tg_id, conn)

            tag_ids = []
            for tag in tags:
                tag_id = self._get_tag_id(tag, conn)
                if tag_id is None:
                    return [], [] 
                tag_ids.append(tag_id)

        favs = self._find_favs(user_id, tag_ids)
        global_sim = self._find_global(tag_ids)

        return favs, global_sim


    def remove_fav(self, tg_id, pid):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                DELETE FROM fav_pics
                WHERE user_id = ? AND pic_id = ?
                """,
                (self._get_user_id(tg_id, conn), pid)
            )
        conn.commit()

