# -*- coding: utf-8 -*-
"""
TK 视频批量下载器 - 极简版
功能：批量下载 TikTok 视频（仅支持视频ID）
"""

import streamlit as st
import os
import tempfile
from pathlib import Path

st.set_page_config(page_title="TK 批量下载器", page_icon="📥")

st.markdown("""
<style>
.stApp { background-color: #0f172a; }
.stTextArea textarea { background-color: #1e293b !important; color: #f8fafc !important; border: 1px solid #334155 !important; }
.stButton > button { background-color: #3b82f6 !important; color: white !important; border-radius: 8px !important; font-size: 1.1rem !important; padding: 0.5rem 2rem !important; }
.stDownloadButton > button { background-color: #10b981 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

st.title("📥 TK 批量下载器")
st.caption("输入视频ID，每行一个，支持纯数字ID或完整TikTok链接")

# 视频ID输入
video_ids_input = st.text_area(
    "视频ID列表",
    placeholder="7382910483728391829\n7456789012345678901\nhttps://www.tiktok.com/@user/video/1234567890",
    height=200
)

# 输出目录
output_dir = st.text_input("保存目录", value=tempfile.gettempdir())

# 下载按钮
if st.button("📥 开始下载", type="primary", use_container_width=True):
    if not video_ids_input.strip():
        st.error("❌ 请输入视频ID")
    else:
        ids = [id.strip() for id in video_ids_input.split("\n") if id.strip()]
        
        if not ids:
            st.error("❌ 未找到有效视频ID")
        else:
            st.success(f"准备下载 {len(ids)} 个视频")
            
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 进度条
            progress = st.progress(0)
            results = []
            
            for i, vid in enumerate(ids):
                progress.progress((i + 1) / len(ids), text=f"下载中 {i+1}/{len(ids)}")
                
                # 提取视频ID（如果是链接）
                import re
                match = re.search(r'/video/(\d+)', vid)
                if match:
                    vid = match.group(1)
                
                try:
                    import yt_dlp
                    
                    ydl_opts = {
                        'outtmpl': os.path.join(output_dir, '%(id)s.%(ext)s'),
                        'format': 'best[ext=mp4]/best',
                        'quiet': True,
                        'no_warnings': True,
                        'extract_flat': False,
                        # 模拟浏览器
                        'http_headers': {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        },
                    }
                    
                    url = f"https://www.tiktok.com/@_/video/{vid}"
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
                        filename = ydl.prepare_filename(info)
                        results.append({"id": vid, "status": "✅ 成功", "file": filename})
                        
                except Exception as e:
                    results.append({"id": vid, "status": f"❌ 失败", "error": str(e)[:50]})
            
            # 显示结果
            st.markdown("---")
            st.markdown("### 📊 下载结果")
            
            for r in results:
                if r["status"] == "✅ 成功":
                    st.success(f"{r['id']} → {r['file']}")
                else:
                    st.error(f"{r['id']} → {r['status']}: {r.get('error', '')}")
            
            # 统计
            success_count = sum(1 for r in results if r["status"] == "✅ 成功")
            st.info(f"✅ 成功: {success_count}/{len(results)}")
