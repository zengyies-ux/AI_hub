#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片自动下载器 - 自动下载生成的图片并按话题命名
"""

import os
import re
import json
import hashlib
import requests
from urllib.parse import urlparse
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path


class 图片下载器:
    """图片自动下载器"""
    
    def __init__(self, 输出目录: str = None):
        # 如果未指定输出目录，使用项目目录下的"输出文件/生成的图片"
        if 输出目录 is None:
            # 获取当前文件所在目录的绝对路径
            当前文件目录 = os.path.dirname(os.path.abspath(__file__))
            # 向上一级到达项目根目录（AI_hub）
            项目目录 = os.path.dirname(当前文件目录)
            self.基础目录 = os.path.join(项目目录, "输出文件/生成的图片")
        else:
            self.基础目录 = 输出目录
        # 按日期时间创建子文件夹
        self.当前下载目录 = os.path.join(
            self.基础目录,
            datetime.now().strftime("%Y%m%d_%H%M%S")
        )
        self.输出目录 = self.当前下载目录
        self.下载记录 = []
        self._确保目录存在()
    
    def _确保目录存在(self):
        """确保输出目录存在"""
        if not os.path.exists(self.输出目录):
            os.makedirs(self.输出目录)
            print(f"✅ 创建图片目录: {self.输出目录}")
    
    def _清理文件名(self, 文件名: str) -> str:
        """清理文件名，移除非法字符"""
        # 移除或替换非法字符
        清理后 = re.sub(r'[\\/*?:"<>|]', '_', 文件名)
        # 移除前后空格
        清理后 = 清理后.strip()
        # 限制长度
        if len(清理后) > 100:
            清理后 = 清理后[:100]
        return 清理后
    
    def _提取关键词(self, 标题: str) -> str:
        """从标题提取关键词作为文件名"""
        # 移除常见的无意义词汇
        停用词 = ['的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
                '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
                '自己', '这', '那', '里', '后', '前', '中', '以', '及', '为', '与', '等', '将',
                '被', '把', '给', '让', '向', '往', '从', '自', '于', '而', '却', '但是', '因为',
                '所以', '如果', '即使', '虽然', '尽管', '无论', '不管', '不论', '或者', '还是',
                '要么', '假如', '假定', '譬如', '例如', '比如', '像是', '像', '如同', '好像',
                '似乎', '仿佛', '一样', '一般', '通常', '常常', '经常', '往往', '一直', '总是',
                '千万', '万一', '一下', '一些', '一点', '一方面', '一直', '一切', '一样', '一般',
                '通常', '常常', '经常', '往往', '一直', '总是', '千万', '万一']
        
        # 提取关键词
        关键词列表 = []
        for 词 in 标题.split():
            清理词 = 词.strip('，。！？、；：""''（）【】《》')
            if 清理词 and len(清理词) >= 2 and 清理词 not in 停用词:
                关键词列表.append(清理词)
        
        # 取前3-5个关键词
        if len(关键词列表) >= 3:
            return '_'.join(关键词列表[:5])
        elif 关键词列表:
            return '_'.join(关键词列表)
        else:
            # 如果提取不到关键词，使用标题前20个字符
            return self._清理文件名(标题[:20])
    
    def _生成文件名(self, 图片信息: Dict, 序号: int = 1) -> str:
        """
        根据图片信息生成文件名
        
        命名规则：
        1. 优先使用话题标题关键词
        2. 添加序号区分同话题的多张图片
        3. 添加时间戳避免覆盖
        4. 保留原始扩展名
        """
        话题标题 = 图片信息.get('title', '')
        图片链接 = 图片信息.get('url', '')
        
        # 提取关键词
        关键词 = self._提取关键词(话题标题)
        
        # 获取当前时间戳
        时间戳 = datetime.now().strftime("%m%d_%H%M")
        
        # 从URL提取扩展名
        解析结果 = urlparse(图片链接)
        路径 = 解析结果.path
        扩展名 = os.path.splitext(路径)[1]
        if not 扩展名 or 扩展名 not in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
            扩展名 = '.jpg'  # 默认使用jpg
        
        # 组合文件名：关键词_序号_时间戳.扩展名
        文件名 = f"{关键词}_{序号:02d}_{时间戳}{扩展名}"
        
        # 清理文件名
        文件名 = self._清理文件名(文件名)
        
        return 文件名
    
    def _获取文件扩展名(self, 响应头: Dict, 默认扩展名: str = '.jpg') -> str:
        """从响应头获取文件扩展名"""
        内容类型 = 响应头.get('Content-Type', '').lower()
        
        类型映射 = {
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'image/bmp': '.bmp',
            'image/svg+xml': '.svg'
        }
        
        for 类型, 扩展名 in 类型映射.items():
            if 类型 in 内容类型:
                return 扩展名
        
        return 默认扩展名
    
    def 下载单张图片(self, 图片信息: Dict, 序号: int = 1, 超时: int = 30) -> Tuple[bool, str, str]:
        """
        下载单张图片
        
        参数:
            图片信息: 包含url和title的字典
            序号: 图片序号
            超时: 下载超时时间
            
        返回:
            (成功标志, 文件路径, 错误信息)
        """
        图片链接 = 图片信息.get('url', '')
        话题标题 = 图片信息.get('title', '未知话题')
        
        if not 图片链接:
            return False, "", "图片链接为空"
        
        try:
            print(f"  📥 正在下载: {话题标题[:30]}...")
            
            # 生成文件名
            文件名 = self._生成文件名(图片信息, 序号)
            文件路径 = os.path.join(self.输出目录, 文件名)
            
            # 检查文件是否已存在
            if os.path.exists(文件路径):
                # 如果文件已存在，添加随机后缀
                基础名, 扩展名 = os.path.splitext(文件名)
                文件名 = f"{基础名}_{datetime.now().strftime('%S')}{扩展名}"
                文件路径 = os.path.join(self.输出目录, 文件名)
            
            # 下载图片
            响应 = requests.get(
                图片链接,
                timeout=超时,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.37'
                },
                stream=True
            )
            响应.raise_for_status()
            
            # 获取实际扩展名
            实际扩展名 = self._获取文件扩展名(响应.headers)
            if 实际扩展名 != os.path.splitext(文件名)[1]:
                # 更新文件名扩展名
                基础名 = os.path.splitext(文件名)[0]
                文件名 = f"{基础名}{实际扩展名}"
                文件路径 = os.path.join(self.输出目录, 文件名)
            
            # 保存文件
            with open(文件路径, 'wb') as f:
                for 块 in 响应.iter_content(chunk_size=8192):
                    if 块:
                        f.write(块)
            
            # 获取文件大小
            文件大小 = os.path.getsize(文件路径)
            文件大小MB = 文件大小 / (1024 * 1024)
            
            print(f"  ✅ 下载成功: {文件名} ({文件大小MB:.2f} MB)")
            
            # 记录下载信息
            下载记录 = {
                '文件名': 文件名,
                '文件路径': 文件路径,
                '话题标题': 话题标题,
                '原始链接': 图片链接,
                '下载时间': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                '文件大小': f"{文件大小MB:.2f} MB"
            }
            self.下载记录.append(下载记录)
            
            return True, 文件路径, ""
            
        except requests.exceptions.Timeout:
            错误信息 = f"下载超时: {话题标题[:30]}"
            print(f"  ❌ {错误信息}")
            return False, "", 错误信息
            
        except requests.exceptions.RequestException as 错误:
            错误信息 = f"下载失败: {str(错误)[:50]}"
            print(f"  ❌ {错误信息}")
            return False, "", 错误信息
            
        except Exception as 错误:
            错误信息 = f"未知错误: {str(错误)[:50]}"
            print(f"  ❌ {错误信息}")
            return False, "", 错误信息
    
    def 批量下载(self, 图片列表: List[Dict], 最大并发: int = 3) -> Dict:
        """
        批量下载图片
        
        参数:
            图片列表: 图片信息列表
            最大并发: 最大并发下载数（当前实现为顺序下载）
            
        返回:
            下载结果统计
        """
        print("\n" + "=" * 60)
        print("🖼️  开始批量下载图片")
        print("=" * 60)
        print(f"共 {len(图片列表)} 张图片待下载")
        print(f"保存目录: {self.输出目录}")
        print("-" * 60)
        
        成功数 = 0
        失败数 = 0
        失败列表 = []
        
        for i, 图片信息 in enumerate(图片列表, 1):
            print(f"\n【{i}/{len(图片列表)}】")
            成功, 文件路径, 错误信息 = self.下载单张图片(图片信息, i)
            
            if 成功:
                成功数 += 1
            else:
                失败数 += 1
                失败列表.append({
                    '序号': i,
                    '标题': 图片信息.get('title', '未知'),
                    '错误': 错误信息
                })
        
        # 保存下载记录
        self._保存下载记录()
        
        # 返回统计结果
        结果 = {
            '总数': len(图片列表),
            '成功': 成功数,
            '失败': 失败数,
            '成功率': f"{(成功数/len(图片列表)*100):.1f}%" if 图片列表 else "0%",
            '失败列表': 失败列表,
            '保存目录': self.输出目录
        }
        
        # 打印统计
        print("\n" + "=" * 60)
        print("📊 下载统计")
        print("=" * 60)
        print(f"总图片数: {结果['总数']}")
        print(f"下载成功: {结果['成功']}")
        print(f"下载失败: {结果['失败']}")
        print(f"成功率: {结果['成功率']}")
        
        if 失败列表:
            print("\n❌ 失败列表:")
            for 失败项 in 失败列表:
                print(f"  [{失败项['序号']}] {失败项['标题'][:30]}... - {失败项['错误']}")
        
        return 结果
    
    def 从JSON文件下载(self, JSON文件路径: str) -> Dict:
        """
        从JSON文件读取图片链接并下载
        
        参数:
            JSON文件路径: 包含图片链接的JSON文件路径
            
        返回:
            下载结果统计
        """
        print(f"\n📄 读取图片链接文件: {JSON文件路径}")
        
        try:
            with open(JSON文件路径, 'r', encoding='utf-8') as f:
                图片列表 = json.load(f)
            
            if not isinstance(图片列表, list):
                print("❌ JSON文件格式错误，应为图片列表")
                return {'总数': 0, '成功': 0, '失败': 0, '成功率': '0%', '失败列表': []}
            
            print(f"✅ 读取到 {len(图片列表)} 个图片链接")
            return self.批量下载(图片列表)
            
        except FileNotFoundError:
            print(f"❌ 文件不存在: {JSON文件路径}")
            return {'总数': 0, '成功': 0, '失败': 0, '成功率': '0%', '失败列表': []}
            
        except json.JSONDecodeError as 错误:
            print(f"❌ JSON解析错误: {str(错误)}")
            return {'总数': 0, '成功': 0, '失败': 0, '成功率': '0%', '失败列表': []}
            
        except Exception as 错误:
            print(f"❌ 读取文件失败: {str(错误)}")
            return {'总数': 0, '成功': 0, '失败': 0, '成功率': '0%', '失败列表': []}
    
    def _保存下载记录(self):
        """保存下载记录到JSON文件"""
        if not self.下载记录:
            return
        
        记录文件 = os.path.join(
            self.输出目录,
            f"下载记录_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        记录数据 = {
            '下载时间': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            '下载数量': len(self.下载记录),
            '下载详情': self.下载记录
        }
        
        with open(记录文件, 'w', encoding='utf-8') as f:
            json.dump(记录数据, f, ensure_ascii=False, indent=2)
        
        print(f"\n📝 下载记录已保存: {os.path.basename(记录文件)}")


def 主函数():
    """主函数 - 演示如何使用"""
    print("=" * 60)
    print("🖼️  图片自动下载器")
    print("=" * 60)
    
    # 获取项目目录绝对路径
    当前文件目录 = os.path.dirname(os.path.abspath(__file__))
    项目目录 = os.path.dirname(当前文件目录)
    图片目录 = os.path.join(项目目录, "输出文件/生成的图片")
    
    if not os.path.exists(图片目录):
        print(f"❌ 找不到目录: {图片目录}")
        print("请确保已经运行过主控制器.py生成图片链接")
        return
    
    # 获取最新的JSON文件
    JSON文件列表 = [f for f in os.listdir(图片目录) if f.endswith('_图片链接.json')]
    
    if not JSON文件列表:
        print(f"❌ 在 {图片目录} 中没有找到图片链接文件")
        return
    
    最新文件 = sorted(JSON文件列表)[-1]
    JSON文件路径 = os.path.join(图片目录, 最新文件)
    
    print(f"\n📄 找到图片链接文件: {最新文件}")
    
    # 创建下载器并下载
    下载器 = 图片下载器()
    结果 = 下载器.从JSON文件下载(JSON文件路径)
    
    print("\n" + "=" * 60)
    print("✅ 图片下载完成！")
    print("=" * 60)
    print(f"\n📁 图片保存位置: {图片目录}")
    print("\n💡 使用建议：")
    print("   1. 查看下载的图片文件")
    print("   2. 查看下载记录JSON了解详情")
    print("   3. 图片已按话题关键词命名，方便管理")


if __name__ == "__main__":
    主函数()
