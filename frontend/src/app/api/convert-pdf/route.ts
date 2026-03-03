import { NextRequest, NextResponse } from "next/server";
import { writeFile, unlink } from "fs/promises";
import { join } from "path";
import os from "os";
import { spawn } from "child_process";

export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  const tempDir = os.tmpdir();
  let pdfFile = "";

  try {
    const formData = await request.formData();
    const pdf = formData.get('pdf') as File;

    if (!pdf) {
      return NextResponse.json({ error: "未找到PDF文件" }, { status: 400 });
    }

    // 保存PDF到临时文件
    const timestamp = Date.now();
    pdfFile = join(tempDir, `input_${timestamp}.pdf`);
    const buffer = await pdf.arrayBuffer();
    await writeFile(pdfFile, Buffer.from(buffer));

    const outputDir = join(tempDir, `output_${timestamp}`);
    // 创建输出目录
    const fs = await import("fs");
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    // 项目根目录
    const projectRoot = join(process.cwd(), "..");

    // 使用Python脚本转换所有页面
    const scriptPath = join(projectRoot, "backend/src/pdf_to_image.py");

    const stdout = await new Promise<string>((resolve, reject) => {
      const proc = spawn("python3", [scriptPath, pdfFile, outputDir], {
        cwd: projectRoot
      });

      let stderr = "";
      let stdoutData = "";

      proc.stdout.on("data", (data) => {
        stdoutData += data.toString();
      });

      proc.stderr.on("data", (data) => {
        stderr += data.toString();
      });

      proc.on("close", (code) => {
        if (code === 0) {
          resolve(stdoutData);
        } else {
          reject(new Error(`转换失败: ${stderr}`));
        }
      });

      proc.on("error", (err) => {
        reject(err);
      });
    });

    // 解析输出的图片路径
    const imagePaths = JSON.parse(stdout);

    // 读取所有图片并转为base64
    const images: string[] = [];
    for (const imgPath of imagePaths) {
      const imageBuffer = fs.readFileSync(imgPath);
      const base64 = imageBuffer.toString("base64");
      images.push(`data:image/png;base64,${base64}`);

      // 删除临时图片文件
      await unlink(imgPath).catch(() => { });
    }

    // 清理临时文件
    await unlink(pdfFile).catch(() => { });
    fs.rmSync(outputDir, { force: true, recursive: true });

    return NextResponse.json({
      images: images,
      totalPages: images.length
    });
  } catch (error) {
    console.error("转换失败:", error);

    // 清理临时文件
    if (pdfFile) await unlink(pdfFile).catch(() => { });

    return NextResponse.json(
      { error: `转换失败: ${error}` },
      { status: 500 }
    );
  }
}
