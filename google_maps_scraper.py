import time
import logging
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Setup logging
logging.basicConfig(filename='errors.log', level=logging.ERROR, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def scrape_google_maps(search_query):
    # Setup WebDriver options
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')  # Open in full-screen mode

    # Launch WebDriver
    driver = webdriver.Chrome(options=options)
    driver.get(f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}")

    try:
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'Nv2PK')))

        # Locate the scrollable div (left sidebar)
        scrollable_div = driver.find_element(By.CLASS_NAME, 'm6QErb.DxyBCb.kA9KIf.dS8AEf')

        # List to store data
        data = []

        last_height = 0
        max_wait_attempts = 3
        attempts_without_change = 0

        while True:
            driver.execute_script("arguments[0].scrollTop += arguments[0].scrollHeight;", scrollable_div)
            time.sleep(2)

            new_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)

            if new_height == last_height:
                attempts_without_change += 1
                if attempts_without_change >= max_wait_attempts:
                    print("✅ Scrolled to the end of the list.")
                    break
            else:
                attempts_without_change = 0

            last_height = new_height

        places = driver.find_elements(By.CLASS_NAME, 'Nv2PK')

        print(f"🔍 Total places found: {len(places)}")

        for place in places:
            try:
                name = place.find_element(By.CLASS_NAME, 'qBF1Pd').text if place.find_elements(By.CLASS_NAME, 'qBF1Pd') else "N/A"
                rating = place.find_element(By.CLASS_NAME, 'MW4etd').text if place.find_elements(By.CLASS_NAME, 'MW4etd') else "N/A"
                category = place.find_elements(By.CLASS_NAME, 'W4Efsd')[1].text if len(place.find_elements(By.CLASS_NAME, 'W4Efsd')) > 1 else "N/A"

                # Click on the place to open details
                place.click()
                time.sleep(3)  # Wait for details to load

                # ✅ Extract website link
                try:
                    website_element = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, "//a[contains(@aria-label, 'Website')]"))
                    )
                    website_link = website_element.get_attribute('href')
                except:
                    website_link = "N/A"

                

                # ✅ Extract Address
                try:
                    address_element = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Address')]")
                    address = address_element.text
                except:
                    address = "N/A"

                # ✅ Extract Mobile Number
                try:
                    phone_element = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Phone')]")
                    phone_number = phone_element.text
                except:
                    phone_number = "N/A"

                data.append([name, rating, category, address, phone_number, website_link])
            except Exception as e:
                logging.error(f"Error scraping place: {e}")

        # Save data to Excel with new columns
        df = pd.DataFrame(data, columns=["Name", "Rating", "Category", "Address", "Mobile No.", "Website"])
        df.to_excel("places_data.xlsx", index=False)

        print("✅ Data saved successfully to places_data.xlsx")

        input("Press Enter to close the browser...")  

    except Exception as e:
        logging.error(f"❌ Failed to load Google Maps data: {e}")
    finally:
        driver.quit()

# Get user input
niche = input("Enter the type of business (e.g., restaurants, cafes, gyms): ").strip()
location = input("Enter the location (e.g., Shahdara, Delhi): ").strip()

if not niche or not location:
    print("❌ Error: Both fields must be filled!")
else:
    search_query = f"{niche} in {location}"
    scrape_google_maps(search_query)
