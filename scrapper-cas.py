from bs4 import BeautifulSoup
import requests

class ClientSession:

    def __init__(self, host, user, pwd):
        self.urls = OpenFireUrl(host,user,pwd)
        with requests.Session() as self.session:
            if self.urls.login:
                login = self.session.get(self.urls.login, timeout=5)
                self.cookies = login.cookies
            if self.cookies:
                login = self.session.post(self.urls.loginMain,
                                          timeout=5,
                                          cookies=self.cookies)

class OpenFireUrl:

    def __init__(self, host, user, pwd):
        self.host = host
        self.user = user
        self.pwd = pwd
        self.login = self.login()
        self.loginMain = self.loginMain()
        self.avayaPluginMain = self.avayaPluginMain()
        self.systemParameters = self.systemParameters()

    def login(self):
        return 'http://'+self.host+':9090/login.jsp'

    def loginMain(self):
        return 'http://'+ self.host + \
            ':9090/login.jsp?url=%2Findex.jsp&login=true&username=' \
            + self.user + '&password='+ self.pwd

    def avayaPluginMain(self):
        return 'http://' + self.host + \
            ':9090/plugins/avaya/avaya-summary'

    def systemParameters(self):
        return 'http://' + self.host + \
            ':9090/server-properties.jsp'


class OpenFire:
    def __init__(self,clientSession):
        self.clientSession = clientSession
        self.urls = clientSession.urls
        self.getParams = self.getParams()
        self.getAvayaPluginSites = self.getAvayaPluginSites()

    def soup(self,htmlObject, parser):
        soup = BeautifulSoup(htmlObject.content, parser)
        return soup

    def getParams(self):
        clientSession = self.clientSession
        paramsUrl = self.urls.systemParameters
        if clientSession.cookies:
            with clientSession.session as sess:
                if clientSession.cookies:
                    params = sess.get(paramsUrl, cookies=clientSession.cookies)
                soupObject = self.soup(params, 'html.parser')
                if soupObject:
                    parametersDict = {} # STORE the parameters in a dictionary
                    span = soupObject.find_all('span')
                    for f in span:
                        if span.index(f) % 2 == 0:
                            parametersDict[f.get('title')] = \
                                            span[span.index(f)+1].get('title')
                return parametersDict

    def getAvayaPluginSites(self):
        clientSession = self.clientSession
        sitesUrl = self.urls.avayaPluginMain
        with clientSession.session as sess:
            if clientSession.cookies:
                sitesHtmlObject = sess.get(sitesUrl,
                                           cookies=clientSession.cookies
                                           )
                soupObject = self.soup(sitesHtmlObject, 'html.parser')
            if soupObject:
                mainDiv = soupObject.find('div', class_='jive-table')
                sitesTable = [tr for tr in mainDiv.find_all('tr',
                                            class_=['jive-odd', 'jive-even'])]
                sites = {}
                for tr in sitesTable:
                    sites[tr.find_all('td')[1].string.strip('\r\n')] = {
                        'id': tr.find_all('td')[0].string.strip('\r\n'),
                        'name': tr.find_all('td')[1].string.strip('\r\n'),
                        'devices': tr.find_all('td')[4].string.strip('\r\n'),
                        'sms': tr.find_all('td')[5].find_all('img')[0]['alt'],
                        'jtapiVersion': tr.find_all('td')[8].string.strip('\r\n'),
                        'signal': tr.find_all('td')[9].find_all('img')[0]['alt'],
                        'refresh': tr.find_all('td')[10].string.strip('\r\n')
                    }

            return sites
