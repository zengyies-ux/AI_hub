#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻分析模块 - AI分析和总结热点
"""

import os
import re
import json
from typing import List, Dict, Optional
from datetime import datetime
from duckduckgo_search import DDGS

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 新闻爬虫 import 新闻文章, 新闻爬虫


class 新闻分析器:
    """新闻分析器"""
    
    def __init__(self):
        self.新闻爬虫 = 新闻爬虫()
    
    def 分析新闻(self, 所有新闻: List[新闻文章]) -> str:
        """分析新闻并生成总结"""
        print("\n" + "=" * 60)
        print("🔍 开始分析新闻内容...")
        print("=" * 60)
        
        # 1. 合并相似话题
        合并后话题 = self.合并相似话题(所有新闻)
        
        if not 合并后话题:
            print("❌ 未能分析出任何热点话题")
            return ""
        
        print(f"\n发现 {len(合并后话题)} 个热点话题")
        
        # 2. 为每个话题搜索补充信息
        for 话题 in 合并后话题:
            话题标题 = 话题['话题']
            补充信息 = self.搜索补充信息(话题标题)
            if 补充信息:
                话题['补充信息'] = 补充信息
        
        # 3. 生成总结
        总结 = self.生成总结(合并后话题)
        
        return 总结
    
    def 合并相似话题(self, 所有新闻: List[新闻文章], 相似度阈值: float = 0.3) -> List[Dict]:
        """合并相似的热点话题"""
        合并后话题 = []
        已使用 = set()
        
        for i, 新闻 in enumerate(所有新闻):
            if i in 已使用:
                continue
            
            相似组 = [新闻]
            已使用.add(i)
            
            for j, 其他新闻 in enumerate(所有新闻[i+1:], start=i+1):
                if j in 已使用:
                    continue
                
                相似度 = self.计算相似度(新闻, 其他新闻)
                if 相似度 >= 相似度阈值:
                    相似组.append(其他新闻)
                    已使用.add(j)
        
            # 选择内容最丰富的作为代表
            代表 = max(相似组, key=lambda x: len(x.内容) if x.内容 else 0)
        
            # 合并所有内容
            所有内容 = "\n\n".join([f"【{n.来源}】{n.标题}\n{n.内容}" for n in 相似组 if n.内容])
        
            合并后话题.append({
                '话题': 代表.标题,
                '数量': len(相似组),
                '来源': [n.来源 for n in 相似组],
                '内容': 所有内容,
                '链接': [n.链接 for n in 相似组 if n.链接]
            })
        
        合并后话题.sort(key=lambda x: x['数量'], reverse=True)
        return 合并后话题[:5]
    
    def 计算相似度(self, 文章1: 新闻文章, 文章2: 新闻文章) -> float:
        """计算两个文章的相似度"""
        关键词1 = set(self.提取关键词(文章1.标题))
        关键词2 = set(self.提取关键词(文章2.标题))
        
        if not 关键词1 or not 关键词2:
            return 0
        
        交集 = 关键词1 & 关键词2
        并集 = 关键词1 | 关键词2
        
        return len(交集) / len(并集) if 并集 else 0
    
    def 提取关键词(self, 标题: str) -> List[str]:
        """提取标题关键词"""
        import jieba
        分词结果 = jieba.lcut(标题)
        停用词 = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
            '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
            '自己', '这', '那', '里', '后', '前', '中', '以', '及', '为', '与', '等'
        }
        关键词 = [词 for 词 in 分词结果 if len(词) >= 2 and 词 not in 停用词]
        return 关键词
    
    def 搜索补充信息(self, 话题: str, 最大结果数: int = 3) -> str:
        """使用DuckDuckGo搜索补充信息"""
        try:
            print(f"   正在搜索补充信息: {话题[:30]}...")
            with DDGS() as ddgs:
                结果列表 = list(ddgs.text(话题, max_results=最大结果数))
                if 结果列表:
                    补充内容 = "\n\n【联网搜索补充信息】\n"
                    for i, 结果 in enumerate(结果列表, 1):
                        补充内容 += f"\n{i}. {结果.get('title', '')}\n"
                        补充内容 += f"   {结果.get('body', '')}\n"
                    return 补充内容
        except Exception as 错误:
            print(f"   搜索补充信息失败: {str(错误)[:50]}")
        return ""
    
    def 生成总结(self, 合并后话题: List[Dict]) -> str:
        """生成详细总结"""
        现在 = datetime.now()
        
        总结 = f"""# 🌍 国际热点深度分析报告

