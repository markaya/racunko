from playwright.sync_api import sync_playwright, expect # type: ignore
import time, base64, os, re
from cache import *


DOWNLOAD_DIR = "/Users/markoristic/open-source/racunko/downloads"
# format for PERIOD = "5/2025"

def download_pdfs_eps(username, password, cache):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    eps_download_dir = f"{DOWNLOAD_DIR}/eps" 
    os.makedirs(eps_download_dir, exist_ok=True)
    year = cache.get('year')
    month = cache.get('month')
    PERIOD = f"{month}/{year}"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://portal.eps.rs/home")
        # Username input (first input)
        page.locator('input.v-field__input').nth(0).fill(username)

        # Password input (second input)
        page.locator('input.v-field__input').nth(1).fill(password)

        submit_button = page.locator('button:has-text("Пријавите се")')

        # ✅ Wait for the button to be enabled (correct way)
        expect(submit_button).to_be_enabled(timeout=10000)  # 10s timeout

        # Click when enabled
        submit_button.click()

        # Wait for the page to fully load
        page.wait_for_load_state("networkidle")

        # Click on "Рачуни"
        # page.locator("div.v-list-item-title:has-text('Рачуни')").click()
        page.get_by_text("Рачуни").click()

        page.wait_for_load_state("networkidle")

        combobox = page.locator('div.select-contract-box')
        combobox.click()

        # Wait for the contract list to appear
        page.wait_for_selector("div.v-overlay--active")

        # STEP 3️⃣ Loop through each contract
        contract_items = page.locator("div.v-overlay--active .v-list-item")

        print(f"Found {contract_items.count()} contracts.")

        for i in range(contract_items.count()):
            # Reopen the dropdown if it closes
            if i > 0:
                #time.sleep(1)  # Allow time for second select to refresh
                combobox.click()
                page.wait_for_selector("div.v-overlay--active")

            item = contract_items.nth(i)
            contract_text = item.inner_text()
            item.click()
            match = re.search(r"Наплатни број:\s*(\d+)", contract_text)
            if match:
                broj = match.group(1)
                id = f"eps-{broj}"
                print(f"➡ item ID: {id}")
                print(f"➡ Selecting contract {i+1}: {contract_text} \n")
                if is_downloaded(cache, id):
                    print(f"already downloaded item with {id}")
                    continue
                else:
                    mark_exists(cache, id)

                    # Wait for page to load relevant content after selecting contract
                    page.wait_for_timeout(2000)  # adjust as needed
            
                    # Find download button for specified period
                    card_title = page.locator(f"div.v-card-title:has(span:text-is('{PERIOD}'))")
                    download_button = card_title.locator("button:has(svg.fa-download)")

                    with context.expect_page() as new_page_info:
                        download_button.click()

                    pdf_page = new_page_info.value
                    pdf_page.wait_for_load_state("domcontentloaded")

                    # Extract blob URL from new PDF page
                    blob_url = pdf_page.evaluate("window.location.href")
                    print("➡ Blob URL:", blob_url)

                    # Download PDF data via page context and save
                    pdf_base64 = pdf_page.evaluate(f"""
                        () => fetch("{blob_url}")
                            .then(response => response.blob())
                            .then(blob => new Promise((resolve, reject) => {{
                                const reader = new FileReader();
                                reader.onloadend = () => resolve(reader.result.split(',')[1]);
                                reader.onerror = reject;
                                reader.readAsDataURL(blob);
                            }}))
                    """)

                    filename = f"downloaded_{i+1}_{PERIOD.replace('/', '_')}.pdf"
                    filepath = os.path.join(eps_download_dir, filename)
                    with open(filepath, "wb") as f:
                        f.write(base64.b64decode(pdf_base64))

                    print(f"✅ Saved as {filepath}")

                    pdf_page.close()
                    page.wait_for_timeout(1000)  # small delay between iterations
                    mark_downloaded(cache, id)

        browser.close()


