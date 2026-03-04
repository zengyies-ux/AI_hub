#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文生图提示词生成器 - 为热点新闻生成AI绘画提示词
"""

import os
import re
import json
from typing import List, Dict, Optional
from datetime import datetime
from openai import OpenAI


def 加载配置():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        raise FileNotFoundError(
            f"配置文件不存在: {config_path}\n"
            "请复制 config.example.json 为 config.json 并填入你的 API 密钥"
        )


class 图片提示词生成器:
    """文生图提示词生成器"""
    
    def __init__(self):
        配置 = 加载配置()
        self.客户端 = OpenAI(
            base_url=配置['deepseek']['base_url'],
            api_key=配置['deepseek']['api_key']
        )
    
    def 为总结生成提示词(self, 总结内容: str, 风格: str = "社交媒体") -> List[Dict]:
        """
        为热点总结生成文生图提示词
        
        参数:
            总结内容: 热点总结内容
            风格: 图片风格 (社交媒体/新闻纪实/插画风格/电影海报/信息图表)
        
        返回:
            所有热点话题的提示词列表
        """
        print("\n" + "=" * 60)
        print("正在分析热点内容并生成文生图提示词...")
        print("=" * 60)
        
        # 提取热点话题
        话题列表 = self.提取热点话题(总结内容)
        
        if not 话题列表:
            print("⚠️ 未能从总结中提取到热点话题，尝试使用整体内容生成...")
            # 使用整体内容生成一个通用提示词
            话题列表 = [{
                '编号': '1',
                '标题': '国际热点综合',
                '内容': 总结内容
            }]
        
        print(f"\n发现 {len(话题列表)} 个热点话题")
        print("-" * 60)
        
        提示词列表 = []
        for i, 话题 in enumerate(话题列表, 1):
            print(f"\n【{i}/{len(话题列表)}】生成提示词: {话题['标题'][:40]}...")
            提示词数据 = self.生成提示词(话题, 风格)
            提示词列表.append(提示词数据)
            
            # 显示生成的提示词
            print(f"✅ 英文提示词: {提示词数据.get('english_prompt', 'N/A')[:80]}...")
            print(f"🎨 中文描述: {提示词数据.get('chinese_description', 'N/A')[:60]}...")
        
        return 提示词列表
    
    def 提取热点话题(self, 总结内容: str) -> List[Dict]:
        """
        从总结内容中提取热点话题
        
        参数:
            总结内容: 热点总结内容
            
        返回:
            提取的热点话题列表
        """
        话题列表 = []
        行列表 = 总结内容.split('\n')
        
        当前话题 = None
        当前内容 = []
        
        for 行 in 行列表:
            # 匹配 1. 标题 或 热点一： 或 一、标题 格式
            匹配 = re.match(r'^##\s*(?:(\d+)\.|热点[一二三四五六七八九十]+|[一二三四五六七八九十]+、)\s*[:：]?\s*(.+)$', 行)
            if 匹配:
                if 当前话题:
                    话题列表.append({
                        '编号': 当前话题['编号'],
                        '标题': 当前话题['标题'],
                        '内容': '\n'.join(当前内容)
                    })
                
                # 获取编号
                编号 = 匹配.group(1)
                # 如果是热点一：或一、标题格式，生成编号
                if not 编号:
                    # 从行中提取中文数字并转换为阿拉伯数字
                    中文数字匹配 = re.search(r'热点([一二三四五六七八九十]+)|([一二三四五六七八九十]+)、', 行)
                    if 中文数字匹配:
                        中文数字 = 中文数字匹配.group(1) or 中文数字匹配.group(2)
                        数字映射 = {'一': '1', '二': '2', '三': '3', '四': '4', '五': '5', '六': '6', '七': '7', '八': '8', '九': '9', '十': '10'}
                        编号 = 数字映射.get(中文数字, '0')
                    else:
                        编号 = str(len(话题列表) + 1)
                当前话题 = {
                    '编号': 编号,
                    '标题': 匹配.group(2).strip()
                }
                当前内容 = []
            elif 当前话题 and 行.strip():
                当前内容.append(行)
        
        # 添加最后一个话题
        if 当前话题:
            话题列表.append({
                '编号': 当前话题['编号'],
                '标题': 当前话题['标题'],
                '内容': '\n'.join(当前内容)
            })
        
        # 最多返回5个热点
        return 话题列表[:5]
    
    def 生成提示词(self, 话题: Dict, 风格: str) -> Dict:
        """
        为单个热点话题生成提示词
        
        参数:
            话题: 热点话题信息
            风格: 图片风格
            
        返回:
            包含中英文提示词的字典
        """
        风格描述 = {
            "社交媒体": "适合在社交媒体上分享的图片，色彩鲜艳，构图简洁，有吸引力",
            "新闻纪实": "新闻风格的图片，真实感强，构图严谨，信息丰富",
            "插画风格": "插画风格的图片，艺术性强，色彩丰富，表现力强",
            "电影海报": "电影海报风格的图片，戏剧性强，构图有冲击力，视觉效果突出",
            "信息图表": "信息图表风格的图片，数据可视化，清晰明了，专业美观"
        }.get(风格, "适合在社交媒体上分享的图片")
        
        系统提示 = """你是一个专业的文生图提示词工程师。

