#!/usr/bin/env python3
"""
Google Maps Scraper - Core Scraping Logic
Robust scraper using Playwright for extracting business information
"""

import asyncio
import re
import urllib.parse
import random
import os
import json
from typing import List, Dict, Optional
import pandas as pd
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage


class GoogleMapsScraper:
    """Google Maps scraper with anti-detection measures"""

    def __init__(
        self,
        headless: bool = False,
        delay_range: tuple = (1, 3),
        max_results: int = 50,
        timeout: int = 30000
    ):
        self.headless = headless
        self.delay_range = delay_range
        self.max_results = max_results
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # Custom user agent to mimic real Chrome browser
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

    async def init_browser(self):
        """Initialize browser with anti-detection settings"""
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            channel="chrome"
        )
        
        self.context = await self.browser.new_context(
            user_agent=self.user_agent,
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="America/New_York"
        )
        
        # Add stealth scripts to avoid detection
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            window.chrome = {
                runtime: {},
                loadTimes: function() {
                    return {
                        commitLoadTime: performance.timing.domContentLoadedEventStart / 1000,
                        connectionInfo: 'h2',
                        finishDocumentLoadTime: performance.timing.domContentLoadedEventEnd / 1000,
                        finishLoadTime: performance.timing.loadEventEnd / 1000,
                        firstPaintAfterLoadTime: 0,
                        firstPaintTime: 0,
                        navigationType: 'Other',
                        npnNegotiatedProtocol: 'h2',
                        requestTime: performance.timing.requestStart / 1000,
                        startLoadTime: performance.timing.requestStart / 1000,
                        wasAlternateProtocolAvailable: false,
                        wasFetchedViaSpdy: true,
                        wasNpnNegotiated: true
                    };
                },
                csi: function() {
                    return {
                        onloadT: Date.now(),
                        pageT: Date.now() - performance.timing.navigationStart,
                        startE: performance.timing.navigationStart,
                        tran: 15
                    };
                }
            };
            
            delete navigator.__proto__.webdriver;
        """)
        
        self.page = await self.context.new_page()
        
        # Set extra HTTP headers
        await self.page.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        })

    async def random_delay(self):
        """Add random delay between interactions"""
        delay = random.uniform(*self.delay_range)
        await asyncio.sleep(delay)

    async def scroll_to_load_all_results(self):
        """Auto-scroll the results sidebar to load all available businesses"""
        if not self.page:
            return
            
        print("📜 Scrolling to load all results...")
        
        # Find the results sidebar
        sidebar_selector = '[role="main"], .section-layout, [data-pane]'
        
        try:
            sidebar = await self.page.wait_for_selector(sidebar_selector, timeout=10000)
            if sidebar:
                previous_count = 0
                same_count_iterations = 0
                max_same_count = 5
                
                while same_count_iterations < max_same_count:
                    # Scroll to bottom of sidebar
                    await sidebar.evaluate("""
                        element => {
                            element.scrollTop = element.scrollHeight;
                        }
                    """)
                    
                    await self.random_delay()
                    
                    # Count current results
                    current_count = await self.page.locator('[data-result-index]').count()
                    
                    if current_count > previous_count:
                        previous_count = current_count
                        same_count_iterations = 0
                        print(f"📊 Loaded {current_count} results so far...")
                    else:
                        same_count_iterations += 1
                    
                    # Stop if we've reached max results
                    if current_count >= self.max_results:
                        break
                        
        except Exception as e:
            print(f"⚠️  Error during scrolling: {e}")

    async def extract_business_info(self, business_element) -> Dict:
        """Extract business information from a single business element"""
        business_data = {
            "name": "",
            "rating": "",
            "reviews_count": "",
            "category": "",
            "address": "",
            "website": "",
            "email": "",
            "phone": "",
            "PIC": "Scrapper by AI"
        }

        try:
            # Extract name
            name_selectors = [
                '.fontHeadlineSmall',
                'h3',
                '[data-result-index] h3',
                '.section-result-title span',
                'div[role="heading"]'
            ]
            
            for selector in name_selectors:
                try:
                    name_element = await business_element.query_selector(selector)
                    if name_element:
                        text = await name_element.text_content()
                        if text and text.strip():
                            business_data["name"] = text.strip()
                            break
                except:
                    continue

            # If name is still empty, try to get the aria-label of the main element
            if not business_data["name"]:
                try:
                    aria_label = await business_element.get_attribute("aria-label")
                    if aria_label:
                        business_data["name"] = aria_label.strip()
                except:
                    pass

            # Only proceed to extract other details if we have a valid name
            # and the name doesn't look like a whole block of text
            if business_data["name"] and len(business_data["name"]) < 100:
                
                # Extract rating
                rating_selectors = [
                    'span[role="img"]',
                    '.section-result-rating',
                    '.rating-text',
                    '[data-result-index] span[role="img"]'
                ]
                
                for selector in rating_selectors:
                    try:
                        rating_element = await business_element.query_selector(selector)
                        if rating_element:
                            rating_text = await rating_element.get_attribute("aria-label") or await rating_element.text_content()
                            if rating_text and ("star" in rating_text.lower() or "bintang" in rating_text.lower() or "." in rating_text or "," in rating_text):
                                rating_text = rating_text.replace(',', '.')
                                rating_match = re.search(r'(\d+\.\d+)', rating_text)
                                if rating_match:
                                    business_data["rating"] = rating_match.group(1)
                                    review_match = re.search(r'(?i)(\d+(?:\.\d+)?)\s*(?:Ulasan|Reviews)', rating_text.replace('.', ''))
                                    if review_match and not business_data["reviews_count"]:
                                        business_data["reviews_count"] = review_match.group(1)
                                    break
                    except:
                        continue

                # Extract reviews count
                reviews_selectors = [
                    'span[role="img"] + span',
                    '.section-result-rating + span',
                    '.reviews-text',
                    'span:has-text("(")'
                ]
                
                for selector in reviews_selectors:
                    try:
                        reviews_element = await business_element.query_selector(selector)
                        if reviews_element:
                            reviews_text = await reviews_element.text_content()
                            if reviews_text and "(" in reviews_text:
                                clean_text = reviews_text.replace('.', '').replace(',', '')
                                reviews_match = re.search(r'\((\d+)\)', clean_text)
                                if reviews_match:
                                    business_data["reviews_count"] = reviews_match.group(1)
                                    break
                    except:
                        continue

                # Extract category and address from the text block
                try:
                    # Look for specific element classes that hold category/address
                    font_elements = await business_element.query_selector_all('.fontBodyMedium')
                    
                    for element in font_elements:
                        text = await element.text_content()
                        if text and "·" in text:
                            # Clean up the text first to remove strange characters
                            clean_text = re.sub(r'[\ue000-\uf8ff]', '', text).strip()
                            parts = [p.strip() for p in clean_text.split("·")]
                            
                            # Sometimes the reviews are hiding in the first part like "4,6(58)"
                            if not business_data["reviews_count"]:
                                for part in parts:
                                    clean_part = part.replace('.', '').replace(',', '')
                                    rev_match = re.search(r'\((\d+)\)', clean_part)
                                    if rev_match:
                                        business_data["reviews_count"] = rev_match.group(1)
                                        break
                                        
                            # Usually the structure is: [Rating (Reviews)] · [Category] · [Address/Location]
                            # Example: "5.0 (12) · Kedai Kopi · Jl. ABC"
                            
                            for i, part in enumerate(parts):
                                # Skip parts that are just ratings/reviews like "5,0(12)"
                                if re.match(r'^[\d\.,\s]+(?:\([\d\.,\s]+\))?$', part):
                                    continue
                                
                                # First text-heavy part is likely the category
                                if not business_data["category"] and len(part) < 50:
                                    # Ensure it's not grabbing the business name or rating
                                    if part != business_data["name"] and not re.match(r'^[\d\.,\s]+(?:\([\d\.,\s]+\))?$', part):
                                        # Sometimes it merges name + rating + category like "First Crack Coffee Rajawali Place  5,0Kedai Kopi"
                                        # Let's clean it up by only taking the actual category words
                                        clean_cat = re.sub(r'^.*?\s+[\d\.,]+\s*', '', part)
                                        
                                        # If the category looks like an address, it means category was missing entirely
                                        if re.search(r'(?i)(Jl\.|Jalan|Kav|RT|RW)', clean_cat):
                                            business_data["address"] = clean_cat.strip()
                                        elif not re.search(r'(?i)(Buka|Tutup|pukul)', clean_cat):
                                            # Avoid things like "Buka Kam pukul 08.30" as category
                                            business_data["category"] = clean_cat.strip() if clean_cat else part.strip()
                                    continue
                                
                                # Next part is likely the address
                                if business_data["category"] and not business_data["address"]:
                                    # Clean up common Google Maps text like "Buka", "Tutup", "Pesan", "Segera tutup"
                                    clean_address = re.sub(r'(Buka|Tutup|Pesan|Segera\s*tutup|Segera).*$', '', part, flags=re.IGNORECASE).strip()
                                    if clean_address and len(clean_address) > 5:
                                        business_data["address"] = clean_address
                                        break
                                        
                            if business_data["category"] and business_data["address"]:
                                break
                except:
                    pass
                
                # Fallback for category and address if the previous method failed
                if not business_data["category"] or not business_data["address"]:
                    try:
                        # Extract the aria-label of the entire element, it often contains the structured info
                        aria_label = await business_element.get_attribute("aria-label")
                        if aria_label:
                            # Typical format: "Gould Coffee & Eatery Setiabudi 4,6(58) · Kedai Kopi ·  · Buka ⋅ Tutup pukul 21.00"
                            
                            # Clean the text
                            clean_label = re.sub(r'[\ue000-\uf8ff]', '', aria_label).strip()
                            parts = [p.strip() for p in clean_label.split("·")]
                            
                            for part in parts:
                                # If it's the name or a rating, skip
                                if business_data["name"] in part or re.match(r'^[\d\.,\s]+(?:\([\d\.,\s]+\))?$', part):
                                    continue
                                
                                # Category fallback
                                if not business_data["category"] and len(part) < 40 and not "Buka" in part and not "Tutup" in part:
                                    business_data["category"] = part
                                    continue
                                    
                                # Address fallback
                                if not business_data["address"] and len(part) > 5:
                                    clean_address = re.sub(r'(Buka|Tutup|Pesan|Segera).*$', '', part, flags=re.IGNORECASE).strip()
                                    if clean_address and clean_address != business_data["category"]:
                                        business_data["address"] = clean_address
                                        break
                    except:
                        pass

        except Exception as e:
            print(f"⚠️  Error extracting business info: {e}")
            
        # Final cleanup of the extracted strings
        for key, value in business_data.items():
            if value and isinstance(value, str):
                # Remove common Google Maps garbage characters and normalize spaces
                clean_val = re.sub(r'[\ue000-\uf8ff\u200e]', '', value).strip()
                # Remove "Buka" or "Tutup" from addresses if it slipped through
                if key == "address":
                    clean_val = re.sub(r'(?i)\s*(Buka|Tutup|Pesan|Segera).*$', '', clean_val).strip()
                business_data[key] = clean_val

        return business_data

    async def _search_website_for_email(self, website_url: str) -> str:
        if not website_url or not self.context:
            return ""

        page = await self.context.new_page()
        try:
            await page.goto(website_url, wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(1)

            mailto = await page.query_selector('a[href^="mailto:"]')
            if mailto:
                href = await mailto.get_attribute("href")
                if href and href.lower().startswith("mailto:"):
                    email = href.split(":", 1)[1].split("?", 1)[0].strip()
                    if email and re.match(r'^[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}$', email, re.IGNORECASE):
                        return email

            body_text = await page.evaluate("document.body ? document.body.innerText : ''")
            if body_text:
                match = re.search(r'[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}', body_text, re.IGNORECASE)
                if match:
                    return match.group(0).strip()
        except Exception:
            return ""
        finally:
            try:
                await page.close()
            except Exception:
                pass

        return ""

    async def _search_instagram_for_phone(self, business_name: str) -> str:
        """
        Search for an Instagram page for the business and try to find a mobile phone number.
        Returns the mobile number if found, otherwise empty string.
        """
        if not self.context:
            return ""
            
        print(f"    📱 Searching Instagram for mobile number of: {business_name}...")
        
        # Create a new page for Instagram search to avoid disrupting Maps
        ig_page = await self.context.new_page()
        mobile_phone = ""
        
        try:
            # We'll use Google search to find the Instagram page
            # Searching directly on Instagram requires login
            search_query = urllib.parse.quote(f"{business_name} instagram jakarta")
            search_url = f"https://www.google.com/search?q={search_query}"
            
            await ig_page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
            
            # Find the first Instagram link
            ig_link = await ig_page.query_selector('a[href*="instagram.com/"]')
            
            if ig_link:
                ig_url = await ig_link.get_attribute("href")
                if ig_url and "instagram.com" in ig_url:
                    # Often the bio is visible in the Google search snippet itself!
                    # Let's try to extract from the snippet first to avoid loading IG
                    snippet_elements = await ig_page.query_selector_all('.VwiC3b, .yXK7lf, .MUxGbd, .aCOpRe')
                    
                    for snippet in snippet_elements:
                        text = await snippet.text_content()
                        if text:
                            # Look for Indonesian mobile numbers (08... or +628...)
                            # Exclude 021...
                            phone_match = re.search(r'(?:\+62\s*8|0\s*8)[\d\s\-\.]{8,15}', text)
                            if phone_match:
                                clean_num = re.sub(r'[^\d\+]', '', phone_match.group(0))
                                if len(clean_num) >= 10:
                                    print(f"    ✅ Found mobile number in IG snippet: {clean_num}")
                                    mobile_phone = clean_num
                                    break
                                    
                    # If not in snippet, try to visit the IG page directly
                    # Note: IG often blocks automated access without login, but public pages sometimes load
                    if not mobile_phone:
                        await ig_page.goto(ig_url, wait_until="domcontentloaded", timeout=20000)
                        await asyncio.sleep(2) # wait for bio to render
                        
                        # Look at the whole page text
                        body_text = await ig_page.evaluate('document.body.innerText')
                        if body_text:
                            # Look for WA or Phone pattern
                            phone_match = re.search(r'(?:WA|WhatsApp|Call|Hubungi|CP|Phone)?[^\w]?(?:\+62\s*8|0\s*8)[\d\s\-\.]{8,15}', body_text, re.IGNORECASE)
                            if phone_match:
                                # Extract just the number part
                                num_only = re.search(r'(?:\+62\s*8|0\s*8)[\d\s\-\.]{8,15}', phone_match.group(0))
                                if num_only:
                                    clean_num = re.sub(r'[^\d\+]', '', num_only.group(0))
                                    if len(clean_num) >= 10:
                                        print(f"    ✅ Found mobile number on IG page: {clean_num}")
                                        mobile_phone = clean_num
        except Exception as e:
            print(f"    ⚠️  Error searching Instagram: {e}")
        finally:
            await ig_page.close()
            
        return mobile_phone

    async def scrape(self, query: str) -> List[Dict]:
        """Main scraping function"""
        print("🚀 Initializing browser...")
        await self.init_browser()
        
        if not self.page:
            raise Exception("Failed to initialize browser")

        try:
            # Encode query for URL
            encoded_query = urllib.parse.quote(query)
            search_url = f"https://www.google.com/maps/search/{encoded_query}"
            
            # Navigate to Google Maps Search directly
            print(f"🗺️  Navigating to Google Maps for: '{query}'...")
            await self.page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            await self.random_delay()
            
            # Wait for results to load
            print("⏳ Waiting for results to load...")
            await self.page.wait_for_selector('[data-result-index], [role="article"], .fontHeadlineSmall', timeout=20000)
            await self.random_delay()

            # Scroll to load all results
            await self.scroll_to_load_all_results()

            # Extract business information
            print("🏪 Extracting business information...")
            results = []
            
            business_selectors = [
                '[data-result-index]',
                '.section-result',
                '[role="article"]'
            ]
            
            businesses = []
            for selector in business_selectors:
                try:
                    businesses = await self.page.query_selector_all(selector)
                    if businesses:
                        break
                except:
                    continue

            if not businesses:
                print("⚠️  No businesses found")
                return results

            print(f"📋 Found {len(businesses)} businesses")
            
            for i, business in enumerate(businesses[:self.max_results]):
                try:
                    print(f"🔍 Processing business {i + 1}/{len(businesses)}")
                    
                    # Click on business to open details
                    await business.click()
                    await self.random_delay()
                    
                    # Extract basic info from the list item
                    business_data = await self.extract_business_info(business)
                    
                    # If name is still missing or looks like a block of text, skip it
                    if not business_data["name"] or len(business_data["name"]) > 100:
                        continue
                        
                    # Try to get additional details from the opened panel
                    try:
                        # Wait for details panel to open (use a more specific selector)
                        await self.page.wait_for_selector('div[role="main"][aria-label]', timeout=10000)
                        
                        # Add a small delay to let content render
                        await asyncio.sleep(1)
                        
                        # Extract website
                        website_selectors = [
                            'a[data-item-id="authority"]',
                            'a[aria-label*="website" i]',
                            'a[aria-label*="situs" i]'
                        ]
                        
                        for selector in website_selectors:
                            try:
                                website_element = await self.page.query_selector(selector)
                                if website_element:
                                    website_href = await website_element.get_attribute("href")
                                    if website_href and "google" not in website_href:
                                        business_data["website"] = website_href
                                        break
                            except:
                                continue

                        email_selectors = [
                            'a[href^="mailto:"]',
                            '[data-item-id^="email:"]',
                            'button[data-item-id^="email:"]',
                            'div:has-text("@")'
                        ]

                        for selector in email_selectors:
                            try:
                                email_element = await self.page.query_selector(selector)
                                if email_element:
                                    href = await email_element.get_attribute("href")
                                    if href and href.lower().startswith("mailto:"):
                                        email_val = href.split(":", 1)[1].split("?", 1)[0].strip()
                                        if email_val and re.match(r'^[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}$', email_val, re.IGNORECASE):
                                            business_data["email"] = email_val
                                            break

                                    text_val = await email_element.text_content() or await email_element.get_attribute("aria-label")
                                    if text_val and "@" in text_val:
                                        match = re.search(r'[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}', text_val, re.IGNORECASE)
                                        if match:
                                            business_data["email"] = match.group(0).strip()
                                            break
                            except:
                                continue

                        if not business_data["email"] and business_data["website"]:
                            business_data["email"] = await self._search_website_for_email(business_data["website"])
                        
                        # Extract phone
                        phone_selectors = [
                            'button[data-item-id^="phone:tel:"]',
                            'button[aria-label*="phone" i]',
                            'button[aria-label*="telepon" i]',
                            'div:has-text("+62")',
                            'div:has-text("08")',
                            'div:has-text("021")'
                        ]
                        
                        for selector in phone_selectors:
                            try:
                                phone_element = await self.page.query_selector(selector)
                                if phone_element:
                                    # First check the data-item-id which contains the clean phone number
                                    data_id = await phone_element.get_attribute("data-item-id")
                                    if data_id and data_id.startswith("phone:tel:"):
                                        business_data["phone"] = data_id.replace("phone:tel:", "").strip()
                                        break
                                        
                                    phone_text = await phone_element.text_content() or await phone_element.get_attribute("aria-label")
                                    if phone_text:
                                        # Look for phone number patterns
                                        phone_match = re.search(r'(?:\+62|0)[\d\s\-]{8,15}', phone_text)
                                        if phone_match:
                                            business_data["phone"] = phone_match.group(0).strip()
                                            break
                            except:
                                continue
                                
                    except Exception as e:
                        print(f"⚠️  Could not extract additional details: {e}")
                    
                    # Logic to handle "021" numbers
                    if business_data["phone"]:
                        # Clean the phone number of spaces and dashes to check
                        clean_phone = business_data["phone"].replace(" ", "").replace("-", "")
                        if clean_phone.startswith("021") or clean_phone.startswith("+6221"):
                            print(f"    ℹ️  Found landline number ({business_data['phone']}). Searching for mobile number on IG...")
                            
                            ig_phone = await self._search_instagram_for_phone(business_data["name"])
                            
                            if ig_phone:
                                business_data["phone"] = ig_phone
                            else:
                                print(f"    ❌ No mobile number found on IG. Clearing the landline number.")
                                business_data["phone"] = ""
                                
                    # Close the details panel if possible
                    try:
                        close_buttons = await self.page.query_selector_all('button[aria-label*="back"], button[aria-label*="close"]')
                        for button in close_buttons:
                            if await button.is_visible():
                                await button.click()
                                break
                    except:
                        pass
                    
                    results.append(business_data)
                    await self.random_delay()
                    
                except Exception as e:
                    print(f"⚠️  Error processing business {i + 1}: {e}")
                    continue

            return results

        except Exception as e:
            print(f"❌ Error during scraping: {e}")
            return []

    def save_to_csv(self, data: List[Dict], filename: str):
        """Save results to CSV file"""
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, encoding='utf-8')

    def save_to_excel(self, data: List[Dict], filename: str):
        """Save results to Excel file"""
        df = pd.DataFrame(data)
        df.to_excel(filename, index=False, engine='openpyxl')

    def analyze_with_ai(self, results: List[Dict]) -> str:
        """Analyze the scraped results using Groq AI model"""
        if not os.getenv("GROQ_API_KEY"):
            raise EnvironmentError(
                "GROQ_API_KEY not found in environment variables."
            )

        print("🤖 Analyzing results with AI (Groq)...")
        try:
            llm = ChatGroq(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                temperature=0
            )

            # Prepare data for AI (limit to top 15 to avoid token limits)
            sample_data = json.dumps(results[:15], indent=2)

            messages = [
                SystemMessage(content="You are an expert data analyst. Analyze the provided Google Maps scraping results. Give a brief summary of the best options based on ratings and review counts, highlight any interesting patterns, and suggest the overall top 3 places."),
                HumanMessage(content=f"Here are the top scraped results:\n{sample_data}\n\nPlease provide a structured summary and recommend the best places.")
            ]

            response = llm.invoke(messages)
            return response.content
        except Exception as e:
            print(f"❌ Error during AI analysis: {e}")
            return f"Failed to analyze data with AI: {e}"

    async def close(self):
        """Clean up browser resources"""
        if self.browser:
            await self.browser.close()
