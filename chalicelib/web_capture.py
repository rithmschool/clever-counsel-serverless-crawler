from selenium import webdriver
from datetime import datetime
from chalicelib.s3_manager import upload_object
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from botocore.exceptions import ClientError
import os

# config settings taken from
# https://github.com/vittorio-nardone/selenium-chromium-lambda/blob/master/src/webdriver_screenshot.py
chrome_options = webdriver.ChromeOptions()
lambda_options = lambda_options = [
    '--autoplay-policy=user-gesture-required',
    '--disable-background-networking',
    '--disable-background-timer-throttling',
    '--disable-backgrounding-occluded-windows',
    '--disable-breakpad',
    '--disable-client-side-phishing-detection',
    '--disable-component-update',
    '--disable-default-apps',
    '--disable-dev-shm-usage',
    '--disable-domain-reliability',
    '--disable-extensions',
    '--disable-features=AudioServiceOutOfProcess',
    '--disable-hang-monitor',
    '--disable-ipc-flooding-protection',
    '--disable-notifications',
    '--disable-offer-store-unmasked-wallet-cards',
    '--disable-popup-blocking',
    '--disable-print-preview',
    '--disable-prompt-on-repost',
    '--disable-renderer-backgrounding',
    '--disable-setuid-sandbox',
    '--disable-speech-api',
    '--disable-sync',
    '--disk-cache-size=33554432',
    '--hide-scrollbars',
    '--ignore-gpu-blacklist',
    '--ignore-certificate-errors',
    '--metrics-recording-only',
    '--mute-audio',
    '--no-default-browser-check',
    '--no-first-run',
    '--no-pings',
    '--no-sandbox',
    '--no-zygote',
    '--password-store=basic',
    '--use-gl=swiftshader',
    '--use-mock-keychain',
    '--single-process',
    '--headless',
    '--user-data-dir=/tmp/user-data',
    '--data-path=/tmp/data-path',
    '--homedir=/tmp',
    '--disk-cache-dir=/tmp/cache-dir'
]

for argument in lambda_options:
    chrome_options.add_argument(argument)

if os.environ.get("CHALICE_ENV") == "production":
    chrome_options.binary_location = '/opt/bin/chromium'


def timestamp():
    """Get URL-safe timestamp"""
    return datetime.today().strftime("%Y_%m_%d_%H%M%S")


def take_screenshot(driver, file_name, s3_directory):
    """
    take_screenshot()

    expects:
    - driver - reference to driver
    - file_name
    - s3_directory

    take_screenshot then:
    - sets size of view window to full scrollWidth and scrollHeight
    of document body element
    - takes screenshot of document body element
    """
    file_path = f"{s3_directory}/{file_name}"
    full_width = driver.execute_script("return document.body.scrollWidth")
    full_height = driver.execute_script("return document.body.scrollHeight")

    driver.set_window_size(full_width, full_height)

    # removes scrollbar
    driver.find_element_by_tag_name("body")

    # gets screenshot as binary
    screenshot = driver.get_screenshot_as_png()
    upload_object(screenshot, file_path)

    return file_path


def capture_sos(entity_number, s3_directory):
    """
    capture_sos()

    expects: 
    - entity_number (CXXXXXXX)
    - s3_directory

    returns:
    - {address, success}

    capture_sos then:
    - browses to SOS business search page filtered by entity number
    - clicks link to go to entity page
    - saves screenshot of entity page
    """
    # make sure that you do error handling for entity_number, s3_directory
    # error produced currently:
    # {
    #     "Code": "InternalServerError",
    #     "Message": "An internal server error occurred."
    # }

    # settings
    file_name = f"{timestamp()}_sos.png"

    # format of entity_number is C5555555
    # id of link to browse to entity details page is btnDetail-05555555
    button_selector_id = "btnDetail-0" + entity_number[1:]

    base_url = "https://businesssearch.sos.ca.gov/CBS/SearchResults"
    query = f"?filing=&SearchType=NUMBER&SearchCriteria={entity_number}"

    driver = webdriver.Chrome(options=chrome_options, executable_path=os.environ.get("EXECUTABLE_PATH"))
    driver.get(f"{base_url}{query}")

    output = {}

    try:
        # entity name - should be link to entity page
        driver.find_element_by_id(button_selector_id).click()

        # finds parent element of 'Entity Address' label
        address = driver.find_element_by_xpath(f"//label[text()='Entity Address']/..")

        output["address"] = address.text.strip().replace("\n", ", ")

        output["file_path"] = take_screenshot(driver, file_name, s3_directory)
        output["file_name"] = file_name

    except TimeoutException:
        output["error"] = "Form data took too long to load"

    except NoSuchElementException:
        output["error"] = "One or more form elements could not be found"

    except ClientError:
        output["error"] = "Could not upload screenshot to S3"

    if not output.get("error"):
        output["success"] = f"Captured screenshot {file_name}"

    driver.quit()
    return output


