#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自媒体图文生成系统 - Web界面
基于Streamlit实现的本地Web应用
"""

import os
import sys
import json
import time
import glob
import zipfile
import subprocess
from datetime import datetime
from pathlib import Path

import streamlit as st

# 添加项目路径
项目目录 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, 项目目录)

# 页面配置
st.set_page_config(
    page_title="自媒体图文生成系统",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2c3e50;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .success-message {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.25rem;
        color: #155724;
    }
    .info-message {
        padding: 1rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 0.25rem;
        color: #0c5460;
    }
    .file-card {
        padding: 1rem;
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def get_output_folders():
    """获取输出文件夹路径"""
    return {
        '爬取的新闻': os.path.join(项目目录, '输出文件/爬取的新闻'),
        '热点分析报告': os.path.join(项目目录, '输出文件/热点分析报告'),
        '文生图提示词': os.path.join(项目目录, '输出文件/文生图提示词'),
        '生成的图片': os.path.join(项目目录, '输出文件/生成的图片'),
        '自媒体内容': os.path.join(项目目录, '输出文件/自媒体内容')
    }


def get_latest_files(folder_path, pattern='*'):
    """获取文件夹中最新的文件"""
    if not os.path.exists(folder_path):
        return []
    
    files = glob.glob(os.path.join(folder_path, pattern))
    if not files:
        return []
    
    # 按修改时间排序，最新的在前
    files.sort(key=os.path.getmtime, reverse=True)
    return files


def read_file_content(file_path):
    """读取文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"读取文件失败: {str(e)}"


