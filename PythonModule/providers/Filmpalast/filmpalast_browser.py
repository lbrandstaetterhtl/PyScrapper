import PythonModule.core as core
from PythonModule.core.network import browser
from PythonModule.core.network.browser.models import COOKIE_FILE, PLAY_BUTTON_SELECTORS

from .. import models




class FilmpalastMediaBrowser(browser.MediaBrowser):
    def _handleResponse(self, response):
        print(response.url)