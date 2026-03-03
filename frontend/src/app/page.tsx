"use client";

import { useState, useRef, useEffect } from "react";
import dynamic from "next/dynamic";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { PenLine, Download, Loader2, Upload, X, FileText, ChevronLeft, ChevronRight, Clock, Minus, Plus, Moon, Sun } from "lucide-react";

interface BoxRegion {
  id: number;
  x: number;
  y: number;
  width: number;
  height: number;
  text: string;
  fontSize?: number; // 可选的独立字体大小
  font?: string; // 可选的独立字体
  expanded?: boolean; // 是否展开参数面板
}

export default function Home() {
  // 主题状态
  const [theme, setTheme] = useState<"light" | "dark">("light");
  
  // 切换主题
  const toggleTheme = () => {
    const newTheme = theme === "light" ? "dark" : "light";
    setTheme(newTheme);
    document.documentElement.classList.toggle("dark", newTheme === "dark");
  };

  const [fontSize, setFontSize] = useState(45);
  const [lineSpacing, setLineSpacing] = useState(50);
  const [wordSpacing, setWordSpacing] = useState(3);
  // A4 纸标准尺寸 (150 DPI: 1240×1754)
  const [width, setWidth] = useState(1240);
  const [height, setHeight] = useState(1754);
  const [inkColor, setInkColor] = useState("#282830");
  const [quality, setQuality] = useState(10);
  const [exportFormat, setExportFormat] = useState<"png" | "pdf">("png");

  // Handright 手写效果参数 - 与"自然手写"风格一致
  const [fontSizeSigma, setFontSizeSigma] = useState(2.5);    // 字体大小波动
  const [lineSpacingSigma, setLineSpacingSigma] = useState(2.0); // 行距波动
  const [wordSpacingSigma, setWordSpacingSigma] = useState(1.2); // 字间距波动
  const [perturbThetaSigma, setPerturbThetaSigma] = useState(0.025); // 角度波动
  // 弹性变形参数 - 让每个字产生结构差异
  const [elasticAlpha, setElasticAlpha] = useState(80);      // 变形幅度
  const [elasticSigma, setElasticSigma] = useState(12);      // 变形平滑度
  const [autoIndent, setAutoIndent] = useState(true); // 首行自动缩进

  // 手写风格预设 - 不同风格有不同的弹性变形程度
  const [handStyle, setHandStyle] = useState<"formal" | "natural" | "casual">("natural");
  const applyHandStyle = (style: "formal" | "natural" | "casual") => {
    setHandStyle(style);
    switch (style) {
      case "formal": // 工整正式（轻微变形，主要靠弹性变形产生差异）
        setFontSizeSigma(1.0);
        setLineSpacingSigma(0.5);
        setWordSpacingSigma(0.3);
        setPerturbThetaSigma(0.01);
        setElasticAlpha(30);    // 轻微弹性变形
        setElasticSigma(15);
        break;
      case "natural": // 自然手写（适中变形）
        setFontSizeSigma(1.5);
        setLineSpacingSigma(1.0);
        setWordSpacingSigma(0.6);
        setPerturbThetaSigma(0.015);
        setElasticAlpha(80);    // 中等弹性变形
        setElasticSigma(12);
        break;
      case "casual": // 潦草随性（较大变形）
        setFontSizeSigma(2.0);
        setLineSpacingSigma(1.5);
        setWordSpacingSigma(1.0);
        setPerturbThetaSigma(0.025);
        setElasticAlpha(150);   // 明显弹性变形
        setElasticSigma(10);
        break;
    }
  };

  // 字体选择
  const [fonts, setFonts] = useState<{ name: string, file: string, path: string }[]>([]);
  const [selectedFont, setSelectedFont] = useState("PingFangShaoHuaTi-2.ttf");
  const [fontsLoading, setFontsLoading] = useState(false);

  const [generating, setGenerating] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  
  // 生成进度和倒计时
  const [showGeneratingModal, setShowGeneratingModal] = useState(false);
  const [progress, setProgress] = useState(0);
  const [estimatedTime, setEstimatedTime] = useState(0);
  const [remainingTime, setRemainingTime] = useState(0);
  const [currentStep, setCurrentStep] = useState("");
  const [filename, setFilename] = useState("handwrite");
  const [previewKey, setPreviewKey] = useState(0);

  // 图片缩放状态
  const [zoom, setZoom] = useState(100);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState<{ x: number, y: number } | null>(null);
  const [pan, setPan] = useState({ x: 0, y: 0 });

  // PDF相关状态
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [pdfImages, setPdfImages] = useState<string[]>([]);
  const [pdfImageUrl, setPdfImageUrl] = useState<string | null>(null);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);

  const [pageRegions, setPageRegions] = useState<{ [page: number]: BoxRegion[] }>({});

  // 获取当前页的区域
  const regions = pageRegions[currentPage] || [];
  const [isSelecting, setIsSelecting] = useState(false);
  const [selectionStart, setSelectionStart] = useState<{ x: number, y: number } | null>(null);
  const [selectionEnd, setSelectionEnd] = useState<{ x: number, y: number } | null>(null);

  // 鼠标按键状态：null=无, 0=左键, 2=右键
  const [mouseButton, setMouseButton] = useState<number | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);

  // 加载字体列表
  useEffect(() => {
    const loadFonts = async () => {
      setFontsLoading(true);
      try {
        const response = await fetch('/api/fonts');
        if (response.ok) {
          const data = await response.json();
          setFonts(data.fonts);
        }
      } catch (error) {
        console.error('加载字体列表失败:', error);
      } finally {
        setFontsLoading(false);
      }
    };
    loadFonts();
  }, []);

  // 处理文件上传
  const handleFileUpload = async (file: File) => {
    setPdfFile(file);
    setPageRegions({});
    setPreviewUrl(null);
    setPdfLoading(true);
    setCurrentPage(1);

    // 检查文件类型
    const isImage = file.type.startsWith('image/');
    const isPdf = file.type === 'application/pdf';

    if (!isImage && !isPdf) {
      alert('请上传PDF或图片文件');
      setPdfLoading(false);
      return;
    }

    try {
      if (isImage) {
        // 图片文件：直接转为Base64
        const reader = new FileReader();
        reader.onload = (e) => {
          const imageUrl = e.target?.result as string;
          setPdfImages([imageUrl]);
          setTotalPages(1);
          setPdfImageUrl(imageUrl);
          setPdfLoading(false);
        };
        reader.readAsDataURL(file);
      } else {
        // PDF文件：上传到后端转换
        const formData = new FormData();
        formData.append('pdf', file);

        const response = await fetch('/api/convert-pdf', {
          method: 'POST',
          body: formData
        });

        if (response.ok) {
          const data = await response.json();
          setPdfImages(data.images);
          setTotalPages(data.totalPages);
          setPdfImageUrl(data.images[0]);
        } else {
          alert('PDF转换失败');
        }
      }
    } catch (error) {
      console.error('文件上传失败:', error);
      alert('文件上传失败');
    } finally {
      if (!isImage) {
        setPdfLoading(false);
      }
    }
  };

  // 切换页面
  const handlePageChange = (page: number) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
      setPdfImageUrl(pdfImages[page - 1]);
      setPreviewUrl(null); // 清空预览图，显示新页面的PDF
    }
  };

  // 鼠标选择区域 - 左键直接框选
  const handleMouseDown = (e: React.MouseEvent) => {
    // 只有左键可以框选
    if (e.button !== 0) return;
    // 预览图模式下左键框选，PDF预览模式下也可以框选
    if (!pdfImageUrl) return;
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    setSelectionStart({ x, y });
    setSelectionEnd({ x, y });
    setIsSelecting(true);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isSelecting) return;
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    setSelectionEnd({ x, y });
  };

  const handleMouseUp = () => {
    if (!isSelecting || !selectionStart || !selectionEnd) return;

    const x = Math.min(selectionStart.x, selectionEnd.x);
    const y = Math.min(selectionStart.y, selectionEnd.y);
    const w = Math.abs(selectionEnd.x - selectionStart.x);
    const h = Math.abs(selectionEnd.y - selectionStart.y);

    if (w > 20 && h > 20) {
      const containerWidth = containerRef.current?.clientWidth || 1;
      const containerHeight = containerRef.current?.clientHeight || 1;

      const xPercent = x / containerWidth * 100;
      const yPercent = y / containerHeight * 100;
      const wPercent = w / containerWidth * 100;
      const hPercent = h / containerHeight * 100;

      const newRegion: BoxRegion = {
        id: Date.now(),
        x: xPercent,
        y: 100 - yPercent - hPercent, // 转换为向上为正的坐标系（Y=0在底部）
        width: wPercent,
        height: hPercent,
        text: "",
        fontSize: fontSize, // 默认使用全局字体大小
        expanded: false // 默认折叠参数面板
      };
      setPageRegions({
        ...pageRegions,
        [currentPage]: [...regions, newRegion]
      });
    }

    // 框选完成后不自动退出框选模式，需要手动关闭
    setIsSelecting(false);
    setSelectionStart(null);
    setSelectionEnd(null);
  };

  const deleteRegion = (id: number) => {
    setPageRegions({
      ...pageRegions,
      [currentPage]: regions.filter(r => r.id !== id)
    });
  };

  const updateRegionText = (id: number, text: string) => {
    setPageRegions({
      ...pageRegions,
      [currentPage]: regions.map(r => r.id === id ? { ...r, text } : r)
    });
  };

  const updateRegionSize = (id: number, updates: Partial<BoxRegion>) => {
    setPageRegions({
      ...pageRegions,
      [currentPage]: regions.map(r => r.id === id ? { ...r, ...updates } : r)
    });
  };

  // 计算预估生成时间（秒）
  const calculateEstimatedTime = () => {
    const totalChars = regions.reduce((sum, r) => sum + (r.text?.length || 0), 0);
    // 时间公式：0.01 * 字符数 + 基础图片处理时间
    // 基础时间：字符处理（每个字符约0.01秒）+ 图片合成（约3-8秒，根据质量调整）
    const baseTime = 0.01 * totalChars;
    const imageTime = 3 + (quality / 10) * 5; // quality=10时约8秒，quality=2时约4秒
    return Math.ceil(baseTime + imageTime + 2); // +2秒缓冲
  };

  const handleGenerate = async () => {
    if (!pdfImageUrl && regions.length === 0) {
      alert("请先上传文件并框选填写区域");
      return;
    }
    if (regions.length === 0) {
      alert("请先框选填写区域");
      return;
    }

    setGenerating(true);
    setPreviewUrl(null);
    setShowGeneratingModal(true);
    
    // 计算预估时间并开始倒计时
    const estimated = calculateEstimatedTime();
    setEstimatedTime(estimated);
    setRemainingTime(estimated);
    setProgress(0);
    setCurrentStep("正在初始化...");

    // 使用 startTime 来跟踪实际经过的时间
    const startTime = Date.now();
    const estimatedMs = estimated * 1000;
    
    // 模拟进度更新
    const progressInterval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const remaining = Math.max(0, estimatedMs - elapsed);
      const newRemainingTime = Math.ceil(remaining / 1000);
      
      setRemainingTime(newRemainingTime);
      
      // 基于实际经过时间计算进度（线性增长，更真实）
      const progressPercent = Math.min(95, Math.floor((elapsed / estimatedMs) * 100));
      setProgress(progressPercent);
      
      // 根据实际进度百分比更新步骤
      const steps = [
        "正在加载字体...",
        "正在渲染手写效果...",
        "正在应用弹性变形...",
        "正在合成图像...",
        "正在优化画质...",
      ];
      const stepIndex = Math.floor((progressPercent / 95) * steps.length);
      setCurrentStep(steps[Math.min(stepIndex, steps.length - 1)]);
    }, 200); // 更频繁更新，让进度条更平滑

    try {
      const requestData = {
        pdfDataUrl: pdfImageUrl?.substring(0, 100) + "..." || null,
        currentPage,
        regions: regions.map(r => ({
          x: r.x / 100 * width,
          y: r.y / 100 * height,
          width: r.width / 100 * width,
          height: r.height / 100 * height,
          text: r.text,
          fontSize,
          lineSpacing,
          wordSpacing,
          inkColor
        })),
        width,
        height,
        quality,
        exportFormat
      };
      console.log("发送请求:", JSON.stringify(requestData, null, 2));

      const response = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          pdfDataUrl: pdfImageUrl,
          currentPage,
          regions: regions.map(r => ({
            x: r.x / 100 * width,
            y: r.y / 100 * height,
            width: r.width / 100 * width,
            height: r.height / 100 * height,
            text: r.text,
            fontSize: r.fontSize ?? fontSize, // 使用区域独立字体大小或全局字体大小
            lineSpacing,
            wordSpacing,
            inkColor,
            fontSizeSigma,
            lineSpacingSigma,
            wordSpacingSigma,
            perturbThetaSigma,
            elasticAlpha,
            elasticSigma,
            font: r.font ?? selectedFont // 使用区域独立字体或全局字体
          })),
          width,
          height,
          quality,
          exportFormat: "png",  // 预览固定使用 PNG 格式
          // Handright 参数
          fontSizeSigma,
          lineSpacingSigma,
          wordSpacingSigma,
          perturbThetaSigma,
          // 弹性变形参数
          elasticAlpha,
          elasticSigma,
          // 字体参数 - 全局默认字体
          font: selectedFont,
          // 首行缩进
          autoIndent
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || "生成失败");
      }

      const data = await response.json();
      setPreviewUrl(data.image);
      setPreviewKey(Date.now());
      setZoom(100);
      setPan({ x: 0, y: 0 });
    } catch (error) {
      console.error("生成失败:", error);
      alert("生成失败，请重试");
    } finally {
      clearInterval(progressInterval);
      setProgress(100);
      setCurrentStep("生成完成！");
      setTimeout(() => {
        setGenerating(false);
        setShowGeneratingModal(false);
      }, 500);
    }
  };

  const handleDownload = async () => {
    if (!previewUrl) return;

    // 构建文件名
    const finalFilename = filename.trim() || "handwrite";

    // 如果选择 PNG 格式，直接下载预览图
    if (exportFormat === "png") {
      const a = document.createElement("a");
      a.href = previewUrl;
      a.download = `${finalFilename}.png`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      return;
    }

    // 如果选择 PDF 格式，需要重新生成
    try {
      setGenerating(true);
      const response = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          pdfDataUrl: pdfImageUrl,
          currentPage,
          regions: regions.map(r => ({
            x: r.x / 100 * width,
            y: r.y / 100 * height,
            width: r.width / 100 * width,
            height: r.height / 100 * height,
            text: r.text,
            fontSize: r.fontSize ?? fontSize, // 使用区域独立字体大小或全局字体大小
            lineSpacing,
            wordSpacing,
            inkColor,
            fontSizeSigma,
            lineSpacingSigma,
            wordSpacingSigma,
            perturbThetaSigma,
            elasticAlpha,
            elasticSigma,
            font: r.font ?? selectedFont // 使用区域独立字体或全局字体
          })),
          width,
          height,
          quality,
          exportFormat: "pdf",  // 下载时使用 PDF 格式
          // Handright 参数
          fontSizeSigma,
          lineSpacingSigma,
          wordSpacingSigma,
          perturbThetaSigma,
          // 弹性变形参数
          elasticAlpha,
          elasticSigma,
          // 字体参数 - 全局默认字体
          font: selectedFont,
          // 首行缩进
          autoIndent
        })
      });

      if (!response.ok) {
        throw new Error("生成 PDF 失败");
      }

      const data = await response.json();
      const a = document.createElement("a");
      a.href = data.image;
      a.download = `${finalFilename}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } catch (error) {
      console.error("下载失败:", error);
      alert("下载失败，请重试");
    } finally {
      setGenerating(false);
    }
  };

  // 选区样式 - 使用屏幕坐标直接显示，符合鼠标拖动直觉
  const getSelectionStyle = () => {
    if (!isSelecting || !selectionStart || !selectionEnd || !containerRef.current) return {};

    const containerWidth = containerRef.current.clientWidth;
    const containerHeight = containerRef.current.clientHeight;

    const x = Math.min(selectionStart.x, selectionEnd.x) / containerWidth * 100;
    const y = Math.min(selectionStart.y, selectionEnd.y) / containerHeight * 100;
    const w = Math.abs(selectionEnd.x - selectionStart.x) / containerWidth * 100;
    const h = Math.abs(selectionEnd.y - selectionStart.y) / containerHeight * 100;

    return {
      left: `${x}%`,
      top: `${y}%`,  // 直接使用屏幕坐标，Y=0在顶部
      width: `${w}%`,
      height: `${h}%`,
    };
  };

  // 缩放控制
  const handleZoomIn = () => setZoom(prev => Math.min(prev + 25, 400));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 25, 25));
  const handleZoomReset = () => {
    setZoom(100);
    setPan({ x: 0, y: 0 });
  };

  return (
    <div className="min-h-screen bg-background">
      {/* 顶部导航 */}
      <header className="bg-card border-b px-6 py-3 flex items-center justify-between">
        <h1 className="text-xl font-bold flex items-center gap-2">
          <PenLine className="w-6 h-6" />
          <span className="bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
            迹墨 HandwriteCraft
          </span>
        </h1>
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          className="h-9 w-9"
        >
          {theme === "light" ? (
            <Moon className="h-5 w-5" />
          ) : (
            <Sun className="h-5 w-5" />
          )}
        </Button>
      </header>

      {/* 三栏布局 */}
      <div className="flex h-[calc(100vh-60px)]">

        {/* 左侧 - 上传PDF、框选区域、填写内容 */}
        <div className="w-[320px] bg-card border-r flex flex-col">
          {/* 可滚动的内容区域 */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* 上传区域 */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">上传文件</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="border-2 border-dashed rounded-lg p-4 text-center">
                  <input
                    type="file"
                    accept="application/pdf,image/*"
                    onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
                    className="hidden"
                    id="file-upload"
                  />
                  <label htmlFor="file-upload" className="cursor-pointer">
                    {pdfLoading ? (
                      <Loader2 className="w-8 h-8 mx-auto mb-2 text-muted-foreground/70 animate-spin" />
                    ) : (
                      <FileText className="w-8 h-8 mx-auto mb-2 text-muted-foreground/70" />
                    )}
                    <span className="text-sm text-muted-foreground">
                      {pdfFile ? pdfFile.name : "点击上传PDF或图片"}
                    </span>
                  </label>
                </div>
              </CardContent>
            </Card>

            {/* 框选提示 - 只要有PDF就显示 */}
            {pdfImageUrl && (
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">框选区域</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-xs text-muted-foreground/80 mb-2">
                    <span className="font-medium">左键拖动</span>：框选区域<br />
                    {previewUrl && <><span className="font-medium">右键拖动</span>：移动预览</>}
                  </p>
                  {regions.length > 0 && (
                    <p className="text-[10px] text-muted-foreground/70">已框选 {regions.length} 个区域</p>
                  )}
                </CardContent>
              </Card>
            )}

            {/* 区域列表 */}
            {regions.length > 0 && (
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">填写内容 ({regions.length}个区域)</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {regions.map((region, index) => (
                    <div key={region.id} className="border rounded p-2">
                      {/* 头部：区域编号 + 展开/删除按钮 */}
                      <div className="flex justify-between items-center mb-2">
                        <button
                          onClick={() => updateRegionSize(region.id, { expanded: !region.expanded })}
                          className="flex items-center gap-1 text-xs font-medium hover:text-muted-foreground/80"
                        >
                          <span>区域 {index + 1}</span>
                          <svg
                            className={`w-3 h-3 transition-transform ${region.expanded ? 'rotate-180' : ''}`}
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                          </svg>
                        </button>
                        <button onClick={() => deleteRegion(region.id)} className="text-red-500 hover:text-red-600">
                          <X className="w-4 h-4" />
                        </button>
                      </div>

                      {/* 文字输入 */}
                      <Textarea
                        value={region.text}
                        onChange={(e) => updateRegionText(region.id, e.target.value)}
                        placeholder="在此区域填写的文字..."
                        className="min-h-[50px] text-sm"
                      />

                      {/* 展开的参数面板 */}
                      {region.expanded && (
                        <div className="mt-3 pt-3 border-t space-y-3">
                          {/* 字体选择 */}
                          <div>
                            <Label className="text-[10px] text-muted-foreground mb-1 block">字体</Label>
                            <Select
                              value={region.font ?? selectedFont}
                              onValueChange={(value) => updateRegionSize(region.id, { font: value })}
                            >
                              <SelectTrigger className="w-full h-7 text-xs">
                                <SelectValue placeholder="选择字体" />
                              </SelectTrigger>
                              <SelectContent>
                                {fonts.map((font) => (
                                  <SelectItem key={font.file} value={font.file} className="text-xs">
                                    {font.name}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>

                          {/* 字体大小 */}
                          <div>
                            <Label className="text-[10px] text-muted-foreground mb-1 block">字体大小 (px)</Label>
                            <Input
                              type="number"
                              value={region.fontSize ?? fontSize}
                              onChange={(e) => updateRegionSize(region.id, { fontSize: Math.max(16, Math.min(60, Number(e.target.value))) })}
                              className="h-7 text-xs"
                              min={16}
                              max={60}
                            />
                          </div>

                          {/* 位置和尺寸输入 */}
                          <div>
                            <Label className="text-[10px] text-muted-foreground mb-1 block">位置和尺寸 (%)</Label>
                            <div className="grid grid-cols-2 gap-2">
                              <div className="relative">
                                <span className="absolute left-2 top-1/2 -translate-y-1/2 text-[10px] text-muted-foreground/70 font-medium">X</span>
                                <Input
                                  type="number"
                                  value={Math.round(region.x * 10) / 10}
                                  onChange={(e) => updateRegionSize(region.id, { x: Math.max(0, Math.min(100, Number(e.target.value))) })}
                                  className="h-7 text-xs pl-5"
                                  placeholder="横坐标"
                                  step="0.1"
                                />
                              </div>
                              <div className="relative">
                                <span className="absolute left-2 top-1/2 -translate-y-1/2 text-[10px] text-muted-foreground/70 font-medium">Y</span>
                                <Input
                                  type="number"
                                  value={Math.round((100 - region.y) * 10) / 10}
                                  onChange={(e) => {
                                    const visualY = Math.max(0, Math.min(100, Number(e.target.value)));
                                    updateRegionSize(region.id, { y: 100 - visualY });
                                  }}
                                  className="h-7 text-xs pl-5"
                                  placeholder="纵坐标（向上为正）"
                                  step="0.1"
                                />
                              </div>
                              <div className="relative">
                                <span className="absolute left-2 top-1/2 -translate-y-1/2 text-[10px] text-muted-foreground/70 font-medium">W</span>
                                <Input
                                  type="number"
                                  value={Math.round(region.width * 10) / 10}
                                  onChange={(e) => updateRegionSize(region.id, { width: Math.max(1, Math.min(100, Number(e.target.value))) })}
                                  className="h-7 text-xs pl-5"
                                  placeholder="宽度"
                                  step="0.1"
                                />
                              </div>
                              <div className="relative">
                                <span className="absolute left-2 top-1/2 -translate-y-1/2 text-[10px] text-muted-foreground/70 font-medium">H</span>
                                <Input
                                  type="number"
                                  value={Math.round(region.height * 10) / 10}
                                  onChange={(e) => updateRegionSize(region.id, { height: Math.max(1, Math.min(100, Number(e.target.value))) })}
                                  className="h-7 text-xs pl-5"
                                  placeholder="高度"
                                  step="0.1"
                                />
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}
          </div>

          {/* 固定在底部的生成按钮 */}
          <div className="p-4 border-t bg-card">
            <Button
              onClick={handleGenerate}
              disabled={generating || regions.length === 0 || !pdfImageUrl}
              className="w-full"
              size="lg"
            >
              {generating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  生成中...
                </>
              ) : (
                "生成手写图片"
              )}
            </Button>
          </div>
        </div>

        {/* 中间 - PDF预览/框选/结果 */}
        <div className="flex-1 bg-muted p-4 overflow-auto flex flex-col items-center relative">
          <div
            ref={containerRef}
            className={`relative bg-white shadow-lg select-none ${isSelecting ? 'cursor-crosshair' : (previewUrl ? 'cursor-default' : 'cursor-crosshair')}`}
            style={{
              width: '600px',
              userSelect: 'none',
              WebkitUserSelect: 'none',
            }}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
          >
            {/* 预览图 */}
            {previewUrl ? (
              <div
                className="w-full h-full relative overflow-hidden"
                style={{ cursor: mouseButton === 2 ? (isDragging ? 'grabbing' : 'grab') : (isSelecting ? 'crosshair' : 'crosshair') }}
                onWheel={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  const delta = e.deltaY > 0 ? -10 : 10;
                  setZoom(prev => Math.min(Math.max(prev + delta, 25), 400));
                }}
                onMouseDown={(e) => {
                  setMouseButton(e.button);
                  if (e.button === 2) { // 右键拖动
                    e.preventDefault();
                    e.stopPropagation();
                    setIsDragging(true);
                    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
                  }
                  // 左键不阻止冒泡，让父容器处理框选
                }}
                onContextMenu={(e) => e.preventDefault()}
                onMouseMove={(e) => {
                  if (isDragging && dragStart) {
                    e.stopPropagation(); // 只有拖动时才阻止冒泡
                    setPan({
                      x: e.clientX - dragStart.x,
                      y: e.clientY - dragStart.y
                    });
                  }
                }}
                onMouseUp={(e) => {
                  setMouseButton(null);
                  if (isDragging) {
                    e.stopPropagation(); // 只有拖动时才阻止冒泡
                    setIsDragging(false);
                    setDragStart(null);
                  }
                }}
                onMouseLeave={(e) => {
                  setMouseButton(null);
                  if (isDragging) {
                    e.stopPropagation();
                    setIsDragging(false);
                    setDragStart(null);
                  }
                }}
              >
                {/* 缩放控制条 - 放在右上角避免和左上角框选按钮冲突 */}
                <div className="absolute top-2 right-2 z-20 bg-background rounded-lg shadow-lg p-1 flex items-center gap-1 border">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={handleZoomOut}
                    className="h-7 w-7"
                    title="缩小"
                  >
                    <Minus className="w-4 h-4" />
                  </Button>
                  <span className="text-xs font-medium min-w-[50px] text-center">{zoom}%</span>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={handleZoomIn}
                    className="h-7 w-7"
                    title="放大"
                  >
                    <Plus className="w-4 h-4" />
                  </Button>
                  <div className="w-px h-4 bg-border mx-1" />
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleZoomReset}
                    className="h-7 text-xs px-2"
                    title="恢复100%"
                  >
                    100%
                  </Button>
                </div>
                {/* 可缩放的图片容器 */}
                <div
                  className="w-full h-full flex items-center justify-center"
                  style={{
                    transform: `scale(${zoom / 100}) translate(${pan.x}px, ${pan.y}px)`,
                    transformOrigin: 'center center',
                    transition: isDragging ? 'none' : 'transform 0.1s ease-out',
                  }}
                >
                  <img
                    key={previewKey}
                    src={previewUrl}
                    alt="预览"
                    className="w-full h-auto max-w-none"
                    draggable={false}
                  />
                  {regions.map((region, index) => (
                    <div
                      key={region.id}
                      className="absolute border-2 border-blue-500 hover:bg-blue-50 hover:bg-opacity-20 flex items-center justify-center group"
                      style={{
                        left: `${region.x}%`,
                        top: `${100 - region.y - region.height}%`,
                        width: `${region.width}%`,
                        height: `${region.height}%`,
                      }}
                    >
                      <span className="text-xs text-blue-600 bg-white px-1 rounded opacity-0 group-hover:opacity-100 transition-opacity">
                        区域{index + 1}
                      </span>
                    </div>
                  ))}
                </div>

                {/* 选区预览 - 预览图模式下（放在可缩放容器外，避免受transform影响） */}
                {isSelecting && selectionStart && selectionEnd && (
                  <div
                    className="absolute border-2 border-dashed border-blue-500 bg-blue-100 bg-opacity-30 pointer-events-none z-10"
                    style={getSelectionStyle()}
                  />
                )}
              </div>
            ) : pdfImageUrl ? (
              /* PDF转换后的图片预览 */
              <div className="w-full h-full relative">
                <img
                  src={pdfImageUrl}
                  alt="PDF预览"
                  className="w-full h-auto"
                  draggable={false}
                />

                {/* 区域框 */}
                {regions.map((region, index) => (
                  <div
                    key={region.id}
                    className="absolute border-2 border-blue-500 bg-blue-50 bg-opacity-30 flex items-center justify-center"
                    style={{
                      left: `${region.x}%`,
                      top: `${100 - region.y - region.height}%`,
                      width: `${region.width}%`,
                      height: `${region.height}%`,
                    }}
                  >
                    <span className="text-xs text-blue-600 bg-white px-1 rounded">
                      区域{index + 1}
                    </span>
                  </div>
                ))}

                {/* 选区预览 */}
                {isSelecting && selectionStart && selectionEnd && (
                  <div
                    className="absolute border-2 border-dashed border-blue-500 bg-blue-100 bg-opacity-30"
                    style={getSelectionStyle()}
                  />
                )}
              </div>
            ) : pdfLoading ? (
              /* PDF加载中 */
              <div className="w-full h-96 flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-muted-foreground/70" />
              </div>
            ) : (
              /* 空状态 */
              <div className="w-full h-96 flex items-center justify-center text-muted-foreground/70">
                <div className="text-center">
                  <Upload className="w-12 h-12 mx-auto mb-2" />
                  <p className="text-sm">上传文件后<br />在此处框选填写区域</p>
                </div>
              </div>
            )}
          </div>

          {/* 翻页控件 - 放在右下角 */}
          {pdfImageUrl && totalPages > 1 && (
            <div className="absolute bottom-4 right-4 z-30 bg-card border rounded-lg shadow p-2 flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage <= 1}
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <span className="text-sm min-w-[60px] text-center">
                {currentPage} / {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage >= totalPages}
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          )}
        </div>

        {/* 右侧 - 参数面板 */}
        <div className="w-[320px] bg-card border-l flex flex-col">
          {/* 可滚动的内容区域 */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* 字体选择 */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">字体选择</CardTitle>
              </CardHeader>
              <CardContent>
                <div>
                  <Label className="text-[10px] text-muted-foreground mb-1 block">选择字体</Label>
                  <Select
                    value={selectedFont}
                    onValueChange={setSelectedFont}
                    disabled={fontsLoading}
                  >
                    <SelectTrigger className="w-full h-8 text-xs">
                      <SelectValue placeholder={fontsLoading ? "加载中..." : "选择字体"} />
                    </SelectTrigger>
                    <SelectContent>
                      {fonts.map((font) => (
                        <SelectItem key={font.file} value={font.file} className="text-xs">
                          {font.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <p className="text-[10px] text-muted-foreground/70 mt-2">
                  提示：将 .ttf/.otf 字体文件放入 fonts 文件夹即可使用
                </p>
              </CardContent>
            </Card>

            {/* 手写风格 */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">手写风格</CardTitle>
              </CardHeader>
              <CardContent>
                <ToggleGroup
                  type="single"
                  value={handStyle}
                  onValueChange={(value) => value && applyHandStyle(value as "formal" | "natural" | "casual")}
                  className="grid grid-cols-3 gap-2"
                >
                  <ToggleGroupItem value="formal" className="text-xs px-2 py-1.5 h-auto">
                    工整正式
                  </ToggleGroupItem>
                  <ToggleGroupItem value="natural" className="text-xs px-2 py-1.5 h-auto">
                    自然手写
                  </ToggleGroupItem>
                  <ToggleGroupItem value="casual" className="text-xs px-2 py-1.5 h-auto">
                    潦草随性
                  </ToggleGroupItem>
                </ToggleGroup>
                <p className="text-[10px] text-muted-foreground/70 mt-2">
                  {handStyle === "formal" && "适合申请书、报告等正式文档"}
                  {handStyle === "natural" && "适合日记、笔记等日常书写（推荐）"}
                  {handStyle === "casual" && "适合草稿、速记等非正式场景"}
                </p>
              </CardContent>
            </Card>

            {/* 排版参数 */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">排版参数</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center space-x-2 pt-1">
                  <Checkbox
                    id="auto-indent"
                    checked={autoIndent}
                    onCheckedChange={(checked) => setAutoIndent(checked as boolean)}
                  />
                  <Label
                    htmlFor="auto-indent"
                    className="text-[12px] font-medium leading-none cursor-pointer"
                  >
                    首行自动缩进 (2字符)
                  </Label>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label className="text-[10px] text-muted-foreground">字体大小</Label>
                    <Input
                      type="number"
                      value={fontSize}
                      onChange={(e) => setFontSize(Number(e.target.value))}
                      min={16}
                      max={60}
                      className="h-7 text-xs"
                    />
                  </div>
                  <div>
                    <Label className="text-[10px] text-muted-foreground">字间距</Label>
                    <Input
                      type="number"
                      value={wordSpacing}
                      onChange={(e) => setWordSpacing(Number(e.target.value))}
                      min={0}
                      max={20}
                      className="h-7 text-xs"
                    />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-[10px] text-muted-foreground mb-1">
                    <Label>行距</Label>
                    <span>{lineSpacing}</span>
                  </div>
                  <Slider
                    value={[lineSpacing]}
                    onValueChange={(value) => setLineSpacing(value[0])}
                    min={30}
                    max={80}
                    step={1}
                    className="w-full"
                  />
                </div>
              </CardContent>
            </Card>

            {/* 图片尺寸 */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">图片尺寸</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label className="text-[10px] text-muted-foreground">宽度</Label>
                    <Input
                      type="number"
                      value={width}
                      onChange={(e) => setWidth(Number(e.target.value))}
                      step={100}
                      className="h-7 text-xs"
                    />
                  </div>
                  <div>
                    <Label className="text-[10px] text-muted-foreground">高度</Label>
                    <Input
                      type="number"
                      value={height}
                      onChange={(e) => setHeight(Number(e.target.value))}
                      step={100}
                      className="h-7 text-xs"
                    />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-[10px] text-muted-foreground mb-1">
                    <Label>清晰度</Label>
                    <span>{quality}x</span>
                  </div>
                  <Slider
                    value={[quality]}
                    onValueChange={(value) => setQuality(value[0])}
                    min={1}
                    max={20}
                    step={1}
                    className="w-full"
                  />
                </div>
              </CardContent>
            </Card>

            {/* 颜色 */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">颜色</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <input
                    type="color"
                    value={inkColor}
                    onChange={(e) => setInkColor(e.target.value)}
                    className="w-7 h-7 rounded cursor-pointer"
                  />
                  <div className="flex-1">
                    <Label className="text-[10px] text-muted-foreground">墨水颜色</Label>
                    <Input
                      value={inkColor}
                      onChange={(e) => setInkColor(e.target.value)}
                      className="h-7 text-xs"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 手写风格 */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">手写风格</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <div className="flex justify-between text-[10px] text-muted-foreground mb-1">
                      <Label>字体波动</Label>
                      <span>{fontSizeSigma}</span>
                    </div>
                    <Slider
                      value={[fontSizeSigma]}
                      onValueChange={(value) => setFontSizeSigma(value[0])}
                      min={0}
                      max={5}
                      step={0.1}
                      className="w-full"
                    />
                  </div>
                  <div>
                    <div className="flex justify-between text-[10px] text-muted-foreground mb-1">
                      <Label>行距波动</Label>
                      <span>{lineSpacingSigma}</span>
                    </div>
                    <Slider
                      value={[lineSpacingSigma]}
                      onValueChange={(value) => setLineSpacingSigma(value[0])}
                      min={0}
                      max={10}
                      step={0.1}
                      className="w-full"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <div className="flex justify-between text-[10px] text-muted-foreground mb-1">
                      <Label>字间距波动</Label>
                      <span>{wordSpacingSigma}</span>
                    </div>
                    <Slider
                      value={[wordSpacingSigma]}
                      onValueChange={(value) => setWordSpacingSigma(value[0])}
                      min={0}
                      max={10}
                      step={0.1}
                      className="w-full"
                    />
                  </div>
                  <div>
                    <div className="flex justify-between text-[10px] text-muted-foreground mb-1">
                      <Label>倾斜度</Label>
                      <span>{perturbThetaSigma}</span>
                    </div>
                    <Slider
                      value={[perturbThetaSigma]}
                      onValueChange={(value) => setPerturbThetaSigma(value[0])}
                      min={0}
                      max={0.1}
                      step={0.001}
                      className="w-full"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 下载区域 - 仅在预览时显示，放在中间栏底部 */}
          {previewUrl && (
            <div className="mt-4 bg-white rounded-lg shadow-lg p-3 flex flex-col items-center gap-2 w-full max-w-[600px]">
              {/* 文件名输入 */}
              <div className="flex items-center gap-2 w-full">
                <Input
                  value={filename}
                  onChange={(e) => setFilename(e.target.value)}
                  placeholder="文件名"
                  className="h-8 text-sm flex-1"
                />
                <span className="text-sm text-muted-foreground">.{exportFormat}</span>
              </div>
              {/* 导出格式选择 */}
              <div className="flex gap-2 w-full">
                <Button
                  variant={exportFormat === "png" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setExportFormat("png")}
                  className="flex-1"
                >
                  PNG
                </Button>
                <Button
                  variant={exportFormat === "pdf" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setExportFormat("pdf")}
                  className="flex-1"
                >
                  PDF
                </Button>
              </div>
              {/* 下载按钮 */}
              <Button onClick={handleDownload} size="lg" className="w-full">
                <Download className="mr-2 h-4 w-4" />
                下载图片
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* 生成中蒙版 Dialog */}
      <Dialog open={showGeneratingModal} modal>
        <DialogContent className="sm:max-w-[400px]" onPointerDownOutside={(e) => e.preventDefault()}>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Loader2 className="h-5 w-5 animate-spin" />
              正在生成手写图片
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-6 py-4">
            {/* 当前步骤 */}
            <div className="text-center text-sm text-muted-foreground/80">
              {currentStep}
            </div>
            
            {/* 进度条 */}
            <div className="space-y-2">
              <Progress value={progress} className="h-2" />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>{Math.round(progress)}%</span>
                <span>预计剩余 {remainingTime} 秒</span>
              </div>
            </div>
            
            {/* 倒计时显示 */}
            <div className="flex items-center justify-center gap-2 text-muted-foreground">
              <Clock className="h-4 w-4" />
              <span className="text-sm">
                总预计时间: {estimatedTime} 秒
              </span>
            </div>
            
            {/* 参数提示 */}
            <div className="text-xs text-muted-foreground/70 text-center">
              质量设置: {quality}x | 字符数: {regions.reduce((sum, r) => sum + (r.text?.length || 0), 0)}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
