import schedule
import time
import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import os
import pytz
import sys

FILE_SINGLE = "result.json"
FILE_HISTORY = "results.json"

is_finished_today = False
last_run_date = None

def get_ist_now():
    return datetime.now(pytz.timezone('Asia/Kolkata'))

def format_amount(amount_str):
    num_str = re.sub(r'[^\d]', '', amount_str)
    if not num_str:
        return amount_str
    
    num = int(num_str)
    if num >= 10000000:
        val = num / 10000000
        text = f"{int(val)} Crore" if val.is_integer() else f"{val} Crore"
        return f"{amount_str} ({text})"
    elif num >= 100000:
        val = num / 100000
        text = f"{int(val)} Lakh" if val.is_integer() else f"{val} Lakh"
        return f"{amount_str} ({text})"
        
    return amount_str

def push_to_github():
    print("Pushing updates to GitHub...")
    # GitHub Actions specific commands
    os.system('git config --global user.name "github-actions[bot]"')
    os.system('git config --global user.email "github-actions[bot]@users.noreply.github.com"')
    os.system('git add result.json results.json')
    if os.system('git diff --staged --quiet') != 0:
        os.system('git commit -m "Auto update results"')
        os.system('git push')
    else:
        print("No changes to commit.")

def scrape_full_homepage():
    url = os.environ.get('LOTTERY_URL')
    if not url:
        print("Error: LOTTERY_URL environment variable is not set!")
        return None, False
        
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        date_tag = soup.find('h2', class_='dt')
        if not date_tag:
            return None, False
        date_text = date_tag.text.strip()
        
        name_tag = soup.find('div', class_='heading_live')
        if name_tag and name_tag.find('h2'):
            raw_name = name_tag.find('h2').text.strip()
            name = raw_name.split(' Lottery')[0].strip()
        else:
            name = "Unknown"
        
        prizes = {}
        is_finished = True
        
        # Check for typing indicator in the whole page
        if soup.find(class_='typing-indicator'):
            is_finished = False
            
        for h2 in soup.find_all('h2'):
            text = h2.get_text(strip=True)
            if "Prize" in text:
                h3 = h2.find_next_sibling('h3')
                amount = h3.get_text(strip=True) if h3 else ""
                amount = format_amount(amount)
                
                numbers = []
                curr = h2.next_sibling
                while curr and getattr(curr, 'name', '') != 'h2':
                    if curr.name == 'p':
                        if curr.get('class') and 'cons-numbers' in curr.get('class'):
                            spans = curr.find_all('span', class_='num')
                            for span in spans:
                                span_text = span.get_text(strip=True)
                                if span_text:
                                    numbers.append(span_text)
                                    if '---' in span_text:
                                        is_finished = False
                        elif curr.get('class') and 'agency-line' in curr.get('class'):
                            pass # Ignore agency line
                        else:
                            t = curr.get_text(strip=True)
                            if t:
                                numbers.append(t)
                                if '---' in t:
                                    is_finished = False
                    elif curr.name == 'div':
                        if curr.get('class') and 'cons-grid' in curr.get('class'):
                            cells = curr.find_all('div', class_='cons-cell')
                            for cell in cells:
                                cell_text = cell.get_text(strip=True)
                                if cell_text:
                                    numbers.append(cell_text)
                                    if '---' in cell_text:
                                        is_finished = False
                    curr = curr.next_sibling
                    
                prizes[text] = {
                    "amount": amount,
                    "numbers": numbers
                }
                
                if not numbers:
                    is_finished = False
                
        return {
            "date": date_text,
            "name": name,
            "prizes": prizes
        }, is_finished
    except Exception as e:
        print(f"Error scraping homepage: {e}")
        return None, False

def update_results():
    print(f"[{get_ist_now()}] Fetching full results...")
    homepage_result, is_finished = scrape_full_homepage()
    if not homepage_result:
        print(f"[{get_ist_now()}] Could not fetch homepage results.")
        return False
        
    # Always update the single latest result in result.json
    with open(FILE_SINGLE, 'w', encoding='utf-8') as f:
        json.dump(homepage_result, f, indent=4, ensure_ascii=False)
    
    # Only update the 7-day history in results.json when the draw is fully finished
    if is_finished:
        existing = []
        if os.path.exists(FILE_HISTORY):
            try:
                with open(FILE_HISTORY, 'r') as f:
                    existing = json.load(f)
            except Exception:
                pass
                
        # Check if we already have today's result in history
        updated = False
        for i, ex in enumerate(existing):
            if ex.get('date') == homepage_result['date']:
                existing[i] = homepage_result
                updated = True
                break
                
        if not updated:
            # Prepend to list
            existing.insert(0, homepage_result)
            
        # Keep only the last 7 days
        existing = existing[:7]
        
        with open(FILE_HISTORY, 'w', encoding='utf-8') as f:
            json.dump(existing, f, indent=4, ensure_ascii=False)
            
        print(f"[{get_ist_now()}] 7-day History Update complete.")
        
    push_to_github()
    return is_finished

def job():
    global is_finished_today, last_run_date
    now = get_ist_now()
    
    # Reset states on a new day
    if last_run_date != now.date():
        is_finished_today = False
        last_run_date = now.date()

    # Start checking from 15:00 onwards
    if now.hour >= 15:
        # If it's past 17:00, we force stop checking to save resources
        if now.hour >= 17:
            print(f"[{get_ist_now()}] Force stopping as time exceeded 5 PM.")
            sys.exit(0)
            
        if not is_finished_today:
            is_finished = update_results()
            if is_finished:
                is_finished_today = True
                print(f"[{get_ist_now()}] Result is fully finished for today. Exiting.")
                sys.exit(0)
            else:
                print(f"[{get_ist_now()}] Result still updating. Will check again in 2 minutes.")

if __name__ == "__main__":
    # Ensure variables are initialized
    last_run_date = get_ist_now().date()
    
    # Run once on startup to grab current state
    if get_ist_now().hour >= 15:
        is_finished_today = update_results()
        if is_finished_today:
            print(f"[{get_ist_now()}] Result already fully finished for today. Exiting.")
            sys.exit(0)
    
    # Schedule every 2 minutes
    schedule.every(2).minutes.do(job)
    
    print(f"[{get_ist_now()}] Scheduler started. Will check for updates every 2 mins.")
    while True:
        schedule.run_pending()
        time.sleep(1)
