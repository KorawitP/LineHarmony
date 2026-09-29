#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GUI ชั่วคราวเพื่อแทนที่ตัวอย่าง CLI (examples/cli_layout_demo.py)

ความสามารถ:
- ระบุไฟล์อินพุต 2 อย่าง: examples/ข้อมูลรูปร่าง.md, examples/คำแปล.md
    - แปลงไฟล์คำแปล: คงหมายเลขลำดับหน้าบรรทัด (1. 2. 3. ...)
      คงหัวข้อรูปแบบเดิม (### <ชื่อไฟล์>.<นามสกุล>) และคงการขึ้นบรรทัดใหม่ตามต้นฉบับ
    - แสดงตัวอย่างผลลัพธ์ในหน้าจอ และบันทึกเป็น examples/คำแปลหลังจัดประโยต.md

วิธีรัน:
  python examples/gui_layout_demo.py
"""

from __future__ import annotations

import os
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, List, Tuple, Optional

# ให้ import src.* ได้เมื่อรันจากโฟลเดอร์ examples
import sys


def _ensure_project_root_on_path() -> None:
    this_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(this_dir, os.pardir))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)


_ensure_project_root_on_path()

# นำ LayoutEngine มาใช้สำหรับการจัดบรรทัดตามรูปทรง
try:
    from src.core.layout_engine_v2 import LayoutEngine  # type: ignore
except Exception:  # หาก import ไม่ได้ จะดีเลย์ไปสร้างตอนกดปุ่ม
    LayoutEngine = None  # type: ignore


def default_path(*parts: str) -> str:
    this_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(this_dir, *parts)


def parse_shape_map(md_text: str) -> Dict[Tuple[str, int], str]:
    """อ่าน mapping จากไฟล์ข้อมูลรูปร่าง.md
    รูปแบบบรรทัด: ชื่อไฟล์,ข้อ,รูปทรงที่วิเคราะห์
    เช่น: 82_2.png,1,square_like
    คืนค่า dict[(filename, item_index)] = shape
    """
    mapping: Dict[Tuple[str, int], str] = {}
    for i, raw in enumerate(md_text.splitlines()):
        if i == 0:
            # ข้าม header
            continue
        parts = [p.strip() for p in raw.split(",")]
        if len(parts) != 3:
            continue
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
    """แปลงไฟล์คำแปล.md เป็นรายการส่วนย่อย: [(filename, [(n, text), ...]), ...]
    - ค้นหา header รูปแบบ '### <fname>.<ext>' (นามสกุลไฟล์อะไรก็ได้)
    - แต่ละข้อเป็นบรรทัดที่ขึ้นต้นด้วย '<เลข>. '
    - รวบรวมข้อความต่อเนื่องหลายบรรทัดสำหรับแต่ละข้อจนกว่าจะเจอข้อใหม่หรือ header ใหม่
    """
    sections: List[Tuple[str, List[Tuple[int, str]]]] = []
    current_fname: Optional[str] = None
    current_items: List[Tuple[int, str]] = []
    current_item_idx: Optional[int] = None
    current_item_text: List[str] = []

    def _finish_current_item():
        """จบข้อปัจจุบันและเพิ่มเข้า current_items"""
        if current_item_idx is not None and current_item_text and current_fname is not None:
            # รวมข้อความหลายบรรทัดเป็นข้อความเดียว (คั่นด้วยช่องว่าง)
            full_text = " ".join(current_item_text).strip()
            if full_text:
                current_items.append((current_item_idx, full_text))

    for raw in md_text.splitlines():
        line = raw.rstrip("\r")
        s = line.strip()
        
        if s.startswith("### ") and "." in s[4:]:
            # จบข้อปัจจุบันก่อน
            _finish_current_item()
            # ปิดของเดิมก่อน
            if current_fname is not None:
                sections.append((current_fname, current_items))
            # เริ่มใหม่
            current_fname = s[4:].strip()
            current_items = []
            current_item_idx = None
            current_item_text = []
            continue

        # ตรวจข้อใหม่
        if s and s[0].isdigit():
            # รูปแบบ '<n>. <text>'
            try:
                pos = s.index(".")
                new_idx = int(s[:pos])
                new_txt = s[pos + 1:].lstrip()
                
                # จบข้อเก่าก่อน
                _finish_current_item()
                
                # เริ่มข้อใหม่
                current_item_idx = new_idx
                current_item_text = [new_txt] if new_txt else []
            except Exception:
                # ถ้า parse ไม่ได้ ให้ถือว่าเป็นข้อความต่อเนื่อง
                if s and current_item_idx is not None:
                    current_item_text.append(s)
            continue

        # บรรทัดอื่นๆ ที่ไม่ใช่ header หรือข้อใหม่
        if s and current_item_idx is not None:
            # เป็นข้อความต่อเนื่องของข้อปัจจุบัน
            current_item_text.append(s)

    # จบข้อสุดท้าย
    _finish_current_item()
    if current_fname is not None:
        sections.append((current_fname, current_items))
    return sections


def layout_item(engine: "LayoutEngine", text: str, shape: str) -> List[str]:
    """ใช้ LayoutEngine จัดบรรทัดตาม shape แล้วคืนรายการบรรทัดผลลัพธ์"""
    try:
        info = engine.get_layout_info(text, shape)
        output = (info or {}).get("output") or ""
    except Exception:
        output = ""
    lines = output.split("\n") if output else []
    return lines or [text]


def build_output_with_layout(
    shape_map: Dict[Tuple[str, int], str], 
    md_text: str, 
    default_shape: str = "square_like",
    engine: Optional["LayoutEngine"] = None
) -> Tuple[str, Dict[str, int], Optional["LayoutEngine"]]:
    """ประมวลผลข้อความคำแปล โดยจัดบรรทัดด้วย LayoutEngine ตามรูปทรงต่อข้อ
    รูปแบบผลลัพธ์:
      ### <fname>
      1. <บรรทัด1>
      <บรรทัด2>
      ...
    
    Args:
        shape_map: แผนที่รูปทรง (ถ้าว่างจะใช้ default_shape)
        md_text: ข้อความคำแปล
        default_shape: รูปทรงเริ่มต้นเมื่อไม่มีใน shape_map
        engine: LayoutEngine ที่มีอยู่แล้ว (ถ้ามี) เพื่อใช้ cache ร่วมกัน
    
    Returns:
        Tuple[str, Dict, LayoutEngine]: (ผลลัพธ์, สถิติ, engine)
    """
    # ใช้ engine ที่ส่งมา หรือสร้างใหม่
    eng = engine if engine else (LayoutEngine() if LayoutEngine else None)  # type: ignore
    if eng is None:
        raise RuntimeError("ไม่สามารถโหลด LayoutEngine ได้")

    sections = parse_translation(md_text)
    out_lines: List[str] = []
    total_items = 0
    
    for fname, items in sections:
        out_lines.append(f"### {fname}")
        if not items:
            out_lines.append("")
            continue
        for idx, text in items:
            shape = shape_map.get((fname, idx), default_shape)
            lines = layout_item(eng, text, shape)
            if not lines:
                lines = [text]
            # บรรทัดแรกคงเลข, บรรทัดถัดไปไม่ใส่เลข
            out_lines.append(f"{idx}. {lines[0]}")
            for more in lines[1:]:
                out_lines.append(more)
            out_lines.append("")  # เว้นวรรคเหมือนโครงเดิม
            total_items += 1
    
    # สถิติ
    stats = {
        "total_items": total_items,
        "cache_size": eng.get_cache_size() if hasattr(eng, 'get_cache_size') else 0
    }
    
    # เพิ่ม newline ปิดท้ายไฟล์
    return "\n".join(out_lines).rstrip("\n") + "\n", stats, eng


def read_text(path: str) -> str:
    # newline='' เพื่อคงรูปแบบ newline เดิม (เช่น \r\n)
    with open(path, "r", encoding="utf-8", newline="") as f:
        return f.read()


def write_text(path: str, data: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # newline='' เพื่อไม่ให้ Python แปลง newline อัตโนมัติ
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(data)


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("LineHarmony GUI (ชั่วคราว)")
        self.geometry("900x700")

        # ค่าเริ่มต้น
        self.shape_path = tk.StringVar(value=default_path("ข้อมูลรูปร่าง.md"))
        self.translation_path = tk.StringVar(value=default_path("คำแปล.md"))
        self.output_path = tk.StringVar(value=default_path("คำแปลหลังจัดประโยต.md"))
        self.cache_path = tk.StringVar(value=default_path("cache", "width_cache.json"))
        
        # ตัวเลือกรูปทรง
        self.use_shape_file = tk.BooleanVar(value=True)  # ใช้ไฟล์รูปร่างหรือไม่
        self.default_shape = tk.StringVar(value="square_like")  # รูปทรงเริ่มต้นเมื่อไม่ใช้ไฟล์


        self._build_widgets()
        self._last_output_raw: str | None = None  # เก็บข้อมูลผลลัพธ์แบบ raw สำหรับการบันทึกแบบไม่เปลี่ยนแปลง
        self._engine: Optional["LayoutEngine"] = None  # เก็บ engine ไว้ใช้ต่อเนื่อง

    def _build_widgets(self) -> None:
        pad = {"padx": 8, "pady": 6}

        frm = ttk.Frame(self)
        frm.pack(fill=tk.X, **pad)

        # แถว: ไฟล์ข้อมูลรูปร่าง (พร้อม checkbox)
        shape_frame = ttk.Frame(frm)
        shape_frame.grid(row=0, column=0, columnspan=3, sticky=tk.W)
        
        ttk.Checkbutton(
            shape_frame, 
            text="ใช้ไฟล์ข้อมูลรูปร่าง (.md)", 
            variable=self.use_shape_file,
            command=self._toggle_shape_file
        ).pack(side=tk.LEFT)
        
        self.shape_entry = ttk.Entry(shape_frame, textvariable=self.shape_path, width=60)
        self.shape_entry.pack(side=tk.LEFT, padx=(8, 0))
        
        self.shape_browse_btn = ttk.Button(shape_frame, text="เลือก...", command=self._browse_shape)
        self.shape_browse_btn.pack(side=tk.LEFT, padx=(6, 0))
        
        # แถว: รูปทรงเริ่มต้น (แสดงเมื่อไม่ใช้ไฟล์)
        default_shape_frame = ttk.Frame(frm)
        default_shape_frame.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(4, 0))
        
        self.default_shape_label = ttk.Label(default_shape_frame, text="รูปทรงเริ่มต้น:")
        self.default_shape_label.pack(side=tk.LEFT)
        
        self.default_shape_combo = ttk.Combobox(
            default_shape_frame,
            textvariable=self.default_shape,
            values=["square_like", "tall_rect"],
            state="readonly",
            width=15
        )
        self.default_shape_combo.pack(side=tk.LEFT, padx=(8, 0))

        # แถว: ไฟล์คำแปล
        ttk.Label(frm, text="ไฟล์คำแปล (.md)").grid(row=2, column=0, sticky=tk.W)
        ttk.Entry(frm, textvariable=self.translation_path, width=80).grid(row=2, column=1, sticky=tk.W)
        ttk.Button(frm, text="เลือก...", command=self._browse_translation).grid(row=2, column=2, sticky=tk.W, padx=(6, 0))

        # แถว: ไฟล์ผลลัพธ์
        ttk.Label(frm, text="บันทึกผลเป็น").grid(row=3, column=0, sticky=tk.W)
        ttk.Entry(frm, textvariable=self.output_path, width=80).grid(row=3, column=1, sticky=tk.W)
        ttk.Button(frm, text="เปลี่ยน...", command=self._browse_output).grid(row=3, column=2, sticky=tk.W, padx=(6, 0))

        # แถว: ไฟล์แคช
        ttk.Label(frm, text="ไฟล์แคชความกว้าง (.json)").grid(row=4, column=0, sticky=tk.W)
        ttk.Entry(frm, textvariable=self.cache_path, width=80).grid(row=4, column=1, sticky=tk.W)
        ttk.Button(frm, text="เลือก...", command=self._browse_cache).grid(row=4, column=2, sticky=tk.W, padx=(6, 0))



        # ปุ่มควบคุม
        btn_bar = ttk.Frame(self)
        btn_bar.pack(fill=tk.X, **pad)
        ttk.Button(btn_bar, text="โหลดแคช", command=self._load_cache).pack(side=tk.LEFT)
        ttk.Button(btn_bar, text="ประมวลผล", command=self._process).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(btn_bar, text="บันทึกไฟล์", command=self._save).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(btn_bar, text="บันทึกแคช", command=self._save_cache).pack(side=tk.LEFT, padx=(8, 0))

        # สถานะ
        self.status = tk.StringVar(value="พร้อมใช้งาน")
        ttk.Label(self, textvariable=self.status, foreground="#444").pack(fill=tk.X, **pad)

        # ตัวอย่างผลลัพธ์
        preview_lbl = ttk.Label(self, text="ตัวอย่างผลลัพธ์ (แสดงผลหลังประมวลผล)")
        preview_lbl.pack(anchor=tk.W, padx=8)

        # แก้ไข: tkinter ใช้ค่าคงที่เป็นตัวพิมพ์ใหญ่ เช่น tk.WORD
        self.preview = tk.Text(self, wrap=tk.WORD, height=25)
        self.preview.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)
        
        # เรียกใช้ toggle เพื่อตั้งค่าสถานะเริ่มต้น
        self._toggle_shape_file()

    # ---------- UI Controls ----------
    def _toggle_shape_file(self) -> None:
        """เปิด/ปิดการใช้ไฟล์รูปร่าง"""
        use_file = self.use_shape_file.get()
        
        # เปิด/ปิด entry และปุ่มเลือกไฟล์
        state = "normal" if use_file else "disabled"
        self.shape_entry.config(state=state)
        self.shape_browse_btn.config(state=state)
        
        # เปิด/ปิด dropdown รูปทรงเริ่มต้น (ตรงข้าม)
        combo_state = "disabled" if use_file else "readonly"
        self.default_shape_combo.config(state=combo_state)
        
        # เปลี่ยนสีข้อความ label
        label_color = "#444" if not use_file else "#999"
        self.default_shape_label.config(foreground=label_color)

    # ---------- Browsers ----------
    def _browse_shape(self) -> None:
        path = filedialog.askopenfilename(
            title="เลือกไฟล์ข้อมูลรูปร่าง (.md)",
            initialdir=os.path.dirname(self.shape_path.get()),
            filetypes=[("Markdown", "*.md"), ("All", "*.*")],
        )
        if path:
            self.shape_path.set(path)

    def _browse_translation(self) -> None:
        path = filedialog.askopenfilename(
            title="เลือกไฟล์คำแปล (.md)",
            initialdir=os.path.dirname(self.translation_path.get()),
            filetypes=[("Markdown", "*.md"), ("All", "*.*")],
        )
        if path:
            self.translation_path.set(path)

    def _browse_output(self) -> None:
        path = filedialog.asksaveasfilename(
            title="เลือกตำแหน่งบันทึกผล",
            initialfile=os.path.basename(self.output_path.get()),
            initialdir=os.path.dirname(self.output_path.get()),
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("All", "*.*")],
        )
        if path:
            self.output_path.set(path)

    def _browse_cache(self) -> None:
        path = filedialog.askopenfilename(
            title="เลือกไฟล์แคชความกว้าง (.json)",
            initialdir=os.path.dirname(self.cache_path.get()),
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        )
        if path:
            self.cache_path.set(path)

    # ---------- Cache Management ----------
    def _load_cache(self) -> None:
        """โหลดแคชจากไฟล์"""
        cache_file = self.cache_path.get().strip()
        
        # สร้าง engine ถ้ายังไม่มี
        if self._engine is None:
            try:
                self._engine = LayoutEngine() if LayoutEngine else None  # type: ignore
                if self._engine is None:
                    messagebox.showerror("ข้อผิดพลาด", "ไม่สามารถสร้าง LayoutEngine ได้")
                    return
            except Exception as e:
                messagebox.showerror("ข้อผิดพลาด", f"สร้าง LayoutEngine ไม่สำเร็จ: {e}")
                return
        
        if not os.path.isfile(cache_file):
            messagebox.showwarning("แจ้งเตือน", f"ไม่พบไฟล์แคช: {cache_file}\nจะสร้างใหม่เมื่อประมวลผล")
            return
        
        try:
            count = self._engine.load_cache_from_file(cache_file)
            self.status.set(f"โหลดแคชสำเร็จ: {count} รายการจาก {cache_file}")
            messagebox.showinfo("สำเร็จ", f"โหลดแคช {count} รายการ")
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"โหลดแคชไม่สำเร็จ: {e}")

    def _save_cache(self) -> None:
        """บันทึกแคชลงไฟล์"""
        if self._engine is None:
            messagebox.showwarning("แจ้งเตือน", "ยังไม่มีแคชให้บันทึก กรุณาประมวลผลก่อน")
            return
        
        cache_file = self.cache_path.get().strip()
        try:
            count = self._engine.save_cache_to_file(cache_file)
            self.status.set(f"บันทึกแคชสำเร็จ: {count} รายการไปยัง {cache_file}")
            messagebox.showinfo("สำเร็จ", f"บันทึกแคช {count} รายการ")
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"บันทึกแคชไม่สำเร็จ: {e}")

    # ---------- Processing ----------
    def _process(self) -> None:
        shp = self.shape_path.get().strip()
        trn = self.translation_path.get().strip()
        cache_file = self.cache_path.get().strip()
        use_shape_file = self.use_shape_file.get()
        default_shape = self.default_shape.get()
        
        if not os.path.isfile(trn):
            messagebox.showerror("ข้อผิดพลาด", f"ไม่พบไฟล์คำแปล: {trn}")
            return
        
        try:
            # สร้าง engine ถ้ายังไม่มี
            if self._engine is None:
                self._engine = LayoutEngine() if LayoutEngine else None  # type: ignore
                if self._engine is None:
                    raise RuntimeError("ไม่สามารถสร้าง LayoutEngine ได้")
                
                # โหลดแคชอัตโนมัติถ้ามีไฟล์
                if os.path.isfile(cache_file):
                    loaded = self._engine.load_cache_from_file(cache_file)
                    if loaded > 0:
                        self.status.set(f"โหลดแคชอัตโนมัติ: {loaded} รายการ")
            
            # โหลด lexicons ใหม่ทุกครั้งก่อนประมวลผล (เพราะอาจมีการแก้ไขระหว่างทำงาน)
            if hasattr(self._engine, 'reload_lexicons'):
                self._engine.reload_lexicons()
                self.status.set("โหลด lexicons ใหม่...")
            
            # โหลด shape_map ถ้าเลือกใช้ไฟล์รูปร่าง
            shape_map = {}
            if use_shape_file:
                if os.path.isfile(shp):
                    raw_shape = read_text(shp)
                    shape_map = parse_shape_map(raw_shape) if raw_shape else {}
                else:
                    messagebox.showwarning(
                        "แจ้งเตือน", 
                        f"ไม่พบไฟล์รูปร่าง: {shp}\nจะใช้รูปทรงเริ่มต้น '{default_shape}' แทน"
                    )
            
            raw = read_text(trn)
            
            # Batch processing: ใช้ engine instance เดียว = ใช้ cache ร่วมกัน
            import time
            start_time = time.time()
            cache_before = self._engine.get_cache_size()
            out, stats, self._engine = build_output_with_layout(
                shape_map, raw, default_shape, self._engine
            )
            elapsed_time = time.time() - start_time
            cache_after = self._engine.get_cache_size()
            new_entries = cache_after - cache_before
            
            # บันทึกแคชอัตโนมัติหลังประมวลผล
            if new_entries > 0:
                self._engine.save_cache_to_file(cache_file)
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ประมวลผลไม่สำเร็จ: {e}")
            return

        # แสดงผลในหน้าต่าง
        self.preview.delete("1.0", tk.END)
        self.preview.insert("1.0", out)
        # เก็บสำเนาแบบเดิมเพื่อบันทึกโดยไม่โดน Text widget แปลง newline
        self._last_output_raw = out

        # รายงานสถานะพร้อมสถิติ
        shape_note = ""
        if use_shape_file and os.path.isfile(shp):
            try:
                cnt = sum(1 for _ in open(shp, "r", encoding="utf-8"))
                shape_note = f" | ข้อมูลรูปร่าง {cnt} บรรทัด"
            except Exception:
                shape_note = " | อ่านข้อมูลรูปร่างไม่สำเร็จ"
        elif not use_shape_file:
            shape_note = f" | ใช้รูปทรงเริ่มต้น: {default_shape}"
        
        # แสดงสถิติประสิทธิภาพ
        cache_note = f" | Cache: {cache_after} คำ"
        if new_entries > 0:
            cache_note += f" (+{new_entries} ใหม่, บันทึกแล้ว)"
        
        # ตรวจสอบการใช้สัญลักษณ์คู่
        paired_symbols_note = ""
        if hasattr(self._engine, 'paired_symbols') and self._engine.paired_symbols:
            paired_count = len(self._engine.paired_symbols)
            paired_symbols_note = f" | สัญลักษณ์คู่: {paired_count} ชนิด"
        
        perf_note = f" | ประมวลผล {stats['total_items']} ข้อความ ใช้เวลา {elapsed_time:.2f}s{cache_note}{paired_symbols_note}"
        self.status.set(f"ประมวลผลสำเร็จ{shape_note}{perf_note}")

    def _save(self) -> None:
        # ใช้สำเนาผลลัพธ์จากขั้นตอนประมวลผล (รูปแบบตาม LayoutEngine)
        data = self._last_output_raw if self._last_output_raw is not None else self.preview.get("1.0", tk.END)
        outp = self.output_path.get().strip()
        if not (data or "").strip():
            messagebox.showwarning("แจ้งเตือน", "ไม่มีข้อมูลให้บันทึก กรุณากด 'ประมวลผล' ก่อน")
            return
        try:
            write_text(outp, data)
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"บันทึกไม่สำเร็จ: {e}")
            return
        self.status.set(f"บันทึกแล้ว: {outp}")
        messagebox.showinfo("สำเร็จ", f"บันทึกผลเป็น\n{outp}")


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
