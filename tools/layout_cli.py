#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Manual Layout CLI
เครื่องมือจัดรูปแบบข้อความโดยใช้ LayoutEngine (โหมดเดียวกับ GUI)
รองรับการประมวลผลทีละหลายไฟล์ (Batch Processing)
"""

import sys
import os
import argparse
import glob
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

# Ensure project root is on sys.path
def _ensure_project_root_on_path():
    this_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(this_dir, os.pardir))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    return project_root

PROJECT_ROOT = _ensure_project_root_on_path()

# Import required project modules
from src.core.layout_engine_v2 import LayoutEngine
from src.core.shape_rules import ShapeRuleLookup
from src.utils.config import get_config

def parse_shape_map(md_text: str) -> Dict[Tuple[str, int], str]:
    """อ่าน mapping จากไฟล์ข้อมูลรูปร่าง.md เหมือน GUI"""
    mapping: Dict[Tuple[str, int], str] = {}
    for i, raw in enumerate(md_text.splitlines()):
        if i == 0: continue
        parts = [p.strip() for p in raw.split(",")]
        if len(parts) != 3: continue
        fname, item_str, shape = parts
        if shape == "(ไม่มีข้อมูล)" or item_str == "-" or not shape:
            continue
        try:
            idx = int(item_str)
        except Exception:
            continue
        mapping[(fname, idx)] = shape
    return mapping

def parse_translation(md_text: str) -> List[Tuple[str, List[Tuple[int, str]]]]:
    """วิเคราะห์โครงสร้างไฟล์คำแปล (.md) เหมือน GUI"""
    sections: List[Tuple[str, List[Tuple[int, str]]]] = []
    current_fname: Optional[str] = None
    current_items: List[Tuple[int, str]] = []
    current_item_idx: Optional[int] = None
    current_item_text: List[str] = []

    def _finish_current_item():
        if current_item_idx is not None and current_item_text and current_fname is not None:
            full_text = " ".join(current_item_text).strip()
            if full_text:
                current_items.append((current_item_idx, full_text))

    for raw in md_text.splitlines():
        line = raw.rstrip("\r")
        s = line.strip()
        
        if s.startswith("### ") and "." in s[4:]:
            _finish_current_item()
            if current_fname is not None:
                sections.append((current_fname, current_items))
            current_fname = s[4:].strip()
            current_items = []
            current_item_idx = None
            current_item_text = []
            continue

        if s and s[0].isdigit():
            try:
                pos = s.index(".")
                new_idx = int(s[:pos])
                new_txt = s[pos + 1:].lstrip()
                _finish_current_item()
                current_item_idx = new_idx
                current_item_text = [new_txt] if new_txt else []
            except Exception:
                if s and current_item_idx is not None:
                    current_item_text.append(s)
            continue

        if s and current_item_idx is not None:
            current_item_text.append(s)

    _finish_current_item()
    if current_fname is not None:
        sections.append((current_fname, current_items))
    return sections

def process_single_file(engine, input_path, output_path, shape_map, default_shape):
    """ประมวลผลไฟล์เดียว"""
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
            
        sections = parse_translation(md_content)
        if not sections:
            print(f"Warning: No sections found in {input_path}")
            return 0
            
        out_lines: List[str] = []
        total_items = 0
        
        for fname, items in sections:
            out_lines.append(f"### {fname}")
            if not items:
                out_lines.append("")
                continue
                
            for idx, text in items:
                shape = shape_map.get((fname, idx), default_shape)
                info = engine.get_layout_info(text, shape)
                output_text = info.get("output", "") or text
                lines = output_text.split("\n")
                
                # บรรทัดแรกคงเลข, บรรทัดถัดไปไม่ใส่เลข
                out_lines.append(f"{idx}. {lines[0]}")
                for more in lines[1:]:
                    out_lines.append(more)
                out_lines.append("")
                total_items += 1
                
        # สร้างโฟลเดอร์ปลายทางถ้าไม่มี
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            f.write("\n".join(out_lines).rstrip("\n") + "\n")
            
        return total_items
    except Exception as e:
        print(f"Error processing {input_path}: {e}")
        return 0

def main():
    parser = argparse.ArgumentParser(description="Layout CLI - Batch Processing Support")
    parser.add_argument("--input", required=True, nargs='+', help="Path to input .md file(s) or directory")
    parser.add_argument("--output", required=True, help="Path to output .md file or directory")
    parser.add_argument("--shape_file", help="Path to ข้อมูลรูปร่าง.md file")
    parser.add_argument("--default_shape", default="square_like", help="Default shape type")
    
    args = parser.parse_args()
    
    # 1. รวบรวมไฟล์อินพุตทั้งหมด
    input_files = []
    for pattern in args.input:
        if os.path.isdir(pattern):
            # ถ้าเป็นโฟลเดอร์ ให้หาไฟล์ .md ทั้งหมด (ไม่รวมผลลัพธ์ที่อาจจะมีคำว่า 'แบ่งคำแล้ว')
            found = glob.glob(os.path.join(pattern, "*.md"))
            input_files.extend([f for f in found if "แบ่งคำแล้ว" not in os.path.basename(f)])
        else:
            # รองรับ wildcard (เช่น *.md)
            found = glob.glob(pattern)
            if found:
                input_files.extend(found)
            elif os.path.exists(pattern):
                input_files.append(pattern)
            else:
                print(f"Warning: Input path not found: {pattern}")

    if not input_files:
        print("Error: No input files found.")
        sys.exit(1)

    # 2. ตรวจสอบโหมด (ไฟล์เดียว vs หลายไฟล์)
    is_batch = len(input_files) > 1 or os.path.isdir(args.output) or (len(input_files) == 1 and os.path.isdir(args.input[0]))
    
    # 3. สร้าง LayoutEngine
    engine = LayoutEngine()
    
    # 4. โหลด shape_map
    shape_map = {}
    shp_path = args.shape_file or os.path.join(PROJECT_ROOT, "examples", "ข้อมูลรูปร่าง.md")
    if os.path.exists(shp_path):
        print(f"Loading shape map from: {shp_path}")
        try:
            with open(shp_path, 'r', encoding='utf-8') as f:
                shape_map = parse_shape_map(f.read())
            print(f"Loaded {len(shape_map)} shape rules.")
        except Exception as e:
            print(f"Warning: Failed to load shape map: {e}")
    
    # 5. เริ่มประมวลผล
    print(f"Processing {len(input_files)} file(s)...\n")
    total_processed_items = 0
    
    for input_path in input_files:
        input_path = os.path.abspath(input_path)
        filename = os.path.basename(input_path)
        
        if is_batch:
            # ถ้าเป็น Batch ให้สร้างชื่อไฟล์ใหม่ในโฟลเดอร์ Output
            if os.path.isdir(args.output):
                out_dir = args.output
            else:
                out_dir = os.path.dirname(args.output) or "."
            
            output_filename = f"แบ่งคำแล้ว_{filename}"
            target_path = os.path.join(out_dir, output_filename)
        else:
            # ถ้าไฟล์เดียว และ output ไม่ใช่โฟลเดอร์ ให้ใช้ชื่อตามที่ระบุ
            if os.path.isdir(args.output):
                target_path = os.path.join(args.output, f"แบ่งคำแล้ว_{filename}")
            else:
                target_path = os.path.abspath(args.output)

        print(f"Processing: {filename} -> {os.path.basename(target_path)}")
        items_count = process_single_file(engine, input_path, target_path, shape_map, args.default_shape)
        total_processed_items += items_count
        print(f"  Done: {items_count} items processed.")

    print(f"\nSuccessfully processed {len(input_files)} files.")
    print(f"Total items: {total_processed_items}")
    print(f"Results saved to: {os.path.abspath(args.output)}")

if __name__ == "__main__":
    main()