def run_generation_process():
    """运行生成过程"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # 步骤1: 爬取新闻
        status_text.text("📰 步骤1: 正在爬取国际热点新闻...")
        progress_bar.progress(10)
        
        爬虫路径 = os.path.join(项目目录, '核心模块/新闻爬虫.py')
        result = subprocess.run(
            [sys.executable, 爬虫路径],
            cwd=项目目录,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode != 0:
            st.error(f"新闻爬取失败: {result.stderr}")
            return False
        
        progress_bar.progress(20)
        status_text.text("✅ 新闻爬取完成")
        time.sleep(0.5)
        
        # 步骤2: AI分析
        status_text.text("🤖 步骤2: 正在进行AI深度分析...")
        progress_bar.progress(30)
        
        分析器路径 = os.path.join(项目目录, '核心模块/新闻分析器.py')
        result = subprocess.run(
            [sys.executable, 分析器路径],
            cwd=项目目录,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode != 0:
            st.error(f"AI分析失败: {result.stderr}")
            return False
        
        progress_bar.progress(50)
        status_text.text("✅ AI分析完成")
        time.sleep(0.5)
        
        # 步骤3-5: 运行主控制器
        status_text.text("🎨 步骤3-5: 正在生成提示词、图片和自媒体内容...")
        progress_bar.progress(60)
        
        主控制器路径 = os.path.join(项目目录, '核心模块/主控制器.py')
        result = subprocess.run(
            [sys.executable, '-c', f'''
import sys
sys.path.insert(0, "{项目目录}")
from 核心模块.主控制器 import 自媒体内容生成器
生成器 = 自媒体内容生成器()
生成器.运行完整工作流()
'''],
            cwd=项目目录,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode != 0:
            st.error(f"内容生成失败: {result.stderr}")
            return False
        
        progress_bar.progress(90)
        status_text.text("✅ 内容生成完成")
        time.sleep(0.5)
        
        progress_bar.progress(100)
        status_text.text("🎉 所有任务已完成！")
        
        return True
        
    except Exception as e:
        st.error(f"执行过程中出现错误: {str(e)}")
        return False


def display_markdown_file(file_path, title):
    """显示Markdown文件"""
    content = read_file_content(file_path)
    if content and not content.startswith("读取文件失败"):
        with st.expander(f"📄 {title}", expanded=False):
            st.markdown(content)
            st.download_button(
                label="📥 下载文件",
                data=content,
                file_name=os.path.basename(file_path),
                mime="text/markdown"
            )


def display_image_gallery(folder_path):
    """显示图片画廊"""
    if not os.path.exists(folder_path):
        st.info("暂无生成的图片")
        return
    
    # 查找所有图片文件
    image_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                image_files.append(os.path.join(root, file))
    
    if not image_files:
        st.info("暂无生成的图片")
        return
    
    # 按修改时间排序
    image_files.sort(key=os.path.getmtime, reverse=True)
    
    # 显示图片
    st.subheader("🖼️ 生成的图片")
    
    cols = st.columns(3)
    for idx, img_path in enumerate(image_files[:9]):  # 最多显示9张
        col = cols[idx % 3]
        with col:
            try:
                st.image(img_path, caption=os.path.basename(img_path), use_container_width=True)
                
                # 下载按钮
                with open(img_path, 'rb') as f:
                    img_data = f.read()
                st.download_button(
                    label="📥 下载图片",
                    data=img_data,
                    file_name=os.path.basename(img_path),
                    mime="image/jpeg",
                    key=f"download_img_{idx}"
                )
            except Exception as e:
                st.error(f"无法显示图片: {str(e)}")


def create_zip_download():
    """创建打包下载"""
    输出文件夹 = get_output_folders()
    
    # 创建临时zip文件
    zip_path = os.path.join(项目目录, '输出文件_打包.zip')
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for folder_name, folder_path in 输出文件夹.items():
            if os.path.exists(folder_path):
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.join(folder_name, os.path.relpath(file_path, folder_path))
                        zipf.write(file_path, arcname)
    
    return zip_path


def main():
    """主函数"""
    # 标题
    st.markdown('<h1 class="main-header">🚀 自媒体图文生成系统</h1>', unsafe_allow_html=True)
    
    # 侧边栏 - 配置管理
    with st.sidebar:
        st.header("⚙️ 配置管理")
        
        # 检查配置文件
        config_path = os.path.join(项目目录, 'config.json')
        if os.path.exists(config_path):
            st.success("✅ 配置文件已存在")
            
            # 显示配置信息
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                st.info(f"DeepSeek API: {'已配置' if config.get('deepseek', {}).get('api_key') else '未配置'}")
                st.info(f"Coze API: {'已配置' if config.get('coze', {}).get('api_url') else '未配置'}")
            except:
                st.warning("配置文件格式错误")
        else:
            st.warning("⚠️ 配置文件不存在")
            st.info("请先创建config.json文件")
        
        st.divider()
        
        # 使用说明
        st.header("📖 使用说明")
        st.markdown("""
        1. 点击"开始生成"按钮
        2. 等待系统完成所有步骤
        3. 查看生成的文件
        4. 下载需要的内容
        """)
        
        st.divider()
        
        # 关于
        st.header("ℹ️ 关于")
        st.markdown("""
        **自媒体图文生成系统**
        
        基于AI的自动化内容生成工具
        
        版本: 1.0.0
        作者: AI 坚果爱学AI
        """)
    
    # 主内容区域
    tab1, tab2, tab3 = st.tabs(["🚀 生成内容", "📊 查看输出", "📥 下载中心"])
    
    # Tab 1: 生成内容
    with tab1:
        st.header("内容生成")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 开始生成", type="primary", use_container_width=True):
                with st.spinner("正在生成内容，请稍候..."):
                    success = run_generation_process()
                    if success:
                        st.success("🎉 内容生成成功！请切换到'查看输出'标签查看结果。")
                        st.balloons()
                    else:
                        st.error("❌ 内容生成失败，请检查日志信息。")
        
        st.divider()
        
        # 显示最近生成状态
        st.subheader("📋 最近生成状态")
        输出文件夹 = get_output_folders()
        
        for folder_name, folder_path in 输出文件夹.items():
            files = get_latest_files(folder_path)
            if files:
                latest_file = files[0]
                mod_time = datetime.fromtimestamp(os.path.getmtime(latest_file))
                st.info(f"📁 {folder_name}: {len(files)} 个文件 (最新: {mod_time.strftime('%Y-%m-%d %H:%M:%S')})")
            else:
                st.warning(f"📁 {folder_name}: 暂无文件")
    
    # Tab 2: 查看输出
    with tab2:
        st.header("输出文件查看")
        
        输出文件夹 = get_output_folders()
        
        # 热点分析报告
        st.subheader("📊 热点分析报告")
        分析报告文件 = get_latest_files(输出文件夹['热点分析报告'], '*.md')
        if 分析报告文件:
            display_markdown_file(分析报告文件[0], os.path.basename(分析报告文件[0]))
        else:
            st.info("暂无热点分析报告")
        
        # 文生图提示词
        st.subheader("🎨 文生图提示词")
        提示词文件 = get_latest_files(输出文件夹['文生图提示词'], '*.md')
        if 提示词文件:
            display_markdown_file(提示词文件[0], os.path.basename(提示词文件[0]))
        else:
            st.info("暂无文生图提示词")
        
        # 自媒体内容
        st.subheader("📱 自媒体内容")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("##### 小红书")
            小红书文件 = get_latest_files(输出文件夹['自媒体内容'], '*小红书*.md')
            if 小红书文件:
                display_markdown_file(小红书文件[0], os.path.basename(小红书文件[0]))
            else:
                st.info("暂无小红书内容")
        
        with col2:
            st.markdown("##### 抖音")
            抖音文件 = get_latest_files(输出文件夹['自媒体内容'], '*抖音*.md')
            if 抖音文件:
                display_markdown_file(抖音文件[0], os.path.basename(抖音文件[0]))
            else:
                st.info("暂无抖音内容")
        
        with col3:
            st.markdown("##### 公众号")
            公众号文件 = get_latest_files(输出文件夹['自媒体内容'], '*公众号*.md')
            if 公众号文件:
                display_markdown_file(公众号文件[0], os.path.basename(公众号文件[0]))
            else:
                st.info("暂无公众号内容")
        
        # 生成的图片
        st.divider()
        display_image_gallery(输出文件夹['生成的图片'])
    
    # Tab 3: 下载中心
    with tab3:
        st.header("📥 下载中心")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📦 打包下载")
            st.info("下载所有生成的文件（包括报告、提示词、内容和图片）")
            
            if st.button("📥 打包下载所有文件", type="primary"):
                with st.spinner("正在打包文件..."):
                    try:
                        zip_path = create_zip_download()
                        with open(zip_path, 'rb') as f:
                            zip_data = f.read()
                        
                        st.download_button(
                            label="💾 点击下载压缩包",
                            data=zip_data,
                            file_name=f"自媒体内容_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                            mime="application/zip"
                        )
                        
                        # 清理临时文件
                        os.remove(zip_path)
                    except Exception as e:
                        st.error(f"打包失败: {str(e)}")
        
        with col2:
            st.subheader("📋 单独下载")
            输出文件夹 = get_output_folders()
            
            # 热点分析报告
            分析报告文件 = get_latest_files(输出文件夹['热点分析报告'], '*.md')
            if 分析报告文件:
                content = read_file_content(分析报告文件[0])
                st.download_button(
                    label="📊 下载热点分析报告",
                    data=content,
                    file_name=os.path.basename(分析报告文件[0]),
                    mime="text/markdown"
                )
            
            # 文生图提示词
            提示词文件 = get_latest_files(输出文件夹['文生图提示词'], '*.md')
            if 提示词文件:
                content = read_file_content(提示词文件[0])
                st.download_button(
                    label="🎨 下载文生图提示词",
                    data=content,
                    file_name=os.path.basename(提示词文件[0]),
                    mime="text/markdown"
                )
            
            # 自媒体内容
            小红书文件 = get_latest_files(输出文件夹['自媒体内容'], '*小红书*.md')
            if 小红书文件:
                content = read_file_content(小红书文件[0])
                st.download_button(
                    label="📱 下载小红书内容",
                    data=content,
                    file_name=os.path.basename(小红书文件[0]),
                    mime="text/markdown"
                )
            
            抖音文件 = get_latest_files(输出文件夹['自媒体内容'], '*抖音*.md')
            if 抖音文件:
                content = read_file_content(抖音文件[0])
                st.download_button(
                    label="📱 下载抖音内容",
                    data=content,
                    file_name=os.path.basename(抖音文件[0]),
                    mime="text/markdown"
                )
            
            公众号文件 = get_latest_files(输出文件夹['自媒体内容'], '*公众号*.md')
            if 公众号文件:
                content = read_file_content(公众号文件[0])
                st.download_button(
                    label="📱 下载公众号内容",
                    data=content,
                    file_name=os.path.basename(公众号文件[0]),
                    mime="text/markdown"
                )


if __name__ == "__main__":
    main()
