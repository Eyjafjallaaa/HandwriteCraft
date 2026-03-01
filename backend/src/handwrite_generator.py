#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手写文字生成器 - 专业级图像合成引擎

使用方法:
    python handwrite_generator.py --text "要转换的文字"
    python handwrite_generator.py --text "文字" --font-size 40 --line-spacing 50
    python handwrite_generator.py --text-file text.txt --output result.png
"""

import os
import sys
import argparse
import numpy as np
import cv2
from PIL import Image, ImageFont
from handright import Template, handwrite


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='手写文字生成器 - 将文本转换为逼真的手写图片',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python handwrite_generator.py --text "你好世界"
  python handwrite_generator.py --text "文字内容" --font-size 36 --line-spacing 55
  python handwrite_generator.py --text-file text.txt --font-size 40
        '''
    )
    
    # 文字内容
    parser.add_argument('--text', '-t', type=str, 
                        help='要转换的文字内容')
    parser.add_argument('--text-file', '-f', type=str,
                        help='从文件读取文字内容')
    
    # 排版参数
    parser.add_argument('--font-size', '-s', type=int, default=36,
                        help='字体大小 (默认: 36)')
    parser.add_argument('--line-spacing', '-l', type=int, default=55,
                        help='行距 (默认: 55)')
    parser.add_argument('--word-spacing', '-w', type=int, default=3,
                        help='字间距 (默认: 3)')
    parser.add_argument('--margin-left', type=int, default=50,
                        help='左边距 (默认: 50)')
    parser.add_argument('--margin-top', type=int, default=60,
                        help='上边距 (默认: 60)')
    parser.add_argument('--margin-right', type=int, default=50,
                        help='右边距 (默认: 50)')
    parser.add_argument('--margin-bottom', type=int, default=60,
                        help='下边距 (默认: 60)')
    
    # 输出参数
    parser.add_argument('--output', '-o', type=str, default='output_handwrite.png',
                        help='输出文件名 (默认: output_handwrite.png)')
    parser.add_argument('--width', type=int, default=1200,
                        help='输出图片宽度 (默认: 1200)')
    parser.add_argument('--height', type=int, default=1600,
                        help='输出图片高度 (默认: 1600)')
    
    # 其他参数
    parser.add_argument('--font', type=str, default=None,
                        help='字体文件路径 (默认使用 Config.FONT_PATH)')
    parser.add_argument('--ink-color', type=str, default='#282830',
                        help='墨水颜色 (默认: #282830)')
    parser.add_argument('--transparent', action='store_true',
                        help='透明背景（无纸张纹理）')
    parser.add_argument('--quality', type=int, default=3,
                        help='清晰度/超采样倍率 (默认: 3)')
    parser.add_argument('--font-size-sigma', type=float, default=1.2,
                        help='字体大小波动 (默认: 1.2)')
    parser.add_argument('--line-spacing-sigma', type=float, default=1.5,
                        help='行距波动 (默认: 1.5)')
    parser.add_argument('--word-spacing-sigma', type=float, default=1.0,
                        help='字间距波动 (默认: 1.0)')
    parser.add_argument('--perturb-theta-sigma', type=float, default=0.015,
                        help='角度波动 (默认: 0.015)')
    
    # 区域渲染参数 (JSON格式)
    parser.add_argument('--regions', type=str, default=None,
                        help='区域渲染参数 (JSON格式)')
    parser.add_argument('--background-image', type=str, default=None,
                        help='背景图片路径 (可选)')
    
    return parser.parse_args()


# 默认文字内容（当没有提供--text参数时使用）
DEFAULT_TEXT = """大三学年（2024-2025学年）是大学期间承上启下，专业技能飞速提升的关键一年。在这一学年里，我始终保持着严谨求学的态度，在专业理论学习、前沿技术探索以及个人综合素质培养方面均取得了显著的进步。

在思想与专业学习方面，我不仅扎实掌握了各项核心专业课程，更将极大的热情投入到了课外的技术钻研中。我深入学习了Node.js与Rust编程语言，并结合Tauri框架进行了实践探索。同时，我对多智能体AI系统产生了浓厚的兴趣，不仅深度剖析了OpenClaw、Eigen等开源项目的底层逻辑，还亲手进行了环境配置与部署调试，极大提升了我的动手能力和系统性思维。在明确了自己偏向于理解而非死记硬背的学习风格后，我确立了备考"系统架构设计师"高级软考的目标，致力于从宏观架构层面提升自己的技术视野。此外，我意识到语言的实用价值，坚持进行英语日常听力和口语的训练，努力摆脱"哑巴英语"，以适应未来更广阔的技术交流需求。

在个人生活方面，我，保持着高度的自律坚持劳逸结合。我养成了每天晚上7点到10点进行体育锻炼的习惯，经常去打羽毛球，这不仅强化了我的身体素质，也让我在面对高强度的代码学习时能保持专注与活力。

