# import plugin
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
import pandas as pd
import time
import mysql.connector
import csv

db = mysql.connector.connect(
  host="localhost",
  user="root",
  passwd="",
  database="data_pendamping_halal"
)
if db.is_connected():
  print("connected to database!")
cursor = db.cursor()

# link to scrap
url = "https://info.halal.go.id/pendampingan/"

# make request with selenium
options = webdriver.ChromeOptions()
service = ChromeService(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
driver.implicitly_wait(10)
driver.get(url)
# sleep and/or wait until web full opened
time.sleep(15)
driver.implicitly_wait(20000)

# Click close button after fetching data from modal
def close_modal():
    try:
        # Wait for the modal to be present and visible
        modal = WebDriverWait(driver, 10).until(
            ec.visibility_of_element_located((By.ID, 'viewModalPPH'))
        )
        if modal:
            # modal_close_buttons = driver.find_elements(By.CLASS_NAME, "btn-close")
            # # Filter visible buttons
            # visible_buttons = [btn for btn in modal_close_buttons if btn.is_displayed()]
            try:
                # First, attempt to find and click the backdrop to close the modal by clicking outside
                modal_backdrop = driver.find_element(By.CSS_SELECTOR, '.modal.fade.show')  # Using CSS selector for multiple classes
                driver.execute_script("arguments[0].click();", modal_backdrop)
                time.sleep(2)  # Wait for modal to close
                print("Modal closed by clicking outside (backdrop).")

            except Exception as e:
                print(f"Error closing modal by clicking outside: {e}. Trying to close using the close button...")

                # If clicking the backdrop fails, fall back to clicking the close button
                modal_close_buttons = driver.find_elements(By.CLASS_NAME, "btn-close")
                visible_buttons = [btn for btn in modal_close_buttons if btn.is_displayed()]

                if visible_buttons:
                    close_button = visible_buttons[-1]  # Click the last visible button
                    driver.execute_script("arguments[0].click();", close_button)
                    time.sleep(2)  # Wait for the modal to close
                    print("Modal closed using the close button.")
                else:
                    print("No visible modal close button found.")
            else:
                print("Modal is not currently displayed")

    except Exception as e:
        print(f"Error closing modal: {e}")


processed_registrations = set()



# Set to keep track of processed registrations to avoid duplicates
processed_registrations = set()
data_pendamping_halal = []  # Assuming this is defined globally or earlier in the code

def openModalGetDataCloseModalPerRow():
    # Wait for data to be fully fetched after clicking the button "lihat"
    driver.implicitly_wait(20)  # Adjusted to reasonable timeout
    driver.switch_to.active_element
    driver.switch_to.window(driver.window_handles[0])
    time.sleep(15)  # Consider replacing with explicit waits if possible

    # Checking if the modal is displayed or not
    try:
        modal = driver.find_element(By.ID, 'viewModalPPH')
        time.sleep(3)  # Wait for the modal content to load
        
        # Fetching data from the modal
        result = driver.execute_script(
            """
            var data_pendamping = [];
            var mentoringTableRows = document.querySelectorAll('.modal#viewModalPPH table.table-sm tr:nth-of-type(n+2)');
            if (mentoringTableRows.length > 0) {
                var tableRows = [];
                for (var row of mentoringTableRows) {
                    var cols = row.querySelectorAll('td');
                    var rowData = [];
                    for (var col of cols) {
                        rowData.push(col.textContent);
                    }
                    tableRows.push(rowData.join(", "));
                }

                // Extracting other relevant data from the modal
                data_pendamping.push({
                    email: document.querySelector('span#lblEmailPendamping').textContent,
                    name: document.querySelector('span#lblNamaPendamping').textContent,
                    no_telp: document.querySelector('span#lblNoTelponPendamping').textContent,
                    kabupaten: document.querySelector('span#lblKabupatenPendamping').textContent,
                    kecamatan: document.querySelector('span#lblKecamatanPendamping').textContent,
                    no_registrasi: document.querySelector('span#lblNoRegPendamping').textContent,
                    tgl_terbit: document.querySelector('span#lblTglTerbitPendamping').textContent,
                    lembaga: document.querySelector('span#lblLembagaPendamping2').textContent,  // Added lembaga (institution)
                    pendampingan_pelaku_usaha: tableRows.join(", ")  // Store table data as a single string
                });
            }
            return data_pendamping;
            """
        )

        if not result:
            print("No data fetched from the modal")
            return
        
        print(f"Fetched data: {result}")

        # Skip if no_registrasi is already processed
        no_reg = result[0]['no_registrasi']
        if no_reg in processed_registrations:
            print(f"Skipping duplicate registration: {no_reg}")
            return  # Skip this row

        # Add to the processed set
        processed_registrations.add(no_reg)

        # Store data for further processing
        data_pendamping_halal.append({
            "name": result[0]['name'],
            "email": result[0]['email'],
            "no_telp": result[0]['no_telp'],
            "kabupaten": result[0]['kabupaten'],
            "kecamatan": result[0]['kecamatan'],
            "pendampingan_pelaku_usaha": result[0]['pendampingan_pelaku_usaha'],
            "no_registrasi": result[0]['no_registrasi'],
            "tgl_terbit": result[0]['tgl_terbit'],
            "lembaga": result[0]['lembaga']  # Added lembaga to the dictionary
        })

        # Insert the data into database
        sql = """
            INSERT INTO data_pph_province (province, email, name, no_telp, kabupaten, kecamatan, pendampingan_pelaku_usaha, no_registrasi, tgl_terbit, lembaga)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                name = VALUES(name), 
                no_telp = VALUES(no_telp), 
                kabupaten = VALUES(kabupaten), 
                kecamatan = VALUES(kecamatan), 
                pendampingan_pelaku_usaha = VALUES(pendampingan_pelaku_usaha), 
                tgl_terbit = VALUES(tgl_terbit), 
                lembaga = VALUES(lembaga)
        """
        
        val = (nameProv, result[0]['email'], result[0]['name'], result[0]['no_telp'], 
               result[0]['kabupaten'], result[0]['kecamatan'], 
               result[0]['pendampingan_pelaku_usaha'], no_reg, 
               result[0]['tgl_terbit'], result[0]['lembaga'])

        cursor.execute(sql, val)
        db.commit()
        print(f"Stored data for: {result[0]['name']} with no_registrasi {no_reg}")

    except Exception as e:
        print(f"Error in modal handling: {e}")

    finally:
        # Close modal after data insertion
        close_modal()  # Ensure this function is defined to close the modal properly


# Note: Reassess the need for additional implicit waits; typically set once at the beginning of your script.



def clickDetailPerRow():
    # Get the number of rows in the table excluding header and pagination rows
    row_table_pendamping = len(driver.find_elements(By.XPATH, "//table[@id='GridView3']/tbody/tr")) - 2

    for i in range(0, row_table_pendamping):
        try:
            print(f"\nProcessing row index {i}\n")

            # Wait until the 'Lihat' button is clickable, then click it
            btn_lihat_click = WebDriverWait(driver, 60).until(ec.element_to_be_clickable(
                (By.XPATH, f"//a[contains(@id,'GridView3_lbView_{i}')]")))
            driver.execute_script("arguments[0].click();", btn_lihat_click)

            # Try to extract data, close modal, and handle potential exceptions
            try:
                openModalGetDataCloseModalPerRow()
            except Exception as e:
                print(f"Error in data extraction for row {i}: {e}")
                continue  # Continue with the next row if the modal extraction fails

        except Exception as e:
            print(f"Error processing row {i}: {e}")
            continue  # Continue with the next row if there is an issue clicking the button

        # Clear cookies/session data every 50 rows to prevent memory leaks
        if i % 50 == 0:
            print("Clearing cookies and refreshing session to prevent memory leaks...")
            driver.delete_all_cookies()
            time.sleep(5)  # Allow some time for session reset if needed




def callDependPageIfLostConnection(last_page):
   btn_page_next_click = WebDriverWait(driver, 50).until(ec.element_to_be_clickable((By.XPATH, f"//table[@id='GridView3']/tbody/tr[@class='GridPager']/td/table/tbody/tr/td/a[contains(@href,'{last_page}')]")))
   driver.execute_script("arguments[0].click();", btn_page_next_click)
   time.sleep(15)
   driver.implicitly_wait(20000)
   print('')
   print(f"click pager's {last_page} --non % 10")
   print('')

# use batch(per provinsi) select provinsi from 1 - 34
selectOptProv = driver.find_elements(By.XPATH, "//select[@id='ddlProv']/option")
print(f'Amount of select option province is {len(selectOptProv) - 1}')
valProv = [11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 31, 32, 33, 34, 35, 36, 51, 52, 53, 61, 62, 63, 64, 65, 71, 72, 73, 74, 75, 76, 81, 82, 91, 92]

# list null for datas
data_pendamping_halal = []

for p in range(0, len(selectOptProv) - 1, 1):
   # select btn
   selectProvBtn = WebDriverWait(driver, 15).until(ec.element_to_be_clickable((By.XPATH, "//select[@id='ddlProv']")))
   driver.execute_script("arguments[0].click();", selectProvBtn)
   time.sleep(4)
   driver.implicitly_wait(60)
   
   # option btn
   test = driver.find_element(By.XPATH, f"//select[@id='ddlProv']/option[@value='{valProv[p]}']").click()
   time.sleep(5)
   driver.implicitly_wait(80)
   
   nameProv = driver.find_element(By.XPATH, "//select[@id='ddlProv']/option[@selected='selected']").text
   print(f'Current Province selected is {nameProv}')

   # driver.implicitly_wait(50)
   # amount_pagination_current_page = len(driver.find_elements(By.XPATH, "//table[@id='GridView3']/tbody/tr[@class='GridPager']/td/table/tbody/tr/td"))
   # Set explicit wait
   wait = WebDriverWait(driver, 20000)
   wait.until(ec.presence_of_element_located((By.XPATH, "//table[@id='GridView3']/tbody/tr[@class='GridPager']/td/table/tbody/tr/td")))

   # Now get the amount of pagination
   amount_pagination_current_page = len(driver.find_elements(By.XPATH, "//table[@id='GridView3']/tbody/tr[@class='GridPager']/td/table/tbody/tr/td"))
   print(f"Amount of pagination elements on the current page: {amount_pagination_current_page}")

   print(f'Amount pagination current page is {amount_pagination_current_page}')

   if amount_pagination_current_page == 12:
      # test
      # click >> count page, back
      # loop count page
      # click last page to count amount of page
      last_page_btn = WebDriverWait(driver, 15).until(ec.element_to_be_clickable((By.XPATH, "//table[@id='GridView3']/tbody/tr[@class='GridPager']/td/table/tbody/tr/td/a[text() = '>>']")))
      driver.execute_script("arguments[0].click();", last_page_btn)
      time.sleep(5)
      driver.implicitly_wait(20000)
      last_page = driver.find_element(By.XPATH, "//table[@id='GridView3']/tbody/tr[@class='GridPager']/td/table/tbody/tr/td/span").text
      time.sleep(5)
      driver.implicitly_wait(20000)
      print('')
      print(f"amount all pagination is {last_page}")
      print('')

      # click firt page to back default
      first_page_btn = WebDriverWait(driver, 18).until(ec.element_to_be_clickable((By.XPATH, "//table[@id='GridView3']/tbody/tr[@class='GridPager']/td/table/tbody/tr/td/a[text() = '<<']")))
      driver.execute_script("arguments[0].click();", first_page_btn)
      time.sleep(1)
      driver.implicitly_wait(20)

      for x in range(int(last_page)):
         print(f"Current page is {x+1}")
         print('')
         print('12 --')

         amount_pagination_current_page = len(driver.find_elements(By.XPATH, "//table[@id='GridView3']/tbody/tr[@class='GridPager']/td/table/tbody/tr/td"))
         print(f"amount pagination {amount_pagination_current_page}")


         lostPage = 0

         for c in range(11, lostPage, 10):
            callDependPageIfLostConnection(c)

         for y in range(lostPage, int(last_page), 1):
            time.sleep(4)
            driver.implicitly_wait(60)

            # if y+1 != 1:
               # callDependPageIfLostConnection(y+1)
               # exception first page cause error
            if y+1 != 1 and y % 10 != 0:
               time.sleep(2)
               driver.implicitly_wait(30)
               btn_page_click = WebDriverWait(driver, 50).until(ec.element_to_be_clickable((By.XPATH,f"//table[@id='GridView3']/tbody/tr[@class='GridPager']/td/table/tbody/tr/td/a[text() = '{y+1}']")))
               # btn_page_click = WebDriverWait(driver, 50).until(ec.element_to_be_clickable((By.XPATH,f"//table[@id='GridView3']/tbody/tr[@class='GridPager']/td/table/tbody/tr/td/a[contains(@href,'{y+1}')]")))
               driver.execute_script("arguments[0].click();", btn_page_click)
               time.sleep(3)
               driver.implicitly_wait(60)
               print('')
               print(f"click pager's {y+1} --non % 10")
               print('')
               clickDetailPerRow()

            elif y+1 == 1:
               # continue
               clickDetailPerRow()

            elif y % 10 == 0 :
               btn_page_next_click = WebDriverWait(driver, 50).until(ec.element_to_be_clickable((By.XPATH,f"//table[@id='GridView3']/tbody/tr[@class='GridPager']/td/table/tbody/tr/td/a[contains(@href,'{y+1}')]")))
               driver.execute_script("arguments[0].click();", btn_page_next_click)
               time.sleep(3)
               driver.implicitly_wait(60)
               print('')
               print(f"click pager's {y+1} --can % 10")
               print('')
               clickDetailPerRow()
            
            # clickDetailPerRow()

   else : 
      # loop count exist
      print('non 12')
      print('')
      amount_pagination_current_page = len(driver.find_elements(By.XPATH, "//table[@id='GridView3']/tbody/tr[@class='GridPager']/td/table/tbody/tr/td"))
      print(f"amount pagination {amount_pagination_current_page}")

      for e in range(0, int(amount_pagination_current_page), 1):
         time.sleep(4)
         driver.implicitly_wait(60)

         if e+1 != 1 and e % 10 != 0:
            time.sleep(2)
            driver.implicitly_wait(30)
            btn_page_click = WebDriverWait(driver, 50).until(ec.element_to_be_clickable((By.XPATH,f"//table[@id='GridView3']/tbody/tr[@class='GridPager']/td/table/tbody/tr/td/a[text() = '{e+1}']")))
            # btn_page_click = WebDriverWait(driver, 50).until(ec.element_to_be_clickable((By.XPATH,f"//table[@id='GridView3']/tbody/tr[@class='GridPager']/td/table/tbody/tr/td/a[contains(@href,'{y+1}')]")))
            driver.execute_script("arguments[0].click();", btn_page_click)
            time.sleep(3)
            driver.implicitly_wait(60)
            print('')
            print(f"click pager's {e+1} --non % 10")
            print('')
            clickDetailPerRow()

         elif e+1 == 1:
            # continue
            clickDetailPerRow()

         elif e % 10 == 0 :
            btn_page_next_click = WebDriverWait(driver, 50).until(ec.element_to_be_clickable((By.XPATH,f"//table[@id='GridView3']/tbody/tr[@class='GridPager']/td/table/tbody/tr/td/a[contains(@href,'{e+1}')]")))
            driver.execute_script("arguments[0].click();", btn_page_next_click)
            time.sleep(3)
            driver.implicitly_wait(60)
            print('')
            print(f"click pager's {e+1} --can % 10")
            print('')
            clickDetailPerRow()
            

print(data_pendamping_halal)
print(f"total data fetched {len(data_pendamping_halal)}")

# get keys (header) of data
keys = data_pendamping_halal[0].keys()

# parsed to csv
with open('data_pendamping_halal.csv', 'w', newline='') as output_file:
    dict_writer = csv.DictWriter(output_file, keys)
    dict_writer.writeheader()
    dict_writer.writerows(data_pendamping_halal)