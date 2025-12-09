import asyncio
import json
import os
from playwright.async_api import async_playwright
from urllib.parse import unquote

async def get_swimmer_details(swimmer_id: int):
    """
    Fetches details for a specific swimmer from Tempus Open.
    """
    print(f"🚀 Starting search for swimmer with ID: {swimmer_id}...")
    
    async with async_playwright() as p:
        print("🚦 Launching browser to fetch tokens...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # Base URL for swimmer details
        swimmer_url = f"https://www.tempusopen.se/swimmers/{swimmer_id}"

        print(f"📥 Fetching {swimmer_url} to get initial cookies and tokens...")
        await page.goto(swimmer_url, timeout=60000)
        await page.wait_for_load_state("networkidle")

        cookies = await context.cookies()
        
        xsrf_token = None
        
        for cookie in cookies:
            if cookie['name'] == 'XSRF-TOKEN':
                xsrf_token = cookie['value']

        if not xsrf_token:
            print("❌ Failed to find XSRF-TOKEN. The site might be blocking or its structure has changed.")
            await browser.close()
            return

        print(f"✅ XSRF-TOKEN found: {xsrf_token[:15]}...")

        header_xsrf = unquote(xsrf_token)

        print(f"📤 Sending GET request to fetch details for swimmer {swimmer_id}...")
        api_response = await page.request.get(
            swimmer_url,
            headers={
                "X-Xsrf-Token": header_xsrf,
                "X-Requested-With": "XMLHttpRequest",
                "X-Inertia": "true",
                "X-Inertia-Version": "0d60a0cef251f76c204b2a1cd16b0d69",
                "Accept": "text/html, application/xhtml+xml",
                "Referer": "https://www.tempusopen.se/swimmers", # Referer is the search page
            }
        )

        if api_response.status == 200:
            try:
                data = await api_response.json()
                print("\n🎉 SUCCESS! JSON Object received.")
                
                script_dir = os.path.dirname(__file__)
                output_path = os.path.join(script_dir, "swimmer_details_output.json")
                print(f"\n💾 Saving full details to {output_path}...")
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"✅ Full details saved to {output_path}")

            except json.JSONDecodeError:
                print("❌ Failed to decode JSON. Raw response:")
                print(await api_response.text())
        else:
            print(f"❌ Request failed with status: {api_response.status}")
            print(await api_response.text())

        await browser.close()

if __name__ == "__main__":
    # Example swimmer ID. You can change this to any valid ID.
    TARGET_SWIMMER_ID = 269397 
    asyncio.run(get_swimmer_details(TARGET_SWIMMER_ID))