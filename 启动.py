#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自媒体图文生成系统 - 启动脚本
一键启动完整工作流
"""

import os
import sys

# 添加项目路径
项目目录 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, 项目目录)

from 核心模块.主控制器 import 自媒体内容生成器


def 主函数():
    """主函数"""
    print("\n" + "=" * 70)
    print("🚀 自媒体图文生成系统")
    print("=" * 70)
    print("\n功能说明：")
    print("  1. 爬取国际热点新闻")
    print("  2. AI深度分析总结")
    print("  3. 生成文生图提示词")
    print("  4. 调用AI生成配图")
    print("  5. 创建自媒体图文内容")
    print("  6. 自动下载图片到本地")
    print("\n" + "=" * 70)
    
    # 运行完整工作流
    生成器 = 自媒体内容生成器()
    生成器.运行完整工作流()
    
    # 询问是否下载图片
    print("\n" + "=" * 70)
    用户输入 = input("\n是否自动下载生成的图片？(y/n): ").strip().lower()
    
    if 用户输入 in ['y', 'yes', '是', '1']:
        print("\n" + "=" * 70)
        print("🖼️  开始下载图片...")
        print("=" * 70)
        
        from 工具模块.图片下载器 import 图片下载器
        
        下载器 = 图片下载器()
        图片目录 = "输出文件/生成的图片"
        
        # 查找最新的JSON文件
        import glob
        JSON文件列表 = glob.glob(os.path.join(图片目录, "*_图片链接.json"))
        
        if JSON文件列表:
            最新文件 = sorted(JSON文件列表)[-1]
            下载器.从JSON文件下载(最新文件)
            print("\n✅ 图片下载完成！")
        else:
            print("❌ 未找到图片链接文件")
    
    print("\n" + "=" * 70)
    print("🎉 所有任务已完成！")
    print("=" * 70)
    print("\n📁 项目结构：")
    print("  • 核心模块/ - 主要功能模块")
    print("  • 工具模块/ - 辅助工具")
    print("  • 输出文件/ - 生成的所有内容")
    print("\n💡 提示：")
    print("  • 所有文件已保存到对应的中文命名文件夹")
    print("  • 图片已按话题关键词自动命名")
    print("  • 查看输出文件/自媒体内容/ 获取各平台文案")


if __name__ == "__main__":
    主函数()
