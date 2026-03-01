# 手写文字生成器 - 后端

Python 手写文字生成后端，基于 Handright 库实现逼真的手写效果。

## 目录结构

```
backend/
├── src/
│   ├── handwrite_generator.py   # 主生成脚本
│   └── pdf_to_image.py          # PDF 转图片工具
└── requirements.txt
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 命令行

```bash
cd src
python handwrite_generator.py --text "要转换的文字"
```

### 常用参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--text` | 要转换的文字内容 | - |
| `--text-file` | 从文件读取文字 | - |
| `--font-size` | 字体大小 | 36 |
| `--line-spacing` | 行距 | 55 |
| `--word-spacing` | 字间距 | 3 |
| `--output` | 输出路径 | output_handwrite.png |
| `--quality` | 清晰度(超采样倍率) | 3 |
| `--ink-color` | 墨水颜色 | #282830 |

### 示例

```bash
# 基本使用
python handwrite_generator.py --text "你好世界"

# 指定字体大小和行距
python handwrite_generator.py --text "文字内容" --font-size 40 --line-spacing 60

# 从文件读取并输出到指定位置
python handwrite_generator.py --text-file input.txt --output ../../output/result.png

# 高质量输出
python handwrite_generator.py --text "内容" --quality 5 --ink-color "#000000"
```

## 资源路径

- 字体文件：`../assets/fonts/`
- 背景模板：`../assets/templates/`
- 输出目录：`../output/`
