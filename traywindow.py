from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMainWindow, QWidget
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QCursor, QFont
import pyqtgraph as pg

class MainWindow(QMainWindow):

    moveFlag  = False
    prevTime = -1

    def __init__(self, trayIcon):
        QMainWindow.__init__(self)

        self.trayIcon = trayIcon

        self.setFixedSize(QSize(660, 420))    
        self.setWindowTitle("Weather") 

        self.makeLayout()

        pg.setConfigOptions(antialias=True)

        self.setGraph()
        self.plotCurrentTime()
        self.plotRegions()

        self.makeButtons()
        self.addDayLabels()

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint) 
        

    def makeLayout(self):
        # Starts basic layout
        self.layout = QtWidgets.QVBoxLayout()

        self.centralWidget = QWidget()
        self.centralWidget.setLayout(self.layout)

        self.setCentralWidget(self.centralWidget)

    def makeButtons(self):
        # Day buttons
        self.btnRow = QtWidgets.QHBoxLayout()

        self.btns = []

        for i in range(7):
            # Each Btn
            self.btns.append(QPushButton(self.trayIcon.days[i], self))
            self.btns[-1].setFixedSize(80, 80)
            self.btns[-1].clicked.connect(self.chooseDayWrapper(i))
            self.btnRow.addWidget(self.btns[-1])
        
        self.layout.addLayout(self.btnRow)

    def addDayLabels(self):

        for i in range(7):
                
            color = (0, 0, 0)
            anchor = (0.5, 1) # Where the "center point" is located for positioning
            text = self.trayIcon.days[i]

            text = pg.TextItem(text, anchor=anchor, color=color)
            text.setPos(12 + i * 24, 90)

            font = QFont()
            font.setStyleHint(QFont.SansSerif)
            font.setPointSize(12)
            text.setFont(font)

            self.graphWidget.addItem(text)

        pass

    def chooseDayWrapper(self, i):
        # Use for attaching chooseDay to the day buttons
        return lambda: self.chooseDay(i)

    def chooseDay(self, day):
        # Update graph for future days
        self.day = day

        self.graphWidget.setXRange(day * 24, (day + 1) * 24, padding=0)

    def plotRegions(self):
        nightBrush = pg.mkBrush((0, 0, 0, 50))
        dayBrush = pg.mkBrush((0, 125, 125, 50))

        pen = pg.mkPen(None)
        for time, daylight in zip(self.trayIcon.x, self.trayIcon.daylight):
            brush = dayBrush if daylight else nightBrush
            region = pg.LinearRegionItem(values=(time, time+1), pen=pen, brush=brush, movable=False)
            self.graphWidget.addItem(region)
        
    def plotCurrentTime(self):

        # Make text for current time
        self.trayIcon.updateCurrentTemp()

        color = (0, 0, 0)
        anchor = (0.5, 1) # Where the "center point" is located for positioning
        text = "%d" % int(round(self.trayIcon.temp, 0))

        text = pg.TextItem(text, anchor=anchor, color=color)
        text.setPos(self.trayIcon.curTime, self.trayIcon.temp + 3)

        font = QFont()
        font.setStyleHint(QFont.SansSerif)
        font.setPointSize(12)
        text.setFont(font)

        self.graphWidget.addItem(text)

        self.graphWidget.plot([self.trayIcon.curTime], [self.trayIcon.temp], pen=None, symbol='o')

    def makeClickTemp(self, x):

        time = max(self.trayIcon.x[0], x)

        intTime = max(0, int(time) - self.trayIcon.x[0])
        timePer = time % 1
        temp = self.trayIcon.temps[intTime] * (1 - timePer) + self.trayIcon.temps[intTime + 1] * timePer


        color = (50, 50, 50)
        anchor = (0.5, 1) # Where the "center point" is located for positioning
        text = "%d" % int(round(temp, 0))

        if "mouseMarker" not in vars(self):
            self.text = pg.TextItem(text, anchor=anchor, color=color)
            self.text.setPos(time, temp + 3)

            font = QFont()
            font.setStyleHint(QFont.SansSerif)
            font.setPointSize(12)
            self.text.setFont(font)

            self.graphWidget.addItem(self.text)
            self.mouseMarker = self.graphWidget.plot([time], [temp], pen=None, symbol='o')
            self.mouseMarkerFirstX = time
            self.mouseMarkerFirstY = temp
        else:
            if self.prevTime == intTime:
                self.text.hide()
                self.mouseMarker.hide()

                self.prevTime = -1
            else:
                self.text.setPos(time, temp + 3)
                self.text.setText("%d" % temp)
                self.mouseMarker.setPos(time - self.mouseMarkerFirstX, temp - self.mouseMarkerFirstY)
                
                self.text.show()
                self.mouseMarker.show()

                self.prevTime = intTime


    def setGraph(self):
        # Graph area
        self.graphWidget = pg.PlotWidget()
        self.graphWidget.scene().sigMouseClicked.connect(self.mouse_clicked)  
        self.graphWidget.setFixedSize(640, 320)

        self.layout.addWidget(self.graphWidget)

        # Light Blue Line at 32F for comparisons
        pen = pg.mkPen(color=(128, 128, 255), width=3)
        self.freezingLine = self.graphWidget.plot([0, 7 * 24], [32, 32], pen=pen)
        self.freezingLine.setAlpha(0.4, False)

        # Make Line and update line to data
        pen = pg.mkPen(color=(255, 0, 0), width=3) 
        self.line = self.graphWidget.plot([0], [1], pen=pen)
        self.updateGraph()

        # Background and scrolling
        self.graphWidget.setBackground('w')
        self.graphWidget.setMouseEnabled(x=True, y=False)

        # Range/Domain and gridlines
        self.graphWidget.setXRange(0, 24, padding=0)
        self.graphWidget.setYRange(0, 100, padding=0)
        self.graphWidget.showGrid(x=True, y=True)
        self.graphWidget.setLimits(xMin=0, xMax=7*24)

        # Day Separators
        pen = pg.mkPen(color=(0, 0, 0), width=3)
        for day in range(8):
            self.graphWidget.plot([day * 24, day * 24], [0, 100], pen=pen)


        # X-axis Labels
        xLabels = ["{0}{1}".format((i - 1) % 12 + 1, "pm" if i >= 12 else "am") for i in range(24)]
        xLabels = 7 * xLabels
        xLabels = dict(enumerate(xLabels))
        xax = self.graphWidget.getAxis('bottom')
        xax.setTicks([list(xLabels.items())[::3]])
        self.graphWidget.setAxisItems(axisItems = {'bottom': xax})

    def updateGraph(self):
        # Updates line to current/new data
        x = self.trayIcon.x
        y = self.trayIcon.temps
        self.line.setData(x, y)

    # https://clay-atlas.com/us/blog/2021/03/04/pyqt5-cn-hide-title-bar-move-interface/
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.moveFlag = True
            self.movePosition = event.globalPos() - self.pos()
            self.setCursor(QCursor(QtCore.Qt.OpenHandCursor))
            event.accept()

    def mouseMoveEvent(self, event):
        if QtCore.Qt.LeftButton and self.moveFlag:
            self.move(event.globalPos() - self.movePosition)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.moveFlag = False
        self.setCursor(QtCore.Qt.ArrowCursor)

    def mouse_clicked(self, mouseClickEvent):
        # mouseClickEvent is a pyqtgraph.GraphicsScene.mouseEvents.MouseClickEvent

        # Modified from https://stackoverflow.com/a/68183325
        pos = mouseClickEvent.scenePos()
        if self.graphWidget.sceneBoundingRect().contains(pos):
            mousePoint = self.graphWidget.plotItem.vb.mapSceneToView(pos)
            x = float("{0:.3f}".format(mousePoint.x()))
            y = float("{0:.3f}".format(mousePoint.y()))
            self.makeClickTemp(x)

    def closeEvent(self, event):
        self.hide()
        event.ignore() # just minimize the window to the tray
        # event.accept() # let the program close
