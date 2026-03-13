import time
import subprocess
import sys
from datetime import datetime

def run_engine():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Otomatik tarama başlatılıyor...")
    try:
        # Ana motoru çalıştırıyoruz
        result = subprocess.run([sys.executable, "categorize_engine.py"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Tarama başarıyla tamamlandı.")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Hata oluştu: {result.stderr}")
    except Exception as e:
        print(f"❌ Sistem hatası: {e}")

def main():
    # İlk çalıştırma
    run_engine()
    
    # 10 dakikada bir çalıştır (Saniyeye çeviriyoruz: 10 * 60)
    # AI maliyeti sıfırlandığı için daha sık çekim yapabiliriz.
    INTERVAL = 10 * 60 
    
    print(f"🤖 Otomasyon devrede. Her {INTERVAL/60} dakikada bir yeni tweetler toplanacak.")
    print("Durdurmak için: CTRL+C")
    
    while True:
        time.sleep(INTERVAL)
        run_engine()

if __name__ == "__main__":
    main()
