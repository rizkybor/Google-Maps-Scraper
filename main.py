#!/usr/bin/env python3
"""
Google Maps Scraper - Main Entry Point
A robust scraper for extracting business information from Google Maps using Playwright
"""

import argparse
import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
from scraper import GoogleMapsScraper


def setup_output_directory(output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def generate_filename(base_name, extension):
    """Generate filename with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}.{extension}"


async def main():
    parser = argparse.ArgumentParser(
        description="Google Maps Scraper - Extract business information from Google Maps"
    )
    parser.add_argument(
        "query",
        type=str,
        help="Search query (e.g., 'restaurants in New York')"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="Run browser in headless mode"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=50,
        help="Maximum number of results to scrape (default: 50)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=None,
        help="Delay antar interaksi (detik). Jika diisi, akan menjadi delay tetap (tanpa random)."
    )
    parser.add_argument(
        "--output-format",
        type=str,
        choices=["csv", "excel", "both"],
        default="both",
        help="Output format: csv, excel, or both (default: both)"
    )
    parser.add_argument(
        "--ai-analyze",
        action="store_true",
        help="Analyze the scraped results using Groq AI"
    )

    args = parser.parse_args()

    # Load environment variables (e.g. GROQ_API_KEY)
    load_dotenv()

    # Setup output directory
    output_dir = setup_output_directory(os.getenv("OUTPUT_DIRECTORY", "output"))

    delay_min = float(os.getenv("DEFAULT_DELAY_MIN", "1"))
    delay_max = float(os.getenv("DEFAULT_DELAY_MAX", "3"))
    delay_range = (delay_min, delay_max)
    if args.delay is not None:
        delay_range = (args.delay, args.delay)

    # Initialize scraper
    scraper = GoogleMapsScraper(
        headless=args.headless,
        delay_range=delay_range,
        max_results=args.max_results
    )

    try:
        print(f"🔍 Starting Google Maps scraper for query: '{args.query}'")
        print(f"📊 Maximum results: {args.max_results}")
        print(f"🌐 Headless mode: {'Yes' if args.headless else 'No'}")
        print("=" * 50)

        # Run scraper
        results = await scraper.scrape(args.query)

        if not results:
            print("❌ No results found or scraping failed")
            return

        print(f"✅ Successfully scraped {len(results)} businesses")

        # Generate output files
        if args.output_format in ["csv", "both"]:
            csv_filename = generate_filename("google_maps_results", "csv")
            csv_path = os.path.join(output_dir, csv_filename)
            try:
                scraper.save_to_csv(results, csv_path)
                print(f"📁 CSV saved: {csv_path}")
            except OSError as e:
                if getattr(e, "errno", None) == 28:
                    print(f"❌ Gagal menyimpan CSV (disk penuh): {csv_path}")
                else:
                    raise

        if args.output_format in ["excel", "both"]:
            excel_filename = generate_filename("google_maps_results", "xlsx")
            excel_path = os.path.join(output_dir, excel_filename)
            try:
                scraper.save_to_excel(results, excel_path)
                print(f"📁 Excel saved: {excel_path}")
            except OSError as e:
                if getattr(e, "errno", None) == 28:
                    print(f"❌ Gagal menyimpan Excel (disk penuh): {excel_path}")
                else:
                    raise

        # Run AI Analysis if requested
        if args.ai_analyze:
            print("\n" + "=" * 50)
            analysis_result = scraper.analyze_with_ai(results)
            print("=" * 50)
            print("🤖 AI Analysis Report:\n")
            print(analysis_result)
            print("\n" + "=" * 50)

            # Save analysis to file
            analysis_filename = generate_filename("ai_analysis", "txt")
            analysis_path = os.path.join(output_dir, analysis_filename)
            try:
                with open(analysis_path, "w", encoding="utf-8") as f:
                    f.write(analysis_result)
                print(f"📁 AI Analysis saved: {analysis_path}")
            except OSError as e:
                if getattr(e, "errno", None) == 28:
                    print(f"❌ Gagal menyimpan AI analysis (disk penuh): {analysis_path}")
                else:
                    raise

        print("🎉 Scraping completed successfully!")

    except KeyboardInterrupt:
        print("\n⚠️  Scraping interrupted by user")
    except Exception as e:
        print(f"❌ Error during scraping: {str(e)}")
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
