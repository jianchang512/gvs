import sys
import os
import time
import json
import base64
import re
import subprocess
import io
import ast
from datetime import datetime, timedelta
import requests
from PIL import Image

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLabel, QComboBox, QLineEdit,
                               QPushButton, QTextEdit, QFileDialog, QMessageBox, QProgressBar, QSlider)
from PySide6.QtCore import Qt, QThread, Signal, QLocale, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QCloseEvent, QDesktopServices,QIcon

def resource_path(relative_path):
    try:
        # PyInstaller 创建临时文件夹，将路径存储在 _MEIPASS 中
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

if sys.platform == 'win32':
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))

    os.environ['PATH'] = application_path + os.pathsep + os.environ['PATH']


if getattr(sys, 'frozen', False):
    ROOT_DIR = os.path.dirname(sys.executable)
else:
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))




OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

CONFIG_FILE = os.path.join(ROOT_DIR, "config.json")
DEBUG_LOG_FILE = os.path.join(ROOT_DIR, "api_debug.log")

def get_system_language():
    """获取系统语言，返回 'zh' 或 'en'"""
    sys_lang = QLocale.system().name().lower() # 例如 zh_cn, en_us
    # 判断逻辑：只要包含 zh, cn, hk, tw 则视为中文
    if any(x in sys_lang for x in ['zh', 'cn', 'hk', 'tw']):
        return 'zh'
    return 'en'

LANG = get_system_language()

TRANS = {
    "zh": {
        "title": "GVS 字幕提取 AI (v1.0)",
        "No subtitles were generated":"未生成字幕，请查看错误日志",
        "drop_hint": "拖拽或点击选择视频到此处",
        "region": "区域:",
        "provider": "服务:",
        "model": "模型:",
        "key_placeholder": "请输入 API Key (明文显示)",
        "zhipu_key_ph": "请输入智谱 API Key",
        "gemini_key_ph": "请输入 Google API Key",
        "start_btn": "开始提取",
        "stop_btn": "停止",
        "open_dir_btn": "打开输出目录",
        "ready": "已就绪: {}",
        "load_file": "加载文件: {}",
        "select_video": "选择视频",
        "msg_hint": "提示",
        "msg_no_video": "请先选择视频",
        "msg_no_key": "请输入 {} 的API Key",
        "task_start": "=== 开始任务: {} ===",
        "service_info": "服务: {} | 模型: {}",
        "ffmpeg_error": "❌ 无法获取视频时长，请检查 ffmpeg。",
        "video_info": "视频时长: {}秒，每批次处理 {} 秒",
        "user_abort": "🛑 任务被用户中止。",
        "ai_analyzing": "🔍 AI分析中: {} -> {}",
        "smart_merge": "🔗 智能拼接: ...{}",
        "save_success": "✅ 字幕已保存至: {}",
        "save_fail": "❌ 保存SRT失败: {}",
        "fatal_error": "❌ 严重错误: {}",
        "api_fail": "❌ API 请求失败 (尝试 {}/3): {}",
        "rate_limit": "⚠️ 触发限流，暂停10秒...",
        "common_error": "⚠️ 常规错误，2秒后重试...",
        "stop_confirm_title": "任务运行中",
        "stop_confirm_msg": "任务正在运行，确定要强制退出吗？",
        "stopping": "正在停止...",
        "force_stop": "正在强制终止线程...",
        "regions": ["全画面", "底部", "中部", "顶部", "自定义"],
        "custom_region_start": "起始:",
        "custom_region_end": "结束:",
        "providers": ["智谱AI", "Gemini", "OpenAI(自定义)", "Gemini(自定义)", "Claude(自定义)"]
    },
    "en": {
        "No subtitles were generated":"No subtitles were generated. Please check the error log",
        "title": "GVS Subtitle AI (v1.0)",
        "drop_hint": "Drag & Drop &Click Video Here",
        "region": "Region:",
        "provider": "Service:",
        "model": "Model:",
        "key_placeholder": "Enter API Key (Plain Text)",
        "zhipu_key_ph": "Enter Zhipu API Key",
        "gemini_key_ph": "Enter Google API Key",
        "openai_custom_key_ph": "Enter API Key",
        "gemini_custom_key_ph": "Enter API Key",
        "claude_custom_key_ph": "Enter API Key",
        "custom_url_ph": "Enter API URL",
        "start_btn": "Start",
        "stop_btn": "Stop",
        "open_dir_btn": "Open Output Dir",
        "ready": "Ready: {}",
        "load_file": "File Loaded: {}",
        "select_video": "Select Video",
        "msg_hint": "Hint",
        "msg_no_video": "Please select a video first",
        "msg_no_key": "Please enter API Key for {}",
        "task_start": "=== Task Started: {} ===",
        "service_info": "Service: {} | Model: {}",
        "ffmpeg_error": "❌ Cannot get video duration. Check ffmpeg.",
        "video_info": "Duration: {}s, Batch Size: {}s",
        "user_abort": "🛑 Task aborted by user.",
        "ai_analyzing": "🔍 AI Analyzing: {} -> {}",
        "smart_merge": "🔗 Smart Merge: ...{}",
        "save_success": "✅ SRT Saved: {}",
        "save_fail": "❌ Failed to save SRT: {}",
        "fatal_error": "❌ Fatal Error: {}",
        "api_fail": "❌ API Failed (Attempt {}/3): {}",
        "rate_limit": "⚠️ Rate limit hit, pausing 10s...",
        "common_error": "⚠️ Error, retrying in 2s...",
        "stop_confirm_title": "Task Running",
        "stop_confirm_msg": "Task is running. Force quit?",
        "stopping": "Stopping...",
        "force_stop": "Forcing thread termination...",
        "regions": ["Full Screen", "Bottom", "Middle", "Top", "Custom"],
        "custom_region_start": "Start:",
        "custom_region_end": "End:",
        "providers": ["Zhipu AI", "Gemini", "OpenAI(Custom)", "Gemini(Custom)", "Claude(Custom)"]
    }
}

