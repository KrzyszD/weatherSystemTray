import os
import sys
import traywindow
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import QTimer, QDateTime
from PIL import Image, ImageDraw, ImageFont
import requests
import json

class SystemTrayIcon(QtWidgets.QSystemTrayIcon):

    zipCode = "60193"

    def __init__(self, icon, parent=None, app=None):
        QtWidgets.QSystemTrayIcon.__init__(self, icon, parent)

        self.makeContextMenu(parent, app)

        self.activated.connect(self.systemIconClick)

        app.focusChanged.connect(self.on_focusChanged)

        self.getData()

        self.updateCurrentTemp()
        self.setTimers()

        self.makeIcon()

    def getData(self):
        
        self.getLngLat()
        self.weatherURLs()
        self.getWeatherData()
        self.getWeekdays()

    def getLngLat(self):

        cwd = os.path.dirname(os.path.abspath(__file__))
        cacheName = cwd + '\\' + 'cache.json'

        with open(cacheName, 'r') as jsonFile:
            self.cache = json.load(jsonFile)

        if self.zipCode not in self.cache:
            URL = "https://www.zipcodeapi.com/rest/{0}/info.json/{1}/degrees"
            URL = URL.format(self.cache["zipApiKey"], self.zipCode)
            
            r = requests.get(url = URL)
            data = r.json()

            self.cache[self.zipCode] = {}
            self.cache[self.zipCode]["lng"] = data["lng"]
            self.cache[self.zipCode]["lat"] = data["lat"]

            json_object = json.dumps(self.cache, indent=4)
            with open(cacheName, 'w') as jsonFile:
                jsonFile.write(json_object)

    def weatherURLs(self):

        lat = self.cache[self.zipCode]["lat"]
        lng = self.cache[self.zipCode]["lng"]

        URL =  "https://api.weather.gov/points/{lat},{lng}"
        URL = URL.format(lat=lat, lng=lng)
        
        r = requests.get(url = URL)
        data = r.json()
        
        forecastHourlyURL = data["properties"]["forecastHourly"]
        self.weatherURL = forecastHourlyURL

    def getWeatherData(self):

        r = requests.get(url = self.weatherURL)
        data = r.json()

        periods = data["properties"]["periods"]

        idx = int(periods[0]["startTime"][11:13])

        self.x = []
        self.temps = []
        self.daylight = []
        self.precipitation = []

        for period in periods:
            self.x.append(idx)
            idx += 1

            self.temps.append(period["temperature"])
            self.daylight.append(period["isDaytime"])
            self.precipitation.append(period["probabilityOfPrecipitation"]["value"])

    def getWeekdays(self):
        self.days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

        weekday = QDateTime.currentDateTime().date().dayOfWeek()

        self.days = self.days[weekday:] + self.days[:weekday]

    def updateCurrentTemp(self):
        currentDateAndTime = QDateTime.currentDateTime().time()

        hour = currentDateAndTime.hour()
        minute = currentDateAndTime.minute()

        self.curTime = hour + minute / 60

        idx = hour - self.x[0]
        self.temp = (1 - minute / 60) * self.temps[idx] + (minute / 60) * self.temps[idx + 1]

    def setTimers(self):
        self.day = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self.timerEvent)
        self.timer.start(1000 * 60 * 30)
        # self.timer.start(1000)
    
    def timerEvent(self):
        day = QDateTime.currentDateTime().date().day()
        
        if day != self.day:
            self.getData()
            self.day = day

        self.updateCurrentTemp()
        self.makeIcon()

    def makeContextMenu(self, parent, app):
        menu = QtWidgets.QMenu(parent)

        prefs_action = menu.addAction('Window')
        prefs_action.triggered.connect(self.openWindows)

        quit_action = menu.addAction('Quit')
        quit_action.triggered.connect(app.quit)

        self.setContextMenu(menu)

    def systemIconClick(self, reason):
        # self.openWindows()
        if reason == QtWidgets.QSystemTrayIcon.Context:
            # print("Right Click")
            pass
        if reason == QtWidgets.QSystemTrayIcon.Trigger:
            # print("Left Click")
            self.openWindows()

    def openWindows(self):
        self.window = traywindow.MainWindow(self)

        # https://stackoverflow.com/a/39064225
        # https://stackoverflow.com/a/26411990
        ag = QtWidgets.QDesktopWidget().availableGeometry()
        sg = QtWidgets.QDesktopWidget().screenGeometry()

        titleBarHeight = QtWidgets.QStyle.PM_TitleBarHeight

        widget = self.window.size()

        x = int(ag.width() - 1.5 * widget.width())
        y = int(2 * ag.height() - sg.height() - widget.height() + 0 * titleBarHeight)

        self.window.move(x, y)
        self.window.show()

        self.window.setFocus(True)
        self.window.raise_()
        self.window.activateWindow()
    
    def on_focusChanged(self):
        if not self.window.isActiveWindow():
            self.window.close()

    def makeIcon(self):
        # Move to trayIcon
        cwd = os.path.dirname(os.path.abspath(__file__))
        filename = cwd + '\\' + 'icon.png'

        curTemp = "%d" % int(round(self.temp))

        fnt = ImageFont.truetype('arial.ttf', 28)

        # create new image
        image = Image.new(mode = "RGBA", size = (32,32), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.text((0,0), curTemp, font=fnt, fill=(255,255,255, 255))

        image.save(filename, 'PNG')

        self.updateIcon()

    def updateIcon(self): 
        cwd = os.path.dirname(os.path.abspath(__file__))
        icon = cwd + '\\' + 'icon.png'
        icon = QtGui.QIcon(icon)
        self.setIcon(icon)


def main():
    cwd = os.path.dirname(os.path.abspath(__file__))
    image = cwd + '\\' + 'icon.png'

    app = QtWidgets.QApplication(sys.argv)
    w = QtWidgets.QWidget()
    trayIcon = SystemTrayIcon(QtGui.QIcon(image), w, app)
    trayIcon.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()