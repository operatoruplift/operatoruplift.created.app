#!/usr/bin/env python3
"""
News Scout - AI News Monitoring Agent

Tracks AI news from RSS feeds with intelligent summarization.

Usage:
    python main.py --monitor
    python main.py --digest
"""

import os
import sys
import yaml
import sqlite3
import logging
import argparse
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import xml.etree.ElementTree as ET

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/news-scout.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('news-scout')


class NewsDatabase:
    """Manages news database"""
    
    def __init__(self, db_path: str = "./data/news.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                content TEXT,
                summary TEXT,
                source TEXT,
                category TEXT,
                published_date DATETIME,
                fetched_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                sentiment TEXT,
                sentiment_score REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id TEXT,
                entity_type TEXT,
                entity_name TEXT,
                FOREIGN KEY (article_id) REFERENCES articles(id)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_articles_date 
            ON articles(published_date)
        ''')
        
        conn.commit()
        conn.close()
    
    def add_article(self, article: Dict) -> bool:
        """Add article to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO articles (
                    id, title, url, content, summary, source, category,
                    published_date, sentiment, sentiment_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                article['id'], article['title'], article['url'],
                article.get('content'), article.get('summary'),
                article['source'], article.get('category'),
                article.get('published_date'),
                article.get('sentiment'), article.get('sentiment_score')
            ))
            
            conn.commit()
            return True
        
        except sqlite3.IntegrityError:
            return False  # Duplicate
        finally:
            conn.close()
    
    def get_recent_articles(self, days: int = 7) -> List[Dict]:
        """Get recent articles"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute(
            'SELECT * FROM articles WHERE published_date >= ? ORDER BY published_date DESC',
            (start_date,)
        )
        
        articles = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return articles


class RSSFetcher:
    """Fetches RSS feeds"""
    
    def __init__(self):
        self.session = None
    
    def fetch_feed(self, url: str) -> List[Dict]:
        """Fetch and parse RSS feed"""
        try:
            import requests
        except ImportError:
            logger.error("requests not installed. Run: pip install requests")
            return []
        
        try:
            logger.info(f"Fetching feed: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            return self._parse_rss(response.content)
        
        except Exception as e:
            logger.error(f"Error fetching feed {url}: {e}")
            return []
    
    def _parse_rss(self, xml_content: bytes) -> List[Dict]:
        """Parse RSS XML"""
        articles = []
        
        try:
            root = ET.fromstring(xml_content)
            
            # Handle different RSS formats
            items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')
            
            for item in items:
                article = self._parse_item(item)
                if article:
                    articles.append(article)
        
        except Exception as e:
            logger.error(f"Error parsing RSS: {e}")
        
        return articles
    
    def _parse_item(self, item) -> Dict:
        """Parse RSS item"""
        try:
            title = item.findtext('title') or item.findtext('{http://www.w3.org/2005/Atom}title')
            link = item.findtext('link') or item.findtext('{http://www.w3.org/2005/Atom}link')
            description = item.findtext('description') or item.findtext('{http://www.w3.org/2005/Atom}summary')
            pub_date = item.findtext('pubDate') or item.findtext('{http://www.w3.org/2005/Atom}published')
            
            if not title or not link:
                return None
            
            article_id = hashlib.md5(link.encode()).hexdigest()
            
            return {
                'id': article_id,
                'title': title,
                'url': link,
                'content': description,
                'published_date': pub_date
            }
        
        except Exception as e:
            logger.error(f"Error parsing item: {e}")
            return None


class NewsScout:
    """Main news scout agent"""
    
    def __init__(self, config_path: str = "agent.yaml"):
        self.config = self._load_config(config_path)
        self.db = NewsDatabase()
        self.fetcher = RSSFetcher()
        logger.info("News Scout initialized")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    def fetch_all_feeds(self):
        """Fetch all configured feeds"""
        feeds = self.config.get('settings', {}).get('feeds', [])
        
        logger.info(f"Fetching {len(feeds)} feeds")
        new_articles = 0
        
        for feed in feeds:
            articles = self.fetcher.fetch_feed(feed['url'])
            
            for article in articles:
                article['source'] = feed['name']
                article['category'] = feed.get('category')
                
                if self.db.add_article(article):
                    new_articles += 1
                    logger.info(f"New article: {article['title'][:50]}...")
        
        logger.info(f"Fetched {new_articles} new articles")
        return new_articles
    
    def generate_digest(self, days: int = 1) -> str:
        """Generate daily digest"""
        articles = self.db.get_recent_articles(days)
        
        digest = f"""
{'='*80}
AI News Digest - {datetime.now().strftime('%Y-%m-%d')}
{'='*80}

Articles from last {days} day(s): {len(articles)}

"""
        
        for i, article in enumerate(articles[:10], 1):
            digest += f"{i}. {article['title']}\n"
            digest += f"   Source: {article['source']}\n"
            if article['summary']:
                digest += f"   Summary: {article['summary'][:100]}...\n"
            digest += f"   URL: {article['url']}\n\n"
        
        # Save digest
        digest_path = Path(f"./reports/digest-{datetime.now().strftime('%Y%m%d')}.txt")
        digest_path.parent.mkdir(exist_ok=True)
        
        with open(digest_path, 'w') as f:
            f.write(digest)
        
        logger.info(f"Digest saved to: {digest_path}")
        print(digest)
        
        return digest
    
    def search_articles(self, query: str, days: int = 30) -> List[Dict]:
        """Search articles"""
        articles = self.db.get_recent_articles(days)
        
        results = [
            article for article in articles
            if query.lower() in article['title'].lower() or
               (article['content'] and query.lower() in article['content'].lower())
        ]
        
        return results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='News Scout - AI News Monitoring')
    parser.add_argument('--monitor', action='store_true', help='Start monitoring')
    parser.add_argument('--fetch', action='store_true', help='Fetch latest news')
    parser.add_argument('--digest', action='store_true', help='Generate digest')
    parser.add_argument('--search', type=str, help='Search articles')
    parser.add_argument('--days', type=int, default=7, help='Number of days')
    
    args = parser.parse_args()
    
    # Create directories
    for directory in ['data', 'logs', 'reports']:
        Path(directory).mkdir(exist_ok=True)
    
    scout = NewsScout()
    
    if args.monitor or args.fetch:
        scout.fetch_all_feeds()
    
    if args.digest:
        scout.generate_digest(days=args.days)
    
    if args.search:
        results = scout.search_articles(args.search, days=args.days)
        print(f"\nFound {len(results)} articles matching '{args.search}':\n")
        for i, article in enumerate(results, 1):
            print(f"{i}. {article['title']}")
            print(f"   {article['url']}\n")
    
    if not any([args.monitor, args.fetch, args.digest, args.search]):
        parser.print_help()


if __name__ == '__main__':
    main()