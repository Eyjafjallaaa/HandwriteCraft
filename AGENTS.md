# AGENTS.md - 迹墨 HandwriteCraft 项目指南

## 项目概述

**迹墨 (HandwriteCraft)** 是一个基于 Web 的智能手写生成工具，将普通文本转换为逼真的手写体效果，支持在 PDF 或图片背景上添加手写文字。

### 核心功能
- 使用 Handright 库模拟真实手写效果
- 支持 PDF/图片上传作为背景
- 可视化框选填写区域
- 多种手写风格预设（工整正式、自然手写、潦草随性）
- 高清输出（最高 20 倍超采样）
- 支持 PNG 和 PDF 导出
- 暗黑/亮色主题切换

## 技术栈

### 前端
- **框架**: Next.js 14 (App Router)
- **语言**: TypeScript 5.0+
- **样式**: Tailwind CSS 3.4
- **组件库**: shadcn/ui (Radix UI 基础上封装)
- **图标**: Lucide React
- **PDF预览**: react-pdf, pdfjs-dist

### 后端
- **API**: Next.js API Routes
- **手写生成**: Python + Handright + OpenCV + Pillow
- **PDF处理**: PyMuPDF (fitz)

## 项目结构

```
HandwriteCraft/
├── backend/                    # Python 后端
│   ├── src/
│   │   ├── handwrite_generator.py   # 手写生成核心 (支持命令行)
│   │   └── pdf_to_image.py          # PDF 转图片工具
│   ├── requirements.txt
│   └── README.md
│
├── frontend/                   # Next.js 前端
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx        # 主页面（三栏布局）
│   │   │   ├── layout.tsx      # 根布局
│   │   │   ├── globals.css     # 全局样式（含暗黑主题变量）
│   │   │   └── api/            # API 路由
│   │   │       ├── generate/route.ts      # 手写生成 API
│   │   │       ├── convert-pdf/route.ts   # PDF 转换 API
│   │   │       └── fonts/route.ts         # 字体列表 API
│   │   ├── components/ui/      # shadcn/ui 组件
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── checkbox.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── input.tsx
│   │   │   ├── label.tsx
│   │   │   ├── progress.tsx
│   │   │   ├── select.tsx      # 下拉选择
│   │   │   ├── slider.tsx
│   │   │   ├── textarea.tsx
│   │   │   ├── toggle.tsx
│   │   │   └── toggle-group.tsx # 切换按钮组
│   │   └── lib/
│   │       └── utils.ts        # 工具函数 (cn 等)
│   ├── components.json         # shadcn 配置
│   ├── tailwind.config.ts      # Tailwind 配置
│   └── public/fonts/           # 字体文件软链接
│
├── assets/                     # 静态资源
│   ├── fonts/                  # 字体文件 (.ttf/.otf)
│   └── templates/              # 背景模板 (A4.png)
│
├── output/                     # 生成的输出文件
├── tests/                      # 测试文件
└── docs/                       # 文档和图片
```

## 常用命令

### 开发启动

```bash
# 1. 安装后端依赖
cd backend
pip install -r requirements.txt

# 2. 安装前端依赖
cd ../frontend
npm install

# 3. 启动开发服务器
npm run dev
# 访问 http://localhost:3000
```

### 构建部署

```bash
cd frontend
npm run build    # 构建生产版本
npm run start    # 启动生产服务器
```

### 命令行使用（后端）

```bash
cd backend/src

# 基本用法
python handwrite_generator.py --text "你好世界" --output ../../output/result.png

# 从文件读取
python handwrite_generator.py --text-file input.txt --output ../../output/result.png

# 自定义参数
python handwrite_generator.py \
  --text "手写文字" \
  --font-size 40 \
  --line-spacing 60 \
  --ink-color "#000000" \
  --quality 5 \
  --output ../../output/result.png
```

## 开发规范

### shadcn/ui 组件管理

项目使用 shadcn/ui 组件库，所有组件位于 `frontend/src/components/ui/`。

**添加新组件:**
```bash
cd frontend
npx shadcn@latest add <component-name>
```

**颜色规范:**
- 必须使用语义化颜色变量（如 `bg-primary`, `text-muted-foreground`）
- 禁止使用硬编码颜色（如 `bg-slate-200`, `text-slate-500`）
- 确保组件在暗黑主题下正常显示

### 主题系统

