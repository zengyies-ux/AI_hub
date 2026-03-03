#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻爬虫模块 - 爬取国际新闻
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
        self._更新用户代理()
    
    def _更新用户代理(self):
        """随机更新User-Agent"""
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
        
        try:
            响应 = self._带重试请求(网址)
            响应.encoding = 'utf-8'
            汤 = BeautifulSoup(响应.text, 'html.parser')
            
            新闻列表 = []
            
            # 尝试多种选择器
            选择器列表 = [
                'h2 a[href*="/world/"]',
                '.news-item h2 a',
                '.blk122 a',
                'a[href*="/w/"]',
                '.news-title a',
            ]
            
            for 选择器 in 选择器列表:
                标题列表 = 汤.select(选择器)
                if 标题列表:
                    for 标题元素 in 标题列表[:15]:
                        文本 = 标题元素.get_text(strip=True)
                        链接 = 标题元素.get('href', '')
                        
                        if 文本 and len(文本) > 8 and len(文本) < 100:
                            if not any(关键词 in 文本 for 关键词 in ['广告', '推广', 'APP', '下载']):
                                文章 = 新闻文章(标题=文本, 链接=链接, 来源='新浪')
                                # 尝试获取正文
                                if 链接:
                                    文章.内容 = self._提取文章正文(链接, '新浪')
                                新闻列表.append(文章)
                                if len(新闻列表) >= 10:
                                    break
                    if len(新闻列表) >= 8:
                        break
            
            return 新闻列表[:10]
            
        except Exception as 错误:
            print(f"   新浪新闻获取失败: {str(错误)}")
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
        网址 = "https://news.baidu.com"
        
        try:
            响应 = self._带重试请求(网址)
            响应.encoding = 'utf-8'
            汤 = BeautifulSoup(响应.text, 'html.parser')
            
            新闻列表 = []
            
            # 尝试多种选择器
            选择器列表 = [
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
                            if not any(关键词 in 文本 for 关键词 in ['广告', '推广', 'APP', '下载']):
                                文章 = 新闻文章(标题=文本, 链接=链接, 来源='百度')
                                if 链接:
                                    文章.内容 = self._提取文章正文(链接, '百度')
                                新闻列表.append(文章)
                                if len(新闻列表) >= 10:
                                    break
                    if len(新闻列表) >= 8:
                        break
            
            return 新闻列表[:10]
            
        except Exception as 错误:
            print(f"   百度新闻获取失败: {str(错误)}")
            return []
    
    def 获取腾讯国际新闻(self) -> List[新闻文章]:
        """获取腾讯国际新闻"""
        # 使用腾讯新闻API接口
        API地址列表 = [
            "https://i.news.qq.com/trpc.qqnews_web.kv_srv.kv_srv_http_proxy/list?sub_srv_id=world&srv_id=pc&limit=20&page=1",
        ]
        
        新闻列表 = []
        
        for 网址 in API地址列表:
            try:
                self.会话.headers.update({
                    'Referer': 'https://new.qq.com/',
                    'Origin': 'https://new.qq.com',
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'zh-CN,zh;q=0.9',
                    'X-Requested-With': 'XMLHttpRequest',
                })
                
                响应 = self._带重试请求(网址)
                
                try:
                    数据 = 响应.json()
                    
                    if 数据 and isinstance(数据, dict) and 'data' in 数据:
                        数据对象 = 数据['data']
                        if isinstance(数据对象, dict) and 'list' in 数据对象:
                            项目列表 = 数据对象['list']
                            if 项目列表 and isinstance(项目列表, list):
                                for 项目 in 项目列表[:15]:
                                    if 项目 and isinstance(项目, dict):
                                        标题 = 项目.get('title', '')
                                        链接 = 项目.get('url', '') or 项目.get('link', '')
                                        if 标题 and len(标题) > 8 and len(标题) < 100:
                                            if not any(关键词 in 标题 for 关键词 in ['广告', '推广', 'APP', '下载', '腾讯']):
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


if __name__ == "__main__":
    主函数()
