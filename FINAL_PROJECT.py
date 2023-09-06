#!/usr/bin/python2

import telepot
from ubidots import ApiClient
import time
import sys
import smbus
from RPLCD.i2c import CharLCD

EMULATE_HX711 = False

referenceUnit = 1

if not EMULATE_HX711:
    import RPi.GPIO as GPIO
    from hx711 import HX711
    GPIO.setmode(GPIO.BCM)
else:
    from emulated_hx711 import HX711

def cleanAndExit():
    if not EMULATE_HX711:
        GPIO.cleanup()
    sys.exit()
    
GPIO.setwarnings(False)
hx = HX711(6, 5)

hx.set_reading_format("MSB", "MSB")

hx.set_reference_unit(-5033.46022727273)
hx.reset()

hx.tare()

# Inisialisasi berat sebelumnya
berat_sebelumnya_gram = 0

# Token Bot Telegram
TOKEN = '6482290126:AAH4EisKGvZyb1xy4qtZ8hn0-yU6HZzx-OA'
bot = telepot.Bot(TOKEN)

# Token akses API Ubidots
UBIDOTS_TOKEN = 'BBFF-LniFHzVPf3BhKJFPS9wpBP2ybWwony'
api = ApiClient(token=UBIDOTS_TOKEN)

# ID variabel Ubidots untuk data berat
UBIDOTS_VARIABLE_ID = '64d7413030002d00104e21ca'

# Fungsi untuk mengirim pesan ke Telegram
def send_telegram_message(message):
    bot.sendMessage('6665684294', message)

# Inisialisasi I2C
i2c = smbus.SMBus(1)  

# Inisialisasi LCD 1602
lcd = CharLCD(i2c_expander='PCF8574', address=0x27, cols=16, rows=2)

# Fungsi untuk menampilkan pesan di LCD
def show_lcd_message(message, row):
    lcd.cursor_pos = (row, 0)
    lcd.write_string(message.ljust(16))

while True:
    try:
        # Baca berat dari HX711 dalam gram
        val = max(0, int(hx.get_weight(5)))
        berat_total_gram = abs(val) * 10

        # Menghitung berat total barang dalam kilogram
        berat_total_kg = berat_total_gram / 1000

        if abs(berat_total_gram - berat_sebelumnya_gram) >= 201:
            # Muncul pesan hanya jika perbedaan berat >= 201 gram
            jumlah_barang = int(berat_total_gram / 450)
            message = f"Berat barang : {berat_total_kg:.2f} kg \nJumlah barang: {jumlah_barang:.0f}"
            print(message)

            # Kirim pesan ke Telegram
            send_telegram_message(message)
            # Tampilkan pesan di LCD pada baris pertama
            show_lcd_message(message, row=0)

            # Update berat sebelumnya
            berat_sebelumnya_gram = berat_total_gram

        elif berat_total_gram <= 0 or (0 < berat_total_gram <= 200):
            # Kirim pesan jika barang keseluruhan kurang dari atau sama dengan 200 gram
            print("Barang Kosong")
            send_telegram_message(" Barang Kosong ")
            lcd.clear()
            # Tampilkan pesan di LCD pada baris pertama
            show_lcd_message("Barang Kosong", row=0)

        elif berat_total_gram > 5000:
            # Muncul pesan jika berat barang keseluruhan lebih dari 5000 g
            print("Berat barang melebihi kapasitas alat")
            send_telegram_message("Berat barang melebihi kapasitas alat")
            # Tampilkan pesan di LCD pada baris pertama
            
            show_lcd_message("Berat melebihi kapasitas", row=0)
    
            hx.power_down()
            hx.power_up()

    except (KeyboardInterrupt, SystemExit):
        cleanAndExit()
