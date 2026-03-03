#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自媒体内容生成器 - 使用AI生成多平台高质量内容
"""

import os
import re
import json
import glob
from typing import List, Dict, Optional
from datetime import datetime
from openai import OpenAI


def 加载配置():
    项目根目录 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(项目根目录, 'config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        raise FileNotFoundError(
            f"配置文件不存在: {config_path}\n"
            "请复制 config.example.json 为 config.json 并填入你的 API 密钥"
        )


class 自媒体内容生成器:
    """自媒体内容生成器 - 使用AI生成多平台内容"""
    
    def __init__(self):
        配置 = 加载配置()
        self.客户端 = OpenAI(
            base_url=配置['deepseek']['base_url'],
            api_key=配置['deepseek']['api_key']
        )
        self.项目根目录 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    def 读取最新分析报告(self) -> str:
        """读取最新的热点分析报告"""
        报告目录 = os.path.join(self.项目根目录, '输出文件', '热点分析报告')
        
        if not os.path.exists(报告目录):
            print(f"❌ 报告目录不存在: {报告目录}")
            return ""
        
        报告文件列表 = glob.glob(os.path.join(报告目录, '*_分析报告.md'))
        
        if not 报告文件列表:
            print("❌ 未找到分析报告文件")
            return ""
        
        最新文件 = sorted(报告文件列表)[-1]
        print(f"📄 读取分析报告: {os.path.basename(最新文件)}")
        
        with open(最新文件, 'r', encoding='utf-8') as f:
            return f.read()
    
    def 读取最新图片链接(self) -> List[Dict]:
        """读取最新的图片链接"""
        图片目录 = os.path.join(self.项目根目录, '输出文件', '生成的图片')
        
        if not os.path.exists(图片目录):
            return []
        
        JSON文件列表 = glob.glob(os.path.join(图片目录, '*_图片链接.json'))
        
        if not JSON文件列表:
            return []
        
        最新文件 = sorted(JSON文件列表)[-1]
        
        with open(最新文件, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def 生成小红书内容(self, 分析报告: str, 图片列表: List[Dict]) -> str:
        """生成小红书风格内容"""
        print("\n📝 正在生成小红书内容...")
        
        系统提示 = """你是一位资深的小红书内容创作者，擅长将严肃的国际新闻转化为吸引人的社交媒体内容。

小红书内容特点：
1. 标题要吸睛，使用emoji，控制在20字以内
2. 开头要有钩子，吸引读者继续阅读
3. 内容要简洁有力，分点陈述
4. 使用大量emoji增加可读性
5. 结尾要有互动引导
6. 添加热门话题标签

输出格式要求：
- 使用Markdown格式
- 标题用一级标题
- 正文分段清晰
- 包含5-8个话题标签"""

        图片描述 = "\n".join([f"- {p.get('title', '')}" for p in 图片列表[:3]]) if 图片列表 else "暂无配图"
        
        用户提示 = f"""请基于以下国际热点分析报告，创作一篇小红书风格的图文内容：

{分析报告[:3000]}

配图说明：
{图片描述}

要求：
1. 标题要足够吸引眼球
2. 内容控制在500字以内
3. 使用大量emoji
4. 结尾引导互动（点赞、收藏、评论）
5. 添加5-8个热门话题标签"""

        try:
            响应 = self.客户端.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": 系统提示},
                    {"role": "user", "content": 用户提示}
                ],
                temperature=0.8,
                max_tokens=1500
            )
            
            内容 = 响应.choices[0].message.content
            
            添加图片 = "\n\n---\n\n## 🖼️ 配图\n\n"
            for i, 图片 in enumerate(图片列表[:3], 1):
                添加图片 += f"![{图片.get('title', f'配图{i}')}]({图片.get('url', '')})\n\n"
            
            return 内容 + 添加图片
            
        except Exception as 错误:
            print(f"❌ 生成失败: {str(错误)}")
            return self._生成小红书备用内容(分析报告, 图片列表)
    
    def 生成抖音内容(self, 分析报告: str, 图片列表: List[Dict]) -> str:
        """生成抖音文案风格内容"""
        print("\n📝 正在生成抖音内容...")
        
        系统提示 = """你是一位资深的抖音短视频文案创作者，擅长将国际新闻转化为爆款短视频脚本。

