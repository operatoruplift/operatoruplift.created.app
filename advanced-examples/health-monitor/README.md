# Health Monitor - Personal Health Tracking Agent

## Overview

The Health Monitor is a privacy-first, local-only health tracking agent that helps you log and analyze your personal health data using AI. All data stays on your machine - no cloud services, no data sharing, complete privacy.

## Features

### 📋 Health Logging
- **Natural Language Input**: "Had a headache this morning"
- **Structured Data**: Automatic categorization and tagging
- **Multi-modal**: Track symptoms, medications, meals, exercise, mood
- **Time-based**: Automatic timestamps and duration tracking

### 📈 Trend Analysis
- **Pattern Detection**: Identify recurring symptoms
- **Correlation Analysis**: Find relationships between factors
- **Visualization**: Charts and graphs of health metrics
- **Insights**: AI-powered health observations

### 🔒 Privacy-First
- **100% Local**: SQLite database on your machine
- **No Cloud Sync**: Data never leaves your computer
- **Encrypted Storage**: Optional database encryption
- **Export Control**: You control data exports

### 📤 Export & Backup
- Export to CSV, JSON, or PDF
- Medical-grade formatting
- Share with healthcare providers
- Automated backups

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Create data directory
mkdir -p data logs

# Run initial setup
python main.py --setup
```

## Usage

### Quick Start

```bash
# Log a health entry
python main.py --log "Had mild headache at 2pm, took aspirin"

# View recent entries
python main.py --view --days 7

# Analyze trends
python main.py --analyze

# Generate report
python main.py --report --month 12
```

### Interactive Mode

```bash
python main.py --interactive

# Then use natural language:
> log headache
> what's my sleep pattern this week?
> show me all medications
> analyze my energy levels
```

### Command Line Options

```
Usage: python main.py [OPTIONS]

Options:
  --log TEXT         Log a health entry
  --view             View recent entries
  --analyze          Analyze health trends
  --report           Generate health report
  --export FORMAT    Export data (csv, json, pdf)
  --days N           Number of days to include
  --month N          Month number (1-12)
  --interactive      Start interactive mode
  --setup            Initial setup
```

## Entry Types

### 1. Symptoms
```bash
python main.py --log "headache, severity 7/10, lasted 2 hours"
python main.py --log "feeling tired and sluggish"
python main.py --log "stomach ache after lunch"
```

### 2. Medications
```bash
python main.py --log "took aspirin 500mg for headache"
python main.py --log "started new vitamin D supplement"
```

### 3. Meals
```bash
python main.py --log "breakfast: oatmeal with berries"
python main.py --log "lunch: large coffee, felt jittery after"
```

### 4. Exercise
```bash
python main.py --log "30 min run, felt great"
python main.py --log "skipped gym, too tired"
```

### 5. Sleep
```bash
python main.py --log "slept 7 hours, woke up twice"
python main.py --log "great sleep, 8 hours straight"
```

### 6. Mood
```bash
python main.py --log "feeling anxious today"
python main.py --log "mood: energetic and motivated"
```

## Analysis Features

### Pattern Detection
```bash
python main.py --analyze --pattern headache
```
Output:
```
Headache Pattern Analysis:
- Frequency: 3x per week
- Common time: afternoon (2-4pm)
- Duration: 1-3 hours average
- Possible triggers:
  * Skipping lunch (75% correlation)
  * Poor sleep (<6h) (60% correlation)
  * High stress days (55% correlation)
```

### Correlation Discovery
```bash
python main.py --analyze --correlate
```
Output:
```
Health Correlations Found:
1. Coffee intake → Sleep quality (-0.7)
2. Exercise → Mood (+0.8)
3. Water intake → Energy levels (+0.6)
4. Screen time → Headaches (+0.5)
```

### Trend Visualization
```bash
python main.py --visualize --metric "sleep_hours"
```
Generates charts showing:
- Sleep hours over time
- 7-day moving average
- Trend line
- Anomaly detection

## Database Schema

```sql
CREATE TABLE health_logs (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    entry_type TEXT,  -- symptom, medication, meal, exercise, sleep, mood
    content TEXT,
    severity INTEGER,  -- 1-10 scale
    duration_minutes INTEGER,
    tags TEXT,  -- JSON array
    mood_score INTEGER,  -- 1-10
    parsed_data TEXT,  -- JSON structured data
    notes TEXT
);

CREATE TABLE medications (
    id INTEGER PRIMARY KEY,
    name TEXT,
    dosage TEXT,
    frequency TEXT,
    started_date DATE,
    ended_date DATE,
    prescriber TEXT,
    notes TEXT
);

CREATE TABLE vitals (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    metric_type TEXT,  -- blood_pressure, heart_rate, weight, temperature
    value REAL,
    unit TEXT,
    notes TEXT
);
```

## AI-Powered Features

### Natural Language Processing
The agent uses Gemini to:
- Parse unstructured health logs
- Extract key information (symptoms, severity, timing)
- Categorize entries automatically
- Identify patterns in language

### Insight Generation
```python
# Example insights:
"Your headaches seem to occur more frequently on days with
less than 6 hours of sleep. Consider prioritizing sleep hygiene."

