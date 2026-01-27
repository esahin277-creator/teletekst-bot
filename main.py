import tweepy
import feedparser
import time
import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# --- AYARLAR ---
RSS_URL = "https://teletekst.tr/feed"
LOG_FILE = "last_news.txt"
IMAGE_FILE = "haber.png"

HASHTAGS = (
    "#SonDakika #Haber #Gundem #Turkiye #Dunya #Siyaset "
    "#Ekonomi #Analiz #Strateji #DisPolitika #FlashHaber "
    "#Guncel #Teletekst #News #BreakingNews #Journalism"
)

API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    # User-Agent ekle (Engeli asmak icin)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def get_screenshot(url, filename):
    driver = setup_driver()
    try:
        print(f"🌍 Siteye gidiliyor: {url}")
        driver.get(url)
        time.sleep(10) 
        driver.save_screenshot(filename)
        print("📸 Ekran görüntüsü alındı.")
    except Exception as e:
        print(f"❌ Screenshot hatası: {e}")
    finally:
        driver.quit()

def run():
    print("📡 RSS taranıyor...")
    # --- KRİTİK DÜZELTME: User-Agent Eklendi ---
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(RSS_URL, headers=headers, timeout=10)
        f = feedparser.parse(response.content)
    except Exception as e:
        print(f"⚠️ RSS çekme hatası: {e}")
        return

    if not f.entries:
        print("⚠️ RSS hala boş veya yapı bozuk.")
        return

    entry = f.entries[0]
    link = entry.link
    title = entry.title.upper()

    # Log dosyasını oluştur (Yoksa hata vermesin)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as file:
            file.write("ILK_KURULUM")

    with open(LOG_FILE, "r", encoding="utf-8") as file:
        if file.read().strip() == link:
            print("✅ Haber zaten paylaşılmış.")
            return

    print(f"🆕 Yeni Haber: {title}")
    get_screenshot(link, IMAGE_FILE)

    if not os.path.exists(IMAGE_FILE):
        print("❌ Resim oluşturulamadı.")
        return

    try:
        auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
        api = tweepy.API(auth)
        client = tweepy.Client(consumer_key=API_KEY, consumer_secret=API_SECRET, 
                               access_token=ACCESS_TOKEN, access_token_secret=ACCESS_SECRET)

        media = api.media_upload(filename=IMAGE_FILE)
        tweet_text = f"🚨 {title}\n\n🔗 Detaylar: teletekst.tr\n\n{HASHTAGS}"
        
        client.create_tweet(text=tweet_text, media_ids=[media.media_id])
        print("🚀 Tweet atıldı!")

        with open(LOG_FILE, "w", encoding="utf-8") as file:
            file.write(link)
            
    except Exception as e:
        print(f"❌ Twitter hatası: {e}")

if __name__ == "__main__":
    run()
