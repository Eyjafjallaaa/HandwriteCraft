#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF转图片脚本 - 支持多页"""

import sys
import fitz
import numpy as np
import cv2
import json

def convert_pdf_to_images(pdf_path, output_dir, base_name="page"):
    """将PDF所有页转为图片"""
    doc = fitz.open(pdf_path)
    images = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        zoom = 2.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        
        # 转为numpy数组
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        
        # RGBA转RGB
        if img.shape[2] == 4:
            img = img[:, :, :3]
        
        # RGB转BGR
        img = img[:, :, ::-1]
        
        # 保存
        output_path = f"{output_dir}/{base_name}_{page_num + 1}.png"
        cv2.imwrite(output_path, img)
        images.append(output_path)
    
    print(json.dumps(images))

if __name__ == "__main__":
    pdf_path = sys.argv[1]
    output_dir = sys.argv[2]
    convert_pdf_to_images(pdf_path, output_dir)
