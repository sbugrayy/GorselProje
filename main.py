import sys
import serial
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QLabel, QComboBox, QPushButton, QTextEdit,
                           QFrame, QStyleFactory)
from PyQt5.QtCore import QTimer, Qt, QTime
from PyQt5.QtGui import QFont, QPalette, QColor

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
        
        # Ana widget ve layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setSpacing(20)
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        # Başlık
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
        
        # Port seçimi için üst kısım
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
        
        # Sıcaklık kartı
        self.sicaklik_label = ModernLabel("🌡️ Sıcaklık\n-- °C")
        self.sicaklik_label.setFont(QFont("Arial", 16))
        
        # Basınç kartı
        self.basinc_label = ModernLabel("🔵 Basınç\n-- hPa")
        self.basinc_label.setFont(QFont("Arial", 16))
        
        # Yükseklik kartı
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
        
        # Buton bağlantıları
        self.refresh_button.clicked.connect(self.portlari_yenile)
        self.connect_button.clicked.connect(self.port_baglan)
        
        # İlk port taraması
        self.portlari_yenile()
    
    def debug_log(self, message):
        """Debug mesajlarını göster"""
        self.debug_text.append(f"[{QTime.currentTime().toString('hh:mm:ss')}] {message}")
        self.debug_text.verticalScrollBar().setValue(
            self.debug_text.verticalScrollBar().maximum()
        )
    
    def portlari_yenile(self):
        """Mevcut seri portları tara ve combo box'a ekle"""
        import serial.tools.list_ports
        
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(port.device)
            self.debug_log(f"Port bulundu: {port.device}")
    
    def port_baglan(self):
        """Seçili porta bağlan veya bağlantıyı kes"""
        if self.serial_port is None:  # Bağlı değilse
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
                self.timer.start(1000)  # Her saniye veri oku
                self.debug_log(f"Port {port} bağlantısı başarılı")
            except Exception as e:
                self.debug_log(f"Bağlantı hatası: {str(e)}")
        else:  # Bağlıysa
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
        """Seri porttan veri oku ve ekrana yazdır"""
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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    window = YerIstasyonu()
    window.show()
    sys.exit(app.exec_()) 