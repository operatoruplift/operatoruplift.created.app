# News Scout - AI News Monitoring Agent

## Overview

News Scout is an intelligent news monitoring agent that tracks AI developments, aggregates content from RSS feeds, removes duplicates, and provides AI-powered summaries and trend analysis.

## Features

### 📰 News Aggregation
- **RSS Feed Monitoring**: Track multiple news sources
- **Content Extraction**: Full article text extraction
- **Deduplication**: Intelligent duplicate detection
- **Categorization**: Automatic topic classification

### 🤖 AI-Powered Analysis
- **Summarization**: Concise article summaries
- **Trend Detection**: Identify emerging topics
- **Sentiment Analysis**: Track sentiment trends
- **Entity Extraction**: Key people, companies, technologies

### 📊 Reporting
- **Daily Digests**: Curated news summaries
- **Weekly Reports**: Trend analysis
- **Custom Alerts**: Notify on specific topics
- **Export**: HTML, PDF, Markdown formats

## Installation

```bash
pip install -r requirements.txt
mkdir -p data logs reports
```

## Configuration

Edit `agent.yaml`:

```yaml
name: news-scout
version: 1.0.0

settings:
  feeds:
    - name: "TechCrunch AI"
      url: "https://techcrunch.com/tag/artificial-intelligence/feed/"
      category: "ai"
    
    - name: "MIT Technology Review"
      url: "https://www.technologyreview.com/feed/"
      category: "research"
  
  monitoring:
    poll_interval: 3600  # 1 hour
    max_articles_per_feed: 50
  
  analysis:
    summarization: true
    sentiment: true
    trends: true
  
  notifications:
    daily_digest: true
    digest_time: "09:00"
    alert_keywords:
      - "breakthrough"
      - "GPT-5"
      - "AGI"
```

## Usage

```bash
# Start monitoring
python main.py --monitor

# Fetch latest news
python main.py --fetch

# Generate daily digest
python main.py --digest

# Search articles
python main.py --search "GPT-4"

# Analyze trends
python main.py --trends --days 7
```

## Example Output

```
=== AI News Digest - 2024-01-15 ===

Top Stories:

1. OpenAI Announces GPT-4.5
   Source: TechCrunch | Sentiment: Positive
   Summary: OpenAI released GPT-4.5 with improved reasoning...
   
2. New AI Regulation Framework
   Source: MIT Tech Review | Sentiment: Neutral
   Summary: European Union proposes comprehensive AI regulation...

Emerging Trends:
- Multimodal AI models
- AI safety research
- Open source LLMs

Most Mentioned:
- Companies: OpenAI, Google, Microsoft
- People: Sam Altman, Demis Hassabis
- Technologies: GPT-4, Claude, Gemini
```

## License

Provided as-is for educational purposes.

---

**Stay informed. 📰**