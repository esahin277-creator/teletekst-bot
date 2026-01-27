import tweepy
import feedparser
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# --- AYARLAR ---
RSS_URL = "https://teletekst.tr/feed"
LOG_FILE = "last_news.txt"
IMAGE_FILE = "haber.png"

# --- SEO VE HASHTAG LİSTESİ ---
HASHTAGS = (
    "#SonDakika #Haber #Gundem #Turkiye #Dunya #Siyaset "
    "#Ekonomi #Analiz #Strateji #DisPolitika #FlashHaber "
    "#Guncel #Teletekst #News #BreakingNews #Journalism"
)

# --- GÜVENLİK (SECRETS) ---
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
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def get_screenshot(url, filename):
    driver = setup_driver()
    try:
        print(f"🌍 Siteye gidiliyor: {url}")
        driver.get(url)
        time.sleep(12) 
        driver.save_screenshot(filename)
        print("📸 Ekran görüntüsü alındı.")
    except Exception as e:
        print(f"❌ Screenshot hatası: {e}")
    finally:
        driver.quit()

def run():
    print("📡 RSS taranıyor...")
    f = feedparser.parse(RSS_URL)
    
    if not f.entries:
        print("⚠️ RSS boş.")
        return

    entry = f.entries[0]
    link = entry.link
    title = entry.title.upper()

    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as file:
                if file.read().strip() == link:
                    print("✅ Haber zaten paylaşılmış.")
                    return
        except:
            pass 

    print(f"🆕 Yeni Haber: {title}")
    get_screenshot(link, IMAGE_FILE)

    if not os.path.exists(IMAGE_FILE):
        print("❌ Resim yok.")
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
