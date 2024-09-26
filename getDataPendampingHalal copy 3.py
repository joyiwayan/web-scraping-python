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

def closeModal():
    try:
        # Wait for the close button to be visible and clickable
        btn_close_click = WebDriverWait(driver, 40).until(ec.presence_of_element_located((By.CLASS_NAME, "btn-close")))
        if btn_close_click.is_displayed():
            btn_close_click.click()
            time.sleep(1)
            print("Modal closed successfully!")
        else:
            print("No visible close button found!")
    except Exception as e:
        print(f"Error in closing modal: {str(e)}")




processed_registrations = set()

def openModalGetDataCloseModalPerRow():
    driver.implicitly_wait(20000)
    driver.switch_to.active_element
    driver.switch_to.window(driver.window_handles[0])
    time.sleep(15)

    modal = driver.find_element(By.ID, 'viewModalPPH')
    time.sleep(3)
    driver.implicitly_wait(50)
    
    result = driver.execute_script("""
        var data_pendamping = [];
        for (var i of document.querySelectorAll('.modal#viewModalPPH')){
            var tableRows = [];
            var mentoringTableRows = i.querySelectorAll('table.table-sm tr:nth-of-type(n+2)');
            for (var row of mentoringTableRows) {
                var cols = row.querySelectorAll('td');
                var rowData = [];
                for (var col of cols) {
                    rowData.push(col.textContent);
                }
                tableRows.push(rowData.join(", "));
            }
            data_pendamping.push({
                email: i.querySelector('span#lblEmailPendamping').textContent,
                name: i.querySelector('span#lblNamaPendamping').textContent,
                no_telp: i.querySelector('span#lblNoTelponPendamping').textContent,
                kabupaten: i.querySelector('span#lblKabupatenPendamping').textContent,
                kecamatan: i.querySelector('span#lblKecamatanPendamping').textContent,
                no_registrasi: i.querySelector('span#lblNoRegPendamping').textContent,
                tgl_terbit: i.querySelector('span#lblTglTerbitPendamping').textContent,
                lembaga: i.querySelector('span#lblLembagaPendamping2').textContent,
                pendampingan_pelaku_usaha: tableRows.join(", ")
            });
        }
        return data_pendamping;
    """)

    print(f"Fetched data: {result}")
    
    data_pendamping_halal.append({
        "name": result[0]['name'],
        "email": result[0]['email'],
        "no_telp": result[0]['no_telp'],
        "kabupaten": result[0]['kabupaten'],
        "kecamatan": result[0]['kecamatan'],
        "pendampingan_pelaku_usaha": result[0]['pendampingan_pelaku_usaha'],
        "no_registrasi": result[0]['no_registrasi'],
        "tgl_terbit": result[0]['tgl_terbit'],
        "lembaga": result[0]['lembaga']
    })

    sql = """
        INSERT INTO data_pph_province (province, email, name, no_telp, kabupaten, kecamatan, pendampingan_pelaku_usaha, no_registrasi, tgl_terbit, lembaga)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE name = VALUES(name), no_telp = VALUES(no_telp), kabupaten = VALUES(kabupaten), kecamatan = VALUES(kecamatan), pendampingan_pelaku_usaha = VALUES(pendampingan_pelaku_usaha), no_registrasi = VALUES(no_registrasi), tgl_terbit = VALUES(tgl_terbit), lembaga = VALUES(lembaga)
    """
    
    val = (nameProv, result[0]['email'], result[0]['name'], result[0]['no_telp'], result[0]['kabupaten'], result[0]['kecamatan'], result[0]['pendampingan_pelaku_usaha'], result[0]['no_registrasi'], result[0]['tgl_terbit'], result[0]['lembaga'])
    cursor.execute(sql, val)
    db.commit()
    print('One row of data stored in the database!')

    # Check for already processed registration
    no_registrasi = result[0]['no_registrasi']
    if no_registrasi in processed_registrations:
        print(f"Skipping already processed no_registrasi: {no_registrasi}")
        return
    processed_registrations.add(no_registrasi)

    # Close modal after data processing
    closeModal()




# Note: Reassess the need for additional implicit waits; typically set once at the beginning of your script.



def clickDetailPerRow():
   # amount of row in current table show, should decrease 2 row, cause first row is thead and last row is pagination
   row_table_pendamping = len(driver.find_elements(By.XPATH, "//table[@id='GridView3']/tbody/tr")) - 2

   time.sleep(3)
   driver.implicitly_wait(60)
   for i in range(0, row_table_pendamping, 1):
         
         
      time.sleep(2)
      driver.implicitly_wait(60)
      print('')
      print(f"data index {i}")
      print('')
      btn_lihat_click = WebDriverWait(driver, 60).until(ec.element_to_be_clickable((By.XPATH, f"//a[contains(@id,'GridView3_lbView_{i}')]")))
      driver.execute_script("arguments[0].click();", btn_lihat_click)

      time.sleep(2)
      driver.implicitly_wait(60)

      openModalGetDataCloseModalPerRow()

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