项目支持暗黑/亮色主题切换：

- CSS 变量定义在 `globals.css` 的 `:root` 和 `.dark` 中
- 主题状态通过 React state 管理（`theme` 状态）
- 切换时通过 `document.documentElement.classList.toggle("dark")` 应用
- 组件必须使用 `bg-card`, `bg-background`, `text-foreground` 等变量

### API 路由规范

所有 API 位于 `frontend/src/app/api/`：

- `generate/route.ts` - 手写生成（POST）
- `convert-pdf/route.ts` - PDF 转图片（POST）
- `fonts/route.ts` - 获取可用字体列表（GET）

### 字体管理

字体文件存放位置：
- 实际文件：`assets/fonts/`
- 前端访问：`frontend/public/fonts/`（创建软链接）

添加新字体后，前端会自动识别并在选择器中显示。

## Git 提交规范

### 提交信息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 类型 (type)

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | 修复 Bug |
| `docs` | 文档更新 |
| `style` | 代码格式调整（不影响功能） |
| `refactor` | 代码重构 |
| `perf` | 性能优化 |
| `test` | 测试相关 |
| `chore` | 构建/工具链/依赖更新 |

### 作用域 (scope)

- `frontend` - 前端相关
- `backend` - 后端相关
- `api` - API 路由
- `ui` - UI 组件
- `deps` - 依赖管理
- `config` - 配置文件

### 示例

```bash
# 新功能
feat(frontend): 添加暗黑主题切换功能

# Bug 修复
fix(backend): 修复 PDF 转换时字体缺失问题

# 组件更新
feat(ui): 新增 Select 下拉选择组件

# 样式调整
style(frontend): 统一使用语义化颜色变量

# 依赖更新
chore(deps): 升级 Next.js 到 14.2

# 文档更新
docs: 更新 README 使用说明
```

### 提交原则

1. **原子性提交**: 每个 commit 只做一件事
2. **清晰描述**: subject 使用简洁的中文描述
3. **关联 Issue**: 如有相关 issue，在 body 中引用 `#123`
4. **避免大提交**: 代码变更过多时拆分为多个 commit

## 核心功能说明

### 手写生成流程

1. **上传背景**: PDF/图片上传后通过 `convert-pdf` API 转为图片
2. **框选区域**: 用户在页面上拖动框选填写区域（支持多区域）
3. **填写内容**: 在左侧面板为每个区域输入文字
4. **调节参数**: 
   - 字体大小、字间距、行距
   - 手写风格（字体波动、行距波动、倾斜度、弹性变形）
   - 清晰度（1-20倍超采样）
   - 墨水颜色
5. **生成预览**: 调用 `generate` API 生成手写图片
6. **下载导出**: 支持 PNG/PDF 格式

### 区域框选逻辑

- 左键拖动框选区域
- 区域坐标以百分比存储（适配不同尺寸）
- 支持每个区域独立设置字体大小
- 支持删除和修改区域

### 手写风格参数

- **fontSizeSigma**: 字体大小波动（0-5）
- **lineSpacingSigma**: 行距波动（0-10）
- **wordSpacingSigma**: 字间距波动（0-10）
- **perturbThetaSigma**: 倾斜度（0-0.1）
- **elasticAlpha**: 弹性变形幅度（0-150）
- **elasticSigma**: 弹性变形平滑度（1-20）

## 常见问题

### 字体不显示
- 检查字体文件是否在 `assets/fonts/` 目录
- 确保字体格式为 `.ttf` 或 `.otf`
- 重启前端开发服务器

### 生成失败
- 检查后端 Python 依赖是否安装完整
- 查看浏览器控制台和网络请求错误
- 检查输入文字是否为空

### 主题切换无效
- 确保使用语义化 CSS 变量而非硬编码颜色
- 检查 `globals.css` 中 `.dark` 变量定义

## 扩展建议

1. **添加新字体**: 直接放入 `assets/fonts/` 目录即可自动识别
2. **自定义模板**: 将背景图片放入 `assets/templates/`
3. **新增手写参数**: 修改 `handwrite_generator.py` 和前端对应 UI
4. **批量处理**: 可扩展支持多页面 PDF 批量生成

## 相关链接

- GitHub: https://github.com/Eyjafjallaaa/HandwriteCraft
- Handright 文档: https://github.com/gsllhandright/handright
- shadcn/ui: https://ui.shadcn.com
