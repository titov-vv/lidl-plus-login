#!/usr/bin/python
# ----------------------------------------------------------------------------------------------------------------------
# Script to get Authentication token for Lidl Plus account identified by username and password
# ----------------------------------------------------------------------------------------------------------------------
import requests
import requests_oauthlib
from oauthlib.oauth2 import MobileApplicationClient
from urllib import parse
from PySide6.QtCore import Signal, QUrl, Slot
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QPlainTextEdit
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage, QWebEngineUrlScheme, \
    QWebEngineUrlSchemeHandler, QWebEngineUrlRequestJob
from PySide6.QtWebEngineWidgets import QWebEngineView

# ----------------------------------------------------------------------------------------------------------------------
# Final URI is returned in form of "com.lidlplus.app://callback?code=..&scope=..&state=..&session_state=..", so
# it requires a special handler for "protocol" "com.lidlplus.app"
# Signal "data_received" is emitted when URI is processed, its parameter contains dictionary with URI parameters
# Page is redirected to "about:blank" in order to clean the browser window
class appDataHanlder(QWebEngineUrlSchemeHandler):
    scheme = b"com.lidlplus.app"
    data_received = Signal(dict)

    def __init__(self, parent = None):
        super().__init__(parent)

    def requestStarted(self, job: QWebEngineUrlRequestJob) -> None:
        url = job.requestUrl().url()
        params = dict(parse.parse_qsl(parse.urlsplit(url).query))
        job.fail(QWebEngineUrlRequestJob.Error.NoError)   # Stop processing but without an error
        self.data_received.emit(params)  # Dict contains 'code', 'scope', 'state' and 'session_state' elements

# ----------------------------------------------------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        self.layout = QVBoxLayout()
        # Push button to initiate login action
        self.button = QPushButton(self)
        self.button.setText("Login")
        self.layout.addWidget(self.button)
        self.button.pressed.connect(self.doLogin)
        # Browser widget for user interaction
        self.browser = QWebEngineView(self)
        self.browser.setMinimumSize(400, 600)
        self.layout.addWidget(self.browser)
        # Text box to display results
        self.text_box = QPlainTextEdit(self)
        self.text_box.setVisible(False)
        self.layout.addWidget(self.text_box)
        # Main widget
        self.central_widget = QWidget(self)
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)

        self.verifier = ''
        self.lidl_client_id = "LidlPlusNativeClient"
        # Create scheme, handler and assign it to web-profile that is used for browser widget
        self.app_lidl_uri_scheme = QWebEngineUrlScheme(appDataHanlder.scheme)
        self.app_lidl_uri_scheme.setSyntax(QWebEngineUrlScheme.Syntax.Path)
        self.app_lidl_uri_scheme.setFlags(QWebEngineUrlScheme.Flag.ContentSecurityPolicyIgnored | QWebEngineUrlScheme.Flag.LocalAccessAllowed)
        QWebEngineUrlScheme.registerScheme(self.app_lidl_uri_scheme)
        self.app_lidl_uri_handler = appDataHanlder(self)
        self.app_lidl_uri_handler.data_received.connect(self.processResponse)
        self.web_profile = QWebEngineProfile(self)
        self.web_profile.installUrlSchemeHandler(appDataHanlder.scheme, self.app_lidl_uri_handler)
        self.browser.setPage(QWebEnginePage(self.web_profile, self))

    def doLogin(self):
        # Show right UI elements
        self.text_box.setVisible(False)
        self.browser.setVisible(True)
        # Get Login URL and open it in browser
        client = MobileApplicationClient(client_id=self.lidl_client_id)
        self.verifier = client.create_code_verifier(86)
        challenge = client.create_code_challenge(self.verifier, code_challenge_method='S256')
        oauth = requests_oauthlib.OAuth2Session(client_id=self.lidl_client_id,
                                                scope='openid profile offline_access lpprofile lpapis')
        oauth_url, oauth_state = oauth.authorization_url(url='https://accounts.lidl.com/')
        url = f"https://accounts.lidl.com/Account/Login?ReturnUrl=%2Fconnect%2Fauthorize%2Fcallback%3Fredirect_uri%3Dcom.lidlplus.app%253A%252F%252Fcallback"
        url += f"%26client_id%3D{self.lidl_client_id}"
        url += f"%26response_type%3Dcode%26state%3D{oauth_state}"  # "%26nonce%3Dt5Z_q8gekXoFRNmOVq2Ufg" - this part was omitted
        url += f"%26scope%3Dopenid%2520profile%2520offline_access%2520lpprofile%2520lpapis"
        url += f"%26code_challenge%3D{challenge}%26code_challenge_method%3DS256%26language%3DPT-PT%26track%3Dfalse%26force%3Dfalse%26Country%3DPT"
        self.browser.load(QUrl(url))   # Country and language are hard-coded to Portugal

    @Slot()
    def processResponse(self, params: dict):
        # Show right UI elements
        self.browser.setVisible(False)
        self.text_box.clear()
        self.text_box.setVisible(True)
        if 'code' not in params:
            self.text_box.appendPlainText("ERROR: no auth code in callback URI")
            return
        # Get Auth token and display it
        s = requests.Session()
        s.headers["Authorization"] = "Basic TGlkbFBsdXNOYXRpdmVDbGllbnQ6c2VjcmV0"
        s.headers['Accept'] = "application/json"
        data = {
            "grant_type": "authorization_code",
            "code": params['code'],
            "redirect_uri": "com.lidlplus.app://callback",
            "code_verifier": self.verifier
        }
        response = s.post("https://accounts.lidl.com/connect/token", data=data)
        self.text_box.appendPlainText(f"Status code: {response.status_code}")
        self.text_box.appendPlainText(f"Result: {response.text}")


# ----------------------------------------------------------------------------------------------------------------------
def main():
    app = QApplication()
    wnd = MainWindow()
    wnd.show()
    return app.exec()

if __name__ == '__main__':
    main()