"You reported increased energy levels on days following
exercise. Current exercise frequency: 3x/week."

"Caffeine intake after 2pm correlates with reduced sleep quality.
Consider cutting off caffeine earlier in the day."
```

## Privacy & Security

### Data Storage
- All data in local SQLite: `./data/health.db`
- Optional AES-256 encryption
- No cloud synchronization by default
- Automatic local backups

### Data Control
```bash
# Encrypt database
python main.py --encrypt

# Create backup
python main.py --backup

# Delete all data (with confirmation)
python main.py --purge

# Export for medical use
python main.py --export-medical
```

### HIPAA Considerations
While this agent prioritizes privacy:
- It is NOT a medical device
- Not intended for diagnosis
- Not HIPAA-certified
- Consult healthcare professionals

## Integration with Healthcare

### Export for Doctors
```bash
# Generate professional medical report
python main.py --medical-report --from 2024-01-01 --to 2024-03-31
```

Creates a PDF with:
- Chronological symptom log
- Medication history
- Vital signs charts
- Pattern analysis
- Formatted for medical review

### Data Sharing
```bash
# Create shareable report (sanitized)
python main.py --share --anonymize
```

## Advanced Usage

### Scheduled Logging

Create daily prompts:
```yaml
# In agent.yaml
triggers:
  - type: schedule
    cron: "0 9,21 * * *"  # Morning and evening
    action: prompt_user
    prompt: "How are you feeling?"
```

### Integrations

**Apple Health (macOS):**
```bash
python main.py --import-apple-health
```

**Google Fit (Android):**
```bash
python main.py --import-google-fit --file export.json
```

**Fitbit:**
```bash
python main.py --import-fitbit --token $FITBIT_TOKEN
```

### Custom Metrics

```python
# Track custom health metrics
from health_monitor import HealthLogger

logger = HealthLogger()
logger.add_custom_metric(
    name="hydration",
    unit="oz",
    target=64,
    reminder_frequency="hourly"
)
```

## Machine Learning Features

### Predictive Analysis
```bash
python main.py --predict --symptom headache
```
Output:
```
Based on your patterns:
- 70% chance of headache tomorrow if sleep < 6h tonight
- 40% chance if you skip lunch
- 20% baseline probability

Preventive suggestions:
- Get 7-8 hours sleep
- Stay hydrated (8+ glasses)
- Regular meal schedule
- Take breaks from screens
```

### Anomaly Detection
```bash
python main.py --detect-anomalies
```

Identifies unusual patterns:
- Sudden changes in baseline
- Concerning symptom clusters
- Medication interaction warnings

## Troubleshooting

### Database Issues
```bash
# Check database integrity
python main.py --check-db

# Repair database
python main.py --repair-db

# Restore from backup
python main.py --restore --file backup-2024-01-01.db
```

### Common Problems

**Entries not saving:**
- Check disk space
- Verify write permissions
- Check database lock

**Analysis not working:**
- Ensure enough data (30+ entries)
- Check Gemini API configuration
- Review logs for errors

## Best Practices

### Daily Logging
1. **Consistency**: Log at same time daily
2. **Detail**: Include context and severity
3. **Honesty**: Accurate self-reporting
4. **Patterns**: Note any triggers

### Data Quality
1. Use consistent terminology
2. Include severity ratings
3. Note duration when relevant
4. Tag related entries

### Privacy
1. Use strong database password
2. Enable encryption for sensitive data
3. Regular backups to encrypted drive
4. Careful with exports

## API Reference

```python
from health_monitor import HealthMonitor

# Initialize
monitor = HealthMonitor(db_path="./data/health.db")

# Add entry
monitor.log_entry(
    entry_type="symptom",
    content="headache",
    severity=7,
    duration=120  # minutes
)

# Get entries
entries = monitor.get_entries(days=7)

# Analyze
analysis = monitor.analyze_patterns(symptom="headache")

# Generate report
report = monitor.generate_report(
    start_date="2024-01-01",
    end_date="2024-01-31",
    format="pdf"
)
```

## Example Workflows

### Morning Routine
```bash
#!/bin/bash
# morning-check.sh

python main.py --log "woke up at $(date +%H:%M)"
python main.py --view --days 1
python main.py --predict --today
```

### Evening Review
```bash
#!/bin/bash
# evening-review.sh

python main.py --log "sleep: $(read -p 'Hours slept: ' h; echo $h) hours"
python main.py --analyze --today
python main.py --export --format json --backup
```

## Contributing

This is a personal health tool. Modifications should:
- Maintain privacy-first approach
- Never add cloud dependencies
- Preserve data security
- Follow medical ethics

## Disclaimer

**Important Medical Disclaimer:**

This tool is for personal tracking only and is NOT:
- A medical device
- A substitute for professional medical advice
- Intended for diagnosis or treatment
- Approved by any medical regulatory body

Always consult healthcare professionals for medical concerns.

## License

Provided as-is for personal use. Handle health data responsibly.

---

**Your health, your data, your control. 🌱**