抖音内容特点：
1. 开头3秒要有爆点，吸引观众停留
2. 内容要口语化，像和朋友聊天
3. 节奏要快，信息密度高
4. 结尾要有行动号召（点赞、关注、评论）
5. 话题标签要热门

输出格式要求：
- 包含【视频标题】
- 包含【开场白】（3秒爆点）
- 包含【正文脚本】（分段标注时长）
- 包含【结尾引导】
- 包含【话题标签】"""

        图片描述 = "\n".join([f"- {p.get('title', '')}" for p in 图片列表[:3]]) if 图片列表 else "暂无配图"
        
        用户提示 = f"""请基于以下国际热点分析报告，创作一个抖音短视频脚本：

{分析报告[:3000]}

可用配图：
{图片描述}

要求：
1. 视频时长控制在60秒以内
2. 开场要足够吸引人
3. 内容口语化，适合口播
4. 结尾引导互动"""

        try:
            响应 = self.客户端.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": 系统提示},
                    {"role": "user", "content": 用户提示}
                ],
                temperature=0.8,
                max_tokens=1500
            )
            
            内容 = 响应.choices[0].message.content
            
            添加图片 = "\n\n---\n\n## 🖼️ 视频配图建议\n\n"
            for i, 图片 in enumerate(图片列表[:3], 1):
                添加图片 += f"**配图{i}**: {图片.get('title', '')}\n"
                添加图片 += f"![配图]({图片.get('url', '')})\n\n"
            
            return 内容 + 添加图片
            
        except Exception as 错误:
            print(f"❌ 生成失败: {str(错误)}")
            return self._生成抖音备用内容(分析报告, 图片列表)
    
    def 生成公众号内容(self, 分析报告: str, 图片列表: List[Dict]) -> str:
        """生成微信公众号风格内容"""
        print("\n📝 正在生成公众号内容...")
        
        系统提示 = """你是一位资深的微信公众号编辑，擅长撰写深度国际新闻分析文章。

公众号内容特点：
1. 标题要专业且有吸引力
2. 开头要有导语，概括全文要点
3. 正文结构清晰，有小标题
4. 内容要有深度，提供独家视角
5. 结尾要有总结和引导关注
6. 语言专业但不晦涩

输出格式要求：
- 使用Markdown格式
- 包含标题、导语、正文、结语
- 正文分3-5个小节
- 每节有小标题
- 适合插入图片的位置标注【配图】"""

        图片描述 = "\n".join([f"- {p.get('title', '')}" for p in 图片列表[:3]]) if 图片列表 else "暂无配图"
        
        用户提示 = f"""请基于以下国际热点分析报告，撰写一篇微信公众号深度文章：

{分析报告[:4000]}

可用配图：
{图片描述}

要求：
1. 标题专业且有吸引力
2. 导语概括核心要点
3. 正文分节论述，有深度
4. 总字数1500-2000字
5. 结尾总结并引导关注"""

        try:
            响应 = self.客户端.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": 系统提示},
                    {"role": "user", "content": 用户提示}
                ],
                temperature=0.7,
                max_tokens=2500
            )
            
            内容 = 响应.choices[0].message.content
            
            添加图片 = "\n\n---\n\n## 📷 文章配图\n\n"
            for i, 图片 in enumerate(图片列表[:3], 1):
                添加图片 += f"### 图{i}: {图片.get('title', '')}\n\n"
                添加图片 += f"![{图片.get('title', '')}]({图片.get('url', '')})\n\n"
            
            添加图片 += "\n---\n\n*本文内容仅供参考，不代表本号立场*\n\n*关注我们，获取更多国际热点深度分析*"
            
            return 内容 + 添加图片
            
        except Exception as 错误:
            print(f"❌ 生成失败: {str(错误)}")
            return self._生成公众号备用内容(分析报告, 图片列表)
    
    def _生成小红书备用内容(self, 分析报告: str, 图片列表: List[Dict]) -> str:
        """小红书备用内容"""
        现在 = datetime.now()
        内容 = f"""# 🔥 今日国际热点速览

> {现在.strftime('%Y年%m月%d日')} | 全球视野

## 📌 核心要点

{self._提取核心要点(分析报告)}

## 💬 小编说

国际形势瞬息万变，保持关注才能把握先机！

---

## 🏷️ 话题标签

