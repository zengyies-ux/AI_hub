#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自媒体图文生成系统 - 主控制器
完整工作流：热点爬取 → AI分析 → 提示词生成 → 图片生成 → 自媒体内容
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from typing import List, Dict

# 添加项目根目录到路径
项目根目录 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 项目根目录)


def 加载配置():
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
    """自媒体图文内容生成器 - 完整工作流"""
    
    def __init__(self):
        self.项目根目录 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.核心模块目录 = os.path.join(self.项目根目录, '核心模块')
        self.工具模块目录 = os.path.join(self.项目根目录, '工具模块')
        self.配置目录 = os.path.join(self.项目根目录, '配置数据')
        self.输出目录 = os.path.join(self.项目根目录, '输出文件')
        self.配置 = 加载配置()
        
        self.输出文件夹 = {
            '爬取的新闻': os.path.join(self.输出目录, '爬取的新闻'),
            '热点分析报告': os.path.join(self.输出目录, '热点分析报告'),
            '文生图提示词': os.path.join(self.输出目录, '文生图提示词'),
            '生成的图片': os.path.join(self.输出目录, '生成的图片'),
            '自媒体内容': os.path.join(self.输出目录, '自媒体内容')
        }
        
        self._确保文件夹存在()
    
    def _确保文件夹存在(self):
        """确保所有输出文件夹存在"""
        for 文件夹名称, 文件夹路径 in self.输出文件夹.items():
            if not os.path.exists(文件夹路径):
                os.makedirs(文件夹路径)
                print(f"✅ 创建文件夹: {文件夹名称}")
    
    def 步骤一_爬取热点新闻(self) -> bool:
        """步骤1：爬取热点新闻"""
        print("\n" + "=" * 70)
        print("📰 步骤1: 爬取国际热点新闻")
        print("=" * 70)
        
        try:
            # 运行新闻爬虫
            爬虫路径 = os.path.join(self.核心模块目录, '新闻爬虫.py')
            结果 = subprocess.run(
                [sys.executable, 爬虫路径],
                cwd=self.项目根目录,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            print(结果.stdout)
            
            if 结果.returncode == 0:
                print("✅ 热点新闻爬取成功")
                return True
            else:
                print(f"❌ 爬取失败: {结果.stderr}")
                return False
                
        except Exception as 错误:
            print(f"❌ 运行失败: {str(错误)}")
            return False
    
    def 步骤二_AI分析新闻(self) -> bool:
        """步骤2：AI分析新闻"""
        print("\n" + "=" * 70)
        print("🤖 步骤2: AI深度分析新闻")
        print("=" * 70)
        
        try:
            # 运行AI分析
            分析器路径 = os.path.join(self.核心模块目录, '新闻分析器.py')
            结果 = subprocess.run(
                [sys.executable, 分析器路径],
                cwd=self.项目根目录,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            print(结果.stdout)
            
            if 结果.returncode == 0:
                print("✅ 新闻分析完成")
                return True
            else:
                print(f"❌ 分析失败: {结果.stderr}")
                return False
                
        except Exception as 错误:
            print(f"❌ 运行失败: {str(错误)}")
            return False
    
    def 步骤三_生成提示词(self) -> List[Dict]:
        """步骤3：生成文生图提示词"""
        print("\n" + "=" * 70)
        print("🎨 步骤3: 生成文生图提示词")
        print("=" * 70)
        
        try:
            # 导入提示词生成器
            sys.path.insert(0, self.核心模块目录)
            from 提示词生成器 import 图片提示词生成器
            
            # 获取最新的热点总结
            总结文件列表 = [f for f in os.listdir(self.输出文件夹['热点分析报告']) if f.endswith('.md')]
            
            if not 总结文件列表:
                print("❌ 未找到热点总结文件")
                return []
            
            最新文件 = sorted(总结文件列表)[-1]
            总结路径 = os.path.join(self.输出文件夹['热点分析报告'], 最新文件)
            
            print(f"📄 读取文件: {最新文件}")
            
            with open(总结路径, 'r', encoding='utf-8') as f:
                总结内容 = f.read()
            
            # 生成提示词
            生成器 = 图片提示词生成器()
            提示词列表 = 生成器.为总结生成提示词(
                总结内容=总结内容,
                风格="社交媒体"
            )
            
            # 保存提示词
            生成器.保存提示词(提示词列表, self.输出文件夹['文生图提示词'])
            
            print(f"✅ 成功生成 {len(提示词列表)} 个提示词")
            return 提示词列表
            
        except Exception as 错误:
            print(f"❌ 生成提示词失败: {str(错误)}")
            return []
    
    def 步骤四_生成图片(self, 提示词列表: List[Dict]) -> List[Dict]:
        """步骤4：生成图片"""
        print("\n" + "=" * 70)
        print("🖼️  步骤4: 生成配图")
        print("=" * 70)
        
        if not 提示词列表:
            print("⚠️ 没有提示词，跳过图片生成")
            return []
        
        图片链接列表 = []
        
        # 使用Coze API生成图片
        import requests
        
        API地址 = self.配置['coze']['api_url']
        
        for i, 提示词数据 in enumerate(提示词列表[:5], 1):  # 最多生成5张
            英文提示词 = 提示词数据.get('english_prompt', '')
            话题标题 = 提示词数据.get('topic_title', f'热点{i}')
            
            print(f"\n【{i}/{min(len(提示词列表), 5)}】生成图片: {话题标题[:30]}...")
            print(f"提示词: {英文提示词[:60]}...")
            
            请求数据 = {
                "prompt": 英文提示词,
                "size": "768x1024",  # 3:4 比例
                "count": 1,
                "model": "doubao-seedream-4-5-251128"
            }
            
            请求头 = {"Content-Type": "application/json"}
            
            try:
                响应 = requests.post(API地址, json=请求数据, headers=请求头, timeout=60)
                
                if 响应.status_code == 200:
                    数据 = 响应.json()
                    if 数据.get("success") and 数据.get("imageUrls"):
                        图片地址 = 数据["imageUrls"][0]
                        图片链接列表.append({
                            'url': 图片地址,
                            'title': 话题标题,
                            'prompt': 英文提示词
                        })
                        print(f"✅ 图片生成成功: {图片地址[:60]}...")
                    else:
                        print(f"⚠️ 生成失败: {数据.get('message', '未知错误')}")
                else:
                    print(f"❌ API错误: {响应.status_code}")
                    
            except Exception as 错误:
                print(f"❌ 请求失败: {str(错误)}")
        
        # 保存图片URL记录
        if 图片链接列表:
            现在 = datetime.now()
            JSON文件 = os.path.join(
                self.输出文件夹['生成的图片'],
                现在.strftime("%Y%m%d_%H%M%S") + "_图片链接.json"
            )
            with open(JSON文件, 'w', encoding='utf-8') as f:
                json.dump(图片链接列表, f, ensure_ascii=False, indent=2)
            print(f"\n✅ 图片链接已保存到: {os.path.basename(JSON文件)}")
        
        return 图片链接列表
    
    def 步骤五_创建自媒体内容(self, 图片链接列表: List[Dict]):
        """步骤5：创建自媒体内容"""
        print("\n" + "=" * 70)
        print("📱 步骤5: 创建自媒体图文内容")
        print("=" * 70)
        
        try:
            sys.path.insert(0, self.核心模块目录)
            from 自媒体内容生成器 import 自媒体内容生成器
            
            生成器 = 自媒体内容生成器()
            
            分析报告 = 生成器.读取最新分析报告()
            
            if not 分析报告:
                print("❌ 未找到分析报告")
                return
            
            小红书内容 = 生成器.生成小红书内容(分析报告, 图片链接列表)
            小红书路径 = 生成器.保存内容(小红书内容, "小红书")
            print(f"✅ 小红书内容: {os.path.basename(小红书路径)}")
            
            抖音内容 = 生成器.生成抖音内容(分析报告, 图片链接列表)
            抖音路径 = 生成器.保存内容(抖音内容, "抖音")
            print(f"✅ 抖音内容: {os.path.basename(抖音路径)}")
            
            公众号内容 = 生成器.生成公众号内容(分析报告, 图片链接列表)
            公众号路径 = 生成器.保存内容(公众号内容, "公众号")
            print(f"✅ 公众号内容: {os.path.basename(公众号路径)}")
            
            print(f"\n🎉 所有自媒体内容已生成！")
            
        except Exception as 错误:
            print(f"❌ 生成失败: {str(错误)}")
    
    def _创建小红书格式(self, 总结: str, 图片列表: List[Dict], 时间: datetime) -> str:
        """创建小红书格式内容"""
        内容 = f"""# 📰 今日国际热点速览

> {时间.strftime('%Y年%m月%d日')} | 全球视野 | 热点追踪

---

## 🔥 今日必看

{self._提取关键要点(总结)}

---

## 📊 深度解读

{self._简化内容(总结)}

---

## 💡 小编观点

国际形势瞬息万变，保持关注才能把握先机！

---

## 🏷️ 标签

#国际新闻 #热点追踪 #全球视野 #今日必看 #新闻解读

---

## 🖼️ 配图

"""
        for i, 图片 in enumerate(图片列表, 1):
            内容 += f"{i}. ![配图{i}]({图片.get('url', '')})\n"
            内容 += f"   *{图片.get('title', '')}*\n\n"
        
        内容 += """
---

*内容来源：新浪、网易、百度、腾讯国际新闻*
*AI辅助生成，仅供参考*
"""
        return 内容
    
    def _创建抖音格式(self, 总结: str, 图片列表: List[Dict], 时间: datetime) -> str:
        """创建抖音文案格式"""
        内容 = f"""# 🌍 国际热点速报

**{时间.strftime('%Y年%m月%d日')} 全球发生了什么？**

---

## 🎬 视频文案

【开场】
家人们！今天国际形势又有大变化！

【正文】
{self._创建简短摘要(总结)}

【结尾】
关注我看更多国际热点！
点赞收藏不迷路！

---

## 📝 评论区引导

💬 "你怎么看这件事？"
💬 "评论区聊聊你的观点"
💬 "转发给关心国际形势的朋友"

---

## 🏷️ 话题标签

#国际新闻 #全球热点 #新闻速报 #国际形势 #今日热点

---

## 🖼️ 视频配图建议

"""
        for i, 图片 in enumerate(图片列表, 1):
            内容 += f"{i}. {图片.get('title', f'配图{i}')}: {图片.get('url', '')}\n"
        
        return 内容
    
    def _创建公众号格式(self, 总结: str, 图片列表: List[Dict], 时间: datetime) -> str:
        """创建微信公众号格式"""
        内容 = f"""# 🌍 国际形势深度分析 | {时间.strftime('%Y年%m月%d日')}

---

## 导语

今日国际热点纷呈，我们为您梳理了最重要的5大事件，带您看清世界格局变化。

---

## 正文

{总结}

---

## 配图展示

"""
        for i, 图片 in enumerate(图片列表, 1):
            内容 += f"### 配图{i}: {图片.get('title', '')}\n\n"
            内容 += f"![{图片.get('title', '')}]({图片.get('url', '')})\n\n"
            内容 += f"*{图片.get('prompt', '')[:100]}...*\n\n"
        
        内容 += """
---

## 结语

国际形势复杂多变，我们将持续为您带来最新、最深入的分析。

**关注我们，掌握全球动态！**

---

*本文数据来源：新浪国际、网易国际、百度国际、腾讯国际*
*AI辅助分析，仅供参考*
"""
        return 内容
    
    def _提取关键要点(self, 总结: str) -> str:
        """提取关键要点"""
        行列表 = 总结.split('\n')
        关键要点 = []
        for 行 in 行列表:
            if any(标记 in 行 for 标记 in ['热点', '###', '**']):
                清理后 = 行.replace('#', '').replace('*', '').strip()
                if 清理后 and len(清理后) > 5:
                    关键要点.append(f"• {清理后}")
            if len(关键要点) >= 5:
                break
        return '\n'.join(关键要点) if 关键要点 else "• 国际热点持续更新中..."
    
    def _简化内容(self, 总结: str) -> str:
        """简化内容"""
        简化后 = 总结.replace('###', '##')
        简化后 = 简化后.replace('**', '')
        return 简化后
    
    def _创建简短摘要(self, 总结: str) -> str:
        """创建简短摘要（适合抖音）"""
        行列表 = 总结.split('\n')
        短行列表 = []
        for 行 in 行列表[:20]:
            清理后 = 行.replace('#', '').replace('*', '').strip()
            if 清理后 and len(清理后) > 10:
                短行列表.append(清理后)
        return '\n'.join(短行列表[:8])
    
    def 运行完整工作流(self):
        """运行完整工作流"""
        print("\n" + "🚀" * 35)
        print("🚀  自媒体图文生成系统 - 完整工作流启动  🚀")
        print("🚀" * 35)
        print("\n工作流程:")
        print("  1️⃣  爬取国际热点新闻")
        print("  2️⃣  AI深度分析总结")
        print("  3️⃣  生成文生图提示词")
        print("  4️⃣  调用AI生成配图")
        print("  5️⃣  创建自媒体图文内容")
        print("\n" + "=" * 70)
        
        # 步骤1：爬取新闻
        if not self.步骤一_爬取热点新闻():
            print("\n❌ 工作流在步骤1中断")
            return
        
        # 步骤2：AI分析
        if not self.步骤二_AI分析新闻():
            print("\n❌ 工作流在步骤2中断")
            return
        
        # 步骤3：生成提示词
        提示词列表 = self.步骤三_生成提示词()
        if not 提示词列表:
            print("\n⚠️ 未能生成提示词，继续执行...")
        
        # 步骤4：生成图片
        图片链接列表 = self.步骤四_生成图片(提示词列表)
        
        # 步骤5：创建最终内容
        self.步骤五_创建自媒体内容(图片链接列表)
        
        print("\n" + "=" * 70)
        print("🎉 全部完成！")
        print("=" * 70)
        print("\n📁 输出文件位置:")
        for 名称, 文件夹 in self.输出文件夹.items():
            print(f"   • {名称}: {文件夹}")
        print("\n💡 使用建议:")
        print("   1. 查看 热点分析报告/ 获取完整分析")
        print("   2. 查看 文生图提示词/ 获取AI绘画提示词")
        print("   3. 查看 自媒体内容/ 获取各平台内容")
        print("   4. 查看 生成的图片/ 获取下载的图片")


def 主函数():
    """主函数"""
    生成器 = 自媒体内容生成器()
    生成器.运行完整工作流()


if __name__ == "__main__":
    主函数()
