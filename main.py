import tweepy
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
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
    # iPhone Boyutları
    options.add_argument("--window-size=375,812")
    options.add_argument("user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def run():
    # DOSYA GARANTİSİ: Hata alsa bile dosya var olsun.
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("KURULUM")

    driver = setup_driver()
    try:
        print("🌍 Siteye giriliyor...")
        driver.get(SITE_URL)
        time.sleep(8) # Sitenin iyice yüklenmesini bekle

        # --- YENİ STRATEJİ: NE OLURSA OLSUN TIKLA ---
        # Sayfadaki tüm tıklanabilir öğeleri al (a tag'leri ve div'ler)
        # İçinde en az 10 harf olan ilk öğeyi bul ve tıkla.
        try:
            elements = driver.find_elements(By.XPATH, "//*[string-length(text()) > 15]")
            
            target_element = None
            for elem in elements:
                # Görünür ve tıklanabilir olan ilkini seç
                if elem.is_displayed():
                    target_element = elem
                    break
            
            if target_element:
                news_text = target_element.text.strip().replace("\n", " ")
                print(f"Buldum ve Tıklıyorum: {news_text}")
                
                # TIKLA
                driver.execute_script("arguments[0].click();", target_element)
                time.sleep(5) # Popup açılma süresi
            else:
                print("❌ Tıklanacak uygun bir haber bulunamadı. Ekran görüntüsü alınıyor.")

        except Exception as e:
            print(f"❌ Tıklama hatası: {e}")

        # Ekran Görüntüsü Al (Açılmışsa popup, açılmamışsa ana sayfa çıkar)
        driver.save_screenshot(IMAGE_FILE)
        print("📸 Fotoğraf çekildi.")

        # Twitter'a Gönder
        try:
            auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
            api = tweepy.API(auth)
            client = tweepy.Client(consumer_key=API_KEY, consumer_secret=API_SECRET, 
                                   access_token=ACCESS_TOKEN, access_token_secret=ACCESS_SECRET)

            media = api.media_upload(filename=IMAGE_FILE)
            
            # Başlık bulunamadıysa standart metin yaz
            if 'news_text' not in locals():
                news_text = "Gündem Özeti"

            tweet_text = f"🚨 {news_text}\n\n🔗 teletekst.tr"
            client.create_tweet(text=tweet_text, media_ids=[media.media_id])
            print("🚀 Tweet gönderildi!")
            
            # Başarılıysa dosyaya yaz
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.write(news_text)

        except Exception as tw_error:
            print(f"❌ Twitter Hatası: {tw_error}")

    except Exception as e:
        print(f"❌ Genel Hata: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