def tr(key):
    return TRANS[LANG].get(key, key)

def log_debug(content):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(DEBUG_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {content}\n{'-'*50}\n")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_config(new_data):
    current = load_config()
    current.update(new_data)
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
    except:
        pass


def ms_to_srt_time(seconds):
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int(td.microseconds / 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

def extract_frame_ffmpeg(video_path, time_sec):
    try:
        cmd = [
            'ffmpeg', '-ss', str(time_sec), '-i', video_path,
            '-vframes', '1', '-q:v', '2', '-f', 'image2', 'pipe:1'
        ]
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo, check=False)
        return result.stdout if result.returncode == 0 else None
    except:
        return None

def crop_image_bytes(img_bytes, region_idx, custom_start=0, custom_end=100):
    """
    根据索引裁切图片
    region_idx: 0=全画面, 1=底部, 2=中部, 3=顶部, 4=自定义
    custom_start: 自定义起始百分比 (0-100)
    custom_end: 自定义结束百分比 (0-100)
    """
    if not img_bytes: return None
    try:
        img = Image.open(io.BytesIO(img_bytes))
        w, h = img.size

        # 默认全画面
        y_start, y_end = 0, h

        if region_idx == 1: # 底部 (取下 1/3)
            y_start = int(h * 0.66)
        elif region_idx == 3: # 顶部 (取上 1/3)
            y_end = int(h * 0.33)
        elif region_idx == 2: # 中部 (取中间 1/3)
            y_start = int(h * 0.33)
            y_end = int(h * 0.66)
        elif region_idx == 4: # 自定义区域
            y_start = int(h * custom_start / 100)
            y_end = int(h * custom_end / 100)
        # region_idx == 0: 全画面，不做改变

        crop_box = (0, y_start, w, y_end)
        cropped_img = img.crop(crop_box)
        
        cw, ch = cropped_img.size
        # 如果图片过小，进行放大，提高OCR准确率
        if ch < 100:
            cropped_img = cropped_img.resize((int(cw * 2), int(ch * 2)), Image.Resampling.BICUBIC)
            
        out_buffer = io.BytesIO()
        cropped_img.save(out_buffer, format='JPEG', quality=95)
        return base64.b64encode(out_buffer.getvalue()).decode('utf-8')
    except:
        return None

def get_video_duration_ffmpeg(video_path):
    try:
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
        return float(result.stdout)
    except:
        return 0.0


class AIClient:
    def __init__(self, provider_idx, api_key, model, log_signal, api_url=None):
        self.provider_idx = provider_idx # 0=智谱, 1=Gemini, 2=OpenAI(自定义), 3=Gemini(自定义), 4=Claude(自定义)
        self.api_key = api_key
        self.model = model
        self.log_signal = log_signal
        self.api_url = api_url  # 自定义API地址

    def chat_smart_batch(self, images_base64, start_sec):
        count = len(images_base64)

        prompt_text = (
            f"I provide {count} chronological video frames.\n"
            f"The first image corresponds to timestamp {start_sec} seconds.\n"
            f"The images are sampled at 1 frame per second (1 fps).\n"
            "Your task:\n"
            "1. Identify hard subtitles in the images.\n"
            "2. MERGE continuous identical subtitles into a single entry.\n"
            "3. Return a JSON list. Format: [{\"start\": 10, \"end\": 12, \"text\": \"Content\"}]\n"
            "4. Use DOUBLE QUOTES for keys and strings.\n"
            "5. If no subtitle, do not include in list.\n"
            "6. Output ONLY the JSON string."
        )

        for i in range(3):
            try:
                resp_text = ""
                if self.provider_idx == 0: # 智谱
                    resp_text = self._call_zhipu(prompt_text, images_base64)
                elif self.provider_idx == 1: # Gemini
                    resp_text = self._call_gemini_rest(prompt_text, images_base64)
                elif self.provider_idx == 2: # OpenAI(自定义)
                    resp_text = self._call_openai_custom(prompt_text, images_base64)
                elif self.provider_idx == 3: # Gemini(自定义)
                    resp_text = self._call_gemini_custom(prompt_text, images_base64)
                elif self.provider_idx == 4: # Claude(自定义)
                    resp_text = self._call_claude_custom(prompt_text, images_base64)

                log_debug(f"Batch {start_sec}s - Response:\n{resp_text}")

                clean_json = resp_text.replace("```json", "").replace("```", "").strip()

                try:
                    data = json.loads(clean_json)
                except json.JSONDecodeError:
                    try:
                        data = ast.literal_eval(clean_json)
                    except Exception as e:
                        log_debug(f"JSON Parse Error: {e}\nRaw content: {clean_json}")
                        return []

                if isinstance(data, list):
                    return data
                else:
                    return []

            except Exception as e:
                err_str = str(e)
                log_debug(f"API Error: {err_str}")

                self.log_signal.emit(tr("api_fail").format(i+1, err_str))

                if "429" in err_str or "quota" in err_str or "exhausted" in err_str:
                    self.log_signal.emit(tr("rate_limit"))
                    time.sleep(10)
                else:
                    self.log_signal.emit(tr("common_error"))
                    time.sleep(2)
        return []

    def _call_zhipu(self, prompt, images_base64):
        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        content = [{"type": "text", "text": prompt}]
        for img in images_base64:
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}})
        data = {"model": self.model, "messages": [{"role": "user", "content": content}], "temperature": 0.05}

        resp = requests.post(url, json=data, headers=headers, timeout=60,verify=False)

        if resp.status_code != 200:
            try:
                err_msg = resp.json()["error"]["message"]
            except:
                err_msg = resp.text
            raise Exception(f"HTTP {resp.status_code}: {err_msg}")

        return resp.json()["choices"][0]["message"]["content"].strip()

    def _call_gemini_rest(self, prompt, images_base64):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        parts = [{"text": prompt}]
        for img in images_base64:
            parts.append({"inline_data": {"mime_type": "image/jpeg", "data": img}})

        data = {
            "contents": [{"parts": parts}],
            "generationConfig": {"temperature": 0.05}
        }

        resp = requests.post(url, json=data, headers=headers, timeout=60,verify=False)

        if resp.status_code != 200:
            try:
                err_msg = resp.json()["error"]["message"]
            except:
                err_msg = resp.text
            raise Exception(f"Gemini Error {resp.status_code}: {err_msg}")

        try:
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except:
            try:
                feedback = resp.json()["promptFeedback"]
                raise Exception(f"Safety Block: {feedback}")
            except:
                raise Exception(f"Invalid Structure: {resp.text[:100]}...")

    def _call_openai_custom(self, prompt, images_base64):
        """OpenAI(自定义) - 使用自定义API地址"""
        if not self.api_url:
            raise Exception("API URL is not set")
        url = self.api_url.rstrip('/') + "/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        content = [{"type": "text", "text": prompt}]
        for img in images_base64:
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}})
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": content}],
            "temperature": 0.05
        }

        resp = requests.post(url, json=data, headers=headers, timeout=60, verify=False)

        if resp.status_code != 200:
            try:
                err_msg = resp.json()["error"]["message"]
            except:
                err_msg = resp.text
            raise Exception(f"HTTP {resp.status_code}: {err_msg}")

        return resp.json()["choices"][0]["message"]["content"].strip()

    def _call_gemini_custom(self, prompt, images_base64):
        """Gemini(自定义) - 使用自定义API地址"""
        if not self.api_url:
            raise Exception("API URL is not set")
        # 自定义URL + /v1beta/models/{model}:generateContent
        url = self.api_url.rstrip('/') + f"/v1beta/models/{self.model}:generateContent"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        parts = [{"text": prompt}]
        for img in images_base64:
            parts.append({"inline_data": {"mime_type": "image/jpeg", "data": img}})

        data = {
            "contents": [{"parts": parts}],
            "generationConfig": {"temperature": 0.05}
        }

        resp = requests.post(url, json=data, headers=headers, timeout=60, verify=False)

        if resp.status_code != 200:
            try:
                err_msg = resp.json()["error"]["message"]
            except:
                err_msg = resp.text
            raise Exception(f"HTTP {resp.status_code}: {err_msg}")

        try:
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except:
            raise Exception(f"Invalid Response Structure: {resp.text[:100]}...")

    def _call_claude_custom(self, prompt, images_base64):
        """Claude(自定义) - 使用自定义API地址"""
        if not self.api_url:
            raise Exception("API URL is not set")
        # Claude 使用 /v1/messages
        url = self.api_url.rstrip('/') + "/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        # Claude 格式需要把图片转成 base64 放入 messages
        content_parts = [{"type": "text", "text": prompt}]
        for img in images_base64:
            content_parts.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img}})

        data = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": content_parts}]
        }

        resp = requests.post(url, json=data, headers=headers, timeout=60, verify=False)

        if resp.status_code != 200:
            try:
                err_msg = resp.json()["error"]["message"]
            except:
                err_msg = resp.text
            raise Exception(f"HTTP {resp.status_code}: {err_msg}")

        return resp.json()["content"][0]["text"].strip()


