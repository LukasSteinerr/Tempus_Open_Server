import asyncio
import json
import os
from playwright.async_api import async_playwright
from urllib.parse import unquote

async def main():
    print("🚀 Starting swimmer search...")
    
    async with async_playwright() as p:
        print("🚦 Launching browser to fetch tokens...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # Visit a page on the site to get the necessary cookies
        print("📥 Fetching https://www.tempusopen.se/swimmers to get initial cookies...")
        await page.goto("https://www.tempusopen.se/swimmers", timeout=60000)
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
            print("❌ Failed to find tokens. The site might be blocking or its structure has changed.")
            await browser.close()
            return

        print(f"✅ XSRF-TOKEN found: {xsrf_token[:15]}...")
        print(f"✅ Session found: {session_token[:15]}...")

        header_xsrf = unquote(xsrf_token)

        # Payload for searching a swimmer
        payload = {
            "first_name": "Victor",
            "last_name": "Johansson",
            "club": "",
            "category": "",
            "class": "",
            "status": ""
        }

        print("📤 Sending POST request to search for a swimmer...")
        api_response = await page.request.post(
            "https://www.tempusopen.se/swimmers",
            data=payload,
            headers={
                "X-Xsrf-Token": header_xsrf,
                "X-Requested-With": "XMLHttpRequest",
                "X-Inertia": "true",
                "X-Inertia-Version": "0d60a0cef251f76c204b2a1cd16b0d69",
                "Content-Type": "application/json",
                "Accept": "text/html, application/xhtml+xml",
                "Referer": "https://www.tempusopen.se/swimmers",
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
                
                script_dir = os.path.dirname(__file__)
                output_path = os.path.join(script_dir, "swimmer_output.json")
                print(f"\n💾 Saving full results to {output_path}...")
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"✅ Full results saved to {output_path}")

            except json.JSONDecodeError:
                print("❌ Failed to decode JSON. Raw response:")
                print(await api_response.text())
        else:
            print(f"❌ Request failed with status: {api_response.status}")
            print(await api_response.text())

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())