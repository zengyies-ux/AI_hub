#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻爬虫模块 - 爬取国际新闻
支持动态网页渲染（使用Playwright）
"""

import os
import re
import json
import time
import random
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 尝试导入Playwright（如果可用）
try:
    from playwright.sync_api import sync_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  Playwright未安装，动态网页爬取功能将不可用")
    print("   安装方法: pip install playwright && playwright install chromium")

# 尝试导入fake-useragent（如果可用）
try:
    from fake_useragent import UserAgent
    UA_AVAILABLE = True
except ImportError:
    UA_AVAILABLE = False


class 新闻文章:
    """新闻文章类"""
    def __init__(self, 标题: str, 链接: str = "", 内容: str = "", 来源: str = ""):
        self.标题 = 标题
        self.链接 = 链接
        self.内容 = 内容
        self.来源 = 来源
        self.关键词 = []
    
    def __repr__(self):
        return f"新闻文章(标题='{self.标题[:30]}...', 来源='{self.来源}')"
    
    def 转为字典(self) -> Dict:
        return {
            '标题': self.标题,
            '链接': self.链接,
            '内容': self.内容,
            '来源': self.来源
        }


class 新闻爬虫:
    """新闻爬虫类"""
    
    def __init__(self):
        self.会话 = requests.Session()
        self.会话.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'DNT': '1',
        })
        
        # 初始化UserAgent
        self.ua = None
        if UA_AVAILABLE:
            try:
                self.ua = UserAgent()
            except:
                self.ua = None
        else:
            self.ua = None
        
        # 更新用户代理
        self._更新用户代理()
        
        # 初始化Playwright
        self.playwright = None
        self.browser = None
        if PLAYWRIGHT_AVAILABLE:
            try:
                self.playwright = sync_playwright().start()
                self.browser = self.playwright.chromium.launch(headless=True)
                print("✅ Playwright浏览器已启动")
            except Exception as e:
                print(f"⚠️  Playwright初始化失败: {e}")
                self.playwright = None
                self.browser = None
    
    def _更新用户代理(self):
        """随机更新User-Agent"""
        if self.ua:
            try:
                self.会话.headers['User-Agent'] = self.ua.random
                return
            except:
                pass
        
        # 备用方案：使用预设列表
        用户代理列表 = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        self.会话.headers['User-Agent'] = random.choice(用户代理列表)
    
    def _随机延迟(self, 最小延迟=1, 最大延迟=3):
        """随机延迟"""
        time.sleep(random.uniform(最小延迟, 最大延迟))
    
    def _带重试请求(self, 网址: str, 最大重试次数: int = 3) -> requests.Response:
        """带重试机制的请求"""
        for 尝试次数 in range(最大重试次数):
            try:
                self._更新用户代理()
                self._随机延迟()
                
                响应 = self.会话.get(
                    网址,
                    timeout=20,
                    allow_redirects=True,
                    verify=False
                )
                响应.raise_for_status()
                return 响应
                
            except requests.exceptions.RequestException as 错误:
                if 尝试次数 < 最大重试次数 - 1:
                    等待时间 = random.uniform(2, 5)
                    time.sleep(等待时间)
                    continue
                raise
        
        raise requests.exceptions.RequestException(f"Failed after {最大重试次数} attempts")
    
    def _使用Playwright爬取(self, 网址: str, 等待时间: int = 3) -> Optional[str]:
        """使用Playwright爬取动态网页"""
        if not self.browser:
            return None
        
        try:
            page = self.browser.new_page()
            
            # 设置随机User-Agent
            if self.ua:
                try:
                    page.set_extra_http_headers({'User-Agent': self.ua.random})
                except:
                    pass
            
            # 访问页面
            page.goto(网址, wait_until='networkidle', timeout=30000)
            
            # 等待页面加载
            time.sleep(等待时间)
            
            # 获取页面HTML
            html_content = page.content()
            
            # 关闭页面
            page.close()
            
            return html_content
            
        except Exception as 错误:
            print(f"   Playwright爬取失败: {str(错误)[:50]}")
            return None
    
    def _提取文章正文(self, 网址: str, 来源: str) -> str:
        """提取新闻正文内容"""
        try:
            响应 = self._带重试请求(网址)
            响应.encoding = 'utf-8'
            汤 = BeautifulSoup(响应.text, 'html.parser')
            
            内容 = ""
            
            # 根据不同来源使用不同的选择器
            if 来源 == '新浪':
                选择器列表 = ['#article_content', '.article-content', '#artibody', '.main-content']
            elif 来源 == '网易':
                选择器列表 = ['.post_content', '.post-body', '#content', '.article-content']
            elif 来源 == '腾讯':
                选择器列表 = ['.content-article', '#article_content', '.article-content', '.main-content']
            elif 来源 == '百度':
                选择器列表 = ['.article-content', '#article', '.content', '.main-content']
            else:
                选择器列表 = ['article', '.article', '.content', '.main-content', '#content']
            
            for 选择器 in 选择器列表:
                内容元素 = 汤.select_one(选择器)
                if 内容元素:
                    # 提取文本，移除脚本和样式
                    for 脚本 in 内容元素.find_all(['script', 'style']):
                        脚本.decompose()
                    内容 = 内容元素.get_text(separator='\n', strip=True)
                    if len(内容) > 100:
                        break
            
            # 清理内容
            内容 = re.sub(r'\n+', '\n', 内容)
            内容 = re.sub(r'\s+', ' ', 内容)
            
            return 内容
            
        except Exception as 错误:
            return ""
    
    def 获取新浪国际新闻(self) -> List[新闻文章]:
        """获取新浪国际新闻"""
        网址 = "https://news.sina.com.cn/world/"
        新闻列表 = []
        
        # 方法1: 使用Playwright爬取（推荐）
        if self.browser:
            print("   使用Playwright爬取新浪新闻...")
            try:
                html_content = self._使用Playwright爬取(网址, 等待时间=8)
                
                if html_content:
                    汤 = BeautifulSoup(html_content, 'html.parser')
                    
                    # 尝试多种选择器
                    选择器列表 = [
                        'a[href*=".sina.com.cn/"]',  # 所有新浪链接
                        'a[href*="/world/"]',         # 国际新闻链接
                        'a[href*="/w/"]',             # 国际新闻链接
                        'h2 a',                         # h2中的链接
                        'h3 a',                         # h3中的链接
                        '.title a',                     # 标题链接
                        '.news-title a',                # 新闻标题链接
                        '.news-item a',                 # 新闻项链接
                        '.blk122 a',                    # 传统新浪样式
                        'a[title]',                     # 有标题属性的链接
                    ]
                    
                    for 选择器 in 选择器列表:
                        标题列表 = 汤.select(选择器)
                        print(f"   选择器 '{选择器}' 找到 {len(标题列表)} 个元素")
                        
                        if 标题列表:
                            for 标题元素 in 标题列表[:20]:
                                try:
                                    文本 = 标题元素.get_text(strip=True)
                                    链接 = 标题元素.get('href', '')
                                    
                                    if 文本 and len(文本) > 8 and len(文本) < 100:
                                        if not any(关键词 in 文本 for 关键词 in ['广告', '推广', 'APP', '下载', '新浪']):
                                            # 确保链接是新浪新闻链接
                                            if 'sina.com.cn' in 链接:
                                                文章 = 新闻文章(标题=文本, 链接=链接, 来源='新浪')
                                                if 链接:
                                                    文章.内容 = self._提取文章正文(链接, '新浪')
                                                新闻列表.append(文章)
                                                print(f"   添加新闻: {文本[:30]}...")
                                                if len(新闻列表) >= 10:
                                                    break
                                except Exception as e:
                                    pass
                            if len(新闻列表) >= 8:
                                break
                    
                    if len(新闻列表) >= 8:
                        print(f"   成功获取 {len(新闻列表)} 条新浪新闻")
                        return 新闻列表[:10]
                        
            except Exception as 错误:
                print(f"   Playwright爬取失败: {str(错误)[:50]}")
        
        # 方法2: 如果Playwright失败，尝试新浪新闻API
        print("   尝试新浪新闻API...")
        try:
            # 新浪新闻API
            api_urls = [
                "https://interface.sina.cn/news/world.d.json",
                "https://news.sina.com.cn/api/roll/get?channel=world&page=1&num=20",
            ]
            
            for api_url in api_urls:
                try:
                    self.会话.headers.update({
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Referer': 'https://news.sina.com.cn/',
                        'Accept': 'application/json, text/plain, */*',
                    })
                    
                    响应 = self._带重试请求(api_url)
                    数据 = 响应.json()
                    
                    # 分析API响应
                    if 'result' in 数据 and 'data' in 数据['result']:
                        新闻数据 = 数据['result']['data']
                    elif 'data' in 数据:
                        新闻数据 = 数据['data']
                    else:
                        新闻数据 = []
                    
                    for 新闻 in 新闻数据[:20]:
                        if isinstance(新闻, dict):
                            标题 = 新闻.get('title', '') or 新闻.get('title', '')
                            链接 = 新闻.get('url', '') or 新闻.get('href', '')
                            
                            if 标题 and 链接:
                                if len(标题) > 8 and len(标题) < 100:
                                    if not any(关键词 in 标题 for 关键词 in ['广告', '推广', 'APP', '下载']):
                                        文章 = 新闻文章(标题=标题, 链接=链接, 来源='新浪')
                                        新闻列表.append(文章)
                                        print(f"   API添加新闻: {标题[:30]}...")
                                        if len(新闻列表) >= 10:
                                            break
                    
                    if len(新闻列表) >= 8:
                        break
                        
                except Exception as e:
                    print(f"   API尝试失败: {str(e)[:30]}")
                    continue
            
            if len(新闻列表) >= 8:
                print(f"   成功从API获取 {len(新闻列表)} 条新浪新闻")
                return 新闻列表[:10]
                
        except Exception as 错误:
            print(f"   API爬取失败: {str(错误)[:50]}")
        
        # 方法3: 最后尝试传统方法
        print("   尝试传统方法...")
        try:
            self.会话.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.sina.com.cn/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9',
            })
            
            响应 = self._带重试请求(网址)
            响应.encoding = 'utf-8'
            汤 = BeautifulSoup(响应.text, 'html.parser')
            
            # 保存HTML用于调试
            with open('sina_debug.html', 'w', encoding='utf-8') as f:
                f.write(响应.text[:5000])  # 只保存前5000字符
            print("   已保存调试HTML到 sina_debug.html")
            
            # 尝试多种选择器
            选择器列表 = [
                'a[href*=".sina.com.cn/"]',
                'h2 a',
                'h3 a',
                '.title a',
                '.news-title a',
            ]
            
            for 选择器 in 选择器列表:
                标题列表 = 汤.select(选择器)
                print(f"   传统选择器 '{选择器}' 找到 {len(标题列表)} 个元素")
                
                if 标题列表:
                    for 标题元素 in 标题列表[:15]:
                        try:
                            文本 = 标题元素.get_text(strip=True)
                            链接 = 标题元素.get('href', '')
                            
                            if 文本 and len(文本) > 8 and len(文本) < 100:
                                if not any(关键词 in 文本 for 关键词 in ['广告', '推广', 'APP', '下载']):
                                    if 'sina.com.cn' in 链接:
                                        文章 = 新闻文章(标题=文本, 链接=链接, 来源='新浪')
                                        if 链接:
                                            文章.内容 = self._提取文章正文(链接, '新浪')
                                        新闻列表.append(文章)
                                        print(f"   传统添加新闻: {文本[:30]}...")
                                        if len(新闻列表) >= 10:
                                            break
                        except Exception as e:
                            pass
                    if len(新闻列表) >= 8:
                        break
            
            print(f"   传统方法获取 {len(新闻列表)} 条新浪新闻")
            return 新闻列表[:10]
            
        except Exception as 错误:
            print(f"   新浪新闻获取失败: {str(错误)[:50]}")
            return []
    
    def 获取网易国际新闻(self) -> List[新闻文章]:
        """获取网易国际新闻"""
        网址 = "https://news.163.com/world/"
        
        try:
            响应 = self._带重试请求(网址)
            响应.encoding = 'utf-8'
            汤 = BeautifulSoup(响应.text, 'html.parser')
            
            新闻列表 = []
            
            # 尝试多种选择器
            选择器列表 = [
                '.news_title h3 a',
                '.hidden-title a',
                'a[href*="/news/"]',
                '.title a',
                'h3 a',
            ]
            
            for 选择器 in 选择器列表:
                标题列表 = 汤.select(选择器)
                if 标题列表:
                    for 标题元素 in 标题列表[:15]:
                        文本 = 标题元素.get_text(strip=True)
                        链接 = 标题元素.get('href', '')
                        
                        if 文本 and len(文本) > 8 and len(文本) < 100:
                            if not any(关键词 in 文本 for 关键词 in ['广告', '推广', 'APP', '下载']):
                                文章 = 新闻文章(标题=文本, 链接=链接, 来源='网易')
                                if 链接:
                                    文章.内容 = self._提取文章正文(链接, '网易')
                                新闻列表.append(文章)
                                if len(新闻列表) >= 10:
                                    break
                    if len(新闻列表) >= 8:
                        break
            
            return 新闻列表[:10]
            
        except Exception as 错误:
            print(f"   网易新闻获取失败: {str(错误)}")
            return []
    
    def 获取百度国际新闻(self) -> List[新闻文章]:
        """获取百度国际新闻"""
        新闻列表 = []
        
        # 方法1: 使用Playwright爬取（推荐）
        if self.browser:
            print("   使用Playwright爬取百度新闻...")
            网页地址列表 = [
                "https://news.baidu.com",
                "https://news.baidu.com/guonei",
                "https://news.baidu.com/world",
            ]
            
            for 网址 in 网页地址列表:
                try:
                    html_content = self._使用Playwright爬取(网址, 等待时间=5)
                    
                    if html_content:
                        汤 = BeautifulSoup(html_content, 'html.parser')
                        
                        # 尝试多种选择器
                        选择器列表 = [
                            '.hotnews a',
                            '.bold-item a',
                            '.item a',
                            'a[href*="/sid/"]',
                            '.news-title a',
                            'h3 a',
                            '.result a',
                            '.c-title a',
                        ]
                        
                        for 选择器 in 选择器列表:
                            标题列表 = 汤.select(选择器)
                            if 标题列表:
                                for 标题元素 in 标题列表[:15]:
                                    文本 = 标题元素.get_text(strip=True)
                                    链接 = 标题元素.get('href', '')
                                    
                                    if 文本 and len(文本) > 8 and len(文本) < 100:
                                        if not any(关键词 in 文本 for 关键词 in ['广告', '推广', 'APP', '下载', '百度']):
                                            文章 = 新闻文章(标题=文本, 链接=链接, 来源='百度')
                                            if 链接:
                                                文章.内容 = self._提取文章正文(链接, '百度')
                                            新闻列表.append(文章)
                                            if len(新闻列表) >= 10:
                                                break
                                if len(新闻列表) >= 8:
                                    break
                        
                        if len(新闻列表) >= 8:
                            break
                            
                except Exception as 错误:
                    print(f"   Playwright爬取失败: {str(错误)[:50]}")
                    continue
        
        # 方法2: 如果Playwright失败，尝试百度新闻搜索接口
        if len(新闻列表) < 5:
            print("   尝试API接口...")
            搜索关键词列表 = ['国际新闻', '国际热点', '国际时事']
            
            for 关键词 in 搜索关键词列表:
                try:
                    # 百度新闻搜索API
                    网址 = f"https://news.baidu.com/ns?word={关键词}&tn=news&from=news&cl=2&rn=20&ct=1"
                    
                    self.会话.headers.update({
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Referer': 'https://news.baidu.com/',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'zh-CN,zh;q=0.9',
                    })
                    
                    响应 = self._带重试请求(网址)
                    响应.encoding = 'utf-8'
                    汤 = BeautifulSoup(响应.text, 'html.parser')
                    
                    # 尝试多种选择器
                    选择器列表 = [
                        '.result a[href]',
                        '.news-title a',
                        'h3 a',
                        'a[href*="baidu.com"]',
                        '.c-title a',
                    ]
                    
                    for 选择器 in 选择器列表:
                        标题列表 = 汤.select(选择器)
                        if 标题列表:
                            for 标题元素 in 标题列表[:15]:
                                文本 = 标题元素.get_text(strip=True)
                                链接 = 标题元素.get('href', '')
                                
                                if 文本 and len(文本) > 8 and len(文本) < 100:
                                    if not any(关键词 in 文本 for 关键词 in ['广告', '推广', 'APP', '下载', '百度']):
                                        文章 = 新闻文章(标题=文本, 链接=链接, 来源='百度')
                                        if 链接:
                                            文章.内容 = self._提取文章正文(链接, '百度')
                                        新闻列表.append(文章)
                                        if len(新闻列表) >= 10:
                                            break
                            if len(新闻列表) >= 8:
                                break
                    
                    if len(新闻列表) >= 8:
                        break
                        
                except Exception as 错误:
                    print(f"   百度新闻搜索尝试失败: {str(错误)[:50]}")
                    continue
        
        # 方法2: 如果搜索失败，尝试百度新闻首页
        if len(新闻列表) < 5:
            print("   尝试百度新闻首页...")
            try:
                网址 = "https://news.baidu.com"
                
                self.会话.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': 'https://www.baidu.com/',
                })
                
                响应 = self._带重试请求(网址)
                响应.encoding = 'utf-8'
                汤 = BeautifulSoup(响应.text, 'html.parser')
                
                # 尝试多种选择器
                选择器列表 = [
                    '.hotnews a',
                    '.bold-item a',
                    '.item a',
                    'a[href*="/sid/"]',
                    '.news-title a',
                    'h3 a',
                ]
                
                for 选择器 in 选择器列表:
                    标题列表 = 汤.select(选择器)
                    if 标题列表:
                        for 标题元素 in 标题列表[:15]:
                            文本 = 标题元素.get_text(strip=True)
                            链接 = 标题元素.get('href', '')
                            
                            if 文本 and len(文本) > 8 and len(文本) < 100:
                                if not any(关键词 in 文本 for 关键词 in ['广告', '推广', 'APP', '下载', '百度']):
                                    文章 = 新闻文章(标题=文本, 链接=链接, 来源='百度')
                                    if 链接:
                                        文章.内容 = self._提取文章正文(链接, '百度')
                                    新闻列表.append(文章)
                                    if len(新闻列表) >= 10:
                                        break
                        if len(新闻列表) >= 8:
                            break
                        
            except Exception as 错误:
                print(f"   百度新闻首页爬取失败: {str(错误)[:50]}")
        
        return 新闻列表[:10]
    
    def 获取腾讯国际新闻(self) -> List[新闻文章]:
        """获取腾讯国际新闻"""
        新闻列表 = []
        
        # 方法1: 使用Playwright爬取（推荐）
        if self.browser:
            print("   使用Playwright爬取腾讯新闻...")
            网页地址列表 = [
                "https://new.qq.com/ch/world/",
                "https://news.qq.com/world/",
            ]
            
            for 网址 in 网页地址列表:
                try:
                    html_content = self._使用Playwright爬取(网址, 等待时间=5)
                    
                    if html_content:
                        汤 = BeautifulSoup(html_content, 'html.parser')
                        
                        # 尝试多种选择器
                        选择器列表 = [
                            '.detail .title a',
                            '.news-list .title a',
                            'a[href*="/rain/a/"]',
                            '.content-list a',
                            'h2 a',
                            '.title a',
                            'a[href*="qq.com"]',
                        ]
                        
                        for 选择器 in 选择器列表:
                            标题列表 = 汤.select(选择器)
                            if 标题列表:
                                for 标题元素 in 标题列表[:15]:
                                    文本 = 标题元素.get_text(strip=True)
                                    链接 = 标题元素.get('href', '')
                                    
                                    if 文本 and len(文本) > 8 and len(文本) < 100:
                                        if not any(关键词 in 文本 for 关键词 in ['广告', '推广', 'APP', '下载', '腾讯视频', '会员']):
                                            文章 = 新闻文章(标题=文本, 链接=链接, 来源='腾讯')
                                            if 链接:
                                                文章.内容 = self._提取文章正文(链接, '腾讯')
                                            新闻列表.append(文章)
                                            if len(新闻列表) >= 10:
                                                break
                                if len(新闻列表) >= 8:
                                    break
                        
                        if len(新闻列表) >= 8:
                            break
                            
                except Exception as 错误:
                    print(f"   Playwright爬取失败: {str(错误)[:50]}")
                    continue
        
        # 方法2: 如果Playwright失败，尝试API接口
        if len(新闻列表) < 5:
            print("   尝试API接口...")
            API地址列表 = [
                "https://i.news.qq.com/trpc.qqnews_web.kv_srv.kv_srv_http_proxy/list?sub_srv_id=world&srv_id=pc&limit=20&page=1",
                "https://pacaio.match.qq.com/irs/rcd?cid=146&token=49cbb2154853ef1a74dc4d8d6f6a4d8f&ext=国际&num=20",
                "https://i.news.qq.com/trpc.qqnews_web.kv_srv.kv_srv_http_proxy/list?sub_srv_id=world&srv_id=pc&limit=20&page=1&is_cache=0",
            ]
            
            for 网址 in API地址列表:
                try:
                    self.会话.headers.update({
                        'Referer': 'https://new.qq.com/',
                        'Origin': 'https://new.qq.com',
                        'Accept': 'application/json, text/plain, */*',
                        'Accept-Language': 'zh-CN,zh;q=0.9',
                        'X-Requested-With': 'XMLHttpRequest',
                        'Cookie': 'pgv_pvid=1234567890; pgv_info=ssid=s1234567890',
                    })
                    
                    响应 = self._带重试请求(网址)
                    
                    try:
                        数据 = 响应.json()
                        
                        # 处理不同的API响应格式
                        项目列表 = None
                        
                        # 格式1: data.list
                        if 数据 and isinstance(数据, dict) and 'data' in 数据:
                            数据对象 = 数据['data']
                            if isinstance(数据对象, dict) and 'list' in 数据对象:
                                项目列表 = 数据对象['list']
                        
                        # 格式2: 直接是列表
                        elif 数据 and isinstance(数据, list):
                            项目列表 = 数据
                        
                        if 项目列表 and isinstance(项目列表, list):
                            for 项目 in 项目列表[:15]:
                                if 项目 and isinstance(项目, dict):
                                    标题 = 项目.get('title', '') or 项目.get('article_title', '')
                                    链接 = 项目.get('url', '') or 项目.get('link', '') or 项目.get('article_url', '')
                                    
                                    if 标题 and len(标题) > 8 and len(标题) < 100:
                                        if not any(关键词 in 标题 for 关键词 in ['广告', '推广', 'APP', '下载', '腾讯视频', '会员']):
                                            文章 = 新闻文章(标题=标题, 链接=链接, 来源='腾讯')
                                            if 链接:
                                                文章.内容 = self._提取文章正文(链接, '腾讯')
                                            新闻列表.append(文章)
                                            if len(新闻列表) >= 10:
                                                break
                        
                        if len(新闻列表) >= 8:
                            break
                            
                    except json.JSONDecodeError:
                        pass
                    
                except Exception as 错误:
                    print(f"   腾讯新闻API尝试失败: {str(错误)[:50]}")
                    continue
        
        # 方法2: 如果API失败，尝试网页爬取
        if len(新闻列表) < 5:
            print("   尝试网页爬取方式...")
            网页地址列表 = [
                "https://new.qq.com/ch/world/",
                "https://news.qq.com/world/",
            ]
            
            for 网址 in 网页地址列表:
                try:
                    self.会话.headers.update({
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Referer': 'https://new.qq.com/',
                    })
                    
                    响应 = self._带重试请求(网址)
                    响应.encoding = 'utf-8'
                    汤 = BeautifulSoup(响应.text, 'html.parser')
                    
                    # 尝试多种选择器
                    选择器列表 = [
                        '.detail .title a',
                        '.news-list .title a',
                        'a[href*="/rain/a/"]',
                        '.content-list a',
                        'h2 a',
                        '.title a',
                    ]
                    
                    for 选择器 in 选择器列表:
                        标题列表 = 汤.select(选择器)
                        if 标题列表:
                            for 标题元素 in 标题列表[:15]:
                                文本 = 标题元素.get_text(strip=True)
                                链接 = 标题元素.get('href', '')
                                
                                if 文本 and len(文本) > 8 and len(文本) < 100:
                                    if not any(关键词 in 文本 for 关键词 in ['广告', '推广', 'APP', '下载', '腾讯视频']):
                                        文章 = 新闻文章(标题=文本, 链接=链接, 来源='腾讯')
                                        if 链接:
                                            文章.内容 = self._提取文章正文(链接, '腾讯')
                                        新闻列表.append(文章)
                                        if len(新闻列表) >= 10:
                                            break
                            if len(新闻列表) >= 8:
                                break
                    
                    if len(新闻列表) >= 8:
                        break
                        
                except Exception as 错误:
                    print(f"   腾讯网页爬取失败: {str(错误)[:50]}")
                    continue
        
        return 新闻列表[:10]
    
    def 获取所有新闻(self) -> List[新闻文章]:
        """获取所有来源的新闻"""
        所有新闻 = []
        
        print("\n【1】正在获取新浪国际新闻...")
        新浪新闻 = self.获取新浪国际新闻()
        所有新闻.extend(新浪新闻)
        print(f"   获取到 {len(新浪新闻)} 条新闻")
        
        print("\n【2】正在获取网易国际新闻...")
        网易新闻 = self.获取网易国际新闻()
        所有新闻.extend(网易新闻)
        print(f"   获取到 {len(网易新闻)} 条新闻")
        
        print("\n【3】正在获取百度国际新闻...")
        百度新闻 = self.获取百度国际新闻()
        所有新闻.extend(百度新闻)
        print(f"   获取到 {len(百度新闻)} 条新闻")
        
        print("\n【4】正在获取腾讯国际新闻...")
        腾讯新闻 = self.获取腾讯国际新闻()
        所有新闻.extend(腾讯新闻)
        print(f"   获取到 {len(腾讯新闻)} 条新闻")
        
        return 所有新闻


def 保存爬取的新闻(所有新闻: List[新闻文章], 文件夹名称: str = "输出文件/爬取的新闻") -> str:
    """保存爬取的新闻内容"""
    if not os.path.exists(文件夹名称):
        os.makedirs(文件夹名称)
    
    现在 = datetime.now()
    时间戳 = 现在.strftime("%Y%m%d_%H%M%S")
    文件名 = f"{时间戳}_爬取的新闻.md"
    文件路径 = os.path.join(文件夹名称, 文件名)
    
    内容 = f"""# 📰 爬取新闻内容记录

