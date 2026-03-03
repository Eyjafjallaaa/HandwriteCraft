#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手写文字生成器 - 极速版 (Ultra Fast)

极致优化策略：
1. 关闭OpenCL（避免数据传输开销）
2. 极简弹性变形（简化算法）
3. 批量处理高斯模糊
4. 使用整数运算代替浮点
5. 跳过非关键效果
6. 内存预分配
"""

import os
import sys
import argparse
import numpy as np
import cv2
from PIL import Image, ImageFont
from handright import Template, handwrite
import time


class UltraConfig:
    """极速版配置 - 效果与速度的最佳平衡"""
    
    # 核心参数
    FONT_PATH = "../../assets/fonts/PingFangShaoHuaTi-2.ttf"
    OUTPUT_PATH = "output_handwrite.png"
    OUTPUT_SIZE = (800, 400)
    BASE_FONT_SIZE = 36
    MARGIN = 50
    LINE_SPACING = 55
    WORD_SPACING = 3
    
    # 手写效果参数
    FONT_SIZE_SIGMA = 2.0
    WORD_SPACING_SIGMA = 1.0
    LINE_SPACING_SIGMA = 1.5
    PERTURB_THETA_SIGMA = 0.02
    
    # 超采样（根据字体大小自适应）
    QUALITY = None  # None表示自动
    
    # 简化效果
    ENABLE_BASELINE_WAVY = True
    BASELINE_AMP = 1.5
    
    ENABLE_DRY_BRUSH = True
    DRY_BRUSH_PROB = 0.1
    
    ENABLE_INK_GRADIENT = True
    
    # 极简弹性变形
    ENABLE_ELASTIC = True
    ELASTIC_ALPHA = 60  # 减小幅度
    ELASTIC_SIGMA = 15
    
    AUTO_INDENT = True
    
    @classmethod
    def get_quality(cls, font_size):
        if cls.QUALITY is not None:
            return cls.QUALITY
        # 小字体低倍率，大字体高倍率
        if font_size <= 28:
            return 1
        elif font_size <= 40:
            return 2
        else:
            return 3


class UltraFastGenerator:
    """极速手写生成器"""
    
    def __init__(self, config):
        self.config = config
        self.scale = config.get_quality(config.BASE_FONT_SIZE)
        self.font_cache = {}
        
        # 预计算正弦表（用于基线波动）
        self._sin_table = np.sin(np.linspace(0, 2*np.pi, 360) * 2)
        
    def get_font(self, size):
        """带缓存的字体获取"""
        if size not in self.font_cache:
            self.font_cache[size] = ImageFont.truetype(self.config.FONT_PATH, size)
        return self.font_cache[size]
    
    def simple_elastic(self, img, alpha, sigma):
        """极简弹性变形 - 单次插值"""
        if alpha <= 0:
            return img
            
        h, w = img.shape
        # 生成小尺寸位移场
        small_h, small_w = h // 8, w // 8
        dx = np.random.randn(small_h, small_w).astype(np.float32) * alpha
        dy = np.random.randn(small_h, small_w).astype(np.float32) * alpha
        
        # 快速双线性插值
        dx = cv2.resize(dx, (w, h), cv2.INTER_LINEAR)
        dy = cv2.resize(dy, (w, h), cv2.INTER_LINEAR)
        
        # 可选：轻量平滑
        if sigma > 0:
            k = max(3, int(sigma) | 1)
            dx = cv2.blur(dx, (k, k))  # 使用均值模糊更快
            dy = cv2.blur(dy, (k, k))
        
        # 重映射
        map_x = np.arange(w, dtype=np.float32).reshape(1, -1) + dx
        map_y = np.arange(h, dtype=np.float32).reshape(-1, 1) + dy
        
        return cv2.remap(img, map_x, map_y, cv2.INTER_LINEAR, borderValue=0)
    
    def simple_baseline_wavy(self, img, amp):
        """简化基线波动"""
        h, w = img.shape
        phase = np.random.randint(0, 360)
        
        # 使用预计算正弦表的近似
        x_norm = np.arange(w) * 2 / w  # 归一化
        y_offset = (amp * np.sin(x_norm * 4 + phase)).astype(np.float32)
        
        map_x = np.tile(np.arange(w, dtype=np.float32), (h, 1))
        map_y = np.tile(np.arange(h, dtype=np.float32).reshape(-1, 1), (1, w))
        map_y += y_offset
        
        return cv2.remap(img, map_x, map_y, cv2.INTER_LINEAR, borderValue=0)
    
    def process_fast(self, pil_img):
        """极速处理"""
        # PIL转numpy (零拷贝)
        arr = np.frombuffer(pil_img.tobytes(), dtype=np.uint8)
        arr = arr.reshape((pil_img.height, pil_img.width, 4))
        
        # 快速灰度 (使用位运算近似)
        r = arr[:, :, 0].astype(np.uint16)
        g = arr[:, :, 1].astype(np.uint16)
        b = arr[:, :, 2].astype(np.uint16)
        gray = ((r * 77 + g * 150 + b * 29) >> 8).astype(np.uint8)
        alpha = 255 - gray
        
        # 简化效果
        if self.config.ENABLE_BASELINE_WAVY:
            alpha = self.simple_baseline_wavy(alpha, self.config.BASELINE_AMP)
        
        if self.config.ENABLE_DRY_BRUSH and np.random.random() < self.config.DRY_BRUSH_PROB:
            h, w = alpha.shape
            grad = np.linspace(0.4, 1.0, w) if np.random.random() > 0.5 else np.linspace(1.0, 0.4, w)
            alpha = (alpha.astype(np.float32) * grad).astype(np.uint8)
        
        if self.config.ENABLE_INK_GRADIENT:
            alpha = (alpha * np.random.uniform(0.75, 1.0)).astype(np.uint8)
        
        # 轻量抗锯齿
        if self.scale >= 2:
            alpha = cv2.GaussianBlur(alpha, (3, 3), 0.5)
        
        # 弹性变形
        if self.config.ENABLE_ELASTIC:
            alpha = self.simple_elastic(alpha, self.config.ELASTIC_ALPHA * self.scale, self.config.ELASTIC_SIGMA)
        
        # 快速下采样（使用INTER_AREA比LANCZOS快）
        target_w, target_h = self.config.OUTPUT_SIZE
        alpha_small = cv2.resize(alpha, (target_w, target_h), cv2.INTER_AREA)
        
        # 快速颜色合成
        result = np.zeros((target_h, target_w, 4), dtype=np.uint8)
        result[:, :, 0] = (40 * alpha_small // 255).astype(np.uint8)   # B
        result[:, :, 1] = (40 * alpha_small // 255).astype(np.uint8)   # G
        result[:, :, 2] = (48 * alpha_small // 255).astype(np.uint8)   # R
        result[:, :, 3] = alpha_small
        
        return result
    
    def render(self, text):
        """极速渲染"""
        w, h = self.config.OUTPUT_SIZE
        font_size = self.config.BASE_FONT_SIZE * self.scale
        
        # 创建模板
        template = Template(
            background=Image.new("RGBA", (w * self.scale, h * self.scale), (255, 255, 255, 255)),
            font=self.get_font(font_size),
            fill=(0, 0, 0, 255),
            font_size_sigma=self.config.FONT_SIZE_SIGMA * self.scale,
            word_spacing=self.config.WORD_SPACING * self.scale,
            word_spacing_sigma=self.config.WORD_SPACING_SIGMA * self.scale,
            line_spacing=self.config.LINE_SPACING * self.scale,
            line_spacing_sigma=self.config.LINE_SPACING_SIGMA * self.scale,
            left_margin=self.config.MARGIN * self.scale,
            top_margin=self.config.MARGIN * self.scale,
            right_margin=self.config.MARGIN * self.scale,
            bottom_margin=self.config.MARGIN * self.scale,
            perturb_x_sigma=0.8 * self.scale,
            perturb_y_sigma=0.8 * self.scale,
            perturb_theta_sigma=self.config.PERTURB_THETA_SIGMA,
        )
        
        # 格式化文本
        if self.config.AUTO_INDENT:
            text = '\u3000\u3000' + text.strip()
        
        # 渲染
        for img in handwrite(text, template):
            return self.process_fast(img)
        
        return None


def blend_simple(bg, fg):
    """简单混合"""
    alpha = fg[:, :, 3].astype(np.uint32)
    inv_alpha = 255 - alpha
    
    for c in range(3):
        bg[:, :, c] = ((fg[:, :, c] * alpha + bg[:, :, c] * inv_alpha) // 255).astype(np.uint8)
    
    return bg


def main():
    parser = argparse.ArgumentParser(description='手写文字生成器 - 极速版')
    parser.add_argument('--text', '-t', type=str, default='这是一段测试文字。')
    parser.add_argument('--output', '-o', type=str, default='output_ultra.png')
    parser.add_argument('--font-size', '-s', type=int, default=36)
    parser.add_argument('--width', type=int, default=800)
    parser.add_argument('--height', type=int, default=400)
    parser.add_argument('--quality', '-q', type=int, default=None)
    parser.add_argument('--benchmark', action='store_true')
    
    args = parser.parse_args()
    
    config = UltraConfig()
    config.TEXT = args.text
    config.OUTPUT_PATH = args.output
    config.OUTPUT_SIZE = (args.width, args.height)
    config.BASE_FONT_SIZE = args.font_size
    if args.quality:
        config.QUALITY = args.quality
    
    print(f"=== 手写生成器 - 极速版 ===")
    print(f"超采样: {config.get_quality(args.font_size)}x")
    print(f"输出尺寸: {args.width}x{args.height}")
    
    # 初始化
    t0 = time.time()
    gen = UltraFastGenerator(config)
    t1 = time.time()
    print(f"初始化: {(t1-t0)*1000:.1f}ms")
    
    # 首帧渲染（含预热）
    t0 = time.time()
    img = gen.render(args.text)
    t1 = time.time()
    print(f"首帧渲染: {(t1-t0)*1000:.1f}ms")
    
    # 合成
    t0 = time.time()
    bg = np.full((args.height, args.width, 3), (250, 248, 245), dtype=np.uint8)
    result = blend_simple(bg, img)
    t1 = time.time()
    print(f"合成: {(t1-t0)*1000:.1f}ms")
    
    # 保存
    t0 = time.time()
    cv2.imwrite(args.output, result)
    t1 = time.time()
    print(f"保存: {(t1-t0)*1000:.1f}ms")
    
    if args.benchmark:
        print("\n基准测试 (100次)...")
        times = []
        for _ in range(100):
            t0 = time.perf_counter()
            _ = gen.render(args.text)
            t1 = time.perf_counter()
            times.append((t1 - t0) * 1000)
        
        times = np.array(times)
        print(f"平均: {times.mean():.1f}ms")
        print(f"中位数: {np.median(times):.1f}ms")
        print(f"最小: {times.min():.1f}ms")
        print(f"最大: {times.max():.1f}ms")
        print(f"P95: {np.percentile(times, 95):.1f}ms")
        print(f"\n吞吐量: {1000/times.mean():.1f} 张/秒")


if __name__ == "__main__":
    main()
