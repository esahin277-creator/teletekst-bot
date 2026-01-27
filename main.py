import tweepy
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- AYARLAR ---
SITE_URL = "https://teletekst.tr/"
LOG_FILE = "last_news.txt"
IMAGE_FILE = "haber.png"

# --- TWITTER TOKENLERİ ---
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # TELEFON GÖRÜNÜMÜ (iPhone X Boyutları)
    # Bu sayede ekran görüntüsü senin attığın örnek gibi dik olacak.
    options.add_argument("--window-size=375,812")
    options.add_argument("user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def run():
    # 1. Kayıt dosyasını kontrol et (Hata vermemesi için)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("KURULUM")

    driver = setup_driver()
    try:
        print("🌍 Siteye mobil modda giriliyor...")
        driver.get(SITE_URL)
        time.sleep(5) # Sitenin yüklenmesi için bekle

        # 2. İlk haberi bul ve Başlığını Al
        # Site yapısını bilmediğimiz için sayfadaki tıklanabilir ilk mantıklı metni buluyoruz.
        # Genellikle en üstteki haber, ana container içindeki ilk div/a olur.
        try:
            # Sayfanın ortasındaki haber akışını bulmaya çalışır
            news_items = driver.find_elements(By.TAG_NAME, "h3") # Başlıklar genelde h3 olur
            if not news_items:
                news_items = driver.find_elements(By.XPATH, "//div[string-length(text()) > 20]") # Uzun metinli divler
            
            if not news_items:
                print("❌ Haber listesi bulunamadı.")
                return

            first_news = news_items[0]
            news_title = first_news.text.strip().replace("\n", " ")
            print(f"🔍 Bulunan Haber: {news_title}")

        except Exception as e:
            print(f"❌ Haber bulma hatası: {e}")
            return

        # 3. Eski haber mi kontrol et
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            last_shared = f.read().strip()

        if news_title == last_shared:
            print("✅ Bu haber zaten paylaşılmış. Çıkılıyor.")
            return

        # 4. Habere Tıkla ve Popup Açılmasını Bekle
        print("point: Habere tıklanıyor...")
        driver.execute_script("arguments[0].click();", first_news)
        
        time.sleep(3) # Animasyon beklemesi

        # 5. Ekran Görüntüsü Al (Tüm Ekran)
        driver.save_screenshot(IMAGE_FILE)
        print("📸 Ekran görüntüsü alındı.")

        # 6. Twitter'a Gönder
        auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
        api = tweepy.API(auth)
        client = tweepy.Client(consumer_key=API_KEY, consumer_secret=API_SECRET, 
                               access_token=ACCESS_TOKEN, access_token_secret=ACCESS_SECRET)

        media = api.media_upload(filename=IMAGE_FILE)
        
        # Tweet metni (Sadece başlık ve site linki)
        tweet_text = f"🚨 {news_title}\n\n🔗 teletekst.tr"
        
        client.create_tweet(text=tweet_text, media_ids=[media.media_id])
        print("🚀 Tweet gönderildi!")

        # 7. Kayıt Dosyasını Güncelle
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(news_title)

    except Exception as e:
        print(f"❌ Genel Hata: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