> 爬取时间：{现在.strftime('%Y年%m月%d日 %H:%M:%S')}
> 数据来源：新浪国际、网易国际、百度国际、腾讯国际
> 新闻总数：{len(所有新闻)} 条

---

## 📊 原始爬取内容

"""
    
    # 按来源分组显示所有新闻
    来源列表 = ['新浪', '网易', '百度', '腾讯']
    for 来源 in 来源列表:
        来源新闻 = [n for n in 所有新闻 if n.来源 == 来源]
        if 来源新闻:
            内容 += f"\n### 【{来源}】共 {len(来源新闻)} 条\n\n"
            for i, 新闻 in enumerate(来源新闻, 1):
                内容 += f"**{i}. {新闻.标题}**\n\n"
                if 新闻.链接:
                    内容 += f"- 链接：{新闻.链接}\n"
                if 新闻.内容:
                    内容 += f"- 完整内容：\n\n{新闻.内容}\n"
                内容 += "\n---\n\n"
    
    with open(文件路径, 'w', encoding='utf-8') as f:
        f.write(内容)
    
    return 文件路径


def 主函数():
    """主函数"""
    print("=" * 60)
    print("📰 新闻爬虫模块")
    print("=" * 60)
    
    # 禁用SSL警告
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # 初始化爬虫
    爬虫 = 新闻爬虫()
    
    try:
        # 获取所有新闻
        所有新闻 = 爬虫.获取所有新闻()
        
        print("\n" + "=" * 60)
        print(f"共获取到 {len(所有新闻)} 条国际新闻")
        print("=" * 60)
        
        if len(所有新闻) == 0:
            print("\n未能获取到任何新闻，请检查网络连接或稍后重试。")
            return
        
        # 保存爬取的新闻
        爬取路径 = 保存爬取的新闻(所有新闻)
        print(f"\n✅ 爬取内容已保存到：{爬取路径}")
        
        # 保存为JSON格式
        现在 = datetime.now()
        JSON文件 = os.path.join("输出文件/爬取的新闻", f"{现在.strftime('%Y%m%d_%H%M%S')}_爬取的新闻.json")
        with open(JSON文件, 'w', encoding='utf-8') as f:
            json.dump([新闻.转为字典() for 新闻 in 所有新闻], f, ensure_ascii=False, indent=2)
        print(f"✅ JSON格式已保存到：{JSON文件}")
        
    finally:
        # 清理Playwright资源
        if 爬虫.browser:
            爬虫.browser.close()
        if 爬虫.playwright:
            爬虫.playwright.stop()
        print("\n✅ 资源清理完成")


if __name__ == "__main__":
    主函数()
