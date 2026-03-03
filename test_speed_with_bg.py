#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试带背景图片时的性能
"""

import time
import sys
import os
import base64

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend/src'))

from handwrite_generator import Config, load_font, render_handwrite_text, process_text_image, multiply_blend, load_background_with_image


def test_with_background(bg_path, text, fast_mode=False):
    """测试带背景的性能"""
    print(f"\n{'='*60}")
    print(f"模式: {'极速' if fast_mode else '标准'}, 背景: {bg_path}")
    print(f"{'='*60}")

    # 配置
    Config.FAST_MODE = fast_mode
    Config.SUPER_SAMPLE_SCALE = 2
    Config.OUTPUT_SIZE = (1240, 1754)
    Config.BASE_FONT_SIZE = 36
    Config.ENABLE_INK_BLOTS = not fast_mode

    # 读取背景图片
    with open(bg_path, 'rb') as f:
        img_data = base64.b64encode(f.read()).decode()
        bg_data_url = f"data:image/png;base64,{img_data}"

    Config.BACKGROUND_IMAGE = bg_path

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

    # 4. 加载背景（包含图片读取和缩放）
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

    return total_time


if __name__ == "__main__":
    # 使用默认模板背景
    bg_path = "assets/templates/a4.png"
    test_text = "测试文字内容，用于验证生成速度。"

    if not os.path.exists(bg_path):
        print(f"背景文件不存在: {bg_path}")
        sys.exit(1)

    # 标准模式
    time_std = test_with_background(bg_path, test_text, fast_mode=False)

    # 极速模式
    time_fast = test_with_background(bg_path, test_text, fast_mode=True)

    print(f"\n{'='*60}")
    print("对比结果")
    print(f"{'='*60}")
    print(f"标准模式: {time_std:.2f}s")
    print(f"极速模式: {time_fast:.2f}s")
    print(f"提速: {(time_std/time_fast):.1f}x")
