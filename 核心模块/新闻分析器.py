#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻分析模块 - AI深度分析和总结热点
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


class 新闻分析器:
    """新闻分析器 - 使用AI深度分析新闻"""
    
    def __init__(self):
        配置 = 加载配置()
        self.客户端 = OpenAI(
            base_url=配置['deepseek']['base_url'],
            api_key=配置['deepseek']['api_key']
        )
        self.项目根目录 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    def 读取最新爬取的新闻(self) -> List[Dict]:
        """读取最新爬取的新闻JSON文件"""
        新闻目录 = os.path.join(self.项目根目录, '输出文件', '爬取的新闻')
        
        if not os.path.exists(新闻目录):
            print(f"❌ 新闻目录不存在: {新闻目录}")
            return []
        
        JSON文件列表 = glob.glob(os.path.join(新闻目录, '*_爬取的新闻.json'))
        
        if not JSON文件列表:
            print("❌ 未找到爬取的新闻文件")
            return []
        
        最新文件 = sorted(JSON文件列表)[-1]
        print(f"📄 读取新闻文件: {os.path.basename(最新文件)}")
        
        with open(最新文件, 'r', encoding='utf-8') as f:
            新闻数据 = json.load(f)
        
        print(f"✅ 读取到 {len(新闻数据)} 条新闻")
        return 新闻数据
    
    def AI分析新闻(self, 新闻列表: List[Dict]) -> str:
        """使用AI深度分析新闻并生成报告"""
        print("\n" + "=" * 60)
        print("🤖 正在进行AI深度分析...")
        print("=" * 60)
        
        准备新闻内容 = self.准备新闻内容(新闻列表)
        
        系统提示 = """你是一位资深的国际新闻分析师，擅长从海量新闻中识别热点话题、分析事件脉络、预测发展趋势。

你的任务：
1. 从提供的新闻中识别出3-5个最重要的热点话题
2. 对每个热点进行深度分析，包括：
   - 事件背景和起因
   - 关键参与方及其立场
   - 事件影响和意义
   - 未来可能的发展趋势
3. 用专业但通俗易懂的语言撰写分析报告
4. 报告结构清晰，适合自媒体传播

输出格式要求：
- 使用Markdown格式
- 每个热点话题用二级标题（##）分隔
- 包含清晰的段落和小标题
- 语言简洁有力，避免冗余"""

        用户提示 = f"""请分析以下国际新闻，生成一份深度分析报告：

{准备新闻内容}

要求：
1. 识别3-5个热点话题
2. 每个话题包含：背景、关键信息、影响分析、趋势预测
3. 总字数控制在2000字左右
4. 适合自媒体平台发布"""

        try:
            响应 = self.客户端.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": 系统提示},
                    {"role": "user", "content": 用户提示}
                ],
                temperature=0.7,
                max_tokens=3000,
                timeout=120  # 设置120秒超时
            )
            
            分析结果 = 响应.choices[0].message.content
            return 分析结果
            
        except Exception as 错误:
            print(f"❌ AI分析失败: {str(错误)}")
            return self.生成基础报告(新闻列表, 错误信息=str(错误))
    
    def 准备新闻内容(self, 新闻列表: List[Dict], 最大条数: int = 20) -> str:
        """准备发送给AI的新闻内容"""
        内容 = ""
        for i, 新闻 in enumerate(新闻列表[:最大条数], 1):
            内容 += f"\n【新闻{i}】\n"
            内容 += f"标题：{新闻.get('标题', '未知')}\n"
            内容 += f"来源：{新闻.get('来源', '未知')}\n"
            if 新闻.get('内容'):
                内容 += f"内容：{新闻['内容'][:500]}...\n"
            内容 += "-" * 40 + "\n"
        return 内容
    
    def 生成基础报告(self, 新闻列表: List[Dict], 错误信息: str = "") -> str:
        """生成基础报告（当AI分析失败时的备用方案）"""
        现在 = datetime.now()
        
        报告 = f"""# 🌍 国际热点分析报告

> 分析时间：{现在.strftime('%Y年%m月%d日 %H:%M:%S')}
> 数据来源：新浪国际、网易国际
> 新闻数量：{len(新闻列表)} 条

---

## ⚠️ 说明

AI深度分析暂时不可用，以下是基础新闻汇总。

"""
        
        if 错误信息:
            报告 += f"**错误信息**：{错误信息}\n\n---\n\n"
        
        for i, 新闻 in enumerate(新闻列表[:10], 1):
            报告 += f"## {i}. {新闻.get('标题', '未知标题')}\n\n"
            报告 += f"- **来源**：{新闻.get('来源', '未知')}\n"
            if 新闻.get('链接'):
                报告 += f"- **链接**：{新闻['链接']}\n"
            if 新闻.get('内容'):
                报告 += f"\n**内容摘要**：\n\n{新闻['内容'][:300]}...\n"
            报告 += "\n---\n\n"
        
        return 报告
    
    def 保存报告(self, 报告内容: str) -> str:
        """保存分析报告"""
        输出目录 = os.path.join(self.项目根目录, '输出文件', '热点分析报告')
        
        if not os.path.exists(输出目录):
            os.makedirs(输出目录)
        
        现在 = datetime.now()
        文件名 = 现在.strftime("%Y%m%d_%H%M%S") + "_分析报告.md"
        文件路径 = os.path.join(输出目录, 文件名)
        
        with open(文件路径, 'w', encoding='utf-8') as f:
            f.write(报告内容)
        
        return 文件路径
    
    def 运行完整分析(self) -> str:
        """运行完整的分析流程"""
        print("=" * 60)
        print("🤖 AI新闻分析模块")
        print("=" * 60)
        
        新闻列表 = self.读取最新爬取的新闻()
        
        if not 新闻列表:
            print("❌ 没有新闻可分析")
            return ""
        
        分析报告 = self.AI分析新闻(新闻列表)
        
        if 分析报告:
            文件路径 = self.保存报告(分析报告)
            print(f"\n✅ 分析报告已保存: {文件路径}")
            
            print("\n" + "=" * 60)
            print("📋 报告预览")
            print("=" * 60)
            预览行数 = 分析报告.split('\n')[:20]
            for 行 in 预览行数:
                print(行)
            if len(分析报告.split('\n')) > 20:
                print("\n... (更多内容请查看完整报告)")
            
            return 文件路径
        
        return ""


def 主函数():
    """主函数"""
    分析器 = 新闻分析器()
    分析器.运行完整分析()


if __name__ == "__main__":
    主函数()
