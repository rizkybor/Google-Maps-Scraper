# Google Maps Scraper 🗺️

A robust Python-based scraper for extracting business information from Google Maps using Playwright. Features anti-detection measures, auto-scrolling, and multiple export formats.

## Features ✨

- **Robust Scraping**: Uses Playwright for reliable browser automation
- **Anti-Detection**: Custom user-agent, random delays, and stealth scripts
- **Auto-Scrolling**: Automatically loads all available business results
- **Multiple Export Formats**: Save data as CSV, Excel, or both
- **Comprehensive Data Extraction**: Name, Rating, Reviews Count, Category, Address, Website, Phone Number
- **AI Analysis**: Integrate with Groq LLM (`meta-llama/llama-4-scout-17b-16e-instruct`) to automatically analyze and summarize top scraped businesses
- **Error Handling**: Graceful handling of missing elements and network issues
- **Configurable**: Command-line arguments for flexible usage

## Installation 🚀

### Quick Setup
```bash
# Clone or download the project
cd Google-Maps-Scraper

# Run the automated setup script
python setup.py
```

### Manual Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
playwright install-deps chromium
```

## Usage 📖

### Basic Usage
```bash
# Scrape restaurants in New York
python main.py "restaurants in New York"

# Scrape with custom options
python main.py "coffee shops in Los Angeles" --max-results 100 --headless
```

### Command Line Options
```bash
python main.py --help
```

**Available Options:**
- `query` (required): Search query (e.g., "restaurants in New York")
- `--headless`: Run browser in headless mode (default: False)
- `--max-results`: Maximum number of results to scrape (default: 50)
- `--delay`: Delay between interactions in seconds (default: 2.0)
- `--output-format`: Output format: csv, excel, or both (default: both)
- `--ai-analyze`: Run AI analysis on the results using Groq LLM (requires `GROQ_API_KEY` in `.env`)

### Examples

```bash
# Basic search
python main.py "pizza restaurants in Chicago"

# Search and run AI analysis on the top results
python main.py "coffee shops in Seattle" --ai-analyze

# Headless mode with more results
python main.py "hotels in Miami" --headless --max-results 200

# Only CSV output with custom delay
python main.py "gyms in Seattle" --output-format csv --delay 3

# Excel output only
python main.py "dentists in Boston" --output-format excel
```

## Output 📊

The scraper extracts the following information for each business:

- **Name**: Business name
- **Rating**: Star rating (e.g., 4.5)
- **Reviews Count**: Number of reviews
- **Category**: Business category (e.g., Restaurant, Hotel)
- **Address**: Full address
- **Website**: Business website (if available)
- **Phone**: Contact phone number (if available)

Output files are saved in the `output/` directory with timestamps:
- `google_maps_results_YYYYMMDD_HHMMSS.csv`
- `google_maps_results_YYYYMMDD_HHMMSS.xlsx`

## Anti-Detection Features 🛡️

- **Random Delays**: 1-3 second delays between interactions
- **Custom User-Agent**: Mimics real Chrome browser
- **Stealth Scripts**: Removes webdriver properties and adds Chrome runtime
- **Browser Arguments**: Multiple anti-detection browser flags
- **Human-like Behavior**: Realistic scrolling and interaction patterns

## Project Structure 📁

```
Google-Maps-Scraper/
├── main.py              # Entry point with CLI interface
├── scraper.py           # Core scraping logic
├── requirements.txt     # Python dependencies
├── setup.py            # Automated setup script
├── README.md           # This file
├── output/             # Output directory (created automatically)
└── .env                # Configuration file (created by setup)
```

## Requirements 📋

- Python 3.7+
- Playwright
- Pandas
- OpenPyXL

## Troubleshooting 🔧

### Common Issues

1. **Playwright Installation Issues**
   ```bash
   # Reinstall Playwright browsers
   playwright install chromium
   playwright install-deps chromium
   ```

2. **Permission Errors**
   ```bash
   # Make scripts executable (Linux/Mac)
   chmod +x main.py setup.py
   ```

3. **Browser Detection**
   - Try running with `--headless` flag
   - Increase delay with `--delay 3`
   - Use more specific search queries

4. **No Results Found**
   - Check your internet connection
   - Try different search queries
   - Ensure Google Maps is accessible in your region

### Error Handling

The scraper includes comprehensive error handling for:
- Missing elements (website, phone, etc.)
- Network timeouts
- Browser initialization failures
- Invalid selectors

## Legal Notice ⚖️

This tool is for educational and research purposes only. Users are responsible for complying with Google's Terms of Service and applicable laws. The authors are not responsible for any misuse of this tool.

## Contributing 🤝

Feel free to submit issues, feature requests, or pull requests to improve the scraper.

## License 📄

This project is open source and available under the MIT License.