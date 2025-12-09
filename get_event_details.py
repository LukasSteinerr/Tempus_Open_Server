import asyncio
import json
import os
from playwright.async_api import async_playwright
from urllib.parse import unquote

async def get_event_details(swimmer_id: int, event_id: int):
    """
    Fetches details for a specific event for a given swimmer from Tempus Open.
    """
    print(f"🚀 Starting search for event {event_id} for swimmer {swimmer_id}...")
    
    async with async_playwright() as p:
        print("🚦 Launching browser to fetch tokens...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # URL for the specific event
        event_url = f"https://www.tempusopen.se/swimmers/{swimmer_id}/events/{event_id}"

        print(f"📥 Fetching {event_url} to get initial cookies and tokens...")
        # We visit the swimmer's page first to ensure context is set up correctly
        await page.goto(f"https://www.tempusopen.se/swimmers/{swimmer_id}/swimming", timeout=60000)
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

        print(f"📤 Sending GET request to fetch details for event {event_id}...")
        api_response = await page.request.get(
            event_url,
            headers={
                "X-Xsrf-Token": header_xsrf,
                "X-Requested-With": "XMLHttpRequest",
                "X-Inertia": "true",
                "X-Inertia-Version": "0d60a0cef251f76c204b2a1cd16b0d69",
                "Accept": "text/html, application/xhtml+xml",
                "Referer": f"https://www.tempusopen.se/swimmers/{swimmer_id}/swimming",
            }
        )

        if api_response.status == 200:
            try:
                data = await api_response.json()
                print("\n🎉 SUCCESS! JSON Object received.")
                
                script_dir = os.path.dirname(__file__)
                output_path = os.path.join(script_dir, "event_details_output.json")
                print(f"\n💾 Saving full event details to {output_path}...")
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"✅ Full event details saved to {output_path}")

            except json.JSONDecodeError:
                print("❌ Failed to decode JSON. Raw response:")
                print(await api_response.text())
        else:
            print(f"❌ Request failed with status: {api_response.status}")
            print(await api_response.text())

        await browser.close()

if __name__ == "__main__":
    # Example swimmer and event IDs.
    TARGET_SWIMMER_ID = 269397 
    TARGET_EVENT_ID = 15 # As per your request
    asyncio.run(get_event_details(TARGET_SWIMMER_ID, TARGET_EVENT_ID))