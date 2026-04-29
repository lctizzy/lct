# -*- coding: utf-8 -*-
"""
TK 视频分析器 - 完整功能版
功能：TikTok 视频下载、Whisper 语音转录、品牌名校验、MiniMax 翻译/分析
"""

import streamlit as st
import subprocess
import os
import re
import tempfile
import hashlib
import time
from pathlib import Path
import requests
import json

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="TK 视频分析器",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== MiniMax API 调用 ====================

def minimax_translate(text: str, api_key: str, model: str = "MiniMax-Text-01") -> str:
    """调用 MiniMax API 进行翻译/分析"""
    if not api_key:
        return "[未配置 API Key]"
    
    url = "https://api.minimax.chat/v1/text/chatcompletion_pro"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "你是一个专业的跨境电商内容分析助手。请将以下TikTok视频语音转录内容翻译成英文，并标注检测到的所有品牌名称（如果有）。格式：\n翻译：[英文翻译]\n品牌：[品牌列表，无则写无]"
            },
            {
                "role": "user", 
                "content": text
            }
        ],
        "temperature": 0.3
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        if response.status_code == 200:
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "[解析失败]")
        elif response.status_code == 401:
            return "[API Key 无效]"
        elif response.status_code == 403:
            return "[无权限，请检查配额]"
        else:
            return f"[请求失败: {response.status_code}]"
    except requests.exceptions.Timeout:
        return "[请求超时]"
    except Exception as e:
        return f"[错误: {str(e)}]"


def minimax_analyze(text: str, api_key: str, model: str = "MiniMax-Text-01") -> str:
    """调用 MiniMax API 进行内容分析"""
    if not api_key:
        return "[未配置 API Key]"
    
    url = "https://api.minimax.chat/v1/text/chatcompletion_pro"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": """你是一个专业的TikTok内容分析师。请分析以下视频转录内容，返回：
1. 视频主要内容类型（种草/测评/剧情/娱乐等）
2. 目标受众（年龄/性别/兴趣）
3. 带货意图分析（强带货/弱带货/无带货）
4. 值得关注的营销亮点（1-3条）
5. 适合投放的产品类型建议

