#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手写生成时间基准测试
测试不同字数、不同质量设置下的真实渲染时间
"""

import time
import sys
import os
import numpy as np
from PIL import Image, ImageFont

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend/src'))

from handwrite_generator_fast import FastHandwriteGenerator, FastConfig, PerformanceConfig
from handwrite_generator import Config as StandardConfig, load_font, render_handwrite_text, process_text_image, multiply_blend, load_background


def generate_test_text(char_count):
    """生成指定字数的测试文本"""
    # 使用一段重复的中文文本
    base_text = """大三学年（2024-2025学年）是大学期间承上启下，专业技能飞速提升的关键一年。
在这一学年里，我始终保持着严谨求学的态度，在专业理论学习、前沿技术探索以及个人综合素质培养方面均取得了显著的进步。
在思想与专业学习方面，我不仅扎实掌握了各项核心专业课程，更将极大的热情投入到了课外的技术钻研中。
我深入学习了Node.js与Rust编程语言，并结合Tauri框架进行了实践探索。
同时，我对多智能体AI系统产生了浓厚的兴趣，不仅深度剖析了OpenClaw、Eigen等开源项目的底层逻辑，
还亲手进行了环境配置与部署调试，极大提升了我的动手能力和系统性思维。"""

    # 重复文本直到达到指定字数
    text = ""
    while len(text) < char_count:
        text += base_text
    return text[:char_count]


def benchmark_standard_mode(text, quality=2):
    """测试标准模式的渲染时间"""
    config = StandardConfig()
    config.TEXT = text
    config.OUTPUT_SIZE = (1240, 1754)
    config.BASE_FONT_SIZE = 36
    config.SUPER_SAMPLE_SCALE = quality
    config.FAST_MODE = False
    config.ELASTIC_ALPHA = 80
    config.ELASTIC_SIGMA = 12

    # 加载字体
    font_path = "assets/fonts/PingFangShaoHuaTi-2.ttf"
    font = load_font(font_path)

    times = {}

    # 1. 渲染时间
    t0 = time.time()
    text_image = render_handwrite_text(text, font)
    t1 = time.time()
    times['render'] = t1 - t0

    # 2. 图像处理时间
    t0 = time.time()
    processed = process_text_image(text_image, fast_mode=False)
    t1 = time.time()
    times['process'] = t1 - t0

    # 3. 背景合成时间
    t0 = time.time()
    background = load_background()
    result = multiply_blend(background, processed)
    t1 = time.time()
    times['compose'] = t1 - t0

    times['total'] = times['render'] + times['process'] + times['compose']
    return times


def benchmark_fast_mode(text, quality=2):
    """测试极速模式的渲染时间"""
    config = FastConfig()
    config.TEXT = text
    config.OUTPUT_SIZE = (1240, 1754)
    config.BASE_FONT_SIZE = 36

    # 设置质量
    PerformanceConfig.MIN_QUALITY = quality
    PerformanceConfig.MAX_QUALITY = quality

    # 加载字体
    font_path = "assets/fonts/PingFangShaoHuaTi-2.ttf"
    font = ImageFont.truetype(font_path, config.BASE_FONT_SIZE)

    times = {}

    # 完整生成流程
    t0 = time.time()
    generator = FastHandwriteGenerator(config)
    text_image = generator.render(text, font)
    t1 = time.time()
    times['total'] = t1 - t0

    return times


def run_benchmark():
    """运行完整基准测试"""
    # 测试不同字数
    char_counts = [50, 100, 200, 300, 500, 800, 1000, 1500]
    qualities = [1, 2, 3]

    print("=" * 80)
    print("手写生成时间基准测试")
    print("=" * 80)

    results = []

    for quality in qualities:
        print(f"\n{'='*80}")
        print(f"质量设置: {quality}x 超采样")
        print(f"{'='*80}")

        for char_count in char_counts:
            text = generate_test_text(char_count)
            print(f"\n测试字数: {char_count} 字")
            print("-" * 40)

            # 测试标准模式
            try:
                times_std = benchmark_standard_mode(text, quality)
                print(f"  标准模式: {times_std['total']:.2f}s "
                      f"(渲染: {times_std['render']:.2f}s, "
                      f"处理: {times_std['process']:.2f}s, "
                      f"合成: {times_std['compose']:.2f}s)")
            except Exception as e:
                print(f"  标准模式失败: {e}")
                times_std = {'total': None}

            # 测试极速模式
            try:
                times_fast = benchmark_fast_mode(text, quality)
                print(f"  极速模式: {times_fast['total']:.2f}s")
            except Exception as e:
                print(f"  极速模式失败: {e}")
                times_fast = {'total': None}

            results.append({
                'char_count': char_count,
                'quality': quality,
                'standard_time': times_std['total'],
                'fast_time': times_fast['total']
            })

    # 输出汇总结果
    print(f"\n{'='*80}")
    print("测试结果汇总")
    print(f"{'='*80}")
    print(f"{'字数':<8} {'质量':<6} {'标准模式(秒)':<15} {'极速模式(秒)':<15}")
    print("-" * 50)

    for r in results:
        std_str = f"{r['standard_time']:.2f}" if r['standard_time'] else "N/A"
        fast_str = f"{r['fast_time']:.2f}" if r['fast_time'] else "N/A"
        print(f"{r['char_count']:<8} {r['quality']:<6} {std_str:<15} {fast_str:<15}")

    # 计算平均每字时间
    print(f"\n{'='*80}")
    print("平均每字处理时间（排除固定开销）")
    print(f"{'='*80}")

    for quality in qualities:
        quality_results = [r for r in results if r['quality'] == quality and r['standard_time']]
        if len(quality_results) >= 2:
            # 使用线性回归计算每字时间
            x = np.array([r['char_count'] for r in quality_results])
            y_std = np.array([r['standard_time'] for r in quality_results])
            y_fast = np.array([r['fast_time'] for r in quality_results if r['fast_time']])

            # 简单线性拟合 y = a*x + b
            a_std, b_std = np.polyfit(x, y_std, 1)
            if len(y_fast) == len(x):
                a_fast, b_fast = np.polyfit(x, y_fast, 1)
                print(f"\n质量 {quality}x:")
                print(f"  标准模式: 每字 {a_std*1000:.2f}ms + 固定开销 {b_std:.2f}s")
                print(f"  极速模式: 每字 {a_fast*1000:.2f}ms + 固定开销 {b_fast:.2f}s")
                print(f"  极速模式提速: {(1-a_fast/a_std)*100:.1f}%")

    return results


if __name__ == "__main__":
    # 检查字体文件是否存在
    font_path = "assets/fonts/PingFangShaoHuaTi-2.ttf"
    if not os.path.exists(font_path):
        print(f"错误: 字体文件不存在: {font_path}")
        print("请确保在正确的工作目录运行脚本")
        sys.exit(1)

    results = run_benchmark()
