import os
import time
import schedule
from dotenv import load_dotenv
load_dotenv(dotenv_path="/home/pankaj620/Documents/short/.env")
from openai import OpenAI
from elevenlabs import set_api_key, generate, save
from moviepy.editor import *
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import requests

# Load environment variables
load_dotenv()
set_api_key(os.getenv("ELEVENLABS_API_KEY"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ShortsFactory:
    def __init__(self):
        self.trending_topics = [
            "AI news", "Space facts", "Psychology tricks",
            "Business hacks", "History mysteries"
        ]

    def get_trending_topic(self):
        """Rotate through trending topics"""
        return self.trending_topics.pop(0)

    def generate_script(self, topic):
        """GPT-4 Turbo script generation"""
        prompt = f"""Create an ultra-engaging 30-second YouTube Short about {topic} with:
1. Shocking hook
2. 3 fast facts
3. Call-to-action

Use emojis and write for 9th grade level."""
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": "You're a viral content creator with 10M+ YouTube subscribers."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

    def create_voiceover(self, script):
        """ElevenLabs realistic voice"""
        audio = generate(
            text=script,
            voice="Rachel",
            model="eleven_turbo_v2"
        )
        filename = f"voiceover_{int(time.time())}.mp3"
        save(audio, filename)
        return filename

    def get_stock_video(self, query):
        """Free stock footage from Pexels"""
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=1"
        headers = {"Authorization": os.getenv("PEXELS_API_KEY")}
        response = requests.get(url, headers=headers).json()
        video_url = response["videos"][0]["video_files"][0]["link"]
        return requests.get(video_url).content

    def render_video(self, script, audio_path):
        """Auto-edit with dynamic captions"""
        stock_video = self.get_stock_video(script.split()[0])
        with open("temp_video.mp4", "wb") as f:
            f.write(stock_video)

        video_clip = VideoFileClip("temp_video.mp4").subclip(0, 30)

        txt_clip = TextClip(script, fontsize=35, color='white', 
                            font='Arial-Bold', method='caption', size=(720, 1280))

        final = CompositeVideoClip([
            video_clip,
            txt_clip.set_position('center').set_duration(30)
        ])
        final.audio = AudioFileClip(audio_path)

        output_path = f"short_{int(time.time())}.mp4"
        final.write_videofile(output_path, fps=24, codec='libx264')
        os.remove("temp_video.mp4")
        return output_path

    def upload_to_youtube(self, video_path, title, description):
        """Automated YouTube upload"""
        creds = Credentials.from_authorized_user_file(
            os.getenv("YOUTUBE_CLIENT_SECRET"),
            ["https://www.googleapis.com/auth/youtube.upload"]
        )
        youtube = build('youtube', 'v3', credentials=creds)
        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description,
                    "categoryId": "22"
                },
                "status": {
                    "privacyStatus": "public",
                    "selfDeclaredMadeForKids": False
                }
            },
            media_body=MediaFileUpload(video_path)
        )
        response = request.execute()
        return response

    def create_and_upload(self):
        """Full automation pipeline"""
        try:
            topic = self.get_trending_topic()
            script = self.generate_script(topic)
            voiceover = self.create_voiceover(script)
            video = self.render_video(script, voiceover)

            self.upload_to_youtube(
                video_path=video,
                title=f"{topic} 🤯 #shorts",
                description=f"⚠️ Mind-blowing {topic} facts! Like & Subscribe!\n\n#shorts #viral #trending"
            )

            os.remove(voiceover)
            os.remove(video)

        except Exception as e:
            print(f"Error: {e}")


def job():
    factory = ShortsFactory()
    factory.create_and_upload()
    print("✅ Successfully created and uploaded Short")

schedule.every(6).hours.do(job)

if __name__ == "__main__":
    print("🚀 YouTube Shorts Factory Running 24/7")
    while True:
        schedule.run_pending()
        time.sleep(1)