#国际新闻 #热点追踪 #全球视野

---

## 🖼️ 配图

"""
        for i, 图片 in enumerate(图片列表[:3], 1):
            内容 += f"![{图片.get('title', f'配图{i}')}]({图片.get('url', '')})\n\n"
        
        return 内容
    
    def _生成抖音备用内容(self, 分析报告: str, 图片列表: List[Dict]) -> str:
        """抖音备用内容"""
        现在 = datetime.now()
        内容 = f"""# 🌍 国际热点速报

**{现在.strftime('%Y年%m月%d日')}**

---

## 【开场白】

家人们！今天国际形势又有大变化！

## 【正文】

{self._提取核心要点(分析报告)}

## 【结尾】

关注我看更多国际热点！

---

## 🏷️ 话题标签

#国际新闻 #全球热点 #新闻速报

---

## 🖼️ 配图

"""
        for i, 图片 in enumerate(图片列表[:3], 1):
            内容 += f"![{图片.get('title', f'配图{i}')}]({图片.get('url', '')})\n\n"
        
        return 内容
    
    def _生成公众号备用内容(self, 分析报告: str, 图片列表: List[Dict]) -> str:
        """公众号备用内容"""
        现在 = datetime.now()
        内容 = f"""# 🌍 国际形势深度分析

> {现在.strftime('%Y年%m月%d日')}

## 导语

今日国际热点纷呈，以下为核心要点。

## 正文

{分析报告[:2000]}

## 配图

"""
        for i, 图片 in enumerate(图片列表[:3], 1):
            内容 += f"![{图片.get('title', f'配图{i}')}]({图片.get('url', '')})\n\n"
        
        内容 += "\n---\n\n*本文内容仅供参考*"
        
        return 内容
    
    def _提取核心要点(self, 分析报告: str) -> str:
        """提取核心要点"""
        行列表 = 分析报告.split('\n')
        要点 = []
        for 行 in 行列表:
            清理后 = 行.replace('#', '').replace('*', '').strip()
            if 清理后 and len(清理后) > 10 and len(清理后) < 100:
                要点.append(f"• {清理后}")
            if len(要点) >= 5:
                break
        return '\n'.join(要点)
    
    def 保存内容(self, 内容: str, 平台: str) -> str:
        """保存内容到文件"""
        输出目录 = os.path.join(self.项目根目录, '输出文件', '自媒体内容')
        
        if not os.path.exists(输出目录):
            os.makedirs(输出目录)
        
        现在 = datetime.now()
        文件名 = 现在.strftime("%Y%m%d_%H%M%S") + f"_{平台}.md"
        文件路径 = os.path.join(输出目录, 文件名)
        
        with open(文件路径, 'w', encoding='utf-8') as f:
            f.write(内容)
        
        return 文件路径
    
    def 运行完整生成(self) -> Dict[str, str]:
        """运行完整的自媒体内容生成流程"""
        print("=" * 60)
        print("📱 自媒体内容生成器")
        print("=" * 60)
        
        分析报告 = self.读取最新分析报告()
        
        if not 分析报告:
            print("❌ 没有分析报告，无法生成内容")
            return {}
        
        图片列表 = self.读取最新图片链接()
        
        结果 = {}
        
        小红书内容 = self.生成小红书内容(分析报告, 图片列表)
        小红书路径 = self.保存内容(小红书内容, "小红书")
        结果['小红书'] = 小红书路径
        print(f"✅ 小红书内容已保存: {小红书路径}")
        
        抖音内容 = self.生成抖音内容(分析报告, 图片列表)
        抖音路径 = self.保存内容(抖音内容, "抖音")
        结果['抖音'] = 抖音路径
        print(f"✅ 抖音内容已保存: {抖音路径}")
        
        公众号内容 = self.生成公众号内容(分析报告, 图片列表)
        公众号路径 = self.保存内容(公众号内容, "公众号")
        结果['公众号'] = 公众号路径
        print(f"✅ 公众号内容已保存: {公众号路径}")
        
        print("\n" + "=" * 60)
        print("🎉 所有自媒体内容生成完成！")
        print("=" * 60)
        
        return 结果


def 主函数():
    """主函数"""
    生成器 = 自媒体内容生成器()
    生成器.运行完整生成()


if __name__ == "__main__":
    主函数()
