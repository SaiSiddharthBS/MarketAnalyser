import sqlite3
import time
import pickle
import threading
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "marketpulse_cache.db")
REDIS_URL = os.getenv("REDIS_URL")

try:
    if REDIS_URL:
        import redis
        HAS_REDIS = True
    else:
        HAS_REDIS = False
except ImportError:
    HAS_REDIS = False

class DataCache:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DataCache, cls).__new__(cls)
                cls._instance._init_db()
        return cls._instance

    def _init_db(self):
        self.hits = 0
        self.misses = 0
        
        if HAS_REDIS and REDIS_URL:
            try:
                self.redis_client = redis.from_url(REDIS_URL)
                self.use_redis = True
                print("✅ Redis Caching Layer initialized")
                return
            except Exception as e:
                print(f"❌ Redis connection failed, falling back to SQLite: {e}")
                self.use_redis = False
        else:
            self.use_redis = False
            
        with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS cache_store (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    expires_at INTEGER
                )
            ''')
            conn.commit()

    def get(self, key, ttl=None):
        if self.use_redis:
            try:
                val = self.redis_client.get(key)
                if val:
                    self.hits += 1
                    return pickle.loads(val)
                self.misses += 1
                return None
            except Exception:
                pass # Fallback to sqlite logic if redis errors
                
        with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value, expires_at FROM cache_store WHERE key=?", (key,))
            row = cursor.fetchone()
            
            if row:
                value_blob, expires_at = row
                if expires_at is None or expires_at > int(time.time()):
                    self.hits += 1
                    try:
                        return pickle.loads(value_blob)
                    except Exception:
                        pass # Corrupted pickle
                else:
                    # Clean up expired
                    cursor.execute("DELETE FROM cache_store WHERE key=?", (key,))
                    conn.commit()
            
            self.misses += 1
            return None

    def set(self, key, value, ttl=None):
        value_blob = pickle.dumps(value)
        
        if self.use_redis:
            try:
                if ttl:
                    self.redis_client.setex(key, ttl, value_blob)
                else:
                    self.redis_client.set(key, value_blob)
                return
            except Exception:
                pass
                
        expires_at = int(time.time()) + ttl if ttl else None
        with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO cache_store (key, value, expires_at)
                VALUES (?, ?, ?)
            ''', (key, value_blob, expires_at))
            conn.commit()

    def get_stats(self):
        total = self.hits + self.misses
        hit_ratio = (self.hits / total * 100) if total > 0 else 0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_ratio_percent": round(hit_ratio, 2)
        }

# Global singleton
cache = DataCache()
