import os
import json
import urllib.request
import urllib.parse
import ssl
import xml.etree.ElementTree as ET
import time

API_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6JAqCNNkbKkO6XP4McXoPb-qPAV-FE7rQ7k4acm0hpFlQ")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID", "389234121692228")
FB_ACCESS_TOKEN = os.environ.get("FB_ACCESS_TOKEN", "EAAisSSmHfJkBScjcnICqZAu6rKGhMUONK3auzXIFl3QGC64u64wCVpPZBRKkcyP87qs0VLKqhKBw5Vgq6zfzkUtcNMGhckzTKYiWPWb8cZCGzpQ9UvJmCiw7igKEABX3YLOh7lNiZBNdMVgclTb2BAEUZBVBWrlABfovxwNgwCMmVrRWBuwHJilqEicHTEXVAEEe1j3zy2TB27LqUoCRWrVZBYK4g1ytWYV4gJ8YPvuW8C")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch_rss_news():
    url = "https://news.google.com/rss/search?q=" + urllib.parse.quote("กฎหมาย ตำรวจ คดี ศาล when:1d") + "&hl=th&gl=TH&ceid=TH:th"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, context=ctx) as resp:
        xml_data = resp.read()
    root = ET.fromstring(xml_data)
    items = root.findall('.//item')[:5]
    news = []
    for item in items:
        title = item.find('title').text if item.find('title') is not None else ""
        link = item.find('link').text if item.find('link') is not None else ""
        desc = item.find('description').text if item.find('description') is not None else ""
        news.append({'title': title, 'link': link, 'description': desc})
    return news

def analyze_and_generate(news_item, api_key):
    prompt = f"""คุณคือผู้เชี่ยวชาญด้านกฎหมายไทยและนักเขียนคอนเทนต์กฎหมายสำหรับประชาชน (Legal Educator)

จงวิเคราะห์ข่าวต่อไปนี้:
หัวข้อข่าว: {news_item['title']}
รายละเอียด: {news_item['description']}

ภารกิจของคุณ:
1. พิจารณาว่าข่าวนี้มีประเด็นข้อกฎหมาย สิทธิ มาตรา หรือ พ.ร.บ. ที่น่าสนใจสำหรับประชาชนหรือไม่
2. หากไม่มีประเด็นกฎหมายเลย ให้ตอบกลับสั้นๆ เพียงคำว่า: IS_RELEVANT: FALSE
3. หากมีประเด็นกฎหมาย ให้ตอบกลับโดยเริ่มต้นด้วย IS_RELEVANT: TRUE แล้วตามด้วยข้อความโพสต์ Facebook ในรูปแบบต่อไปนี้:

IS_RELEVANT: TRUE

⚖️ [ชื่อหัวข้อโพสต์ที่ดึงดูดใจและเข้าใจง่าย เกี่ยวกับกฎหมายจากข่าวนี้]

📌 จากเหตุการณ์ในข่าว: [สรุปเหตุการณ์สั้นๆ 2-3 บรรทัด]

💡 ประเด็นกฎหมายที่น่ารู้และต้องระวัง:
• [ข้อกฎหมาย/มาตรา/พ.ร.บ. ที่เกี่ยวข้อง อธิบายภาษาพูดเข้าใจง่าย]
• [สิทธิหน้าที่ หรือบทลงโทษที่ประชาชนควรรู้]
• [แนวทางการรับมือหรือข้อแนะนำตามกฎหมาย]

📣 สรุปสำหรับประชาชน:
[คำแนะนำสั้นๆ 1-2 บรรทัด]

#กฎหมายน่ารู้ #สาระกฎหมาย #ข่าววันนี้ #ความรู้กฎหมาย #กฎหมายใกล้ตัว
⚠️ หมายเหตุ: ข้อความนี้จัดทำขึ้นเพื่อการให้ความรู้ทางกฎหมายเบื้องต้นจากเหตุการณ์ในข่าวเท่านั้น ไม่ใช่คำปรึกษาทางกฎหมายสำหรับคดีความเฉพาะราย"""

    models = ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-flash-latest"]
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode('utf-8')
        req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, context=ctx) as resp:
                    res_data = json.loads(resp.read().decode('utf-8'))
                    text = res_data['candidates'][0]['content']['parts'][0]['text']
                    return text
            except Exception as e:
                time.sleep(2)
    raise Exception("All Gemini models and retry attempts failed.")

def post_to_facebook(message, page_id, access_token):
    url = f"https://graph.facebook.com/v19.0/{page_id}/feed"
    data = urllib.parse.urlencode({'message': message, 'access_token': access_token}).encode('utf-8')
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, context=ctx) as resp:
        return json.loads(resp.read().decode('utf-8'))

def run_pipeline():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ⚖️ Starting Legal News Auto-Post Pipeline...")
    news_items = fetch_rss_news()
    print(f"Fetched {len(news_items)} news items from Google News RSS.")
    
    for item in news_items:
        print(f"\nAnalyzing news: {item['title']}")
        try:
            analysis = analyze_and_generate(item, API_KEY)
            if "IS_RELEVANT: TRUE" in analysis:
                post_content = analysis.replace("IS_RELEVANT: TRUE", "").strip()
                print("✨ Legal content generated successfully!")
                res = post_to_facebook(post_content, FB_PAGE_ID, FB_ACCESS_TOKEN)
                print(f"🎉 Successfully posted to Facebook Page! (Post ID: {res.get('id')})")
                return True
            else:
                print("News item was not relevant to legal topics. Checking next news item...")
        except Exception as e:
            print(f"Error during processing: {e}")
    print("No relevant news found to post in this run.")
    return False

if __name__ == "__main__":
    run_pipeline()
