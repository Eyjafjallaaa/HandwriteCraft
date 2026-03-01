import { NextRequest, NextResponse } from "next/server";
import { readdir } from "fs/promises";
import { join } from "path";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  try {
    const fontsDir = "/Users/vincent/Downloads/学年鉴定/handwrite/frontend/public/fonts";
    
    // 读取字体文件夹
    const files = await readdir(fontsDir);
    
    // 过滤出字体文件 (.ttf, .otf)
    const fontFiles = files.filter(file => {
      const ext = file.toLowerCase().slice(file.lastIndexOf('.'));
      return ext === '.ttf' || ext === '.otf';
    });
    
    // 构建字体列表
    const fonts = fontFiles.map(file => {
      const name = file.slice(0, file.lastIndexOf('.'));
      return {
        name: name,
        file: file,
        path: join(fontsDir, file)
      };
    });
    
    return NextResponse.json({ fonts });
  } catch (error) {
    console.error("读取字体列表失败:", error);
    return NextResponse.json({ fonts: [] });
  }
}
