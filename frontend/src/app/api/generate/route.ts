import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import { writeFile, unlink } from "fs/promises";
import { join } from "path";
import os from "os";

export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  const tempDir = os.tmpdir();
  let outputFile = "";
  let regionsFile = "";
  let backgroundFile = "";

  try {
    const body = await request.json();

    const {
      pdfDataUrl,
      currentPage = 1,
      regions = [],
      width = 1200,
      height = 1600,
      quality = 2,
      fontSize = 45,
      lineSpacing = 55,
      wordSpacing = 3,
      inkColor = "#282830",
      exportFormat = "png",  // png 或 pdf
      // Handright 手写效果参数
      fontSizeSigma = 1.2,
      lineSpacingSigma = 1.5,
      wordSpacingSigma = 1.0,
      perturbThetaSigma = 0.015,
      // 字体参数
      font = "PingFangShaoHuaTi-2.ttf",
      autoIndent = true
    } = body;

    // 创建临时文件
    const timestamp = Date.now();
    const ext = exportFormat === "pdf" ? "pdf" : "png";
    outputFile = join(tempDir, `output_${timestamp}.${ext}`);
    regionsFile = join(tempDir, `regions_${timestamp}.json`);
    backgroundFile = join(tempDir, `background_${timestamp}.txt`);

    // 项目根目录
    const projectRoot = join(process.cwd(), "..");

    // Python脚本路径
    const scriptPath = join(projectRoot, "backend/src/handwrite_generator.py");

    // 字体路径 - 从 assets/fonts 读取
    const fontsDir = join(projectRoot, "assets/fonts");
    const fs = await import("fs");

    // 处理全局字体路径
    let fontPath = join(fontsDir, font);
    if (!fs.existsSync(fontPath)) {
      // 如果指定字体不存在，回退到默认字体
      fontPath = join(fontsDir, "PingFangShaoHuaTi-2.ttf");
    }

    // 处理每个区域的字体路径
    const processedRegions = regions.map((r: any) => {
      const regionFont = r.font || font;
      const regionFontPath = join(fontsDir, regionFont);
      return {
        ...r,
        font: fs.existsSync(regionFontPath) ? regionFontPath : fontPath
      };
    });

    // 准备区域数据
    const regionsJson = JSON.stringify(processedRegions);
    await writeFile(regionsFile, regionsJson, "utf-8");

    // 将背景图片数据写入临时文件（避免命令行参数过长）
    if (pdfDataUrl) {
      await writeFile(backgroundFile, pdfDataUrl, "utf-8");
    }

    // 构建Python命令参数
    const pythonArgs = [
      scriptPath,
      "--regions", regionsFile,
      "--background-image", pdfDataUrl ? backgroundFile : "",
      "--font-size", fontSize.toString(),
      "--line-spacing", lineSpacing.toString(),
      "--word-spacing", wordSpacing.toString(),
      "--width", width.toString(),
      "--height", height.toString(),
      "--ink-color", inkColor,
      "--quality", quality.toString(),
      "--output", outputFile,
      "--font", fontPath,
      // Handright 手写效果参数
      "--font-size-sigma", fontSizeSigma.toString(),
      "--line-spacing-sigma", lineSpacingSigma.toString(),
      "--word-spacing-sigma", wordSpacingSigma.toString(),
      "--perturb-theta-sigma", perturbThetaSigma.toString(),
    ];

    if (autoIndent) {
      pythonArgs.push("--auto-indent");
    } else {
      pythonArgs.push("--no-indent");
    }

    console.log("执行Python脚本...");
    console.log("区域数量:", regions.length);
    console.log("导出格式:", exportFormat);
    console.log("输出文件:", outputFile);
    console.log("区域文件:", regionsFile);
    console.log("背景文件:", pdfDataUrl ? backgroundFile : "无");

    await new Promise<void>((resolve, reject) => {
      const proc = spawn("python3", pythonArgs, {
        cwd: join(projectRoot, "backend/src"),
        env: {
          ...process.env,
          PYTHONIOENCODING: "utf-8",
        },
      });

      let stderr = "";
      let stdout = "";

      proc.stdout.on("data", (data) => {
        stdout += data.toString();
      });

      proc.stderr.on("data", (data) => {
        stderr += data.toString();
      });

      proc.on("close", (code) => {
        console.log("Python stdout:", stdout);
        console.log("Python stderr:", stderr);
        if (code !== 0) {
          reject(new Error(`Python脚本执行失败 (code ${code}): ${stderr || stdout}`));
        } else if (stderr && stderr.includes("错误")) {
          reject(new Error(`Python脚本执行出错: ${stderr}`));
        } else {
          resolve();
        }
      });

      proc.on("error", (err) => {
        reject(err);
      });
    });

    // 检查输出文件是否存在
    if (!fs.existsSync(outputFile)) {
      throw new Error(`输出文件未生成: ${outputFile}`);
    }

    // 读取生成的文件并转为base64
    const fileBuffer = fs.readFileSync(outputFile);
    const base64 = fileBuffer.toString("base64");

    const mimeType = exportFormat === "pdf" ? "application/pdf" : "image/png";
    const dataUrl = `data:${mimeType};base64,${base64}`;

    // 清理临时文件
    await unlink(regionsFile).catch(() => { });
    await unlink(outputFile).catch(() => { });
    if (backgroundFile) await unlink(backgroundFile).catch(() => { });

    return NextResponse.json({
      image: dataUrl,
      format: exportFormat
    });
  } catch (error) {
    console.error("生成失败:", error);

    // 清理临时文件
    if (regionsFile) await unlink(regionsFile).catch(() => { });
    if (outputFile) await unlink(outputFile).catch(() => { });
    if (backgroundFile) await unlink(backgroundFile).catch(() => { });

    return NextResponse.json(
      { error: `生成失败: ${error}` },
      { status: 500 }
    );
  }
}