import sys
import serial
import serial.tools.list_ports
import json
import sqlite3
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QLabel, QComboBox, QPushButton, QTextEdit,
                           QFrame, QStyleFactory, QStackedWidget, QLineEdit,
                           QCheckBox, QMessageBox, QListWidget, QListWidgetItem)
from PyQt5.QtCore import QTimer, Qt, QTime, QPropertyAnimation, QEasingCurve, QPoint, QRect
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon
from PyQt5.uic import loadUi
from functools import partial

# Veritabanı bağlantısı ve tablo oluşturma
def create_database():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, remember_me INTEGER)''')
    conn.commit()
    conn.close()

# Veritabanını oluştur
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

class YerIstasyonu(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.start_timer()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Başlık
        title_widget = QWidget()
        title_layout = QHBoxLayout(title_widget)
        
        icon_label = QLabel("🌡️")
        icon_label.setStyleSheet("""
            QLabel {
                font-size: 48px;
                background: transparent;
            }
        """)
        
        title_label = QLabel("BMP280 Sensör Verileri")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                background: transparent;
            }
        """)
        
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # Port seçimi
        port_widget = QWidget()
        port_layout = QHBoxLayout(port_widget)
        
        port_label = QLabel("Port:")
        port_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                background: transparent;
            }
        """)
        
        self.port_combo = QComboBox()
        self.port_combo.setStyleSheet("""
            QComboBox {
                background: #34495E;
                border: 2px solid #2C3E50;
                border-radius: 5px;
                padding: 5px;
                color: white;
                min-width: 150px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }
            QComboBox:hover {
                background: #2C3E50;
            }
        """)
        
        self.connect_btn = QPushButton("Bağlan")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background: #2ECC71;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #27AE60;
            }
            QPushButton:pressed {
                background: #219A52;
            }
        """)
        
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_combo)
        port_layout.addWidget(self.connect_btn)
        port_layout.addStretch()
        
        # Sensör verileri
        data_widget = QWidget()
        data_layout = QHBoxLayout(data_widget)
        data_layout.setSpacing(20)
        
        # Sıcaklık kartı
        temp_card = self.create_data_card("🌡️", "Sıcaklık", "°C")
        self.temp_value = temp_card.findChild(QLabel, "value_label")
        
        # Basınç kartı
        pressure_card = self.create_data_card("📊", "Basınç", "hPa")
        self.pressure_value = pressure_card.findChild(QLabel, "value_label")
        
        # Yükseklik kartı
        altitude_card = self.create_data_card("🗻", "Yükseklik", "m")
        self.altitude_value = altitude_card.findChild(QLabel, "value_label")
        
        data_layout.addWidget(temp_card)
        data_layout.addWidget(pressure_card)
        data_layout.addWidget(altitude_card)
        
        # Log alanı
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background: #2C3E50;
                border: none;
                border-radius: 10px;
                padding: 10px;
                color: #ECF0F1;
                font-family: 'Consolas', monospace;
            }
        """)
        
        # Layout'a widget'ları ekle
        layout.addWidget(title_widget)
        layout.addWidget(port_widget)
        layout.addWidget(data_widget)
        layout.addWidget(self.log_text)
        
        # Arka plan
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1: 0, y1: 0,
                    x2: 1, y2: 1,
                    stop: 0 #2C3E50,
                    stop: 1 #34495E
                );
            }
        """)
        
        # Bağlantılar
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.update_ports()
    
    def create_data_card(self, icon, title, unit):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: rgba(44, 62, 80, 0.7);
                border-radius: 15px;
                padding: 20px;
            }
            QFrame:hover {
                background: rgba(44, 62, 80, 0.9);
            }
        """)
        
        layout = QVBoxLayout(card)
        
        # İkon ve başlık
        header = QWidget()
        header_layout = QHBoxLayout(header)
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px;")
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            color: #BDC3C7;
            font-size: 16px;
        """)
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Değer
        value_widget = QWidget()
        value_layout = QHBoxLayout(value_widget)
        
        value_label = QLabel("0.00")
        value_label.setObjectName("value_label")
        value_label.setStyleSheet("""
            color: white;
            font-size: 32px;
            font-weight: bold;
        """)
        
        unit_label = QLabel(unit)
        unit_label.setStyleSheet("""
            color: #BDC3C7;
            font-size: 16px;
        """)
        
        value_layout.addWidget(value_label)
        value_layout.addWidget(unit_label)
        value_layout.addStretch()
        
        layout.addWidget(header)
        layout.addWidget(value_widget)
        
        return card
    
    def update_ports(self):
        self.port_combo.clear()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo.addItems(ports)
    
    def toggle_connection(self):
        if self.connect_btn.text() == "Bağlan":
            try:
                port = self.port_combo.currentText()
                self.serial = serial.Serial(port, 9600)
                self.connect_btn.setText("Bağlantıyı Kes")
                self.connect_btn.setStyleSheet("""
                    QPushButton {
                        background: #E74C3C;
                        border: none;
                        border-radius: 5px;
                        padding: 8px 15px;
                        color: white;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background: #C0392B;
                    }
                    QPushButton:pressed {
                        background: #A93226;
                    }
                """)
                self.log_text.append(f"[{QTime.currentTime().toString('HH:mm:ss')}] {port} portuna bağlantı başarılı!")
            except:
                QMessageBox.warning(self, "Hata", "Bağlantı kurulamadı!")
        else:
            self.serial.close()
            self.connect_btn.setText("Bağlan")
            self.connect_btn.setStyleSheet("""
                QPushButton {
                    background: #2ECC71;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 15px;
                    color: white;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #27AE60;
                }
                QPushButton:pressed {
                    background: #219A52;
                }
            """)
            self.log_text.append(f"[{QTime.currentTime().toString('HH:mm:ss')}] Bağlantı kesildi!")
    
    def start_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)  # Her saniye güncelle
    
    def update_data(self):
        if hasattr(self, 'serial') and self.serial.is_open:
            try:
                if self.serial.in_waiting:
                    data = self.serial.readline().decode().strip()
                    temp, pressure, altitude = map(float, data.split(','))
                    
                    self.temp_value.setText(f"{temp:.2f}")
                    self.pressure_value.setText(f"{pressure:.2f}")
                    self.altitude_value.setText(f"{altitude:.2f}")
                    
                    self.log_text.append(f"[{QTime.currentTime().toString('HH:mm:ss')}] Sıcaklık: {temp:.2f}°C, Basınç: {pressure:.2f}hPa, Yükseklik: {altitude:.2f}m")
            except:
                pass

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        loadUi('login.ui', self)
        
        # Şeffaflık efekti için
        self.setWindowOpacity(0.0)
        
        # Giriş butonu bağlantısı
        self.login_btn.clicked.connect(self.login)
        
        # Fade-in animasyonu
        fade_in = QPropertyAnimation(self, b"windowOpacity")
        fade_in.setDuration(500)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.start()
    
    def login(self):
        username = self.username.text()
        password = self.password.text()
        remember = self.remember_me.isChecked()
        
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        
        if user:
            if remember:
                c.execute("UPDATE users SET remember_me=1 WHERE username=?", (username,))
                conn.commit()
            
            # Fade-out animasyonu
            fade_out = QPropertyAnimation(self, b"windowOpacity")
            fade_out.setDuration(500)
            fade_out.setStartValue(1.0)
            fade_out.setEndValue(0.0)
            fade_out.finished.connect(self._handle_successful_login)
            fade_out.start()
        else:
            QMessageBox.warning(self, "Hata", "Kullanıcı adı veya şifre hatalı!")
        
        conn.close()
    
    def _handle_successful_login(self):
        # Ana pencereyi aç
        self.main_window = MainWindow()
        self.main_window.show()
        
        # Ana pencere için fade-in animasyonu
        fade_in = QPropertyAnimation(self.main_window, b"windowOpacity")
        fade_in.setDuration(500)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.start()
        
        self.close()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi('main.ui', self)
        
        # Menü öğelerini ekle
        menu_items = [
            ("BMP280", "🌡️", "Sıcaklık, Basınç ve Yükseklik Sensörü"),
            ("BNO055", "🔄", "9 Eksenli IMU Sensörü"),
            ("NEO-M8N", "📍", "GPS Modülü"),
            ("Strain Gage", "📊", "Gerilme Ölçer"),
            ("Grafikler", "📈", "Sensör Verileri Grafikleri")
        ]
        
        for name, icon, description in menu_items:
            item = QListWidgetItem(f"{icon} {name}")
            item.setToolTip(description)  # Fare üzerine gelince açıklama göster
            self.side_menu.addItem(item)
        
        # BMP280 sayfasını ekle
        self.bmp280_widget = YerIstasyonu()
        self.content_stack.addWidget(self.bmp280_widget)
        
        # Diğer sensör sayfalarını ekle
        for i in range(4):
            temp_widget = QWidget()
            temp_layout = QVBoxLayout(temp_widget)
            temp_layout.setContentsMargins(20, 20, 20, 20)
            temp_layout.setSpacing(20)
            
            # İkon ve başlık
            header_widget = QWidget()
            header_layout = QHBoxLayout(header_widget)
            header_layout.setAlignment(Qt.AlignCenter)
            
            icons = ["🔄", "📍", "📊", "📈"]
            titles = ["BNO055 Sensörü", "NEO-M8N GPS", "Strain Gage", "Sensör Grafikleri"]
            descriptions = [
                "9 Eksenli IMU sensörü için geliştirme çalışmaları devam etmektedir.",
                "GPS modülü için geliştirme çalışmaları devam etmektedir.",
                "Gerilme ölçer için geliştirme çalışmaları devam etmektedir.",
                "Sensör grafikleri için geliştirme çalışmaları devam etmektedir."
            ]
            
            icon_label = QLabel(icons[i])
            icon_label.setStyleSheet("""
                QLabel {
                    font-size: 64px;
                    background: transparent;
                }
            """)
            
            title_label = QLabel(titles[i])
            title_label.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 32px;
                    font-weight: bold;
                    background: transparent;
                }
            """)
            
            header_layout.addWidget(icon_label)
            header_layout.addWidget(title_label)
            
            # Açıklama
            description_label = QLabel(descriptions[i])
            description_label.setStyleSheet("""
                QLabel {
                    color: #BDC3C7;
                    font-size: 18px;
                    background: transparent;
                }
            """)
            description_label.setWordWrap(True)
            description_label.setAlignment(Qt.AlignCenter)
            
            # Geliştiriliyor etiketi
            dev_widget = QWidget()
            dev_layout = QHBoxLayout(dev_widget)
            dev_layout.setAlignment(Qt.AlignCenter)
            
            dev_icon = QLabel("👨‍💻")
            dev_icon.setStyleSheet("font-size: 48px; background: transparent;")
            
            dev_label = QLabel("Geliştirme Aşamasında")
            dev_label.setStyleSheet("""
                QLabel {
                    color: #E74C3C;
                    font-size: 24px;
                    font-weight: bold;
                    background: transparent;
                }
            """)
            
            dev_layout.addWidget(dev_icon)
            dev_layout.addWidget(dev_label)
            
            # Layout'a widget'ları ekle
            temp_layout.addWidget(header_widget)
            temp_layout.addWidget(description_label)
            temp_layout.addWidget(dev_widget)
            temp_layout.addStretch()
            
            # Arka plan efekti
            temp_widget.setStyleSheet("""
                QWidget {
                    background: qlineargradient(
                        x1: 0, y1: 0,
                        x2: 1, y2: 1,
                        stop: 0 #2C3E50,
                        stop: 1 #34495E
                    );
                    border-radius: 15px;
                }
            """)
            
            self.content_stack.addWidget(temp_widget)
        
        # Bağlantılar
        self.side_menu.currentRowChanged.connect(self.change_page)
        self.logout_btn.clicked.connect(self.logout)
        
        # Başlangıç sayfası
        self.side_menu.setCurrentRow(0)
    
    def change_page(self, index):
        # Sayfa geçiş animasyonu
        current_widget = self.content_stack.currentWidget()
        next_widget = self.content_stack.widget(index)
        
        if current_widget and next_widget:
            # Geçerli widget'ı sola kaydır
            current_anim = QPropertyAnimation(current_widget, b"geometry")
            current_anim.setDuration(300)
            current_anim.setEasingCurve(QEasingCurve.OutCubic)
            
            start_rect = current_widget.geometry()
            end_rect = QRect(start_rect.x() - start_rect.width(), start_rect.y(),
                           start_rect.width(), start_rect.height())
            
            current_anim.setStartValue(start_rect)
            current_anim.setEndValue(end_rect)
            
            # Yeni widget'ı sağdan getir
            next_widget.setGeometry(QRect(start_rect.x() + start_rect.width(), start_rect.y(),
                                        start_rect.width(), start_rect.height()))
            next_widget.show()
            
            next_anim = QPropertyAnimation(next_widget, b"geometry")
            next_anim.setDuration(300)
            next_anim.setEasingCurve(QEasingCurve.OutCubic)
            
            next_anim.setStartValue(next_widget.geometry())
            next_anim.setEndValue(start_rect)
            
            # Animasyonları başlat
            current_anim.start()
            next_anim.start()
            
            # Animasyon bitince sayfayı değiştir
            next_anim.finished.connect(lambda: self.content_stack.setCurrentIndex(index))
    
    def logout(self):
        # Çıkış animasyonu
        fade_out = QPropertyAnimation(self, b"windowOpacity")
        fade_out.setDuration(500)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.finished.connect(self._handle_logout)
        fade_out.start()
    
    def _handle_logout(self):
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("UPDATE users SET remember_me=0")
        conn.commit()
        conn.close()
        
        # Giriş ekranına dön
        self.login_window = LoginWindow()
        self.login_window.show()
        
        # Giriş ekranı için fade-in animasyonu
        fade_in = QPropertyAnimation(self.login_window, b"windowOpacity")
        fade_in.setDuration(500)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.start()
        
        self.close()

def main():
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    
    # Veritabanı bağlantısı
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    # Kullanıcı tablosunu oluştur
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        remember_me INTEGER DEFAULT 0
    )""")
    
    # Test kullanıcısı ekle
    c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?)", ('admin', 'admin', 0))
    conn.commit()
    
    # Otomatik giriş kontrolü
    c.execute("SELECT username FROM users WHERE remember_me=1")
    remembered_user = c.fetchone()
    
    conn.close()
    
    if remembered_user:
        window = MainWindow()
    else:
        window = LoginWindow()
    
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 