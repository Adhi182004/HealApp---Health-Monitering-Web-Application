<<<<<<< HEAD
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
import time

# STEP 1: Paste your actual ChromeDriver path here
path = r"C:/Users/YourName/Downloads/chromedriver-win64/chromedriver.exe"
service = Service(executable_path=path)

# STEP 2: Launch browser
driver = webdriver.Chrome(service=service)

# STEP 3: Go to Google
driver.get("https://www.google.com")

# STEP 4: Search "Selenium Python"
search_box = driver.find_element(By.NAME, "q")
search_box.send_keys("Selenium Python")
search_box.send_keys(Keys.RETURN)

# STEP 5: Wait 5 seconds, then close
time.sleep(5)
driver.quit()
=======
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
import time

# STEP 1: Paste your actual ChromeDriver path here
path = r"C:/Users/YourName/Downloads/chromedriver-win64/chromedriver.exe"
service = Service(executable_path=path)

# STEP 2: Launch browser
driver = webdriver.Chrome(service=service)

# STEP 3: Go to Google
driver.get("https://www.google.com")

# STEP 4: Search "Selenium Python"
search_box = driver.find_element(By.NAME, "q")
search_box.send_keys("Selenium Python")
search_box.send_keys(Keys.RETURN)

# STEP 5: Wait 5 seconds, then close
time.sleep(5)
driver.quit()
>>>>>>> 07cab6649c4bdb8b053dba20e02ddbbdbe3112a2