请用中文回复，格式清晰。"""
            },
            {
                "role": "user",
                "content": text
            }
        ],
        "temperature": 0.5
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=90)
        if response.status_code == 200:
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "[解析失败]")
        elif response.status_code == 401:
            return "[API Key 无效]"
        elif response.status_code == 403:
            return "[无权限，请检查配额]"
        else:
            return f"[请求失败: {response.status_code}]"
    except requests.exceptions.Timeout:
        return "[请求超时]"
    except Exception as e:
        return f"[错误: {str(e)}]"


# ==================== TikTok 视频下载 ====================

def extract_video_id(url_or_id: str) -> str:
    """从 TikTok URL 或直接输入提取视频 ID"""
    url_or_id = url_or_id.strip()
    
    # 直接是数字ID
    if url_or_id.isdigit():
        return url_or_id
    
    # 各种 TikTok URL 格式
    patterns = [
        r'/video/(\d+)',
        r'vm\.tiktok\.com/(\w+)',
        r'tiktok\.com/@[^/]+/video/(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    
    return url_or_id


def download_tiktok_video(url_or_id: str, output_dir: str = None) -> dict:
    """使用 yt-dlp Python API 下载 TikTok 视频"""
    video_id = extract_video_id(url_or_id)
    
    if not output_dir:
        output_dir = tempfile.gettempdir()
    
    # 直接使用原始 URL（如果是完整 URL）
    if url_or_id.startswith("http"):
        full_url = url_or_id
    else:
        # 如果只有视频 ID，构造标准 URL
        full_url = f"https://www.tiktok.com/@user/video/{video_id}"
    
    try:
        import yt_dlp
        
        output_template = os.path.join(output_dir, f"tk_{video_id}.%(ext)s")
        
        ydl_opts = {
            'format': 'best',
            'outtmpl': output_template,
            'noplaylist': True,
            'quiet': False,
            'no_warnings': False,
            'socket_timeout': 30,
            'retries': 3,
            # 添加 User-Agent 模拟浏览器
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.tiktok.com/',
            },
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ret = ydl.download([full_url])
        
        # 查找下载的文件
        files = list(Path(output_dir).glob(f"tk_{video_id}.*"))
        if files:
            return {"success": True, "path": str(files[0]), "video_id": video_id}
        
        # 尝试查找任何新下载的文件
        all_files = list(Path(output_dir).glob("*.*"))
        recent = [f for f in all_files if f.stat().st_mtime > (time.time() - 60)]
        if recent:
            return {"success": True, "path": str(recent[0]), "video_id": video_id}
        
        return {"success": False, "error": f"下载完成但未找到文件，返回码: {ret}"}
        
    except ImportError:
        return {"success": False, "error": "yt-dlp 未安装，请运行: pip install yt-dlp"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== Whisper 转录 ====================

def transcribe_audio(video_path: str, model_size: str = "small") -> dict:
    """使用 Whisper 本地模型进行语音转录"""
    try:
        import whisper
        
        # 尝试设置 ffmpeg 路径（多种方式）
        try:
            import imageio_ffmpeg
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            os.environ["FFMPEG_BINARY"] = ffmpeg_path
        except ImportError:
            # imageio-ffmpeg 不可用时，使用系统 ffmpeg
            # Streamlit Cloud 通过 packages.txt 安装了 ffmpeg
            pass
        
        model = whisper.load_model(model_size)
        
        result = model.transcribe(
            video_path,
            task="transcribe",
            verbose=False
        )
        
        return {
            "success": True,
            "text": result.get("text", "").strip(),
            "language": result.get("language", "unknown"),
            "segments": result.get("segments", [])
        }
    
    except ImportError as e:
        if "whisper" in str(e).lower():
            return {"success": False, "error": "Whisper 未安装，请运行: pip install openai-whisper"}
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== 批量下载（视频ID列表） ====================

def batch_download_videos(video_ids: str, output_dir: str = None) -> list:
    """批量下载多个 TikTok 视频"""
    if not output_dir:
        output_dir = tempfile.gettempdir()
    
    ids = [id.strip() for id in video_ids.split("\n") if id.strip()]
    results = []
    
    for vid in ids:
        st.info(f"📥 正在下载: {vid}")
        result = download_tiktok_video(vid, output_dir)
        results.append({
            "video_id": vid,
            **result
        })
    
    return results


# ==================== 自定义样式 ====================

st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
    }
    [data-testid="stSidebar"] {
        background-color: #1a1d24;
    }
    h1, h2, h3 {
        color: #ffffff !important;
    }
    .subtitle {
        color: #9ca3af;
        font-size: 1rem;
        margin-top: -0.5rem;
    }
    label {
        color: #9ca3af !important;
        font-size: 0.9rem !important;
    }
    .stSelectbox > div > div,
    .stTextInput > div > div > input,
    .stTextArea > div > textarea {
        background-color: #262730 !important;
        border: 1px solid #3d4049 !important;
        border-radius: 8px !important;
        color: #ffffff !important;
    }
    .stButton > button {
        background-color: #4f46e5 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 600 !important;
    }
    .stButton > button:hover {
        background-color: #6366f1 !important;
    }
    .stRadio > div {
        background-color: transparent !important;
    }
    .stRadio label {
        color: #ffffff !important;
    }
    hr {
        border-color: #3d4049 !important;
    }
    .main-header {
        text-align: center;
        padding: 2rem 0;
    }
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #ffffff;
    }
    .main-subtitle {
        font-size: 1rem;
        color: #9ca3af;
    }
    .input-section {
        background-color: #1a1d24;
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 1rem;
    }
    .result-box {
        background-color: #1a1d24;
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 1rem;
        border: 1px solid #3d4049;
    }
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1a1d24;
        border-radius: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #9ca3af !important;
    }
    .stTabs [aria-selected="true"] {
        color: #ffffff !important;
        border-bottom: 2px solid #4f46e5 !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stExpander {
        background-color: #1a1d24;
        border: 1px solid #3d4049;
        border-radius: 8px;
    }
    .stProgress > div > div {
        background-color: #4f46e5 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 侧边栏 ====================

with st.sidebar:
    st.markdown("### ⚙️ 设置")
    
    # 目标市场
    st.markdown("**📍 目标市场**")
    target_market = st.selectbox(
        "目标市场",
        ["🇵🇭 菲律宾", "🇺🇸 美国", "🇮🇩 印尼", "🇹🇭 泰国", "🇻🇳 越南", "🇸🇬 新加坡", "🇲🇾 马来西亚"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # API 配置
    st.markdown("**🔑 API 配置**")
    
    ai_provider = st.selectbox(
        "AI 厂商",
        ["MiniMax", "OpenAI", "Anthropic"],
        label_visibility="collapsed"
    )
    
    api_key = st.text_input(
        "API Key",
        type="password",
        placeholder="输入您的 API Key",
        label_visibility="collapsed"
    )
    
    model = st.selectbox(
        "模型",
        ["MiniMax-Text-01", "MiniMax-M2.7", "gpt-4o", "gpt-4o-mini"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Whisper 模型选择
    st.markdown("**🎤 Whisper 模型**")
    whisper_model = st.selectbox(
        "模型大小",
        ["small（推荐）", "base", "medium", "large"],
        label_visibility="collapsed"
    )
    whisper_model_size = whisper_model.split("（")[0].strip()
    
    st.markdown("---")
    
    # 输出目录
    st.markdown("**📁 下载目录**")
    output_dir = st.text_input(
        "保存路径",
        value=tempfile.gettempdir(),
        label_visibility="collapsed"
    )

# ==================== 主内容区 ====================

st.markdown("""
<div class="main-header">
    <div class="main-title">🎬 TK 视频分析器</div>
    <div class="main-subtitle">Whisper small 语音转录 + 品牌名校验 + 智能翻译</div>
