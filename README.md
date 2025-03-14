# Yer İstasyonu Uygulaması

Bu uygulama, BMP280 sensöründen gelen sıcaklık, basınç ve yükseklik verilerini seri port üzerinden okuyup görselleştiren bir PyQt5 arayüzüdür.

## Gereksinimler

- Python 3.x
- PyQt5
- pyserial

## Kurulum

1. Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

2. Uygulamayı çalıştırın:
```bash
python main.py
```

## Kullanım

1. Uygulamayı başlattıktan sonra, üst kısımdaki açılır menüden Arduino'nun bağlı olduğu seri portu seçin.
2. "Bağlan" butonuna tıklayarak veri almaya başlayın.
3. Veriler her saniye güncellenecektir.
4. Bağlantıyı kesmek için "Bağlantıyı Kes" butonuna tıklayın.

## Veri Formatı

Arduino'dan gelen veriler JSON formatında olmalıdır:

```json
{
    "sicaklik": 25.6,
    "basinc": 1013.25,
    "yukseklik": 100.5
}
``` 