# format for PERIOD = "2025.05"
def download_pdfs_informatika(username, password, cache):
  PERIOD = f"{cache['year']}.{cache['month']:02d}"
  os.makedirs(DOWNLOAD_DIR, exist_ok=True)
  info_download_dir = f"{DOWNLOAD_DIR}/informatika"
  os.makedirs(info_download_dir, exist_ok=True)
  with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    page.goto("https://mojiracuni.nsinfo.co.rs/web/")
    # Username input (first input)
    page.fill('input#username', username)
    page.fill('input#password', password)

    # Click the submit button with visible text "Пријављивање"
    page.click("button:has-text('Пријављивање')")

    # Wait until the navigation or some post-login element appears
    page.wait_for_load_state("networkidle")

    print("✅ Logged in successfully")

    # Click "Моји рачуни"
    page.goto("https://mojiracuni.nsinfo.co.rs/web/user/sr_Cyrl_RS/3001")

    page.wait_for_load_state("networkidle")

    # Loop over first <select> (obveznici)
    obveznici = page.locator('select[name="DS_SRV_3001[P_OBV_ID]"] option')
    count = obveznici.count()

    for i in range(1, count):  # skip index 0 ('- изаберите обвезника -')
        obveznik_value = obveznici.nth(i).get_attribute("value")
        obveznik_text = obveznici.nth(i).inner_text()
        print(f"📌 Selecting: {obveznik_text}")

        # Select obveznik
        page.select_option('select[name="DS_SRV_3001[P_OBV_ID]"]', obveznik_value)
        time.sleep(2)  # Allow time for second select to refresh

        # Loop over second <select> (addresses/contracts)
        addresses = page.locator('select[name="DS_SRV_3001[P_PRO_ID]"] option')
        addr_count = addresses.count()

        for j in range(1, addr_count):  # skip first "-"
            address_value = addresses.nth(j).get_attribute("value")
            address_text = addresses.nth(j).inner_text()
            print(f"  🏠 Address: {address_text}")

            match = re.search(r"\[(\d+)\]", address_text)
            if match:
              broj = match.group(1)
              id = f"info-{broj}"
              if is_downloaded(cache, id):
                  print(f"already downloaded item with {id}")
                  continue
              else:
                print(broj)
                mark_exists(cache, id)
                # Select the address
                page.select_option('select[name="DS_SRV_3001[P_PRO_ID]"]', address_value)
                time.sleep(2)  # Allow time for second select to refresh

                page.wait_for_selector("#DS_SRV_3001_Submit", timeout=10000) 
                # Submit "Резултати"
                page.click('#DS_SRV_3001_Submit')
                page.wait_for_load_state("networkidle")

                # Wait for table to load
                try:
                    page.wait_for_selector("table.dataTable", timeout=10000) 
                    table = page.locator("table.dataTable")
                    table.wait_for(state="visible", timeout=5000)

                    first_row = table.locator("tbody tr").first
                    first_td = first_row.locator("td").first.inner_text()

                    if first_td == PERIOD:
                        download_link = first_row.locator('td >> a:has-text("Преузимање")')
                        with context.expect_page() as new_page_info:
                            download_link.click()

                        pdf_page = new_page_info.value
                        pdf_page.wait_for_load_state("domcontentloaded")

                        # Download PDF content as base64
                        pdf_base64 = pdf_page.evaluate(f"""
                            () => fetch(window.location.href)
                                .then(response => response.blob())
                                .then(blob => new Promise((resolve, reject) => {{
                                    const reader = new FileReader();
                                    reader.onloadend = () => resolve(reader.result.split(',')[1]);
                                    reader.onerror = reject;
                                    reader.readAsDataURL(blob);
                                }}))
                        """)

                        # Save to file
                        filename = os.path.join(info_download_dir, f"{obveznik_value}_{address_value}_{PERIOD.replace('.', '_')}.pdf")
                        with open(filename, "wb") as f:
                            f.write(base64.b64decode(pdf_base64))
                        print(f"✅ PDF saved as {filename}")
                        pdf_page.close()
                        mark_downloaded(cache, id)

                except Exception as e:
                    print("⚠️ Error or no table found:", e)

    browser.close()
