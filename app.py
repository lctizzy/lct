# -*- coding: utf-8 -*-
"""
TK 批量下载器 - 极简版
"""

import streamlit as st
import os

st.set_page_config(page_title="TK 批量下载器", page_icon="📥")

st.title("📥 TK 批量下载器")

ids = st.text_area("视频ID（每行一个）", height=300, placeholder="7382910483728391829\n7456789012345678901")

if st.button("📥 下载", type="primary", use_container_width=True):
    if not ids.strip():
        st.stop()
    
    lines = [l.strip() for l in ids.split("\n") if l.strip()]
    
    for i, vid in enumerate(lines):
        # 提取ID
        if "/video/" in vid:
            vid = vid.split("/video/")[-1].split("?")[0]
        
        try:
            import yt_dlp
            url = f"https://www.tiktok.com/@_/video/{vid}"
            
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
                info = ydl.extract_info(url, download=True)
                st.success(f"✅ {vid} → {ydl.prepare_filename(info)}")
        except Exception as e:
            st.error(f"❌ {vid}: {str(e)[:80]}")
