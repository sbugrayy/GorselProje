import sys
import serial
import json
import sqlite3
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QLabel, QComboBox, QPushButton, QTextEdit,
                           QFrame, QStyleFactory,QMessageBox)
from PyQt5.QtCore import QTimer, Qt, QTime
from PyQt5.QtGui import QFont
from PyQt5.uic import loadUi

# Veritabanı bağlantısı ve tablo oluşturma 
def create_database():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, remember_me INTEGER)''')
    conn.commit()
    conn.close()
create_database()

class ModernLabel(QLabel):
    def __init__(self, text):
        super().__init__(text)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: #2C3E50;
                color: white;
                border-radius: 10px;
                padding: 15px;
                margin: 5px;
            }
        """)

class YerIstasyonu(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yer İstasyonu - BMP280 Sensör Verileri")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #34495E;
            }
            QWidget {
                background-color: #34495E;
                color: white;
            }
            QPushButton {
                background-color: #3498DB;
                border: none;
                color: white;
                padding: 8px 16px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
            QPushButton:pressed {
                background-color: #2574A9;
            }
            QComboBox {
                background-color: #2C3E50;
                border: 2px solid #3498DB;
                border-radius: 5px;
                padding: 8px;
                color: white;
                min-width: 150px;
                font-size: 14px;
            }
            QComboBox:hover {
                border-color: #2980B9;
                background-color: #34495E;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: url(none);
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #3498DB;
                margin-right: 10px;
            }
            QComboBox::down-arrow:hover {
                border-top: 5px solid #2980B9;
            }
            QComboBox QAbstractItemView {
                background-color: #2C3E50;
                border: 2px solid #3498DB;
                border-radius: 5px;
                selection-background-color: #3498DB;
                selection-color: white;
                color: white;
                outline: none;
            }
            QTextEdit {
                background-color: #2C3E50;
                border: none;
                border-radius: 10px;
                padding: 10px;
                color: #BDC3C7;
            }
        """)
        
        # Ana widgetlar ve layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setSpacing(20)
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        # BMP280 Başlık
        self.title_label = QLabel("BMP280 Sensör Verileri")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 20px;
            }
        """)
        self.layout.addWidget(self.title_label)
        
        # Port seçimi için üst layout
        self.port_frame = QFrame()
        self.port_frame.setStyleSheet("""
            QFrame {
                background-color: #2C3E50;
                border-radius: 10px;
                padding: 10px;
            }
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #3498DB;
            }
        """)
        self.port_layout = QHBoxLayout(self.port_frame)
        self.port_layout.setContentsMargins(10, 10, 10, 10)
        self.port_layout.setSpacing(15)
        
        self.port_label = QLabel("📡 Port Seçiniz:")
        self.port_combo = QComboBox()
        self.port_combo.setPlaceholderText("Port Seçin...")
        self.refresh_button = QPushButton("🔄 Yenile")
        self.connect_button = QPushButton("🔌 Bağlan")
        
        self.port_layout.addWidget(self.port_label)
        self.port_layout.addWidget(self.port_combo)
        self.port_layout.addWidget(self.refresh_button)
        self.port_layout.addWidget(self.connect_button)
        
        self.layout.addWidget(self.port_frame)
        
        # Sensör verileri için kartlar
        self.data_layout = QHBoxLayout()
        
        self.sicaklik_label = ModernLabel("🌡️ Sıcaklık\n-- °C")
        self.sicaklik_label.setFont(QFont("Arial", 16))
        
        self.basinc_label = ModernLabel("🔵 Basınç\n-- hPa")
        self.basinc_label.setFont(QFont("Arial", 16))
        
        self.yukseklik_label = ModernLabel("🏔️ Yükseklik\n-- m")
        self.yukseklik_label.setFont(QFont("Arial", 16))
        
        self.data_layout.addWidget(self.sicaklik_label)
        self.data_layout.addWidget(self.basinc_label)
        self.data_layout.addWidget(self.yukseklik_label)
        
        self.layout.addLayout(self.data_layout)
        
        # Debug alanı
        self.debug_text = QTextEdit()
        self.debug_text.setReadOnly(True)
        self.debug_text.setMaximumHeight(150)
        self.debug_text.setPlaceholderText("Debug mesajları burada görünecek...")
        self.layout.addWidget(self.debug_text)
        
        # Serial port ve timer
        self.serial_port = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.veri_oku)
        
        # Butonlar
        self.refresh_button.clicked.connect(self.portlari_yenile)
        self.connect_button.clicked.connect(self.port_baglan)
        
        self.portlari_yenile()
    
    def debug_log(self, message):
        self.debug_text.append(f"[{QTime.currentTime().toString('hh:mm:ss')}] {message}") # şuanki zaman alınır ve ui güncellenir
        self.debug_text.verticalScrollBar().setValue(
            self.debug_text.verticalScrollBar().maximum()
        )
    
    def portlari_yenile(self):
        import serial.tools.list_ports 
        
        self.port_combo.clear() 
        ports = serial.tools.list_ports.comports() # portları tarar
        for port in ports:
            self.port_combo.addItem(port.device) # combo box güncellenir
            self.debug_log(f"Port bulundu: {port.device}")
    
    # seçili porta bağlan veya bağlantıyı kes
    def port_baglan(self):
        if self.serial_port is None:  # bağlı değilse
            try:
                port = self.port_combo.currentText()
                self.serial_port = serial.Serial(port, 9600, timeout=1)
                self.connect_button.setText("🔌 Bağlantıyı Kes")
                self.connect_button.setStyleSheet("""
                    QPushButton {
                        background-color: #E74C3C;
                    }
                    QPushButton:hover {
                        background-color: #C0392B;
                    }
                """)
                self.timer.start(1000)
                self.debug_log(f"Port {port} bağlantısı başarılı")
            except Exception as e:
                self.debug_log(f"Bağlantı hatası: {str(e)}")
        else:  # bağlıysa
            self.timer.stop()
            self.serial_port.close()
            self.serial_port = None
            self.connect_button.setText("🔌 Bağlan")
            self.connect_button.setStyleSheet("")
            self.sicaklik_label.setText("🌡️ Sıcaklık\n-- °C")
            self.basinc_label.setText("🔵 Basınç\n-- hPa")
            self.yukseklik_label.setText("🏔️ Yükseklik\n-- m")
            self.debug_log("Port bağlantısı kesildi")
    

    def veri_oku(self):
        if self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting:
                    veri = self.serial_port.readline().decode().strip()
                    self.debug_log(f"Ham veri: {veri}")
                    try:
                        sensor_data = json.loads(veri)
                        self.sicaklik_label.setText(f"🌡️ Sıcaklık\n{sensor_data['sicaklik']:.1f} °C")
                        self.basinc_label.setText(f"🔵 Basınç\n{sensor_data['basinc']:.1f} hPa")
                        self.yukseklik_label.setText(f"🏔️ Yükseklik\n{sensor_data['yukseklik']:.1f} m")
                    except json.JSONDecodeError as e:
                        self.debug_log(f"JSON çözümleme hatası: {str(e)}")
            except Exception as e:
                self.debug_log(f"Veri okuma hatası: {str(e)}")

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        loadUi('login.ui', self)
        
        # butonlar
        self.login_btn.clicked.connect(self.login)
        self.register_btn.clicked.connect(self.register)
        
        # enter ile giriş 
        self.username.returnPressed.connect(self.login)
        self.password.returnPressed.connect(self.login)
    
    def login(self):
        username = self.username.text()
        password = self.password.text()
        remember = self.remember.isChecked()
        
        if not username or not password:
            QMessageBox.warning(self, "Hata", "Lütfen tüm alanları doldurun!")
            return
            
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        
        if user:
            if remember:
                c.execute("UPDATE users SET remember_me=0")  # önce tümünü sıfırla
                c.execute("UPDATE users SET remember_me=1 WHERE username=?", (username,))
                conn.commit()
            conn.close()
            
            # ana pencere
            self.main_window = MainWindow()
            self.main_window.show()
            self.close()
        else:
            conn.close()
            QMessageBox.warning(self, "Hata", "Kullanıcı adı veya şifre hatalı!")
    
    def register(self):
        username = self.username.text()
        password = self.password.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Hata", "Lütfen tüm alanları doldurun!")
            return
            
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        try:
            c.execute("INSERT INTO users (username, password, remember_me) VALUES (?, ?, 0)", 
                     (username, password))
            conn.commit()
            QMessageBox.information(self, "Başarılı", "Kayıt başarıyla oluşturuldu!")
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Hata", "Bu kullanıcı adı zaten kullanılıyor!")
        finally:
            conn.close()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi('main.ui', self)
        
        # Menü öğeleri
        menu_items = [
            ("BMP280", "🌡️"),
            ("BNO055", "🔄"),
            ("NEO-M8N", "📍"),
            ("Strain Gage", "📊"),
            ("Grafikler", "📈")
        ]
        
        for name, icon in menu_items:
            self.side_menu.addItem(f"{icon} {name}")
        
        # BMP280 sayfası
        self.bmp280_widget = YerIstasyonu()
        self.content_stack.addWidget(self.bmp280_widget)
        
        # diğer sensör sayfaları
        for _ in range(4):
            temp_widget = QWidget()
            temp_layout = QVBoxLayout(temp_widget)
            temp_label = QLabel("Bu özellik yakında eklenecek!")
            temp_label.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 24px;
                    padding: 20px;
                }
            """)
            temp_label.setAlignment(Qt.AlignCenter)
            temp_layout.addWidget(temp_label)
            self.content_stack.addWidget(temp_widget)
        
        # Menü değişikliğini dinle
        self.side_menu.currentRowChanged.connect(self.change_page)
        
        # Çıkış butonunu bağla
        self.logout_btn.clicked.connect(self.logout)
        
        # İlk sayfayı seç
        self.side_menu.setCurrentRow(0)
    
    def change_page(self, index):
        self.content_stack.setCurrentIndex(index)
    
    def logout(self):
        # Veritabanındaki remember_me değerini sıfırla
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("UPDATE users SET remember_me=0")
        conn.commit()
        conn.close()
        
        # Giriş ekranını aç
        self.login_window = LoginWindow()
        self.login_window.show()
        
        # Mevcut pencereyi kapat
        self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    
    # Otomatik giriş kontrolü
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE remember_me=1")
    user = c.fetchone()
    conn.close()
    
    if user:
        window = MainWindow()
    else:
        window = LoginWindow()
    
    window.show()
    sys.exit(app.exec_()) 