class Processor(QThread):
    log = Signal(str)
    progress = Signal(int, int)
    finished = Signal()

    def __init__(self, video_path, region_idx, api_key, model, provider_idx, api_url=None, custom_region=(0, 100)):
        super().__init__()
        self.video_path = video_path
        self.region_idx = region_idx # int
        self.api_key = api_key
        self.model = model
        self.provider_idx = provider_idx # int
        self.api_url = api_url  # 自定义API地址
        self.custom_start, self.custom_end = custom_region  # 自定义裁切区域百分比
        self.running = True
        self.BATCH_SIZE = 20

    def run(self):
        provider_name = tr("providers")[self.provider_idx]
        self.log.emit(tr("task_start").format(os.path.basename(self.video_path)))
        self.log.emit(tr("service_info").format(provider_name, self.model))

        duration = get_video_duration_ffmpeg(self.video_path)
        if duration == 0:
            self.log.emit(tr("ffmpeg_error"))
            self.finished.emit()
            return
        total_seconds = int(duration)
        self.log.emit(tr("video_info").format(total_seconds, self.BATCH_SIZE))

        try:
            client = AIClient(self.provider_idx, self.api_key, self.model, self.log, self.api_url)
            final_subtitles = []
            
            batch_imgs = []
            batch_start_sec = 0
            
            for sec in range(total_seconds + 1):
                if not self.running: 
                    self.log.emit(tr("user_abort"))
                    break
                
                if len(batch_imgs) == 0:
                    batch_start_sec = sec
                    
                img_bytes = extract_frame_ffmpeg(self.video_path, sec)
                if img_bytes:
                    b64 = crop_image_bytes(img_bytes, self.region_idx, self.custom_start, self.custom_end)
                    if b64:
                        batch_imgs.append(b64)
                
                self.progress.emit(sec, total_seconds)
                
                if len(batch_imgs) >= self.BATCH_SIZE:
                    self.process_smart_batch(client, batch_imgs, batch_start_sec, final_subtitles)
                    batch_imgs = []
            
            if batch_imgs and self.running:
                self.process_smart_batch(client, batch_imgs, batch_start_sec, final_subtitles)
                
            if self.running:
                if not final_subtitles:
                    raise RuntimeError(tr("No subtitles were generated"))
                self.save_srt(final_subtitles)

        except Exception as e:
            self.log.emit(tr("fatal_error").format(str(e)))
            import traceback
            traceback.print_exc()
            
        self.finished.emit()

    def process_smart_batch(self, client, imgs, start_sec, final_subtitles):
        if not self.running: return

        end_sec = start_sec + len(imgs)
        self.log.emit(tr("ai_analyzing").format(ms_to_srt_time(start_sec), ms_to_srt_time(end_sec)))
        
        ai_results = client.chat_smart_batch(imgs, start_sec)
        
        if not ai_results:
            return

        for item in ai_results:
            text = item.get('text', '').strip()
            if not text or self.is_junk(text): continue
            
            s_time = float(item.get('start', 0))
            e_time = float(item.get('end', 0))
            
            if final_subtitles:
                last_global = final_subtitles[-1]
                if self.is_same_sentence(last_global['text'], text):
                    if abs(s_time - last_global['end']) <= 2.5: 
                        self.log.emit(tr("smart_merge").format(text[-5:]))
                        last_global['end'] = max(last_global['end'], e_time)
                        continue 
            
            final_subtitles.append({"start": s_time, "end": e_time, "text": text})

    def is_same_sentence(self, t1, t2):
        def clean(s): return re.sub(r'[^\w]', '', s).lower()
        return clean(t1) == clean(t2)

    def is_junk(self, text):
        if not text: return True
        low = text.lower()
        if "no subtitle" in low: return True
        if "no text" in low: return True
        if text == "[EMPTY]": return True
        return False

    def save_srt(self, subs):
        # 1. 确定文件名
        base_name = os.path.splitext(os.path.basename(self.video_path))[0]
        srt_name = f"{base_name}.srt"
        full_path = os.path.join(OUTPUT_DIR, srt_name)
        
        # 2. 检查重名，不覆盖
        if os.path.exists(full_path):
            timestamp = datetime.now().strftime("%H%M%S")
            srt_name = f"{base_name}-{timestamp}.srt"
            full_path = os.path.join(OUTPUT_DIR, srt_name)

        try:
            with open(full_path, "w", encoding="utf-8") as f:
                for i, s in enumerate(subs):
                    f.write(f"{i+1}\n")
                    f.write(f"{ms_to_srt_time(s['start'])} --> {ms_to_srt_time(s['end'])}\n")
                    f.write(f"{s['text']}\n\n")
            self.log.emit(tr("save_success").format(full_path))
        except Exception as e:
            self.log.emit(tr("save_fail").format(str(e)))

    def stop(self):
        self.running = False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("title"))
        self.resize(850, 700)
        self.worker = None
        icon_path = resource_path("ico.ico") 
        self.setWindowIcon(QIcon(icon_path))

        
        # 内存中缓存 Key
        # 0=Zhipu, 1=Gemini, 2=OpenAI(自定义), 3=Gemini(自定义), 4=Claude(自定义)
        self.api_keys = ["", "", "", "", ""]
        self.custom_api_urls = ["", "", ""]  # 2,3,4 对应的URL
        
        self.apply_stylesheet()
        self.setup_ui()
        self.load_settings()

    def apply_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: #2b2b2b; color: #e0e0e0; font-family: "Segoe UI", sans-serif; font-size: 14px; }
            QLabel { color: #cccccc; }
            QLineEdit, QComboBox { background-color: #3c3f41; border: 1px solid #555; border-radius: 4px; padding: 5px; color: #fff; }
            QPushButton { background-color: #4a90e2; color: white; border-radius: 4px; padding: 8px 16px; border: none; }
            QPushButton:hover { background-color: #357abd; }
            QPushButton:disabled { background-color: #555; color: #888; }
            QPushButton#btnStop { background-color: #d9534f; }
            QPushButton#btnStop:hover { background-color: #c9302c; }
            QPushButton#btnOpenDir { background-color: #5f6368; font-size: 12px; }
            QPushButton#btnOpenDir:hover { background-color: #70747a; }
            QProgressBar { border: 1px solid #555; border-radius: 4px; text-align: center; background-color: #1e1e1e; }
            QProgressBar::chunk { background-color: #5cb85c; width: 10px; }
            QTextEdit { background-color: #1e1e1e; border: 1px solid #444; color: #0f0; font-family: Consolas; font-size: 12px; }
        """)

    def setup_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        
        self.drop_label = QLabel(tr("drop_hint"))
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setStyleSheet("border: 2px dashed #666; border-radius: 8px; font-size: 18px; color: #888; background-color: #252526;")
        self.drop_label.setFixedHeight(150)
        layout.addWidget(self.drop_label)
        
        row1 = QHBoxLayout()
        self.region_combo = QComboBox()
        self.region_combo.addItems(tr("regions"))
        # 连接区域选择变化信号
        self.region_combo.currentIndexChanged.connect(self.on_region_changed)

        # 自定义裁切滑块
        self.custom_start_slider = QSlider(Qt.Horizontal)
        self.custom_start_slider.setRange(0, 100)
        self.custom_start_slider.setValue(0)
        self.custom_start_slider.setFixedWidth(80)
        self.custom_start_slider.setVisible(False)
        self.custom_start_slider.valueChanged.connect(self.on_custom_region_changed)

        self.custom_end_slider = QSlider(Qt.Horizontal)
        self.custom_end_slider.setRange(0, 100)
        self.custom_end_slider.setValue(100)
        self.custom_end_slider.setFixedWidth(80)
        self.custom_end_slider.setVisible(False)
        self.custom_end_slider.valueChanged.connect(self.on_custom_region_changed)

        # 自定义裁切百分比显示标签
        self.custom_start_label = QLabel("0%")
        self.custom_start_label.setVisible(False)
        self.custom_end_label = QLabel("100%")
        self.custom_end_label.setVisible(False)

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(tr("providers"))
        # 使用 currentIndexChanged (int) 触发
        self.provider_combo.currentIndexChanged.connect(self.on_provider_changed)
        
        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText(tr("key_placeholder"))
        self.key_edit.setEchoMode(QLineEdit.Normal)
        self.key_edit.textChanged.connect(self.on_key_edited)

        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("gpt-4o-mini")
        self.model_edit.setFixedWidth(180)

        self.api_url_edit = QLineEdit()
        self.api_url_edit.setPlaceholderText(tr("custom_url_ph"))
        self.api_url_edit.setFixedWidth(250)
        self.api_url_edit.setVisible(False)

        row1.addWidget(QLabel(tr("region")))
        row1.addWidget(self.region_combo)
        # 自定义裁切区域控件
        row1.addWidget(QLabel(tr("custom_region_start")))
        row1.addWidget(self.custom_start_slider)
        row1.addWidget(self.custom_start_label)
        row1.addWidget(QLabel(tr("custom_region_end")))
        row1.addWidget(self.custom_end_slider)
        row1.addWidget(self.custom_end_label)
        row1.addSpacing(10)  # 分隔
        row1.addWidget(QLabel(tr("provider")))
        row1.addWidget(self.provider_combo)
        row1.addWidget(self.key_edit)
        row1.addWidget(QLabel(tr("model")))
        row1.addWidget(self.model_edit)
        row1.addWidget(self.api_url_edit)
        layout.addLayout(row1)
        
        row2 = QHBoxLayout()
        self.btn_start = QPushButton(tr("start_btn"))
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.clicked.connect(self.start)
        
        self.btn_stop = QPushButton(tr("stop_btn"))
        self.btn_stop.setObjectName("btnStop")
        self.btn_stop.setCursor(Qt.PointingHandCursor)
        self.btn_stop.clicked.connect(self.stop)
        self.btn_stop.setEnabled(False)
        
        # 新增打开目录按钮
        self.btn_open_dir = QPushButton(tr("open_dir_btn"))
        self.btn_open_dir.setObjectName("btnOpenDir")
        self.btn_open_dir.setCursor(Qt.PointingHandCursor)
        self.btn_open_dir.setFixedSize(150, 25) # 固定大小
        self.btn_open_dir.clicked.connect(self.open_output_dir)
        
        row2.addWidget(self.btn_start)
        row2.addWidget(self.btn_stop)
        row2.addWidget(self.btn_open_dir) # 添加到右侧
        layout.addLayout(row2)
        
        self.pbar = QProgressBar(); self.pbar.setValue(0)
        layout.addWidget(self.pbar)
        self.log_box = QTextEdit(); self.log_box.setReadOnly(True)
        layout.addWidget(self.log_box)
        self.setAcceptDrops(True)

    def on_provider_changed(self, idx):
        """切换服务商 (int idx)"""
        # 显示/隐藏 API URL 输入框
        show_url = idx >= 2  # 自定义服务需要URL
        self.api_url_edit.setVisible(show_url)

        if idx == 0: # 智谱
            self.key_edit.setPlaceholderText(tr("zhipu_key_ph"))
            self.model_edit.setPlaceholderText("glm-4-vision-flash")
            self.api_url_edit.setPlaceholderText("")
            self.api_url_edit.setText("")
        elif idx == 1: # Gemini
            self.key_edit.setPlaceholderText(tr("gemini_key_ph"))
            self.model_edit.setPlaceholderText("gemini-2.0-flash-exp")
            self.api_url_edit.setPlaceholderText("")
            self.api_url_edit.setText("")
        elif idx == 2: # OpenAI(自定义)
            self.key_edit.setPlaceholderText(tr("openai_custom_key_ph"))
            self.model_edit.setPlaceholderText("gpt-4o")
            self.api_url_edit.setPlaceholderText(tr("custom_url_ph"))
            self.api_url_edit.setText(self.custom_api_urls[0])
        elif idx == 3: # Gemini(自定义)
            self.key_edit.setPlaceholderText(tr("gemini_custom_key_ph"))
            self.model_edit.setPlaceholderText("gemini-2.0-flash")
            self.api_url_edit.setPlaceholderText(tr("custom_url_ph"))
            self.api_url_edit.setText(self.custom_api_urls[1])
        elif idx == 4: # Claude(自定义)
            self.key_edit.setPlaceholderText(tr("claude_custom_key_ph"))
            self.model_edit.setPlaceholderText("claude-sonnet-4-20250514")
            self.api_url_edit.setPlaceholderText(tr("custom_url_ph"))
            self.api_url_edit.setText(self.custom_api_urls[2])

        self.key_edit.setText(self.api_keys[idx])

    def on_region_changed(self, idx):
        """切换区域选择"""
        # idx=4 是自定义区域，显示滑块
        show_custom = (idx == 4)
        self.custom_start_slider.setVisible(show_custom)
        self.custom_end_slider.setVisible(show_custom)
        self.custom_start_label.setVisible(show_custom)
        self.custom_end_label.setVisible(show_custom)

    def on_custom_region_changed(self):
        """自定义裁切滑块变化"""
        start = self.custom_start_slider.value()
        end = self.custom_end_slider.value()

        # 确保起始位置不超过结束位置
        if start > end:
            if self.sender() == self.custom_start_slider:
                self.custom_end_slider.setValue(start)
                end = start
            else:
                self.custom_start_slider.setValue(end)
                start = end

        self.custom_start_label.setText(f"{start}%")
        self.custom_end_label.setText(f"{end}%")

    def on_key_edited(self, text):
        idx = self.provider_combo.currentIndex()
        if 0 <= idx < len(self.api_keys):
            self.api_keys[idx] = text.strip()

    def open_output_dir(self):
        """打开输出目录"""
        QDesktopServices.openUrl(QUrl.fromLocalFile(OUTPUT_DIR))

    def load_settings(self):
        cfg = load_config()

        # 加载 keys
        self.api_keys[0] = cfg.get("zhipu_key", "")
        self.api_keys[1] = cfg.get("gemini_key", "")
        self.api_keys[2] = cfg.get("openai_custom_key", "")
        self.api_keys[3] = cfg.get("gemini_custom_key", "")
        self.api_keys[4] = cfg.get("claude_custom_key", "")

        # 加载自定义URL
        self.custom_api_urls[0] = cfg.get("openai_custom_url", "")
        self.custom_api_urls[1] = cfg.get("gemini_custom_url", "")
        self.custom_api_urls[2] = cfg.get("claude_custom_url", "")

        # 加载自定义裁切区域
        self.custom_start_slider.setValue(int(cfg.get("custom_region_start", 0)))
        self.custom_end_slider.setValue(int(cfg.get("custom_region_end", 100)))

        # 恢复索引 (int)
        self.region_combo.setCurrentIndex(int(cfg.get("region_idx", 1))) # 默认底部(1)

        last_provider_idx = int(cfg.get("provider_idx", 0)) # 默认智谱(0)
        self.provider_combo.setCurrentIndex(last_provider_idx)

        # 手动刷新一次确保状态同步
        self.on_provider_changed(last_provider_idx)
        self.on_region_changed(self.region_combo.currentIndex())
        self.on_custom_region_changed()  # 更新标签显示

        self.model_edit.setText(cfg.get("model", ""))

    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls(): e.accept()

    def dropEvent(self, e: QDropEvent):
        self.load_video(e.mimeData().urls()[0].toLocalFile())

    def mousePressEvent(self, e):
        # 兼容性修复
        pos = e.position().toPoint() if hasattr(e, 'position') else e.pos()
        if self.childAt(pos) == self.drop_label:
            cfg = load_config(); last = cfg.get("last_dir", "")
            f, _ = QFileDialog.getOpenFileName(self, tr("select_video"), last, "Videos (*.mp4 *.mkv *.avi)")
            if f: self.load_video(f)

    def load_video(self, path):
        self.video_path = path
        self.drop_label.setText(tr("ready").format(os.path.basename(path)))
        save_config({"last_dir": os.path.dirname(path)})
        self.log(tr("load_file").format(path))

    def log(self, s):
        self.log_box.append(s); sb = self.log_box.verticalScrollBar(); sb.setValue(sb.maximum())

    def start(self):
        if not hasattr(self, 'video_path'): return QMessageBox.warning(self, tr("msg_hint"), tr("msg_no_video"))

        p_idx = self.provider_combo.currentIndex()
        p_name = self.provider_combo.currentText()
        key = self.api_keys[p_idx]
        model = self.model_edit.text().strip()
        api_url = None

        # 自定义服务需要获取API URL
        if p_idx >= 2:
            api_url = self.api_url_edit.text().strip()
            # 保存到对应索引
            url_idx = p_idx - 2
            if url_idx == 0:
                self.custom_api_urls[0] = api_url
            elif url_idx == 1:
                self.custom_api_urls[1] = api_url
            elif url_idx == 2:
                self.custom_api_urls[2] = api_url

        if not key: return QMessageBox.warning(self, tr("msg_hint"), tr("msg_no_key").format(p_name))
        if not model: return QMessageBox.warning(self, tr("msg_hint"), tr("msg_no_key").format("Model"))
        if p_idx >= 2 and not api_url: return QMessageBox.warning(self, tr("msg_hint"), "请输入 API URL")

        # 保存配置 (使用索引)
        save_config({
            "region_idx": self.region_combo.currentIndex(),
            "provider_idx": p_idx,
            "model": model,
            "zhipu_key": self.api_keys[0],
            "gemini_key": self.api_keys[1],
            "openai_custom_key": self.api_keys[2],
            "gemini_custom_key": self.api_keys[3],
            "claude_custom_key": self.api_keys[4],
            "openai_custom_url": self.custom_api_urls[0],
            "gemini_custom_url": self.custom_api_urls[1],
            "claude_custom_url": self.custom_api_urls[2],
            "custom_region_start": self.custom_start_slider.value(),
            "custom_region_end": self.custom_end_slider.value()
        })

        self.btn_start.setEnabled(False); self.btn_stop.setEnabled(True)
        self.log_box.clear(); self.pbar.setValue(0)

        # 获取自定义裁切区域
        custom_region = (self.custom_start_slider.value(), self.custom_end_slider.value())

        # 传入 region_idx 和 provider_idx (均为 int)
        self.worker = Processor(self.video_path, self.region_combo.currentIndex(), key, model, p_idx, api_url, custom_region)
        self.worker.log.connect(self.log)
        self.worker.progress.connect(lambda c, t: (self.pbar.setMaximum(t), self.pbar.setValue(c)))
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def stop(self):
        if self.worker: 
            self.worker.stop()
            self.log(tr("stopping"))
            self.btn_stop.setEnabled(False)

    def on_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.worker = None

    def closeEvent(self, event: QCloseEvent):
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(self, tr("stop_confirm_title"), 
                                         tr("stop_confirm_msg"), 
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.log(tr("force_stop"))
                self.worker.stop()
                self.worker.wait(2000) 
                if self.worker.isRunning():
                    self.worker.terminate()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    w = MainWindow()
    w.show()
    sys.exit(app.exec())