</div>
""", unsafe_allow_html=True)

# 标签页
tab1, tab2 = st.tabs(["📊 单视频分析", "📥 批量下载"])

# ==================== 标签1：单视频分析 ====================

with tab1:
    st.markdown('<div class="input-section">', unsafe_allow_html=True)
    
    st.markdown("#### 📥 输入视频")
    
    input_method = st.radio(
        "输入方式",
        ["🔗 TikTok 链接", "📁 上传视频"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    if input_method == "🔗 TikTok 链接":
        tiktok_url = st.text_input(
            "TikTok 链接或视频ID",
            placeholder="https://www.tiktok.com/@用户名/video/123456789 或直接输入视频ID",
            label_visibility="collapsed"
        )
    else:
        uploaded_file = st.file_uploader(
            "上传视频文件",
            type=['mp4', 'mov', 'avi', 'mkv', 'webm'],
            label_visibility="collapsed"
        )
    
    col_analysis, col_clear = st.columns([1, 3])
    with col_analysis:
        start_analysis = st.button("🚀 开始分析", type="primary", use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 分析流程
    if start_analysis:
        video_path = None
        
        if input_method == "🔗 TikTok 链接":
            if not tiktok_url:
                st.error("❌ 请输入 TikTok 链接或视频ID")
            else:
                with st.spinner("📥 正在下载视频..."):
                    dl_result = download_tiktok_video(tiktok_url, output_dir)
                
                if not dl_result["success"]:
                    st.error(f"❌ 下载失败: {dl_result.get('error', '未知错误')}")
                else:
                    video_path = dl_result["path"]
                    st.success(f"✅ 视频下载成功: {os.path.basename(video_path)}")
        
        else:  # 上传视频
            if uploaded_file is None:
                st.error("❌ 请上传视频文件")
            else:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4', dir=output_dir) as f:
                    f.write(uploaded_file.getvalue())
                    video_path = f.name
                st.success(f"✅ 视频已上传: {uploaded_file.name}")
        
        if video_path and os.path.exists(video_path):
            # 步骤1：Whisper 转录
            st.markdown("---")
            st.markdown("#### 🎤 语音转录中...")
            
            with st.spinner(f"🤖 使用 Whisper {whisper_model_size} 模型转录，请耐心等待..."):
                transcribe_result = transcribe_audio(video_path, whisper_model_size)
            
            if not transcribe_result["success"]:
                st.error(f"❌ 转录失败: {transcribe_result.get('error')}")
            else:
                transcript_text = transcribe_result["text"]
                detected_lang = transcribe_result.get("language", "unknown")
                
                st.success(f"✅ 转录完成（语言: {detected_lang}）")
                st.markdown(f"**📝 转录内容：**")
                st.info(transcript_text if transcript_text else "[未检测到语音]")
                
                if transcript_text:
                    # 步骤2：MiniMax 翻译 + 品牌检测
                    st.markdown("---")
                    st.markdown("#### 🌐 翻译 & 品牌检测")
                    
                    if not api_key:
                        st.warning("⚠️ 未配置 API Key，跳过翻译和品牌检测")
                    else:
                        with st.spinner("🔄 MiniMax 分析中..."):
                            translation = minimax_translate(transcript_text, api_key, model)
                        
                        st.markdown("**翻译 & 品牌分析结果：**")
                        st.info(translation)
                        
                        # 步骤3：内容分析
                        st.markdown("---")
                        st.markdown("#### 📊 内容分析")
                        
                        with st.spinner("🔄 MiniMax 内容分析中..."):
                            analysis = minimax_analyze(transcript_text, api_key, model)
                        
                        st.markdown("**内容分析结果：**")
                        st.info(analysis)
                
                # 清理临时文件
                try:
                    if input_method == "🔗 TikTok 链接":
                        os.remove(video_path)
                except:
                    pass

# ==================== 标签2：批量下载 ====================

with tab2:
    st.markdown('<div class="input-section">', unsafe_allow_html=True)
    
    st.markdown("#### 📥 批量下载视频")
    st.caption("输入视频ID，每行一个（支持直接输入数字ID或完整TikTok链接）")
    
    video_ids_input = st.text_area(
        "视频ID列表",
        placeholder="7382910483728391829\n7456789012345678901\nhttps://www.tiktok.com/@user/video/1234567890",
        height=200,
        label_visibility="collapsed"
    )
    
    col_batch, col_clear2 = st.columns([1, 3])
    with col_batch:
        start_batch = st.button("📥 开始批量下载", type="primary", use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if start_batch and video_ids_input:
        ids = [id.strip() for id in video_ids_input.split("\n") if id.strip()]
        
        if not ids:
            st.error("❌ 请输入至少一个视频ID")
        else:
            st.success(f"📋 准备下载 {len(ids)} 个视频")
            
            progress_bar = st.progress(0)
            results = []
            
            for i, vid in enumerate(ids):
                progress_bar.progress((i + 1) / len(ids), text=f"下载中 {i+1}/{len(ids)}: {vid}")
                
                result = download_tiktok_video(vid, output_dir)
                results.append({
                    "video_id": vid,
                    "status": "✅ 成功" if result["success"] else "❌ 失败",
                    "path": result.get("path", ""),
                    "error": result.get("error", "")
                })
            
            progress_bar.empty()
            
            # 显示结果
            st.markdown("#### 📊 下载结果")
            
            success_count = sum(1 for r in results if "成功" in r["status"])
            st.success(f"✅ 完成：{success_count}/{len(ids)} 个视频下载成功")
            
            for r in results:
                if "成功" in r["status"]:
                    st.write(f"✅ {r['video_id']} → {os.path.basename(r['path'])}")
                else:
                    st.write(f"❌ {r['video_id']} → {r['error']}")

# ==================== 底部 ====================

st.markdown("---")
st.caption("💡 提示：首次使用 Whisper 转录会自动下载模型（约几百MB）。视频分析需要 MiniMax API Key。")