综上所述，大三学年是我明确技术方向、沉淀专业技能的一年。我将带着这份对技术的热爱和对生活的自律，以更加饱满的精神状态迎接大四的挑战与未来的职业发展。"""


class Config:
    """全局配置类 - 参数通过命令行传入"""
    
    # 占位符，会被命令行参数覆盖
    TEXT = ""
    FONT_PATH = "../../assets/fonts/PingFangShaoHuaTi-2.ttf"
    BACKGROUND_PATH = "../../assets/templates/a4.png"  # 纸张背景图片
    BACKGROUND_IMAGE = None  # 背景图片(Base64或路径)
    OUTPUT_PATH = "output_handwrite.png"
    OUTPUT_SIZE = (1200, 1600)
    BASE_FONT_SIZE = 36
    MARGIN_LEFT = 50
    MARGIN_TOP = 60
    MARGIN_RIGHT = 50
    MARGIN_BOTTOM = 60
    LINE_SPACING = 55
    WORD_SPACING = 3
    
    # 区域渲染配置
    REGIONS = []  # 区域列表，每个区域包含x, y, width, height, text, fontSize等
    
    # 手写扰动参数
    FONT_SIZE_SIGMA = 1.2
    WORD_SPACING_SIGMA = 1.0
    LINE_SPACING_SIGMA = 1.5
    PERTURB_THETA_SIGMA = 0.015
    
    # 图形增强参数
    SUPER_SAMPLE_SCALE = 3
    INK_BLEED_KERNEL = 3
    DOWNSAMPLE_INTERPOLATION = cv2.INTER_LANCZOS4
    INK_COLOR = (40, 40, 48)  # BGR
    
    # 纸张参数
    PAPER_COLOR = (250, 248, 245)
    TEXTURE_STRENGTH = 6
    TRANSPARENT_BACKGROUND = False  # 透明背景选项
    
    # 清晰度和手写参数
    SUPER_SAMPLE_SCALE = 2  # 2倍超采样保证清晰度
    FONT_SIZE_SIGMA = 1.2
    WORD_SPACING_SIGMA = 1.0
    LINE_SPACING_SIGMA = 1.5
    PERTURB_THETA_SIGMA = 0.015
    
    @classmethod
    def from_args(cls, args):
        """从命令行参数更新配置"""
        # 文字内容
        if args.text:
            cls.TEXT = args.text
        elif args.text_file:
            if os.path.exists(args.text_file):
                with open(args.text_file, 'r', encoding='utf-8') as f:
                    cls.TEXT = f.read()
            else:
                print(f"[警告] 文件不存在: {args.text_file}，使用默认文字")
                cls.TEXT = DEFAULT_TEXT
        else:
            cls.TEXT = DEFAULT_TEXT
        
        # 文件路径
        if args.font:
            cls.FONT_PATH = args.font
        cls.OUTPUT_PATH = args.output
        
        # 尺寸
        cls.OUTPUT_SIZE = (args.width, args.height)
        
        # 字体和排版
        cls.BASE_FONT_SIZE = args.font_size
        cls.LINE_SPACING = args.line_spacing
        cls.WORD_SPACING = args.word_spacing
        cls.MARGIN_LEFT = args.margin_left
        cls.MARGIN_TOP = args.margin_top
        cls.MARGIN_RIGHT = args.margin_right
        cls.MARGIN_BOTTOM = args.margin_bottom
        
        # 墨水颜色
        if args.ink_color.startswith('#'):
            hex_color = args.ink_color[1:]
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            cls.INK_COLOR = (b, g, r)  # BGR
        
        # 透明背景
        cls.TRANSPARENT_BACKGROUND = getattr(args, 'transparent', False)
        
        # 清晰度和手写参数
        cls.SUPER_SAMPLE_SCALE = getattr(args, 'quality', 3)
        cls.FONT_SIZE_SIGMA = getattr(args, 'font_size_sigma', 1.2)
        cls.WORD_SPACING_SIGMA = getattr(args, 'word_spacing_sigma', 1.0)
        cls.LINE_SPACING_SIGMA = getattr(args, 'line_spacing_sigma', 1.5)
        cls.PERTURB_THETA_SIGMA = getattr(args, 'perturb_theta_sigma', 0.015)
        
        # 背景图片
        cls.BACKGROUND_IMAGE = getattr(args, 'background_image', None)
        
        # 区域渲染参数
        regions_file = getattr(args, 'regions', None)
        if regions_file and os.path.exists(regions_file):
            import json
            try:
                with open(regions_file, 'r', encoding='utf-8') as f:
                    cls.REGIONS = json.load(f)
                print(f"[*] 解析到 {len(cls.REGIONS)} 个渲染区域")
                for i, region in enumerate(cls.REGIONS):
                    print(f"    区域 {i+1}: {region.get('text', '')[:30]}...")
            except (json.JSONDecodeError, IOError) as e:
                print(f"[警告] 区域参数解析失败: {e}")
                cls.REGIONS = []
        elif regions_file:
            print(f"[警告] 区域文件不存在: {regions_file}")
        
        return cls


def load_font(font_path: str, font_size: int):
    """加载字体文件"""
    
    if not os.path.exists(font_path):
        raise FileNotFoundError(
            f"字体文件未找到: {font_path}\n"
            f"请检查字体文件路径"
        )
    
    font = ImageFont.truetype(font_path, font_size)
    print(f"[OK] 字体加载成功: {font_path}")
    return font


def create_paper_texture(width: int, height: int) -> np.ndarray:
    """生成带纹理的纸张背景"""
    print(f"[*] 生成纸张纹理: {width}x{height}")
    
    # 1. 创建基础颜色层
    base_color = np.full((height, width, 3), Config.PAPER_COLOR, dtype=np.float32)
    
    # 2. 生成随机纹理
    texture = np.random.randn(height, width).astype(np.float32) * Config.TEXTURE_STRENGTH
    
    # 3. 高斯模糊使纹理平滑 (先模糊再扩展)
    texture = cv2.GaussianBlur(texture, (21, 21), 0)
    
    # 4. 扩展到三通道 (广播到每个颜色通道)
    texture = texture[:, :, np.newaxis]
    
    # 5. 叠加纹理
    paper = base_color + texture
    
    # 6. 裁剪到有效范围
    paper = np.clip(paper, 0, 255)
    
    # 7. 转换为uint8
    paper = paper.astype(np.uint8)
    
    print(f"[OK] 纸张纹理生成完成")
    return paper


def load_background() -> np.ndarray:
    """加载或生成背景图片"""
    width, height = Config.OUTPUT_SIZE
    
    # 如果透明背景，返回全透明图像
    if Config.TRANSPARENT_BACKGROUND:
        print(f"[*] 使用透明背景")
        return np.zeros((height, width, 3), dtype=np.uint8)
    
    if Config.BACKGROUND_PATH and os.path.exists(Config.BACKGROUND_PATH):
        print(f"[*] 加载背景图片: {Config.BACKGROUND_PATH}")
        background = cv2.imread(Config.BACKGROUND_PATH)
        
        if background is not None:
            mean_brightness = np.mean(background)
            if mean_brightness > 250:
                print(f"[*] 检测到空白背景，自动生成纹理")
                background = create_paper_texture(width, height)
            else:
                background = cv2.resize(background, (width, height), 
                                       interpolation=cv2.INTER_LANCZOS4)
                print(f"[OK] 背景图片加载成功")
                return background
    
    return create_paper_texture(width, height)


def render_handwrite_text(text: str, font) -> Image.Image:
    """
    使用Handright渲染手写文本
    
    核心原理：
    Template定义了渲染参数，包括各种随机扰动幅度
    handwrite()对每个字符应用随机扰动，模拟手写的不规则性
    """
    print(f"[*] 开始 Handright 渲染...")
    
    scale = Config.SUPER_SAMPLE_SCALE
    output_width, output_height = Config.OUTPUT_SIZE
    
    # 超采样尺寸
    render_width = output_width * scale
    render_height = output_height * scale
    
    # 超采样后的参数
    render_font_size = Config.BASE_FONT_SIZE * scale
    render_margin_left = Config.MARGIN_LEFT * scale
    render_margin_top = Config.MARGIN_TOP * scale
    render_margin_right = Config.MARGIN_RIGHT * scale
    render_margin_bottom = Config.MARGIN_BOTTOM * scale
    render_line_spacing = Config.LINE_SPACING * scale
    render_word_spacing = Config.WORD_SPACING * scale
    
    # 重新创建字体
    font = ImageFont.truetype(font.path, render_font_size)
    
    # 创建Handright模板
    template = Template(
        # 背景设为白色不透明，这样文字才能渲染出来
        background=Image.new("RGBA", (render_width, render_height), (255, 255, 255, 255)),
        font=font,
        # 文字颜色 - 黑色(RGBA)
        fill=(0, 0, 0, 255),
        # 字体大小波动 - 让每个字的大小略有不同
        font_size_sigma=Config.FONT_SIZE_SIGMA * scale,
        # 字间距设置
        word_spacing=render_word_spacing,
        word_spacing_sigma=Config.WORD_SPACING_SIGMA * scale,
        # 行间距设置
        line_spacing=render_line_spacing,
        line_spacing_sigma=Config.LINE_SPACING_SIGMA * scale,
        # 边距
        left_margin=render_margin_left,
        top_margin=render_margin_top,
        right_margin=render_margin_right,
        bottom_margin=render_margin_bottom,
        # 位置扰动
        perturb_x_sigma=0.5 * scale,
        perturb_y_sigma=0.5 * scale,
        # 旋转角度扰动
        perturb_theta_sigma=Config.PERTURB_THETA_SIGMA,
    )
    
    # 执行渲染
    text_image = None
    for img in handwrite(text, template):
        text_image = img
        break
    
    print(f"[OK] Handright渲染完成，尺寸: {text_image.size}")
    return text_image


def apply_ink_bleed(image: np.ndarray, kernel_size: int) -> np.ndarray:
    """
    应用墨水晕染效果 - 高斯模糊
    
    【为什么高斯模糊能模拟墨水晕染？】
    
    物理背景：
    当墨水接触纸张时，发生毛细现象、扩散作用和吸附作用。
    墨水在落笔点周围形成一个"扩散圈"。
    
    数学模型：
    扩散方程在无限时间后的稳态解恰好是高斯分布！
    G(x,y) = (1/2πσ²) × e^(-(x²+y²)/2σ²)
    
    卷积视角：
    高斯模糊是图像与高斯核的卷积，本质是"加权平均"。
    中心像素的值向周围扩散，这与墨水扩散的物理过程高度吻合。
    
    核大小的影响：
    - 3: 轻微晕染，适合钢笔
    - 5: 中等晕染，适合毛笔
    """
    print(f"[*] 应用墨水晕染 (核大小: {kernel_size})")
    
    if kernel_size % 2 == 0:
        kernel_size += 1
    
    blurred = cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
    print(f"[OK] 墨水晕染完成")
    return blurred


def downsample_image(image: np.ndarray, target_size: tuple, 
                     interpolation: int = cv2.INTER_LANCZOS4) -> np.ndarray:
    """
    下采样图像
    
    【为什么超采样能抗锯齿？】
    
    假设3倍超采样：
    - 原来1个像素 → 3×3=9个像素
    - 渲染时，细节被记录在这9个像素中
    - 缩小时，这9个像素的信息被"融合"成1个像素
    - 融合过程就是插值算法
    
    插值算法比较：
    - INTER_NEAREST: 最近邻，速度快但有锯齿
    - INTER_LINEAR: 双线性，效果中等
    - INTER_CUBIC: 双三次，效果较好
    - INTER_LANCZOS4: Lanczos，最高质量，保留最多细节
    """
    print(f"[*] 下采样: {image.shape[1]}x{image.shape[0]} -> {target_size[0]}x{target_size[1]}")
    
    resized = cv2.resize(image, target_size, interpolation=interpolation)
    print(f"[OK] 下采样完成")
    return resized


def process_text_image(text_image_pil: Image.Image) -> np.ndarray:
    """处理文字图像 - 改进抗锯齿"""
    print(f"[*] 开始处理文字图像...")
    
    # PIL转NumPy - 使用更高精度
    text_image_rgba = np.array(text_image_pil)
    
    # 提取灰度 - 使用加权平均更符合人眼感知
    r = text_image_rgba[:, :, 0].astype(np.float32)
    g = text_image_rgba[:, :, 1].astype(np.float32)
    b = text_image_rgba[:, :, 2].astype(np.float32)
    gray_mean = 0.299 * r + 0.587 * g + 0.114 * b
    
    # alpha = 255 - 灰度
    alpha = (255 - gray_mean).astype(np.uint8)
    
    # 抗锯齿优化：在超采样图像上进行轻微高斯模糊
    scale = Config.SUPER_SAMPLE_SCALE
    if scale >= 2:
        if scale <= 5:
            blur_kernel = 3
        elif scale <= 10:
            blur_kernel = 5
        else:
            blur_kernel = 7
        sigma = 0.5 + (scale / 20)
        alpha = cv2.GaussianBlur(alpha, (blur_kernel, blur_kernel), sigma)
        print(f"[*] 应用抗锯齿模糊 (核大小: {blur_kernel}, sigma: {sigma:.2f})")
    
    # 下采样到目标尺寸 - 使用PIL的LANCZOS高质量缩放
    target_width, target_height = Config.OUTPUT_SIZE
    
    # 转换回PIL进行高质量缩放
    alpha_pil = Image.fromarray(alpha)
    alpha_resized = alpha_pil.resize((target_width, target_height), Image.Resampling.LANCZOS)
    alpha_downsampled = np.array(alpha_resized)
    
    # 创建带颜色的文字图像
    height, width = alpha_downsampled.shape
    text_image_final = np.zeros((height, width, 4), dtype=np.uint8)
    
    # 颜色映射
    alpha_normalized = alpha_downsampled.astype(np.float32) / 255.0
    
    for i, color_value in enumerate(Config.INK_COLOR):
        text_image_final[:, :, i] = (color_value * alpha_normalized).astype(np.uint8)
    
    text_image_final[:, :, 3] = alpha_downsampled
    
    print(f"[OK] 文字图像处理完成")
    return text_image_final


def multiply_blend(background: np.ndarray, foreground: np.ndarray) -> np.ndarray:
    """
    正片叠底混合模式
    
    【数学公式】
    Result = (Background × Foreground) / 255
    
    【为什么能产生"渗入"效果？】
    
    情况1：背景白色(255)
    Result = (255 × Ink) / 255 = Ink
    白纸上墨水保持原色
    
    情况2：背景米黄色(250,248,245)，墨水深蓝黑(40,40,50)
    R: (250 × 40) / 255 ≈ 39
    G: (248 × 40) / 255 ≈ 39  
    B: (245 × 50) / 255 ≈ 48
    结果是略带蓝调的深灰色，像墨水渗入纸张
    
    物理解释：
    正片叠底模拟光线穿过墨水层照射到纸张再反射回眼睛的过程：
    最终光 = 入射光 × 墨水透过率 × 纸张反射率 × 墨水透过率
    """
    print(f"[*] 应用正片叠底混合...")
    
    fg_alpha = foreground[:, :, 3:4].astype(np.float32) / 255.0
    fg_color = foreground[:, :, :3].astype(np.float32)
    bg_color = background.astype(np.float32)
    
    # 正片叠底
    multiply_result = (bg_color * fg_color) / 255.0
    
    # Alpha混合
    final_result = multiply_result * fg_alpha + bg_color * (1 - fg_alpha)
    
    final_result = np.clip(final_result, 0, 255).astype(np.uint8)
    
    # 最终抗锯齿：轻微平滑处理
    # 使用双边滤波在保持边缘的同时减少锯齿
    final_result = cv2.edgePreservingFilter(final_result, flags=1, sigma_s=10, sigma_r=0.15)
    
    print(f"[OK] 正片叠底完成")
    return final_result


def load_background_with_image() -> np.ndarray:
    """加载背景图片，支持Base64编码、文件路径或PDF"""
    width, height = Config.OUTPUT_SIZE
    
    # 如果透明背景，返回全透明图像
    if Config.TRANSPARENT_BACKGROUND:
        print(f"[*] 使用透明背景")
        return np.zeros((height, width, 3), dtype=np.uint8)
    
    # 优先使用背景图片
    if Config.BACKGROUND_IMAGE:
        # 检查是否是文件路径（包含base64数据的文本文件）
        if os.path.exists(Config.BACKGROUND_IMAGE):
            try:
                with open(Config.BACKGROUND_IMAGE, 'r', encoding='utf-8') as f:
                    file_content = f.read().strip()
                
                # 如果文件内容以 data:image 开头，则是base64图片数据
                if file_content.startswith('data:image/png') or file_content.startswith('data:image/jpeg'):
                    print(f"[*] 从文件加载Base64背景图片")
                    base64_data = file_content.split(',')[1]
                    import base64
                    img_data = base64.b64decode(base64_data)
                    img_array = np.frombuffer(img_data, np.uint8)
                    background = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                    if background is not None:
                        background = cv2.resize(background, (width, height), 
                                              interpolation=cv2.INTER_LANCZOS4)
                        print(f"[OK] Base64背景图片加载成功")
                        return background
            except Exception as e:
                print(f"[警告] 读取背景文件失败: {e}")
        
        # 检查是否是直接的Base64编码的图片
        if Config.BACKGROUND_IMAGE.startswith('data:image/png') or Config.BACKGROUND_IMAGE.startswith('data:image/jpeg'):
            # 提取Base64数据
            base64_data = Config.BACKGROUND_IMAGE.split(',')[1]
            import base64
            img_data = base64.b64decode(base64_data)
            img_array = np.frombuffer(img_data, np.uint8)
            background = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            if background is not None:
                background = cv2.resize(background, (width, height), 
                                      interpolation=cv2.INTER_LANCZOS4)
                print(f"[OK] Base64背景图片加载成功")
                return background
        
        # 检查是否是PDF (data:application/pdf)
        elif Config.BACKGROUND_IMAGE.startswith('data:application/pdf'):
            print(f"[*] 检测到PDF背景，转换为图片...")
            try:
                import fitz  # PyMuPDF
                import base64
                
                base64_data = Config.BACKGROUND_IMAGE.split(',')[1]
                pdf_data = base64.b64decode(base64_data)
                
                pdf_doc = fitz.open(stream=pdf_data, filetype="pdf")
                page = pdf_doc[0]
                
                zoom = 2.0
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                
                if img.shape[2] == 4:
                    img = img[:, :, :3]
                img = img[:, :, ::-1]
                
                background = cv2.resize(img, (width, height), interpolation=cv2.INTER_LANCZOS4)
                print(f"[OK] PDF转换为图片成功")
                return background
            except Exception as e:
                print(f"[警告] PDF转换失败: {e}")
        
        elif os.path.exists(Config.BACKGROUND_IMAGE):
            # 检查是否是PDF文件
            if Config.BACKGROUND_IMAGE.lower().endswith('.pdf'):
                print(f"[*] 检测到PDF文件，转换为图片...")
                try:
                    import fitz
                    
                    pdf_doc = fitz.open(Config.BACKGROUND_IMAGE)
                    page = pdf_doc[0]
                    
                    zoom = 2.0
                    mat = fitz.Matrix(zoom, zoom)
                    pix = page.get_pixmap(matrix=mat)
                    
                    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                    
                    if img.shape[2] == 4:
                        img = img[:, :, :3]
                    img = img[:, :, ::-1]
                    
                    background = cv2.resize(img, (width, height), interpolation=cv2.INTER_LANCZOS4)
                    print(f"[OK] PDF文件转换为图片成功")
                    return background
                except Exception as e:
                    print(f"[警告] PDF转换失败: {e}")
            else:
                # 普通图片文件
                background = cv2.imread(Config.BACKGROUND_IMAGE)
                if background is not None:
                    background = cv2.resize(background, (width, height), 
                                          interpolation=cv2.INTER_LANCZOS4)
                    print(f"[OK] 背景图片加载成功: {Config.BACKGROUND_IMAGE}")
                    return background
    
    # 默认使用配置中的背景路径
    if Config.BACKGROUND_PATH and os.path.exists(Config.BACKGROUND_PATH):
        print(f"[*] 加载背景图片: {Config.BACKGROUND_PATH}")
        background = cv2.imread(Config.BACKGROUND_PATH)
        
        if background is not None:
            mean_brightness = np.mean(background)
            if mean_brightness > 250:
                print(f"[*] 检测到空白背景，自动生成纹理")
                background = create_paper_texture(width, height)
            else:
                background = cv2.resize(background, (width, height), 
                                       interpolation=cv2.INTER_LANCZOS4)
                print(f"[OK] 背景图片加载成功")
                return background
    
    return create_paper_texture(width, height)


def render_region_text(region: dict, font, background: np.ndarray) -> np.ndarray:
    """在指定区域渲染手写文字
    
    Args:
        region: 区域参数，包含 x, y, width, height, text, fontSize, lineSpacing, wordSpacing, inkColor 等
        font: 字体对象
        background: 背景图片
    
    Returns:
        合成后的图片
    """
    scale = Config.SUPER_SAMPLE_SCALE
    
    # 获取区域参数
    x = int(region.get('x', 0))
    y = int(region.get('y', 0))
    region_width = int(region.get('width', 200))
    region_height = int(region.get('height', 100))
    text = region.get('text', '')
    font_size = region.get('fontSize', Config.BASE_FONT_SIZE)
    line_spacing = region.get('lineSpacing', Config.LINE_SPACING)
    word_spacing = region.get('wordSpacing', Config.WORD_SPACING)
    
    # 获取手写风格参数（从region或全局Config）
    font_size_sigma = region.get('fontSizeSigma', Config.FONT_SIZE_SIGMA)
    line_spacing_sigma = region.get('lineSpacingSigma', Config.LINE_SPACING_SIGMA)
    word_spacing_sigma = region.get('wordSpacingSigma', Config.WORD_SPACING_SIGMA)
    perturb_theta_sigma = region.get('perturbThetaSigma', Config.PERTURB_THETA_SIGMA)
    
    # 解析墨水颜色
    ink_color_hex = region.get('inkColor', '#282830')
    if ink_color_hex.startswith('#'):
        hex_color = ink_color_hex[1:]
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        ink_color = (b, g, r)  # BGR
    else:
        ink_color = Config.INK_COLOR
    
    if not text.strip():
        return background
    
    # 超采样尺寸
    render_width = region_width * scale
    render_height = region_height * scale
    render_font_size = font_size * scale
    render_line_spacing = line_spacing * scale
    render_word_spacing = word_spacing * scale
    
    # 重新创建字体
    font = ImageFont.truetype(font.path, render_font_size)
    
    # 动态计算边距，确保区域高度足够
    # Handright 要求: height >= top_margin + line_spacing + bottom_margin
    min_required_height = render_line_spacing + 20 * scale  # 最小需要行距 + 上下边距
    if render_height < min_required_height:
        # 如果区域太小，调整行距和边距
        render_line_spacing = max(render_font_size, render_height // 2)
        margin = max(2 * scale, (render_height - render_line_spacing) // 3)
    else:
        margin = 10 * scale
    
    # 创建Handright模板
    template = Template(
        background=Image.new("RGBA", (render_width, render_height), (255, 255, 255, 255)),
        font=font,
        fill=(0, 0, 0, 255),
        font_size_sigma=font_size_sigma * scale,
        word_spacing=render_word_spacing,
        word_spacing_sigma=word_spacing_sigma * scale,
        line_spacing=render_line_spacing,
        line_spacing_sigma=line_spacing_sigma * scale,
        left_margin=int(margin),
        top_margin=int(margin),
        right_margin=int(margin),
        bottom_margin=int(margin),
        perturb_x_sigma=0.5 * scale,
        perturb_y_sigma=0.5 * scale,
        perturb_theta_sigma=perturb_theta_sigma,
    )
    
    # 渲染文字
    text_image = None
    for img in handwrite(text.strip(), template):
        text_image = img
        break
    
    # 处理文字图像
    text_image_rgba = np.array(text_image)
    r = text_image_rgba[:, :, 0].astype(np.float32)
    g = text_image_rgba[:, :, 1].astype(np.float32)
    b = text_image_rgba[:, :, 2].astype(np.float32)
    gray_mean = 0.299 * r + 0.587 * g + 0.114 * b
    alpha = (255 - gray_mean).astype(np.uint8)
    
    # 抗锯齿：根据倍率选择模糊核
    if scale >= 2:
        if scale <= 5:
            blur_kernel = 3
        elif scale <= 10:
            blur_kernel = 5
        else:
            blur_kernel = 7
        sigma = 0.5 + (scale / 20)
        alpha = cv2.GaussianBlur(alpha, (blur_kernel, blur_kernel), sigma)
    
    # 下采样到目标尺寸 - 使用PIL高质量缩放
    alpha_pil = Image.fromarray(alpha)
    alpha_resized = alpha_pil.resize((region_width, region_height), Image.Resampling.LANCZOS)
    alpha_downsampled = np.array(alpha_resized)
    
    # 创建带颜色的文字图像
    h, w = alpha_downsampled.shape
    text_image_final = np.zeros((h, w, 4), dtype=np.uint8)
    alpha_normalized = alpha_downsampled.astype(np.float32) / 255.0
    
    for i, color_value in enumerate(ink_color):
        text_image_final[:, :, i] = (color_value * alpha_normalized).astype(np.uint8)
    text_image_final[:, :, 3] = alpha_downsampled
    
    # 合成到背景
    result = background.copy()
    
    # 确保区域在边界内
    x = max(0, min(x, result.shape[1] - 1))
    y = max(0, min(y, result.shape[0] - 1))
    end_x = min(x + w, result.shape[1])
    end_y = min(y + h, result.shape[0])
    
    # 裁剪文字图像
    text_crop = text_image_final[:end_y-y, :end_x-x]
    
    # Alpha混合
    fg_alpha = text_crop[:, :, 3:4].astype(np.float32) / 255.0
    fg_color = text_crop[:, :, :3].astype(np.float32)
    bg_color = result[y:end_y, x:end_x].astype(np.float32)
    
    # 正片叠底
    multiply_result = (bg_color * fg_color) / 255.0
    blended = multiply_result * fg_alpha + bg_color * (1 - fg_alpha)
    blended = np.clip(blended, 0, 255).astype(np.uint8)
    
    result[y:end_y, x:end_x] = blended
    
    return result


def composite_and_export_pdf(text_image: np.ndarray, background: np.ndarray, 
                             output_path: str) -> None:
    """合成并导出为PDF"""
    print(f"[*] 开始合成PDF...")
    
    target_size = (text_image.shape[1], text_image.shape[0])
    if background.shape[:2] != (target_size[1], target_size[0]):
        background = cv2.resize(background, target_size, 
                               interpolation=cv2.INTER_LANCZOS4)
    
    # 应用正片叠底混合
    result = multiply_blend(background, text_image)
    
    # 保存为PNG临时文件
    temp_png = output_path.replace('.pdf', '_temp.png')
    success = cv2.imwrite(temp_png, result)
    if not success:
        raise IOError(f"无法写入临时文件: {temp_png}")
    
    # 使用reportlab生成PDF
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    from PIL import Image as PILImage
    
    # 创建PDF
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    # 计算图片尺寸以适应A4
    img = PILImage.open(temp_png)
    img_width, img_height = img.size
    scale = min(width / img_width, height / img_height) * 0.95
    draw_width = img_width * scale
    draw_height = img_height * scale
    x = (width - draw_width) / 2
    y = (height - draw_height) / 2
    
    # 绘制图片
    c.drawImage(ImageReader(temp_png), x, y, width=draw_width, height=draw_height)
    c.save()
    
    # 删除临时PNG
    os.remove(temp_png)
    
    print(f"[OK] PDF导出完成: {output_path}")
    print(f"    尺寸: {text_image.shape[1]}x{text_image.shape[0]}")


def composite_and_export(text_image: np.ndarray, background: np.ndarray, 
                         output_path: str) -> None:
    """合成并导出"""
    print(f"[*] 开始合成...")
    
    target_size = (text_image.shape[1], text_image.shape[0])
    if background.shape[:2] != (target_size[1], target_size[0]):
        background = cv2.resize(background, target_size, 
                               interpolation=cv2.INTER_LANCZOS4)
    
    if Config.TRANSPARENT_BACKGROUND:
        # 透明背景：直接使用文字图像（带Alpha通道）
        # 将BGRA转换为RGBA（OpenCV是BGR，PIL是RGB）
        rgba = cv2.cvtColor(text_image, cv2.COLOR_BGRA2RGBA)
        result = Image.fromarray(rgba)
        result.save(output_path, "PNG")
    else:
        # 正常背景：应用正片叠底混合
        result = multiply_blend(background, text_image)
        
        # 检查是否是PDF输出
        if output_path.lower().endswith('.pdf'):
            # 先保存为临时PNG
            temp_png = output_path.replace('.pdf', '_temp.png')
            success = cv2.imwrite(temp_png, result)
            if not success:
                raise IOError(f"无法写入临时文件: {temp_png}")
            
            # 使用reportlab生成PDF
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.lib.utils import ImageReader
            from PIL import Image as PILImage
            
            c = canvas.Canvas(output_path, pagesize=A4)
            width, height = A4
            
            img = PILImage.open(temp_png)
            img_width, img_height = img.size
            scale = min(width / img_width, height / img_height) * 0.95
            draw_width = img_width * scale
            draw_height = img_height * scale
            x = (width - draw_width) / 2
            y = (height - draw_height) / 2
            
            c.drawImage(ImageReader(temp_png), x, y, width=draw_width, height=draw_height)
            c.save()
            
            # 删除临时PNG
            os.remove(temp_png)
            
            print(f"[OK] 已导出PDF: {output_path}")
        else:
            success = cv2.imwrite(output_path, result)
            if not success:
                raise IOError(f"无法写入文件: {output_path}")
    
    print(f"[OK] 已导出: {output_path}")
    print(f"    尺寸: {text_image.shape[1]}x{text_image.shape[0]}")


def main():
    # 解析命令行参数
    args = parse_args()
    
    # 从参数更新配置
    Config.from_args(args)
    
    print("=" * 50)
    print("    手写文字生成器")
    print("=" * 50)
    print(f"字体: {Config.FONT_PATH}")
    print(f"输出: {Config.OUTPUT_PATH}")
    print(f"尺寸: {Config.OUTPUT_SIZE[0]}x{Config.OUTPUT_SIZE[1]}")
    print(f"字体大小: {Config.BASE_FONT_SIZE}")
    print(f"行距: {Config.LINE_SPACING}")
    print(f"边距: {Config.MARGIN_LEFT}/{Config.MARGIN_TOP}/{Config.MARGIN_RIGHT}/{Config.MARGIN_BOTTOM}")
    print("-" * 50)
    
    try:
        # 1. 加载字体
        print("\n[步骤1/5] 加载字体...")
        font = load_font(Config.FONT_PATH, Config.BASE_FONT_SIZE)
        
        # 2. 准备背景
        print("\n[步骤2/5] 准备背景...")
        if Config.REGIONS:
            # 多区域渲染模式
            background = load_background_with_image()
        else:
            # 传统模式
            background = load_background()
        
        # 3. 渲染文字
        print("\n[步骤3/5] 渲染手写文字...")
        if Config.REGIONS:
            # 多区域渲染
            result = background
            for i, region in enumerate(Config.REGIONS):
                print(f"    渲染区域 {i+1}/{len(Config.REGIONS)}: {region.get('text', '')[:20]}...")
                result = render_region_text(region, font, result)
            text_image_processed = result
        else:
            # 传统模式
            text_image_pil = render_handwrite_text(Config.TEXT.strip(), font)
            text_image_processed = process_text_image(text_image_pil)
        
        # 4. 图形学增强
        if not Config.REGIONS:
            print("\n[步骤4/5] 应用图形学增强...")
            # 传统模式需要处理
        else:
            print("\n[步骤4/5] 区域渲染完成，跳过增强...")
        
        # 5. 合成导出
        print("\n[步骤5/5] 合成并导出...")
        if Config.REGIONS:
            # 多区域模式：直接导出背景（已合成）
            
            # 如果输出是PDF，先保存为临时PNG，然后转换
            if Config.OUTPUT_PATH.lower().endswith('.pdf'):
                pdf_output = Config.OUTPUT_PATH
                png_output = pdf_output.replace('.pdf', '_temp.png')
                success = cv2.imwrite(png_output, text_image_processed)
                if not success:
                    raise IOError(f"无法写入临时文件: {png_output}")
                
                from reportlab.lib.pagesizes import A4
                from reportlab.pdfgen import canvas
                from reportlab.lib.utils import ImageReader
                from PIL import Image as PILImage
                
                c = canvas.Canvas(pdf_output, pagesize=A4)
                width, height = A4
                
                img = PILImage.open(png_output)
                img_width, img_height = img.size
                scale = min(width / img_width, height / img_height) * 0.95
                draw_width = img_width * scale
                draw_height = img_height * scale
                x = (width - draw_width) / 2
                y = (height - draw_height) / 2
                
                c.drawImage(ImageReader(png_output), x, y, width=draw_width, height=draw_height)
                c.save()
                os.remove(png_output)
                
                print(f"[OK] 已导出PDF: {pdf_output}")
                print(f"    尺寸: {text_image_processed.shape[1]}x{text_image_processed.shape[0]}")
            else:
                # PNG输出
                success = cv2.imwrite(Config.OUTPUT_PATH, text_image_processed)
                if not success:
                    raise IOError(f"无法写入文件: {Config.OUTPUT_PATH}")
                print(f"[OK] 已导出: {Config.OUTPUT_PATH}")
                print(f"    尺寸: {text_image_processed.shape[1]}x{text_image_processed.shape[0]}")
        else:
            composite_and_export(text_image_processed, background, Config.OUTPUT_PATH)
        
        print("\n" + "=" * 50)
        print("    完成！")
        print("=" * 50)
        print(f"输出: {os.path.abspath(Config.OUTPUT_PATH)}")
        
    except FileNotFoundError as e:
        print(f"\n错误: {e}")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
