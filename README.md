# Fireworks: SEC Filing Validator

Automated pipeline to download, validate, clean, summarize, and alert on SEC EDGAR filings using Arelle.

## Features
- Daily validation via systemd
- Cleans nulls from Arelle logs
- Sends email alerts if errors found
- Generates readable CSV summaries
- Deletes old files automatically

## Setup
1. Clone this repo
2. Set up `.env` with your Gmail app password
3. Install Python 3 and Arelle
4. Enable the systemd timer

## License
MIT
