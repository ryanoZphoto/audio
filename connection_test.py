import logging
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_postgres():
    """Test PostgreSQL connection"""
    try:
        import psycopg2
        logger.info("Testing PostgreSQL connection...")
        
        conn = psycopg2.connect(
            dbname="railway",
            user="postgres",
            password="YsvFnWeygwfKLPLcNMScRohVdMhLhKcm",
            host="monorail.proxy.rlwy.net",
            port="54967",
            sslmode="require"
        )
        with conn.cursor() as cur:
            cur.execute('SELECT version();')
            version = cur.fetchone()[0]
            logger.info("PostgreSQL Connection: SUCCESS")
            logger.info(f"PostgreSQL version: {version}")
        conn.close()
    except ImportError:
        logger.error("PostgreSQL Connection: FAILED - psycopg2 not installed")
    except Exception as e:
        logger.error(f"PostgreSQL Connection: FAILED - {str(e)}")


def test_redis():
    """Test Redis connection"""
    try:
        import redis
        logger.info("Testing Redis connection...")
        
        r = redis.Redis(
            host="monorail.proxy.rlwy.net",
            port=54967,
            password="YsvFnWeygwfKLPLcNMScRohVdMhLhKcm",
            ssl=True,
            ssl_cert_reqs=None,
            socket_timeout=5,
            socket_connect_timeout=5
        )
        if r.ping():
            logger.info("Redis Connection: SUCCESS")
            info = r.info()
            logger.info(f"Redis version: {info.get('redis_version', 'unknown')}")
        r.close()
    except ImportError:
        logger.error("Redis Connection: FAILED - redis-py not installed")
    except Exception as e:
        logger.error(f"Redis Connection: FAILED - {str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test database connections')
    parser.add_argument('--postgres', action='store_true', help='Test PostgreSQL connection')
    parser.add_argument('--redis', action='store_true', help='Test Redis connection')
    args = parser.parse_args()

    logger.info("=== Testing Database Connections ===")
    
    # If no specific tests are requested, run all tests
    if not args.postgres and not args.redis:
        test_postgres()
        test_redis()
    else:
        if args.postgres:
            test_postgres()
        if args.redis:
            test_redis() 