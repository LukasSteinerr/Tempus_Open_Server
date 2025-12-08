import asyncio
import json
import httpx
import os
from playwright.async_api import async_playwright

BASE_URL = "https://www.tempusopen.se/statistics/swimming"

async def main():
    print("🚀 Starting Test...")
    
    print("🚦 About to launch Playwright...")
    async with async_playwright() as p:
        print("✅ Playwright launched.")
        print("🔍 Initializing Playwright...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        print(f"📥 Fetching {BASE_URL} to get tokens...")
        await page.goto(BASE_URL, timeout=60000)
        await page.wait_for_load_state("networkidle")

        cookies = await context.cookies()
        
        xsrf_token = None
        session_token = None
        
        for cookie in cookies:
            if cookie['name'] == 'XSRF-TOKEN':
                xsrf_token = cookie['value']
            if cookie['name'] == 'tempusopen_session':
                session_token = cookie['value']

        if not xsrf_token or not session_token:
            print("❌ Failed to find tokens. The site might be blocking or structure changed.")
            await browser.close()
            return

        print(f"✅ XSRF-TOKEN found: {xsrf_token[:15]}...")
        print(f"✅ Session found: {session_token[:15]}...")

        from urllib.parse import unquote
        header_xsrf = unquote(xsrf_token)

        payload = {"year":"","class":"1","swim_event":8,"pool_type":1,"competition_group":"","best_time_only":True,"from_age":13,"to_age":99,"district":"","club":"","filter":{"age_filter":True,"best_time_only":True},"limit":20}

        print("📤 Sending POST request with Playwright's request context...")
        api_response = await page.request.post(
            BASE_URL,
            data=payload,
            headers={
                "X-Xsrf-Token": header_xsrf,
                "X-Requested-With": "XMLHttpRequest",
                "X-Inertia": "true",
                "X-Inertia-Version": "0d60a0cef251f76c204b2a1cd16b0d69",
                "Content-Type": "application/json",
                "Accept": "text/html, application/xhtml+xml",
                "Referer": "https://www.tempusopen.se/statistics/swimming",
                "Origin": "https://www.tempusopen.se",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Priority": "u=1, i",
                "Sec-Ch-Ua": '"Chromium";v="143", "Not A(Brand";v="24"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
            }
        )

        if api_response.status == 200:
            try:
                data = await api_response.json()
                print("\n🎉 SUCCESS! JSON Object received.")
                
                # 1. Inspect the keys to confirm structure (Debugging step)
                print(f"Top-level keys: {list(data.keys())}")
                
                # 2. Drill down into 'props' to find the actual list
                # Usually it is data['props']['swimmers'] or data['props']['results']
                if 'props' in data:
                    props = data['props']
                    print(f"Keys inside 'props': {list(props.keys())}")
                    
                    # DYNAMICALLY FIND THE LIST
                    # We look for the key that holds the list of swimmers
                    target_list = None
                    if 'results' in props:
                        target_list = props['results']
                    elif 'swimmers' in props:
                        target_list = props['swimmers']
                    elif 'statistics' in props: # Sometimes named statistics
                        target_list = props['statistics']
                    
                    # Handle pagination wrappers (Laravel usually wraps lists in 'data')
                    if isinstance(target_list, dict) and 'data' in target_list:
                        target_list = target_list['data']
                    
                    if target_list and isinstance(target_list, list):
                        print(f"\n🏊 Found {len(target_list)} actual swimmers!")
                        if len(target_list) > 0:
                            print("First Swimmer Data Preview:")
                            print(json.dumps(target_list[0], indent=2))
                            
                            # Save the full list to a file
                            # Save the full list to a file
                            script_dir = os.path.dirname(__file__)
                            output_path = os.path.join(script_dir, "output.json")
                            print(f"\n💾 Saving full results to {output_path}...")
                            with open(output_path, "w", encoding="utf-8") as f:
                                json.dump(target_list, f, indent=2, ensure_ascii=False)
                                f.flush()
                                os.fsync(f.fileno())
                            print("✅ Full results saved to output.json")

                            # Verify the file by reading it back
                            print("\n🔍 Verifying file content...")
                            with open(output_path, "r", encoding="utf-8") as f:
                                verification_data = json.load(f)
                                print(f"✅ Verification successful. Read {len(verification_data)} records from output.json.")
                    else:
                        print("⚠️ Could not locate the swimmer list inside 'props'. Check the keys printed above.")
                        print("Full props dump:", json.dumps(props, indent=2))
                else:
                    print("⚠️ Response did not contain 'props'. It might be a raw list after all?")
                    print(json.dumps(data, indent=2))

            except json.JSONDecodeError:
                print("❌ Failed to decode JSON. Raw response:")
                print(await api_response.text())
        else:
            print(f"❌ Request failed with status: {api_response.status}")
            print(await api_response.text())

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())