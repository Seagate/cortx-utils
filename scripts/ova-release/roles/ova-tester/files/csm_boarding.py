# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import unittest, time
import gui_element_locators as loc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import yaml

class CSM_boarding(unittest.TestCase):
    def setUp(self):
        #self.driver = webdriver.Firefox()
        chrome_options = Options()
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--ignore-ssl-errors=yes')
        chrome_options.add_argument('--ignore-certificate-errors')
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(30)
        with open(r'/root/config.yaml') as file:
            self.cfg = yaml.safe_load(file)

    def test_preboarding(self):
        try:
            browser = self.driver
            browser.get(self.cfg['preboarding']['url'])
            ele = self.get_element(By.ID, loc.Preboarding.start_btn)
            ele.click()
            ele = self.get_element(By.ID, loc.Preboarding.terms_btn)
            ele.click()
            ele = self.get_element(By.ID,loc.Preboarding.accept_btn)
            ele.click()
            ele = self.get_element(By.ID, loc.Preboarding.username_ip)
            ele.send_keys(self.cfg['preboarding']['username'])
            ele = self.get_element(By.ID, loc.Preboarding.password_ip)
            ele.send_keys(self.cfg['preboarding']['password'])
            ele = self.get_element(By.ID, loc.Preboarding.confirmpwd_ip)
            ele.send_keys(self.cfg['preboarding']['password'])
            ele = self.get_element(By.ID, loc.Preboarding.email_ip)
            ele.send_keys(self.cfg['preboarding']['email'])
            ele = self.get_element(By.ID, loc.Preboarding.create_btn)
            ele.click()
            ele = self.get_element(By.ID, loc.Preboarding.userlogin_ip)
            print("Admin user is created")
        except Exception as e:
            print(e)
            self.assertTrue(False,"ERROR: Failed to create Admin User")

    def test_onboarding(self):
        try:
            browser = self.driver
            browser.get(self.cfg['onboarding']['url'])
            ele = self.get_element(By.ID, loc.Onboarding.username_ip)
            self.clear_send(ele, self.cfg['onboarding']['username'])
            ele = self.get_element(By.ID, loc.Onboarding.password_ip)
            self.clear_send(ele, self.cfg['onboarding']['password'])
            ele = self.get_element(By.ID, loc.Onboarding.login_btn)
            ele.click()
            ele = self.get_element(By.ID, loc.Onboarding.sys_ip)
            self.clear_send(ele, self.cfg['onboarding']['system'])
            ele = self.get_element(By.XPATH, loc.Onboarding.continue_btn)
            ele.click()
            ele = self.get_element(By.XPATH, loc.Onboarding.continue_btn)
            ele.click()
            ele  = self.get_element(By.ID,loc.Onboarding.dns_server_ip)
            self.clear_send(ele, self.cfg['onboarding']['dns'])
            ele  = self.get_element(By.ID,loc.Onboarding.dns_search_ip)
            self.clear_send(ele, self.cfg['onboarding']['search'])
            ele = self.get_element(By.XPATH, loc.Onboarding.continue_btn)
            ele.click()
            ele  = self.get_element(By.ID,loc.Onboarding.ntp_server_ip)
            self.clear_send(ele, self.cfg['onboarding']['ntp'])
            ele = self.get_element(By.XPATH, loc.Onboarding.continue_btn)
            ele.click()
            ele  = self.get_element(By.XPATH,loc.Onboarding.skip_step_chk)
            ele.click()
            ele = self.get_element(By.XPATH, loc.Onboarding.continue_btn)
            ele.click()
            ele = self.get_element(By.XPATH, loc.Onboarding.continue_btn)
            ele.click()
            ele  = self.get_element(By.ID,loc.Onboarding.confirm_btn)
            ele.click()
            ele  = self.get_element(By.ID,loc.Onboarding.finish_btn)
            ele.click()
            print("Onboarding completed!")
        except Exception as e:
            print(e)
            self.assertTrue(False,"ERROR: Onboarding Failed")
			
    def get_element(self, by, loc):
        time.sleep(2)
        ele = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((by,loc)))
        return ele

    def clear_send(self, ele, txt):
        time.sleep(2)
        ele.click()
        ele.send_keys(Keys.CONTROL + "a")
        ele.send_keys(Keys.DELETE)
        ele.send_keys(txt)

    def is_element_present(self, how, what):
        try: self.driver.find_element(by=how, value=what)
        except NoSuchElementException: return False
        return True
    

    
if __name__ == "__main__":
    unittest.main()