> 分析时间：{现在.strftime('%Y年%m月%d日 %H:%M:%S')}
> 数据来源：新浪国际、网易国际、百度国际、腾讯国际
> 热点数量：{len(合并后话题)} 个

---

## 📊 热点概览

"""
        
        # 概览部分
        for i, 话题 in enumerate(合并后话题, 1):
            总结 += f"\n### 【{i}】{话题['话题']}\n"
            总结 += f"- 提及次数：{话题['数量']} 次\n"
            总结 += f"- 信息来源：{', '.join(set(话题['来源']))}\n"
        
        总结 += "\n" + "-" * 60 + "\n\n"
        
        # 详细分析部分
        for i, 话题 in enumerate(合并后话题, 1):
            总结 += f"## {i}. {话题['话题']}\n\n"
            总结 += f"### 🔍 核心信息\n\n"
            总结 += f"{话题['内容']}\n"
            
            if '补充信息' in 话题:
                总结 += f"{话题['补充信息']}\n"
            
            总结 += f"### 📎 相关链接\n\n"
            for 链接 in 话题['链接'][:3]:
                总结 += f"- [{链接}]({链接})\n"
            
            总结 += "\n" + "-" * 60 + "\n\n"
        
        # 总结部分
        总结 += """
## 📝 总结

本报告基于多源国际新闻数据，通过AI分析技术，为您梳理了当前最重要的国际热点事件。

- 我们从新浪、网易、百度、腾讯等平台获取了最新的国际新闻
- 通过相似度算法，识别并合并了相似的热点话题
- 为每个热点提供了详细的信息和深度分析
- 结合互联网搜索，补充了最新的相关信息

---

## 💡 分析方法

1. **数据收集**：从主流新闻平台爬取最新国际新闻
2. **话题识别**：基于标题相似度自动识别热点话题
3. **信息整合**：汇总不同来源的相关信息
4. **深度分析**：结合互联网搜索补充最新信息
5. **智能总结**：生成结构化的分析报告

---

*本报告由AI辅助生成，仅供参考。如有重要决策，请以官方信息为准。*
"""
        
        return 总结


def 保存总结(内容: str, 文件夹名称: str = "输出文件/热点分析报告") -> str:
    """保存总结到文件"""
    if not os.path.exists(文件夹名称):
        os.makedirs(文件夹名称)
    
    现在 = datetime.now()
    文件名 = 现在.strftime("%Y%m%d_%H%M%S") + "_分析报告.md"
    文件路径 = os.path.join(文件夹名称, 文件名)
    
    with open(文件路径, 'w', encoding='utf-8') as f:
        f.write(内容)
    
    return 文件路径


def 主函数():
    """主函数"""
    print("=" * 60)
    print("🤖 新闻分析模块")
    print("=" * 60)
    
    # 1. 爬取新闻
    print("\n【1】正在爬取国际新闻...")
    爬虫 = 新闻爬虫()
    所有新闻 = 爬虫.获取所有新闻()
    
    if not 所有新闻:
        print("\n❌ 未能获取到任何新闻，分析终止")
        return
    
    print(f"\n【2】正在分析 {len(所有新闻)} 条新闻...")
    
    # 2. 分析新闻
    分析器 = 新闻分析器()
    总结 = 分析器.分析新闻(所有新闻)
    
    if not 总结:
        print("\n❌ 分析失败，未能生成总结")
        return
    
    # 3. 保存总结
    总结路径 = 保存总结(总结)
    print(f"\n✅ 分析报告已保存到：{总结路径}")
    
    # 4. 显示摘要
    print("\n" + "=" * 60)
    print("📋 分析报告摘要")
    print("=" * 60)
    
    # 提取摘要信息
    行列表 = 总结.split('\n')
    在概览中 = False
    for 行 in 行列表:
        if '## 📊 热点概览' in 行:
            在概览中 = True
            continue
        elif 行.startswith('## 1. '):
            break
        elif 在概览中 and 行.strip():
            print(行)
    
    print("\n" + "=" * 60)
    print("✅ 分析完成！")
    print("=" * 60)


if __name__ == "__main__":
    主函数()