请基于提供的热点新闻内容，为AI绘画模型生成高质量的提示词。

要求：
1. 分析热点内容，提炼核心信息和视觉元素
2. 生成一个详细的英文提示词，适合AI绘画模型使用
3. 同时生成一个中文描述，说明图片的内容和风格
4. 考虑指定的风格要求
5. 提示词要具体、详细，包含场景、人物、动作、色彩、构图等元素
6. 输出格式为JSON，包含以下字段：
   {
     "english_prompt": "详细的英文提示词",
     "chinese_description": "中文描述",
     "scene_elements": [场景元素列表],
     "color_scheme": "色彩方案",
     "composition": "构图方式",
     "mood": "整体氛围"
   }

请确保生成的提示词能够准确表达热点内容的核心信息，同时符合指定的风格要求。"""
        
        用户提示 = f"""热点标题：{话题['标题']}

热点内容：{话题['内容']}

风格要求：{风格描述}

请为这个热点新闻生成文生图提示词。"""
        
        try:
            响应 = self.客户端.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": 系统提示},
                    {"role": "user", "content": 用户提示}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            AI响应 = 响应.choices[0].message.content
            
            # 尝试解析JSON
            try:
                # 查找JSON部分
                JSON匹配 = re.search(r'\{[\s\S]*\}', AI响应)
                if JSON匹配:
                    结果 = json.loads(JSON匹配.group())
                else:
                    结果 = json.loads(AI响应)
                
                # 添加元数据
                结果['topic_title'] = 话题['标题']
                结果['style'] = 风格
                结果['generated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                return 结果
                
            except json.JSONDecodeError:
                # 如果解析失败，返回结构化数据
                return {
                    'topic_title': 话题['标题'],
                    'english_prompt': AI响应,
                    'chinese_description': f"基于热点'{话题['标题']}'生成的图片",
                    'scene_elements': ['新闻场景', '国际事件', '热点话题'],
                    'color_scheme': '根据内容自动匹配',
                    'composition': '适合社交媒体的构图',
                    'mood': '专业、权威',
                    'style': 风格,
                    'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'raw_response': AI响应
                }
                
        except Exception as 错误:
            print(f"❌ 生成提示词失败: {str(错误)}")
            return {
                'topic_title': 话题['标题'],
                'english_prompt': f"News scene about {话题['标题']}, professional news style, clear composition",
                'chinese_description': f"关于'{话题['标题']}'的新闻场景",
                'scene_elements': ['新闻场景', '国际事件'],
                'color_scheme': '新闻风格配色',
                'composition': '标准新闻构图',
                'mood': '专业、客观',
                'style': 风格,
                'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'error': str(错误)
            }
    
    def 保存提示词(self, 提示词列表: List[Dict], 文件夹名称: str = "输出文件/文生图提示词") -> str:
        """
        保存生成的提示词到文件
        
        参数:
            提示词列表: 提示词列表
            文件夹名称: 保存文件夹名称
            
        返回:
            保存的文件路径
        """
        if not os.path.exists(文件夹名称):
            os.makedirs(文件夹名称)
        
        现在 = datetime.now()
        文件名 = 现在.strftime("%Y%m%d_%H%M%S") + "_文生图提示词.json"
        文件路径 = os.path.join(文件夹名称, 文件名)
        
        # 保存为JSON
        with open(文件路径, 'w', encoding='utf-8') as f:
            json.dump(提示词列表, f, ensure_ascii=False, indent=2)
        
        # 同时生成Markdown文件，方便查看
        Markdown文件名 = 现在.strftime("%Y%m%d_%H%M%S") + "_文生图提示词.md"
        Markdown文件路径 = os.path.join(文件夹名称, Markdown文件名)
        
        Markdown内容 = f"""# 🎨 文生图提示词

