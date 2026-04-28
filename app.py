# -*- coding: utf-8 -*-
"""
TK 视频分析器 - TikTok 视频脚本翻译与分析
双通道原文提取:Whisper语音 + MiniMax视觉读画面文字
"""

import streamlit as st
import urllib.request
import urllib.parse
import urllib.error
import subprocess
import json
import re
import time
import base64
import os
from pathlib import Path
import config
import tempfile

st.set_page_config(page_title="TK 视频分析器", page_icon="🎬", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0a0a0a; color: #ffffff; }
    h1 { font-size: 2.2rem; font-weight: 700; color: #00f2ea; text-align: center; margin-bottom: 0.5rem; }
    .subtitle { font-size: 1rem; color: #888; text-align: center; margin-bottom: 2rem; }
    .card { background-color: #1a1a1a; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; border: 1px solid #333; }
    .card-title { font-size: 1.05rem; font-weight: 600; color: #00f2ea; margin-bottom: 0.8rem; }
    .highlight-item { padding: 0.8rem 1rem; background: #222; border-radius: 8px; margin-bottom: 0.8rem; border-left: 3px solid #ff0050; }
    .section-label { font-size: 0.8rem; color: #888; font-weight: 600; margin-bottom: 3px; margin-top: 8px; }
    .text-block { background: #111; border-radius: 8px; padding: 0.8rem 1rem; font-size: 0.95rem; line-height: 1.8; color: #e0e0e0; margin-bottom: 0.5rem; white-space: pre-wrap; }
    .stButton>button { background: linear-gradient(90deg, #ff0050 0%, #00f2ea 100%); color: white; border: none; border-radius: 25px; padding: 0.7rem 2rem; font-weight: 600; width: 100%; }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea { background-color: #1a1a1a; border: 1px solid #333; color: white; border-radius: 8px; }
    .stSelectbox>div>div>div { background-color: #1a1a1a; color: white; }
    .info-box { background: #1a1a2e; border: 1px solid #333; border-radius: 8px; padding: 0.8rem; margin-bottom: 0.5rem; font-size: 0.85rem; color: #aaa; }
</style>
""", unsafe_allow_html=True)

for key, val in {
    "api_key_input": "",
    "result": None,
    "current_url": "",
    "current_market": "",
    "video_path": "",
    "whisper_transcript": "",
    "vision_text": "",
    "detected_lang": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

MARKETS = {
    "🇵🇭 菲律宾": {
        "context": "菲律宾市场:3合1甜口咖啡、吕宋芒果干等本土零食,高性价比,街头/通勤场景。",
        "lang_hint": "他加禄语(Tagalog)+英语混用(Taglish)。Tagalog词:Masarap(好吃)、Sulit(超值)、Ang sarap(太好吃了)、Pwede na(还行)。英语词:nice one、check it out、guys。",
    },
    "🇻🇳 越南": {
        "context": "越南市场:即溶咖啡、罗望子/辣味零食,注重便捷性和性价比。",
        "lang_hint": "越南语(Tiếng Việt)。常见:Ngon quá(太好吃了)、Rẻ quá(太便宜)、Mọi người ơi(各位)、Xem ngay(快看)。",
    },
    "🇮🇩 印尼": {
        "context": "印尼市场:甜食和咖啡饮品,注重本土风味和清真认证。",
        "lang_hint": "印尼语(Bahasa Indonesia)。常见:Enak banget(超好吃)、Murah banget(超便宜)、Cekidot(来看看)。",
    },
    "🇸🇬 新加坡": {
        "context": "新加坡市场:发达经济体,多元文化,注重品质和健康,喜欢简洁现代风格。",
        "lang_hint": "英语+Singlish。语气词:lah(肯定)、leh(疑问)、lor(陈述)、meh(质疑)。",
    },
    "🇲🇾 马来西亚": {
        "context": "马来西亚市场:多元文化,注重清真认证,价格敏感,线上社交活跃。",
        "lang_hint": "马来语+英语+中文混用(Manglish)。常见:Sedap(好吃)、Murah(便宜)、Best(超棒)、Gila(超)。",
    },
    "🇹🇭 泰国": {
        "context": "泰国市场:泰式冰咖啡、泰式零食,注重口味正宗,价格偏低,TikTok非常活跃。",
        "lang_hint": "泰语。礼貌语气词:ka(女性用,句尾)、krub(男性用,句尾)。常见:อร่อยมาก(超好吃)、ถูกมาก(超便宜)。",
    },
}

# ==============================================================================
# 核心功能函数
# ==============================================================================

def resolve_short_url(url):
    short = [r'vm\.tiktok\.com', r'vt\.tiktok\.com', r'tiktok\.com/t/']
    if not any(re.search(p, url) for p in short):
        return url
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        r = urllib.request.urlopen(req, timeout=15)
        if '/video/' in r.url:
            return r.url
    except:
        pass
    return None

def get_video_id(url):
    clean = url.split('?')[0].split('#')[0]
    for p in [r'tiktok\.com/@[^/]+/video/(\d+)', r'tiktok\.com/[^/]+/video/(\d+)',
              r'm\.tiktok\.com/v/(\d+)', r'id=(\d+)', r'/(\d{15,25})']:
        m = re.search(p, clean)
        if m:
            return m.group(1)
    return None

def download_via_tikwm(vid, max_retries=3):
    api_url = "https://www.tikwm.com/api/?url=" + urllib.parse.quote("https://www.tiktok.com/@a/video/" + vid, safe='')
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(api_url)
            req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            req.add_header("Referer", "https://www.tikwm.com/")
            r = urllib.request.urlopen(req, timeout=30)
            d = json.loads(r.read())
            code = d.get("code")
            if code == 0:
                play = d.get("data", {}).get("play", "")
                wm = d.get("data", {}).get("wmplay", "")
                return play or wm
            msg = str(d.get("msg", ""))
            if attempt < max_retries - 1:
                time.sleep(1.5)
                continue
            raise Exception(f"tikwm错误:{msg}(code={code})")
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1.5)
                continue
            raise

def download_via_ssstik(vid):
    post_data = urllib.parse.urlencode({'id': vid, 'locale': 'en', 'tt': 'UlRiVmRlNzZjT3Zs'}).encode()
    req = urllib.request.Request('https://www.ssstik.io/abc', data=post_data)
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    req.add_header("Accept", "text/html,application/xhtml+xml")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("Origin", "https://www.ssstik.io")
    req.add_header("Referer", "https://www.ssstik.io/")
    r = urllib.request.urlopen(req, timeout=30)
    html = r.read().decode('utf-8', errors='ignore')
    match = re.search(r'href="(https?://[^"]+tiktok[^"]+)"[^>]*>.*?Download</a>', html, re.I)
    if not match:
        match = re.search(r'(https?://[^"\'\\]+\.mp4[^"\'\\]*)', html)
    if match:
        return match.group(1).split('"')[0].split("'")[0]
    raise Exception("ssstik解析失败")

def download_via_snaptik(vid):
    """备用下载源:SnapTik"""
    api_url = "https://snaptik.app/api.php?url=" + urllib.parse.quote("https://www.tiktok.com/@a/video/" + vid)
    req = urllib.request.Request(api_url)
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    req.add_header("Referer", "https://snaptik.app/")
    r = urllib.request.urlopen(req, timeout=30)
    d = json.loads(r.read())
    if d.get("status") == "ok" or d.get("code") == 0:
        url = d.get("url", "") or d.get("data", {}).get("url", "")
        if url:
            return url
    raise Exception("snaptik解析失败")

def download_video(url):
    url = url.strip()
    short = [r'vm\.tiktok\.com', r'vt\.tiktok\.com', r'tiktok\.com/t/']
    if any(re.search(p, url) for p in short):
        resolved = resolve_short_url(url)
        if not resolved or '/video/' not in resolved:
            raise Exception("⚠️ 短链接无法解析,请在浏览器打开后复制完整视频链接")
        url = resolved
    vid = get_video_id(url)
    if not vid:
        raise Exception("❌ 未找到视频ID,请确保粘贴的是完整视频链接")
    out = Path(config.VIDEO_OUTPUT_DIR)
    out.mkdir(exist_ok=True)
    p = out / "input_video.mp4"
    dl_url = None
    errors = []
    for name, fn in [("tikwm", download_via_tikwm), ("ssstik", download_via_ssstik), ("snaptik", download_via_snaptik)]:
        try:
            dl_url = fn(vid)
            if dl_url:
                break
        except Exception as e:
            errors.append(f"{name}:{e}")
    if not dl_url:
        raise Exception(f"下载失败。{';'.join(errors)}。请尝试:1上传视频文件 2稍后重试")
    if not dl_url:
        raise Exception("所有下载接口均失败,请尝试上传视频文件")
    req2 = urllib.request.Request(dl_url)
    req2.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    req2.add_header("Referer", "https://www.tikwm.com/")
    r2 = urllib.request.urlopen(req2, timeout=120)
    with open(p, "wb") as f:
        f.write(r2.read())
    return str(p), url

def extract_audio(vid_path):
    audio = str(Path(vid_path).with_suffix('.mp3'))
    subprocess.run(['ffmpeg', '-y', '-i', vid_path, '-vn', '-acodec', 'libmp3lame', '-q:a', '2', audio], capture_output=True, check=True)
    return audio

def transcribe(audio_path):
    import whisper
    # small 模型比 base 准确率高 7-10%,尤其对口音语音
    model = whisper.load_model("small")
    result = model.transcribe(
        audio_path,
        language=None,
        condition_on_previous_text=False,  # 防止错误传播
        compression_ratio_threshold=2.4,     # 过滤幻觉片段
        no_speech_threshold=0.6,              # 跳过静音段
        log_prob_threshold=-1.0,              # 过滤低置信度
    )
    return result.get("text", ""), result.get("language", "unknown")

def get_video_duration(vid_path):
    """获取视频时长(秒)"""
    result = subprocess.run(
        ['ffmpeg', '-i', vid_path],
        capture_output=True, text=True, errors='ignore'
    )
    output = result.stderr + result.stdout
    m = re.search(r'Duration: (\d+):(\d+):(\d+)', output)
    if m:
        h, mn, s = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return h * 3600 + mn * 60 + s
    return 60  # 默认60秒

def extract_video_frames(vid_path, num_frames=6):
    """从视频中均匀抽取帧,返回base64编码的图片数据列表"""
    duration = get_video_duration(vid_path)
    frames = []
    tmp_dir = tempfile.gettempdir()

    # 均匀抽取时间点
    timestamps = [duration * i / (num_frames + 1) for i in range(1, num_frames + 1)]

    for i, ts in enumerate(timestamps):
        tmp_file = os.path.join(tmp_dir, f'frame_{int(ts)}s_{i}.jpg')
        r = subprocess.run(
            ['ffmpeg', '-y', '-ss', str(ts), '-i', vid_path,
             '-frames:v', '1', '-q:v', '2', '-s', '720x1280', tmp_file],
            capture_output=True, errors='ignore'
        )
        if os.path.exists(tmp_file) and os.path.getsize(tmp_file) > 5000:
            with open(tmp_file, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode('utf-8')
            frames.append(b64)
        try:
            os.remove(tmp_file)
        except:
            pass

    return frames

def extract_text_from_frames(frames_b64, api_key):
    """
    当前 API Key 不支持 MiniMax 视觉模型(VL-01 需自行部署)
    保留接口但返回空,走纯 Whisper 路径
    """
    return ""

def call_llm_api(prompt, api_key, model_name, api_base=None):
    """统一 LLM 调用入口,根据模型名路由到对应 provider"""
    # 智谱 GLM 系列
    if model_name.startswith("glm-"):
        zhipu_key = api_key or config.ZHIPU_API_KEY
        zhipu_base = api_base or config.ZHIPU_API_BASE
        data = json.dumps({
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 3000
        }).encode()
        req = urllib.request.Request(f"{zhipu_base}/chat/completions", data=data)
        req.add_header("Authorization", "Bearer " + zhipu_key)
        req.add_header("Content-Type", "application/json")
        r = urllib.request.urlopen(req, timeout=120)
        resp = json.loads(r.read())
        msg = resp["choices"][0]["message"]
        # GLM-5 系列内容在 reasoning_content,普通 GLM 在 content
        content = msg.get("content") or msg.get("reasoning_content", "")
        return content

    # MiniMax 系列(默认)
    minimax_base = api_base or config.API_BASE
    data = json.dumps({
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 3000,
        "extra_body": {"thinking": {"type": "off"}}
    }).encode()
    req = urllib.request.Request(f"{minimax_base}/chat/completions", data=data)
    req.add_header("Authorization", "Bearer " + api_key)
    req.add_header("Content-Type", "application/json")
    r = urllib.request.urlopen(req, timeout=120)
    resp = json.loads(r.read())
    return resp["choices"][0]["message"]["content"]


def analyze(whisper_transcript, vision_text, lang, api_key, market, model_name="MiniMax-M2.7", api_base=None):
    market_info = MARKETS.get(market, MARKETS["🇵🇭 菲律宾"])
    market_context = market_info["context"]
    lang_hint = market_info["lang_hint"]

    # 根据是否有画面文字,选择不同的prompt
    if vision_text and not vision_text.startswith("["):
        # 双通道模式:Whisper + 视觉
        prompt = f"""你是一位精通东南亚多语言的TikTok视频脚本翻译专家。

【目标市场】{market_context}
【语言特点】{lang_hint}

【语音转文字结果】
{whisper_transcript}

【视频画面中的文字】
{vision_text}

请综合语音和画面文字,还原最准确的原文:
1. 台词以语音为准,但品牌名/产品名优先采用画面文字
2. 画面中字幕内容也纳入原文
3. 如果语音和画面冲突,以画面为准

然后翻译成通顺流畅的中文。

最后选出3个最能体现视频效果的亮点原句。

亮点标准:强力开场钩子 / 有效卖点 / 情绪调动 / 受众共鸣 / 行动号召

严格按JSON输出:
{{
  "original": "还原后的完整原文(连贯段落)",
  "translation": "完整中文翻译(连贯段落)",
  "highlights": [
    {{"original_sentence": "亮点原句", "sentence_translation": "中文翻译", "why": "为什么是亮点"}},
    {{"original_sentence": "亮点原句", "sentence_translation": "中文翻译", "why": "为什么是亮点"}},
    {{"original_sentence": "亮点原句", "sentence_translation": "中文翻译", "why": "为什么是亮点"}}
  ]
}}"""
    else:
        # 纯Whisper模式：只用语音转录，但加领域知识辅助校验
        prompt = f"""你是一位在菲律宾生活10年的华人编导，精通他加禄语、英语和中文，熟悉菲律宾TikTok带货视频的所有套路。

【目标市场】{market_context}
【语言特点】{lang_hint}

【语音转文字结果（Whisper转录，可能有些词听错）】
{whisper_transcript}

⚠️ 重要提醒：Whisper 转录常见错误
1. 品牌名/产品名最容易听错（如把 Dojoso 听成 Chanmo）
2. 菲律宾口音重，"肚子大" 可能听成 "浓到" 之类的错误
3. 语速快时漏字或错字
4. 背景噪音干扰

【菲律宾咖啡品牌库（听到类似发音优先匹配）】
Dojoso、Kopiko 3in1、Great Taste 3in1、Nescafe、San Mig Coffee、Boost Coffee、Barako、Kape、Figaro、Benguet、Lamudi、Kape Barako

【菲律宾零食品牌库】
7D、Cebu、Oishi、Regent、Chippy、Piattos、Nova、Vcut、Clover、La Pacita、Merzci、BongBong's

【常见他加禄语词】
Masarap(好吃)、Sulit(超值)、Ang sarap(太好吃了)、Presyo(价格)、Libre(免费)、Pwede na(还行)、Kuya(哥)、Ate(姐)、Bes(姐妹)、Guys(家人们)

【语义校验规则】
- "怀孕" + "咖啡" → 应该是 "瘦肚子/减肥/大肚子" 相关（减肥咖啡广告常见套路）
- "浓到/甜到" + 奇怪比喻 → 可能是 "肚子大到..." 的误听
- 语义不通时，优先按 "减肥/瘦肚子/黑咖啡" 方向理解

请你完成以下任务：

第一步：理解视频内容（先不写输出，只在脑中分析）
- 这是什么类型的视频？（减肥咖啡/零食/其他）
- 核心卖点是什么？（瘦肚子？好喝？便宜？）
- 目标受众是谁？（想减肥的女性？学生？上班族？）
- 主播用了什么套路？（痛点共鸣→产品介绍→效果证明→行动号召）

第二步：还原准确原文
- 根据上下文和品牌库，修正 Whisper 的错误识别
- 品牌名如果确定就写正确品牌名，不确定加⟨?⟩标记
- 语义不通的句子，按视频类型重新理解修正
- 保留原文语言（他加禄语+英语），不要翻译
- 输出连贯的原文段落

第三步：翻译成地道中文（不要直译！要像中国带货主播说的话）
- 先理解意思，再用中文自然表达
- 口语化！像抖音/快手主播的说话风格
- "Guys/Bes/Mga sis" → "家人们/姐妹们/老铁"
- "Sulit" → "超值/划算/白菜价"
- "Masarap" → "巨好吃/香迷糊了"
- 品牌名保留英文或音译
- 价格保留原货币，可括号标注人民币约价
- 禁止凭空添加内容
- 输出流畅的中文段落，不要逐句对应

第四步：选3个最能体现视频效果的亮点原句
亮点标准：强力开场钩子 / 有效卖点 / 情绪调动 / 受众共鸣 / 行动号召

严格按JSON输出：
{{
  "original": "还原后的完整原文（连贯段落，保留原语言）",
  "translation": "地道中文翻译（连贯段落，口语化，像中国带货主播）",
  "highlights": [
    {{"original_sentence": "亮点原句", "sentence_translation": "中文翻译", "why": "为什么是亮点"}},
    {{"original_sentence": "亮点原句", "sentence_translation": "中文翻译", "why": "为什么是亮点"}},
    {{"original_sentence": "亮点原句", "sentence_translation": "中文翻译", "why": "为什么是亮点"}}
  ]
}}"""

    content = call_llm_api(prompt, api_key, model_name, api_base)

    for start in range(len(content)):
        if content[start] == '{':
            depth = 0
            end = start
            for i, ch in enumerate(content[start:], start):
                if ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
            try:
                result = json.loads(content[start:end+1])
                if "original" in result and "translation" in result and "highlights" in result:
                    return result
            except json.JSONDecodeError:
                continue
    return None

# ==============================================================================
# Streamlit 界面
# ==============================================================================

st.markdown('<h1>🎬 TK 视频分析器</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Whisper small 语音转录 + 品牌名校验 + 智能翻译</p>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ 设置")
    market = st.selectbox("📍 目标市场", list(MARKETS.keys()), index=0)

    st.subheader("🔑 API 配置")
    provider = st.selectbox("AI 厂商", ["MiniMax", "智谱 GLM"], index=0)

    if provider == "MiniMax":
        api_key = st.text_input("MiniMax API Key", type="password", key="api_key_input", placeholder="输入 Key")
        model_name = st.selectbox("🤖 模型", ["MiniMax-M2.7", "MiniMax-Text-01"], index=0)
        api_base = None
    else:
        api_key = st.text_input("智谱 API Key", type="password", key="zhipu_key_input", placeholder="输入 Key")
        model_name = st.selectbox("🤖 模型", ["glm-5.1", "glm-5-turbo", "glm-5", "glm-4.7"], index=0)
        api_base = config.ZHIPU_API_BASE

    st.markdown("""
    <div class="info-box">
    <b>工作原理:</b><br>
    1. Whisper small 转录音频台词<br>
    2. AI 根据领域知识校验品牌名<br>
    3. 翻译为通顺中文 + 提取亮点
    </div>
    """, unsafe_allow_html=True)

st.markdown("## 📥 输入视频")

input_method = st.radio("输入方式", ["🔗 TikTok 链接", "📁 上传视频"], horizontal=True)

video_path = None
url_input = ""

if input_method == "🔗 TikTok 链接":
    url_input = st.text_input("TikTok 链接", placeholder="https://www.tiktok.com/@用户名/video/数字ID", label_visibility="collapsed")

    if url_input and url_input != st.session_state.current_url:
        st.session_state.result = None
        st.session_state.current_url = url_input
    if market != st.session_state.current_market:
        st.session_state.result = None
        st.session_state.current_market = market

    if url_input:
        with st.spinner("下载中(可能需要10-30秒)..."):
            try:
                video_path, final_url = download_video(url_input)
                st.session_state.current_url = final_url
                st.session_state.video_path = video_path
                st.success("✅ 下载成功")
            except Exception as e:
                st.error(f"❌ {str(e)}")
else:
    uploaded = st.file_uploader("上传视频", type=["mp4", "mov", "avi", "webm"], label_visibility="collapsed")
    if uploaded:
        st.session_state.result = None
        tmp = Path(config.VIDEO_OUTPUT_DIR)
        tmp.mkdir(exist_ok=True)
        p = tmp / "input_video.mp4"
        with open(p, "wb") as f:
            f.write(uploaded.read())
        video_path = str(p)
        st.session_state.video_path = video_path
        st.success("✅ 上传成功")

if video_path and st.button("🚀 开始分析"):
    if not api_key:
        st.error("请先填写 MiniMax API Key")
        st.stop()

    with st.spinner("🔊 第一步:Whisper转录音频..."):
        try:
            audio = extract_audio(video_path)
            whisper_transcript, lang = transcribe(audio)
            if not whisper_transcript or len(whisper_transcript.strip()) < 3:
                st.error("❌ 音频转录失败,视频可能无声音,请尝试上传视频文件")
                st.stop()
            st.session_state.whisper_transcript = whisper_transcript
            st.session_state.detected_lang = lang
        except Exception as e:
            st.error(f"❌ 转录失败:{str(e)}")
            st.stop()

    with st.spinner("📸 第二步:检查画面文字..."):
        try:
            frames = extract_video_frames(video_path, num_frames=6)
            vision_text = extract_text_from_frames(frames, api_key)
            st.session_state.vision_text = vision_text
            if vision_text:
                st.success("✅ 画面文字识别成功")
            else:
                st.info("i️ 当前仅使用语音转录(视觉识别待接入)")
        except Exception as e:
            st.session_state.vision_text = ""
            st.info("i️ 当前仅使用语音转录")

    with st.spinner("🧠 第三步:合并分析 + 翻译..."):
        try:
            result = analyze(
                st.session_state.whisper_transcript,
                st.session_state.vision_text,
                st.session_state.detected_lang,
                api_key, market, model_name, api_base
            )
            if result:
                st.session_state.result = result
                st.success("✅ 分析完成!")
            else:
                st.error("❌ AI分析失败,请检查API Key或重试")
        except Exception as e:
            st.error(f"❌ 分析失败:{str(e)}")

# ===== 视频下载按钮 =====
if st.session_state.get('video_path'):
    vp = st.session_state.video_path
    if Path(vp).exists():
        with open(vp, 'rb') as f:
            video_bytes = f.read()
        vid = get_video_id(st.session_state.get('current_url', '')) or 'tiktok_video'
        st.download_button(
            label="💾 保存视频到本地",
            data=video_bytes,
            file_name=f"tiktok_{vid}.mp4",
            mime="video/mp4",
            use_container_width=True
        )

# ===== 显示中间结果(Whisper + 视觉识别)=====
if st.session_state.get('whisper_transcript'):
    with st.expander("🔊 Whisper音频转录(原始)", expanded=False):
        st.text(whisper_transcript := st.session_state.whisper_transcript)
        st.caption(f"检测语言:{st.session_state.get('detected_lang', 'unknown')}")

if st.session_state.get('vision_text'):
    with st.expander("📸 画面文字识别(MiniMax视觉)", expanded=False):
        st.text(st.session_state.vision_text)

# ===== 显示最终结果 =====
if st.session_state.get('result'):
    r = st.session_state.result

    st.markdown("---")
    st.markdown("## 📊 翻译与分析结果")

    original_text = r.get("original", "")
    translation_text = r.get("translation", "")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📝 还原原文")
        st.markdown(f'<div class="text-block" style="border-left:2px solid #ff0050;">{original_text}</div>', unsafe_allow_html=True)
    with col2:
        st.markdown("### 🇨🇳 中文翻译")
        st.markdown(f'<div class="text-block" style="border-left:2px solid #00f2ea;">{translation_text}</div>', unsafe_allow_html=True)

    highs = r.get("highlights", [])
    if highs:
        st.markdown("### ✨ 亮点分析")
        for i, h in enumerate(highs, 1):
            orig = h.get("original_sentence", "")
            trans_h = h.get("sentence_translation", "")
            why = h.get("why", "")
            st.markdown(f"""
            <div class="highlight-item">
                <div style="margin-bottom:0.8rem;color:#ff0050;font-weight:700;">✨ 亮点 {i}</div>
                <div class="section-label">原文原句</div>
                <div class="text-block" style="border-left:2px solid #ff0050;">{orig}</div>
                <div class="section-label">中文翻译</div>
                <div class="text-block" style="border-left:2px solid #00f2ea;">{trans_h}</div>
                <div style="color:#888;font-size:0.85rem;margin-top:0.3rem;">💡 {why}</div>
            </div>
            """, unsafe_allow_html=True)
