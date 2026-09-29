#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI ทดสอบ Layout Engine (โหมดง่าย)

ฟีเจอร์:
- เลือกรูปร่าง (square_like, tall_rect) หรือจบโปรแกรม
- รับข้อความอินพุต
- แสดงผลการตัดคำ (NLP), จำนวนอักษร, และบรรทัดที่จัดวาง (ตัดตามคำ ไม่คำนวณสมดุล)

วิธีรัน:
  python examples/cli_layout_demo.py
"""

from __future__ import annotations

import sys
import os
from typing import List, Tuple


def _ensure_project_root_on_path():
    # เพิ่ม project root ลงใน sys.path เพื่อให้ import แบบ src.* ได้เมื่อรันจาก examples/
    this_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(this_dir, os.pardir))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)


_ensure_project_root_on_path()

from src.core.layout_engine_v2 import LayoutEngine  # noqa: E402
from src.core.shape_rules import ShapeRuleLookup  # noqa: E402
from src.utils.config import get_config  # noqa: E402


SHAPE_CHOICES = {
    "1": ("square_like", "สี่เหลี่ยมจัตุรัส (บอลลูนทั่วไป)"),
    "2": ("tall_rect", "สี่เหลี่ยมผืนผ้าสูง (บอลลูนแคบยาว)"),
    "3": ("exit", "จบโปรแกรม"),
}


def print_menu():
    print("\n=== ทดสอบ Layout Engine V2 ===")
    for key, (_, label) in SHAPE_CHOICES.items():
        print(f"  {key}) {label}")


def read_choice() -> str:
    while True:
        choice = input("\nเลือกตัวเลือก (1-3): ").strip()
        if choice in SHAPE_CHOICES:
            return choice
        print("ตัวเลือกไม่ถูกต้อง ลองใหม่อีกครั้งครับ/ค่ะ")


def summarize_tokens(tokens: List[str]) -> str:
    # แสดง tokens เป็นรูปแบบอ่านง่าย
    # เช่น: [ฉัน, กิน, ข้าว, , ค่ะ]
    if not tokens:
        return "[]"
    return "[" + ", ".join(tokens) + "]"


def compute_actual_ratio(widths: List[int]) -> List[float]:
    if not widths:
        return []
    # base = ค่าต่ำสุดที่ > 0 ถ้าไม่มีใช้ 1 เพื่อกันหารศูนย์
    positives = [w for w in widths if w > 0]
    base = min(positives) if positives else 1
    return [round(w / base, 2) for w in widths]


def evaluate_balance(widths: List[int], target_ratio: List[float], tolerance: float) -> Tuple[bool, List[Tuple[int, float, float, Tuple[float, float]]]]:
    """
    ตรวจสอบสมดุลตามตรรกะ ± tolerance จากเป้าหมาย
    คืนค่า:
      - is_balanced
      - per_line รายละเอียด: (width, target, expected, (min_ok, max_ok)) ต่อบรรทัด
    """
    details = []
    if not widths or len(widths) != len(target_ratio):
        return False, details

    # base width = ค่าเฉลี่ยของบรรทัดที่ target == 1.0 ถ้ามี มิฉะนั้นใช้ค่าต่ำสุด
    base_indices = [i for i, t in enumerate(target_ratio) if t == 1.0]
    if base_indices:
        base_width = sum(widths[i] for i in base_indices) / len(base_indices)
    else:
        base_width = min(widths)
    if base_width <= 0:
        return False, details

    ok = True
    for w, t in zip(widths, target_ratio):
        expected = base_width * t
        min_ok = expected * (1 - tolerance)
        max_ok = expected * (1 + tolerance)
        details.append((w, t, expected, (min_ok, max_ok)))
        if not (min_ok <= w <= max_ok):
            ok = False
    return ok, details


def run_once(engine: LayoutEngine, shape_key: str):
    shape_type, shape_label = SHAPE_CHOICES[shape_key]
    if shape_type == "exit":
        return False

    print(f"\nเลือก: {shape_label} [{shape_type}]")
    text = input("พิมพ์ประโยค/ข้อความ: ").strip()
    if not text:
        print("(ไม่มีข้อความ)")
        return True

    # ดึงข้อมูลการจัดวาง
    info = engine.get_layout_info(text, shape_type)
    rules = info.get("rules", {})
    
    # คำนวณข้อมูล Adaptive Width
    base_width = rules.get("base_width", rules.get("max_width", 0))
    max_width = info.get("max_width", 0)
    
    # วัดความกว้างข้อความก่อนแบ่ง
    text_width_before = 0
    if engine.font_metrics:
        text_width_before = engine.font_metrics.get_text_width(text)
    
    # โหลด config สำหรับ Adaptive Width
    cfg = get_config()
    shapes_cfg = cfg.get("shapes", {}) or {}
    adaptive_cfg = shapes_cfg.get("adaptive_width", {}) or {}
    
    # อ่านค่า threshold จาก config
    short_threshold = adaptive_cfg.get("short_text_threshold", 1.0)
    normal_threshold = adaptive_cfg.get("normal_text_threshold", 2.0)
    medium_threshold = adaptive_cfg.get("medium_text_threshold", 3.0)
    long_threshold = adaptive_cfg.get("long_text_threshold", 4.0)
    very_long_s_threshold = adaptive_cfg.get("very_long_s_threshold", 5.0)
    very_long_m_threshold = adaptive_cfg.get("very_long_m_threshold", 6.0)
    very_long_l_threshold = adaptive_cfg.get("very_long_l_threshold", 7.0)
    
    # คำนวณ ratio
    ratio = 0
    if base_width > 0:
        ratio = text_width_before / base_width
    
    scale = max_width / base_width if base_width > 0 else 1.0
    
    # กำหนดเกณฑ์ตาม config (7 ช่วง)
    if ratio < short_threshold:
        category = f"ข้อความสั้น (< {short_threshold*100:.0f}%)"
    elif ratio < normal_threshold:
        category = f"ข้อความปกติ ({short_threshold*100:.0f}-{normal_threshold*100:.0f}%)"
    elif ratio < medium_threshold:
        category = f"ข้อความยาวปานกลาง ({normal_threshold*100:.0f}-{medium_threshold*100:.0f}%)"
    elif ratio < long_threshold:
        category = f"ข้อความยาวมาก ({medium_threshold*100:.0f}-{long_threshold*100:.0f}%)"
    elif ratio < very_long_s_threshold:
        category = f"ข้อความยาวมาก s ({long_threshold*100:.0f}-{very_long_s_threshold*100:.0f}%)"
    elif ratio < very_long_m_threshold:
        category = f"ข้อความยาวมาก m ({very_long_s_threshold*100:.0f}-{very_long_m_threshold*100:.0f}%)"
    elif ratio < very_long_l_threshold:
        category = f"ข้อความยาวมาก l ({very_long_m_threshold*100:.0f}-{very_long_l_threshold*100:.0f}%)"
    else:
        category = f"ข้อความยาวเกิน (> {very_long_l_threshold*100:.0f}%)"

    # เตรียมข้อมูลบรรทัดผลลัพธ์
    output = info.get("output", "") or ""
    lines = output.split("\n") if output else []
    line_widths = info.get("line_widths", [])
    num_chars_input = len(text)

    # แสดงผล
    print("\n--- ผลลัพธ์ ---")
    print(f"รูปทรง: {shape_type}")
    print(f"ข้อความต้นฉบับ: {text}")
    print(f"จำนวนอักษร (ต้นฉบับ): {num_chars_input}")
    print(f"การแบ่งคำ (NLP): {summarize_tokens(info.get('tokens', []))}")
    print(f"จำนวนคำ (หลังตัดคำ): {info.get('num_tokens', 0)}")
    
    print(f"\n--- Adaptive Width ---")
    print(f"ความกว้างข้อความก่อนแบ่ง: {text_width_before:.2f} px")
    print(f"ความกว้าง prototype: {base_width:.2f} px")
    print(f"อัตราส่วน (ratio): {ratio:.2f} ({ratio*100:.0f}%)")
    print(f"เกณฑ์: {category}")
    print(f"ขยาย: {scale:.2f}x ({scale*100:.0f}%)")
    print(f"ความกว้างสูงสุดที่ใช้: {max_width:.2f} px")

    print("\n--- ข้อความที่แบ่งแล้ว ---")
    if not lines:
        print("(ไม่มีผลลัพธ์การจัดวาง)")
    else:
        print(output)
        
    print("\nบรรทัดที่จัดวาง:")
    if not lines:
        print("  (ไม่มีผลลัพธ์การจัดวาง)")
    else:
        for idx, (line, width) in enumerate(zip(lines, line_widths), start=1):
            percent = (width / max_width * 100) if max_width > 0 else 0
            print(f"  บรรทัดที่ {idx}: {line}")
            print(f"    ความกว้าง: {width:.2f} px ({percent:.1f}%)")

    return True


def main():
    engine = LayoutEngine()
    while True:
        print_menu()
        choice = read_choice()
        if choice == "3":
            print("จบโปรแกรม ขอบคุณที่ทดลองครับ/ค่ะ")
            break
        keep_going = run_once(engine, choice)
        if not keep_going:
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nยกเลิกโดยผู้ใช้")