def capture_locality(home_number, street_name, zip_code, s3_directory):
    """
    capture_locality()

    expects: 
    - home_number (number)
    - street_name 
        => won't work with direction (NESW) or street type (ave, st, blvd, etc)
    - zip_code
    - s3_directory

    returns:
    - data => [{address, locality, screenshot}, ...]
    - error (if error)

    capture_locality then:
    1. browses to LA County Precincts Maps Application
    2. selects dropdown and changes to "District Map Look Up by Address"
    3. enters home_number into input field
    4. enters street_name into input field
    5. submits form
    6. waits for ajax to finish by looking for home_number to show up in
    results element
    7. grabs each result that match supplied zip code
    8. clicks on first (or next) result
    9. waits for locality content to load by looking for links to show up
    in results element
    10. takes full page screenshot of locality page
    11. clicks back button
    12. submits search page again
    13. if more addresses, repeats from step 8
    """

    # settings
    ajax_timeout_in_seconds = 5
    file_name = f"{timestamp()}_locality"

    # set html elements ids
    select_element_id = "list"
    select_option_id = "1"
    home_number_input_id = "HomeNumber"
    street_name_input_id = "StreetName"
    submit_button_id = "btnSubmit"
    results_div_id = "divAddress"
    district_results_div_id = "divDistrict"
    back_button_id = "btnBack"

    # create driver, get url
    driver = webdriver.Chrome(options=chrome_options, executable_path=os.environ.get("EXECUTABLE_PATH"))
    driver.get("https://lavote.net/apps/PrecinctsMaps/")

    output = {}

    try:
        # select search by address dropdown
        select = Select(driver.find_element_by_id(select_element_id))
        select.select_by_value(select_option_id)

        # input home humber
        home_number_input = driver.find_element_by_id(home_number_input_id)
        home_number_input.send_keys(home_number)

        # input street name
        street_name_input = driver.find_element_by_id(street_name_input_id)
        street_name_input.send_keys(street_name)

        # click submit
        driver.find_element_by_id(submit_button_id).click()

        # wait for ajax request to complete
        wait = WebDriverWait(driver, ajax_timeout_in_seconds)
        result = wait.until(
            EC.text_to_be_present_in_element((By.ID, results_div_id), home_number)
        )

        if not result:
            raise TimeoutException

        # get all addresses with text matching zip_code
        address_nodes = driver.find_element_by_id(
            results_div_id
        ).find_elements_by_xpath(f"//a[contains(text(),{zip_code})]")
        address_list = [address.text for address in address_nodes]

        counter = 1

        for address in address_list:
            current_file_name = file_name + f"_{counter}.png"
            current_file_path = ""

            # click link for current address
            driver.find_element_by_link_text(address).click()

            # wait until links are populated in locality results
            wait = WebDriverWait(driver, ajax_timeout_in_seconds)
            result = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//*[@id='{district_results_div_id}']//a")
                )
            )

            if not result:
                raise TimeoutException
            else:
                current_file_path = take_screenshot(
                    driver, current_file_name, s3_directory
                )
                counter += 1

            # get 6th item in locality results list
            locality = driver.find_element_by_xpath(
                f"//*[@id='{district_results_div_id}']//a[6]"
            )

            if not output.get("data"):
                output["data"] = []

            output["data"].append(
                {
                    "address": address,
                    "locality": locality.text,
                    "file_path": current_file_path,
                    "file_name": current_file_name,
                }
            )

            driver.find_element_by_id(back_button_id).click()
            driver.find_element_by_id(submit_button_id).click()

            # wait for ajax request to complete
            wait = WebDriverWait(driver, ajax_timeout_in_seconds)
            result = wait.until(
                EC.text_to_be_present_in_element((By.ID, results_div_id), home_number)
            )

    except TimeoutException:
        output["error"] = "Form data took too long to load"

    except NoSuchElementException:
        output["error"] = "One or more form elements could not be found"

    except Exception:
        output["error"] = "Ran into an error."

    finally:
        driver.quit()
        return output