> 生成时间：{现在.strftime('%Y年%m月%d日 %H:%M:%S')}
> 提示词数量：{len(提示词列表)} 个

---

"""
        
        for i, 提示词数据 in enumerate(提示词列表, 1):
            Markdown内容 += f"## {i}. {提示词数据.get('topic_title', f'热点{i}')}\n\n"
            Markdown内容 += f"### 英文提示词\n\n"
            Markdown内容 += f"```\n{提示词数据.get('english_prompt', '')}\n```\n\n"
            Markdown内容 += f"### 中文描述\n\n"
            Markdown内容 += f"{提示词数据.get('chinese_description', '')}\n\n"
            
            if 'scene_elements' in 提示词数据:
                Markdown内容 += f"### 场景元素\n\n"
                Markdown内容 += "\n".join([f"- {元素}" for 元素 in 提示词数据['scene_elements']])
                Markdown内容 += "\n\n"
            
            Markdown内容 += f"### 风格\n\n"
            Markdown内容 += f"{提示词数据.get('style', '')}\n\n"
            Markdown内容 += f"### 色彩方案\n\n"
            Markdown内容 += f"{提示词数据.get('color_scheme', '根据内容自动匹配')}\n\n"
            Markdown内容 += f"### 构图\n\n"
            Markdown内容 += f"{提示词数据.get('composition', '标准构图')}\n\n"
            Markdown内容 += f"### 氛围\n\n"
            Markdown内容 += f"{提示词数据.get('mood', '专业、权威')}\n\n"
            Markdown内容 += "---\n\n"
        
        with open(Markdown文件路径, 'w', encoding='utf-8') as f:
            f.write(Markdown内容)
        
        return 文件路径


def 主函数():
    """主函数 - 演示如何使用"""
    print("=" * 60)
    print("🎨 文生图提示词生成器")
    print("=" * 60)
    
    # 示例：读取最新的热点总结文件
    总结文件夹 = "输出文件/热点分析报告"
    
    if not os.path.exists(总结文件夹):
        print(f"❌ 找不到文件夹: {总结文件夹}")
        print("请确保已经运行过新闻分析器.py")
        return
    
    # 获取最新的总结文件
    总结文件列表 = [f for f in os.listdir(总结文件夹) if f.endswith('.md')]
    if not 总结文件列表:
        print(f"❌ 在 {总结文件夹} 中没有找到总结文件")
        return
    
    最新文件 = sorted(总结文件列表)[-1]
    总结路径 = os.path.join(总结文件夹, 最新文件)
    
    print(f"\n📄 读取热点总结: {最新文件}")
    
    # 读取内容
    with open(总结路径, 'r', encoding='utf-8') as f:
        总结内容 = f.read()
    
    # 初始化生成器
    生成器 = 图片提示词生成器()
    
    # 生成提示词
    提示词列表 = 生成器.为总结生成提示词(
        总结内容=总结内容,
        风格="社交媒体"  # 可选：新闻纪实、社交媒体、插画风格、电影海报、信息图表
    )
    
    # 保存提示词
    生成器.保存提示词(提示词列表)
    
    print("\n" + "=" * 60)
    print("✅ 文生图提示词生成完成！")
    print("=" * 60)
    print("\n💡 使用建议：")
    print("   1. 查看生成的Markdown文件了解详细内容")
    print("   2. 复制英文提示词到文生图API使用")
    print("   3. 可以使用主控制器.py的完整工作流")


if __name__ == "__main__":
    主函数()
