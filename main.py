import os
import requests
import tweepy
import random
import io
import time

# 1. Twitter Kimlik Doğrulaması
def get_twitter_conn_v1(api_key, api_secret, access_token, access_secret):
    """Medya yüklemek için v1.1 API bağlantısı"""
    auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
    return tweepy.API(auth)

def get_twitter_conn_v2(api_key, api_secret, access_token, access_secret):
    """Tweet atmak için v2 API bağlantısı"""
    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_secret
    )
    return client

# 2. Chicago Art Institute API'den Veri Çekme
def get_random_artwork():
    base_url = "https://api.artic.edu/api/v1/artworks"
    
    # Rastgelelik sağlamak için 1 ile 1000 arasında rastgele bir sayfa seçiyoruz
    page = random.randint(1, 1000)
    
    params = {
        'page': page,
        'limit': 1,
        'fields': 'id,title,artist_display,date_display,image_id,medium_display'
    }

    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        artwork = data['data'][0]
        
        # Eğer eserin görseli yoksa (image_id null ise), tekrar dene
        if not artwork.get('image_id'):
            print("Görseli olmayan eser geldi, tekrar deneniyor...")
            return get_random_artwork()
            
        return artwork
    except Exception as e:
        print(f"API Hatası: {e}")
        return None

# 3. Görsel İndirme
def download_image(image_id):
    # Chicago API IIIF formatı kullanır. Genişliği 843px olarak ayarlıyoruz.
    image_url = f"https://www.artic.edu/iiif/2/{image_id}/full/843,/0/default.jpg"
    response = requests.get(image_url)
    
    if response.status_code == 200:
        return io.BytesIO(response.content)
    else:
        print("Görsel indirilemedi.")
        return None

# 4. Ana Çalıştırma Fonksiyonu
def main():
    # Secret'ları ortam değişkenlerinden al
    api_key = os.environ.get("API_KEY")
    api_secret = os.environ.get("API_SECRET")
    access_token = os.environ.get("ACCESS_TOKEN")
    access_secret = os.environ.get("ACCESS_SECRET")

    # API'den eser bul
    artwork = get_random_artwork()
    if not artwork:
        print("Eser bulunamadı, işlem iptal.")
        return

    title = artwork.get('title', 'Untitled')
    artist = artwork.get('artist_display', 'Unknown Artist')
    date = artwork.get('date_display', 'Unknown Date')
    
    # Metni hazırla (Gereksiz satırları temizle)
    artist_clean = artist.split('\n')[0] if artist else "Unknown"
    caption = f"{title}\n\n🖌 {artist_clean}\n📅 {date}\n\n#Art #History #ChicagoArtInstitute #DailyArt"

    # Görseli indir
    image_file = download_image(artwork['image_id'])
    if not image_file:
        return

    # Twitter'a yükle ve paylaş
    try:
        # V1 ile görsel yükle
        api_v1 = get_twitter_conn_v1(api_key, api_secret, access_token, access_secret)
        media = api_v1.media_upload(filename="art.jpg", file=image_file)
        
        # V2 ile tweet at
        client_v2 = get_twitter_conn_v2(api_key, api_secret, access_token, access_secret)
        client_v2.create_tweet(text=caption, media_ids=[media.media_id])
        
        print(f"Başarıyla paylaşıldı: {title}")
        
    except Exception as e:
        print(f"Twitter Hatası: {e}")

if __name__ == "__main__":
    main()
