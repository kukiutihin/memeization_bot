from database.db import Database

# === FUNCTIONS FOR WORKING WITH DATABASE ===

def search_memes_in_db(tg_id: int, tags: str, db: Database, required_match: float, recs_len: int, ghosts: int):
    search_tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
    
    try:
        global_results = db.find(tg_id, search_tags, required_match, recs_len, ghosts)
        return global_results

    except Exception as e:
        print(f"Failed to find in database: {e}")
        return []


def add_meme_to_db(tg_id: int, photo_url: str, tags: list[str], db: Database, ghosts: int, is_private: bool = False):
    try:
        db.add_to(tg_id, is_private, photo_url, tags, ghosts)
        return True

    except Exception as e:
        print(f"Failed to add in database: {e}")
        return False


def add_to_favorites(tg_id: int, pic_id: int, db: Database):
    try:
        db.add_from(tg_id, pic_id)
        return True

    except Exception as e:
        print(f"Failed to add in favorites: {e}")
        return False


def remove_fav(tg_id: int, pic_id: int, db: Database):
    try:
        db.remove_fav(tg_id, pic_id)
        return True

    except Exception as e:
        print(f"Failed to remove from favorites: {e}")
        return False