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

# Fireworks

**Fireworks** is an automated SEC filing validator built by Ronnie Lee Sherfey Jr under Aysher Intelligence Agency.

### Features

- Validates investment-related SEC files using Arelle
- Saves detailed validation logs and summaries
- Automatically pushes updates to GitHub twice daily
- Built with Linux, Bash, Python

---

**Maintainer:** rsherfey@aysherintel.com
