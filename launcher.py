import sys
import os
import json
import subprocess
import psutil
from PyQt6.QtCore import QObject, pyqtSlot, QUrl, Qt, QTimer
from PyQt6.QtWidgets import QApplication, QMainWindow, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction, QPixmap, QColor
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
import ctypes

class Bridge(QObject):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.track_title = "AGUARDANDO MÍDIA..."
        self.track_artist = "SYSTEM_STANDBY"
        
        # Timer para consultar a mídia do Windows a cada 2 segundos em background
        self.media_timer = QTimer()
        self.media_timer.timeout.connect(self.fetch_windows_media)
        self.media_timer.start(2000)

    def fetch_windows_media(self):
        try:
            # Script PowerShell nativo para extrair a sessão de mídia ativa do Windows
            ps_script = """
            Add-Type -AssemblyName Windows.Foundation
            [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager, Windows.Media.Control, ContentType=WindowsRuntime] | Out-Null
            $sessionManager = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager]::RequestAsync().GetAwaiter().GetResult()
            $session =$sessionManager.GetCurrentSession()
            if ($session) {
                $props =$session.TryGetMediaPropertiesAsync().GetAwaiter().GetResult()
                [PSCustomObject]@{
                    Title = $props.Title
                    Artist = $props.Artist
                } | ConvertTo-Json
            }
            """
            # Configuração de STARTUPINFO para rodar em segundo plano sem janela nem piscar de terminal
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 0  # SW_HIDE

            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script], 
                capture_output=True, text=True, timeout=1,
                startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.stdout.strip():
                data = json.loads(result.stdout)
                if data.get("Title"):
                    self.track_title = data.get("Title")
                    self.track_artist = data.get("Artist") if data.get("Artist") else "STREAMING"
                    return
        except Exception:
            pass
        
        # Fallback por varredura limpa de processos
        try:
            for proc in psutil.process_iter(['name', 'title']):
                pinfo = proc.info
                name = (pinfo.get('name') or '').lower()
                p_title = pinfo.get('title') or ''
                if p_title and any(target in name for target in ['spotify', 'chrome', 'brave', 'firefox']):
                    if " - " in p_title and not any(ign in p_title for ign in ["Visual Studio", "Google"]):
                        parts = p_title.split(" - ")
                        self.track_title = parts[0].strip()
                        self.track_artist = parts[1].replace(" - YouTube Music", "").replace(" - Spotify", "").strip()
                        return
        except Exception:
            pass

        self.track_title = "AGUARDANDO MÍDIA..."
        self.track_artist = "SYSTEM_STANDBY"

    @pyqtSlot(result=str)
    def getSystemStats(self):
        try:
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent
            data = {
                "cpu": cpu,
                "ram": ram,
                "title": self.track_title,
                "artist": self.track_artist
            }
            return json.dumps(data)
        except Exception:
            return json.dumps({"cpu": 0, "ram": 0, "title": "AGUARDANDO MÍDIA...", "artist": "SYSTEM_STANDBY"})

    @pyqtSlot(result=str)
    def getImagesList(self):
        try:
            images_dir = os.path.join(os.path.dirname(__file__), 'images')
            if os.path.exists(images_dir):
                files = [f"images/{f}" for f in os.listdir(images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif'))]
                return json.dumps(files)
        except Exception:
            pass
        return json.dumps([])

    @pyqtSlot()
    def nextImage(self):
        self.main_window.web_view.page().runJavaScript("if (window.forceNextImage) window.forceNextImage();")

class WallpaperWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnBottomHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)

        self.web_view = QWebEngineView(self)
        self.setCentralWidget(self.web_view)

        self.channel = QWebChannel()
        self.bridge = Bridge(self)
        self.channel.registerObject("bridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)

        html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'index.html'))
        self.web_view.setUrl(QUrl.fromLocalFile(html_path))

        # Acoplamento na camada de fundo real do desktop (WorkerW)
        try:
            hwnd = int(self.winId())
            user32 = ctypes.windll.user32
            progman = user32.FindWindowW("Progman", None)
            user32.SendMessageTimeoutW(progman, 0x052C, 0, 0, 0, 1000, None)
            
            def enum_windows_callback(top_hwnd, extra):
                p_fenestra = user32.FindWindowExW(top_hwnd, 0, "SHELLDLL_DefView", None)
                if p_fenestra != 0:
                    workerw = user32.FindWindowExW(0, top_hwnd, "WorkerW", None)
                    if workerw != 0:
                        user32.SetParent(hwnd, workerw)
                        return False
                return True
            
            from ctypes import WINFUNCTYPE, c_bool, c_int
            CMPFUNC = WINFUNCTYPE(c_bool, c_int, c_int)
            user32.EnumWindows(CMPFUNC(enum_windows_callback), 0)
        except Exception:
            pass

        self.tray_icon = QSystemTrayIcon(self)
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(255, 0, 60))
        self.tray_icon.setIcon(QIcon(pixmap))

        tray_menu = QMenu()
        next_action = QAction("Próxima Imagem ➔", self)
        next_action.triggered.connect(self.bridge.nextImage)
        tray_menu.addAction(next_action)
        
        tray_menu.addSeparator()

        exit_action = QAction("Fechar Wallpaper", self)
        exit_action.triggered.connect(app.quit)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            app.quit()
        else:
            super().keyPressEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = WallpaperWindow()
    window.show()
    sys.exit(app.exec())