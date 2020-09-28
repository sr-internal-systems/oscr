"""
oscr.clients.linkedin
~~~~~~~~~~~~~~~~~~~~~

This module contains a high-level LinkedIn scraping API class.

This is an incomplete experimental module. It should not be used in production.
"""

import os

from selenium import webdriver


class LinkedInClient:
    """Implement the `LinkedInClient` class.

    This class provides a high-level interface for collecting data
    via a system of web scrapers/drivers.
    """

    def __init__(self, username: str = None, password: str = None):
        self.driver: webdriver = webdriver.Chrome()

        username: str = username or os.getenv("LI_USERNAME")
        password: str = password or os.getenv("LI_PASSWORD")
        self._login(username, password)

    def _login(self, username: str, password: str):
        """Log into LinkedIn via a Selenium ChromeDriver.

        :param username: A valid `str` LinkedIn username.
        :param password: A valid `str` LinkedIn password.
        """
        self.driver.get("https://www.linkedin.com/login")

        username_input = self.driver.find_element_by_id("username")
        password_input = self.driver.find_element_by_id("password")

        username_input.send_keys(username)
        password_input.send_keys(password)

        password_input.submit()
