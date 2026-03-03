#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试极速模式性能修复
"""

import time
import sys
import os

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend/src'))

from handwrite_generator import Config, load_font, render_handwrite_text, process_text_image, multiply_blend, load_background_with_image


def test_generation(text, fast_mode=False, quality=2):
    """测试生成性能"""
    print(f"\n{'='*60}")
    print(f"模式: {'极速' if fast_mode else '标准'}, 字数: {len(text)}, 质量: {quality}x")
    print(f"{'='*60}")

    # 配置
    Config.FAST_MODE = fast_mode
    Config.SUPER_SAMPLE_SCALE = quality
    Config.OUTPUT_SIZE = (1240, 1754)
    Config.BASE_FONT_SIZE = 36
    Config.ELASTIC_ALPHA = 80 if not fast_mode else 40  # 极速模式降低变形
    Config.ELASTIC_SIGMA = 12
    Config.ENABLE_INK_BLOTS = not fast_mode  # 极速模式跳过墨点

    total_start = time.time()

    # 1. 加载字体
    t0 = time.time()
    font_path = "assets/fonts/PingFangShaoHuaTi-2.ttf"
    font = load_font(font_path, Config.BASE_FONT_SIZE)
    t1 = time.time()
    print(f"字体加载: {(t1-t0)*1000:.1f}ms")

    # 2. 渲染文字
    t0 = time.time()
    text_image = render_handwrite_text(text, font)
    t1 = time.time()
    print(f"文字渲染: {(t1-t0)*1000:.1f}ms")

    # 3. 处理图像
    t0 = time.time()
    processed = process_text_image(text_image, fast_mode=fast_mode)
    t1 = time.time()
    print(f"图像处理: {(t1-t0)*1000:.1f}ms")

    # 4. 加载背景
    t0 = time.time()
    background = load_background_with_image()
    t1 = time.time()
    print(f"背景加载: {(t1-t0)*1000:.1f}ms")

    # 5. 合成
    t0 = time.time()
    result = multiply_blend(background, processed, fast_mode=fast_mode)
    t1 = time.time()
    print(f"图像合成: {(t1-t0)*1000:.1f}ms")

    total_time = time.time() - total_start
    print(f"\n总耗时: {total_time*1000:.1f}ms ({total_time:.2f}s)")
    print(f"平均每字: {(total_time/len(text))*1000:.2f}ms")

    return total_time


if __name__ == "__main__":
    # 测试50字文本
    test_text = "大三学年是大学期间承上启下的关键一年。在这一年里，我始终保持着严谨求学的态度。"
    print(f"测试文本: {test_text}")
    print(f"字数: {len(test_text)}")

    # 测试标准模式
    time_std = test_generation(test_text, fast_mode=False, quality=2)

    # 测试极速模式
    time_fast = test_generation(test_text, fast_mode=True, quality=2)

    print(f"\n{'='*60}")
    print("对比结果")
    print(f"{'='*60}")
    print(f"标准模式: {time_std:.2f}s")
    print(f"极速模式: {time_fast:.2f}s")
    print(f"提速: {(time_std/time_fast):.1f}x")
