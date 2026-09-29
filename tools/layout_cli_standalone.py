#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Standalone Manual Layout CLI

เวอร์ชันไฟล์เดียวของ tools/layout_cli.py
- ไม่ import โมดูลจาก src/
- ตัด logic เสริมออก เหลือโหมด split ตาม "|" แล้วจัดบรรทัด
- ภายนอกยังพึ่ง Pillow แบบ optional เพื่อวัดความกว้างฟอนต์
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


FONT_FILENAME = "THSarabunNew.ttf"
FONT_SIZE = 16

SHAPE_PROTOTYPES: Dict[str, str] = {
    "square_like": "ต้องไปรับการรักษา",
    "tall_rect": "ต้องไปรับการ",
}

ADAPTIVE_WIDTH: Dict[str, float | bool] = {
    "enabled": True,
    "short_text_threshold": 1.0,
    "short_text_scale": 0.7,
    "normal_text_threshold": 2.0,
    "normal_text_scale": 1.0,
    "medium_text_threshold": 3.0,
    "medium_text_scale": 1.25,
    "long_text_threshold": 4.0,
    "long_text_scale": 1.5,
    "very_long_s_threshold": 5.0,
    "very_long_s_scale": 1.6,
    "very_long_m_threshold": 6.0,
    "very_long_m_scale": 1.7,
    "very_long_l_threshold": 7.0,
    "very_long_l_scale": 1.8,
    "extreme_text_scale": 1.8,
    "min_scale": 1.0,
    "max_scale": 1.8,
}


def _find_font_path() -> str:
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir / FONT_FILENAME,
        script_dir.parent / FONT_FILENAME,
        Path.cwd() / FONT_FILENAME,
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return str(script_dir / FONT_FILENAME)


class FontMetrics:
    def __init__(self, font_path: str, font_size: int = FONT_SIZE):
        self.font_path = font_path
        self.font_size = font_size
        self._font = None
        self._pil_available = False
        self._initialize_font()

    def _initialize_font(self) -> None:
        try:
            from PIL import ImageFont

            if not os.path.exists(self.font_path):
                raise FileNotFoundError(f"ไม่พบไฟล์ฟอนต์: {self.font_path}")

            self._font = ImageFont.truetype(self.font_path, self.font_size)
            self._pil_available = True
        except ImportError:
            self._pil_available = False
        except Exception:
            self._pil_available = False

    def get_text_width(self, text: str) -> float:
        if not text:
            return 0.0
        if not self._pil_available or self._font is None:
            return len(text) * self.font_size * 0.6
        try:
            bbox = self._font.getbbox(text)
            return float(bbox[2] - bbox[0])
        except Exception:
            return len(text) * self.font_size * 0.6


_FONT_METRICS_SINGLETON: Optional[FontMetrics] = None


def create_font_metrics() -> Optional[FontMetrics]:
    global _FONT_METRICS_SINGLETON
    if _FONT_METRICS_SINGLETON is None:
        _FONT_METRICS_SINGLETON = FontMetrics(_find_font_path(), FONT_SIZE)
    return _FONT_METRICS_SINGLETON


class ThaiTokenizer:
    def tokenize(self, text: str) -> List[str]:
        if not text or not text.strip():
            return []
        return [token for token in text.split("|") if token]


class ShapeRuleLookup:
    SUPPORTED_SHAPES = ["square_like", "tall_rect"]
    DEFAULT_MAX_WIDTH: Dict[str, float] = {
        "square_like": 180.0,
        "tall_rect": 100.0,
    }

    @classmethod
    def _get_font_metrics(cls) -> Optional[FontMetrics]:
        return create_font_metrics()

    @classmethod
    def get_rules(cls, shape_type: str, text: Optional[str] = None) -> Dict[str, Any]:
        if shape_type not in cls.SUPPORTED_SHAPES:
            valid_shapes = ", ".join(cls.SUPPORTED_SHAPES)
            raise ValueError(
                f"ไม่รู้จักรูปทรง '{shape_type}'. รูปทรงที่รองรับ: {valid_shapes}"
            )

        base_width = cls.DEFAULT_MAX_WIDTH.get(shape_type, 180.0)
        prototype_text = SHAPE_PROTOTYPES.get(shape_type, "").strip() or None

        if prototype_text:
            font_metrics = cls._get_font_metrics()
            if font_metrics:
                base_width = font_metrics.get_text_width(prototype_text)
            else:
                base_width = len(prototype_text) * 10.0

        max_width = base_width
        if text and prototype_text and ADAPTIVE_WIDTH.get("enabled", True):
            font_metrics = cls._get_font_metrics()
            if font_metrics:
                clean_text = text.replace("|", "")
                text_width = font_metrics.get_text_width(clean_text)
                proto_width = font_metrics.get_text_width(prototype_text)
                ratio = text_width / proto_width if proto_width > 0 else 1.0

                min_scale = float(ADAPTIVE_WIDTH["min_scale"])
                max_scale = float(ADAPTIVE_WIDTH["max_scale"])

                if ratio < float(ADAPTIVE_WIDTH["short_text_threshold"]):
                    scale = max(min_scale, float(ADAPTIVE_WIDTH["short_text_scale"]))
                elif ratio < float(ADAPTIVE_WIDTH["normal_text_threshold"]):
                    scale = max(min_scale, float(ADAPTIVE_WIDTH["normal_text_scale"]))
                elif ratio < float(ADAPTIVE_WIDTH["medium_text_threshold"]):
                    scale = min(max_scale, float(ADAPTIVE_WIDTH["medium_text_scale"]))
                elif ratio < float(ADAPTIVE_WIDTH["long_text_threshold"]):
                    scale = min(max_scale, float(ADAPTIVE_WIDTH["long_text_scale"]))
                elif ratio < float(ADAPTIVE_WIDTH["very_long_s_threshold"]):
                    scale = min(max_scale, float(ADAPTIVE_WIDTH["very_long_s_scale"]))
                elif ratio < float(ADAPTIVE_WIDTH["very_long_m_threshold"]):
                    scale = min(max_scale, float(ADAPTIVE_WIDTH["very_long_m_scale"]))
                elif ratio < float(ADAPTIVE_WIDTH["very_long_l_threshold"]):
                    scale = min(max_scale, float(ADAPTIVE_WIDTH["very_long_l_scale"]))
                else:
                    scale = min(max_scale, float(ADAPTIVE_WIDTH["extreme_text_scale"]))

                max_width = base_width * scale

        return {
            "max_width": max_width,
            "base_width": base_width,
            "shape_type": shape_type,
        }

    @classmethod
    def validate_shape_type(cls, shape_type: str) -> bool:
        return shape_type in cls.SUPPORTED_SHAPES


class LayoutEngine:
    def __init__(self):
        self.tokenizer = ThaiTokenizer()
        self.font_metrics = create_font_metrics()
        self._width_cache: Dict[str, float] = {}

    def _get_text_width(self, text: str) -> float:
        if not text:
            return 0.0
        if text in self._width_cache:
            return self._width_cache[text]

        if self.font_metrics:
            width = self.font_metrics.get_text_width(text)
        else:
            width = len(text) * 10.0

        self._width_cache[text] = width
        return width

    def _calculate_balance_score(self, lines: List[List[str]]) -> float:
        if not lines:
            return 0.0

        widths = [self._get_text_width("".join(line)) for line in lines]
        if len(widths) == 1:
            return 0.0

        avg_width = sum(widths) / len(widths)
        variance = sum((width - avg_width) ** 2 for width in widths) / len(widths)
        return variance ** 0.5

    def _try_balance_lines(self, lines: List[List[str]], max_width: float) -> List[List[str]]:
        if len(lines) <= 1:
            return lines

        balanced = [line[:] for line in lines]
        current_score = self._calculate_balance_score(balanced)
        if current_score < 2.0:
            return balanced

        max_iterations = 30
        improved = True
        iteration = 0
        no_improvement_count = 0

        while improved and iteration < max_iterations:
            improved = False
            iteration += 1
            widths = [self._get_text_width("".join(line)) for line in balanced]
            avg_width = sum(widths) / len(widths)
            best_move = None
            best_score = current_score

            for i in range(len(balanced) - 1):
                if not balanced[i] or not balanced[i + 1]:
                    continue

                current_width_i = widths[i]
                current_width_i1 = widths[i + 1]

                if len(balanced[i]) > 1:
                    word = balanced[i][-1]
                    word_width = self._get_text_width(word)
                    new_width_i = current_width_i - word_width
                    new_width_i1 = current_width_i1 + word_width

                    if new_width_i1 <= max_width * 1.05:
                        old_diff = abs(current_width_i - avg_width) + abs(current_width_i1 - avg_width)
                        new_diff = abs(new_width_i - avg_width) + abs(new_width_i1 - avg_width)
                        if new_diff < old_diff:
                            test_lines = [line[:] for line in balanced]
                            test_lines[i].pop()
                            test_lines[i + 1].insert(0, word)
                            new_score = self._calculate_balance_score(test_lines)
                            if new_score < best_score - 0.01:
                                best_score = new_score
                                best_move = test_lines

                if len(balanced[i + 1]) > 1:
                    word = balanced[i + 1][0]
                    word_width = self._get_text_width(word)
                    new_width_i = current_width_i + word_width
                    new_width_i1 = current_width_i1 - word_width

                    if new_width_i <= max_width * 1.05:
                        old_diff = abs(current_width_i - avg_width) + abs(current_width_i1 - avg_width)
                        new_diff = abs(new_width_i - avg_width) + abs(new_width_i1 - avg_width)
                        if new_diff < old_diff:
                            test_lines = [line[:] for line in balanced]
                            test_lines[i + 1].pop(0)
                            test_lines[i].append(word)
                            new_score = self._calculate_balance_score(test_lines)
                            if new_score < best_score - 0.01:
                                best_score = new_score
                                best_move = test_lines

            if best_move is not None:
                balanced = best_move
                current_score = best_score
                improved = True
                no_improvement_count = 0
                if current_score < 2.0:
                    break
            else:
                no_improvement_count += 1
                if no_improvement_count >= 5:
                    break

        return balanced

    def layout_text(self, text: str, shape_type: str) -> str:
        if not text or not text.strip():
            return ""

        if not ShapeRuleLookup.validate_shape_type(shape_type):
            raise ValueError(f"ไม่รู้จักรูปทรง: {shape_type}")

        rules = ShapeRuleLookup.get_rules(shape_type, text)
        max_width = rules["max_width"]
        tokens = self.tokenizer.tokenize(text)
        if not tokens:
            return text

        lines: List[List[str]] = []
        cur: List[str] = []
        cur_width = 0.0
        i = 0

        while i < len(tokens):
            tok = tokens[i]
            tok_width = self._get_text_width(tok)

            if not cur:
                cur.append(tok)
                cur_width = tok_width
                i += 1
            elif cur_width + tok_width <= max_width:
                cur.append(tok)
                cur_width += tok_width
                i += 1
            else:
                lines.append(cur)
                cur = [tok]
                cur_width = tok_width
                i += 1

        if cur:
            lines.append(cur)

        if len(lines) > 1 and shape_type != "square_like":
            lines = self._try_balance_lines(lines, max_width)

        return "\n".join("".join(line) for line in lines)

    def get_layout_info(self, text: str, shape_type: str) -> Dict[str, Any]:
        rules = ShapeRuleLookup.get_rules(shape_type, text)
        tokens = self.tokenizer.tokenize(text)
        result = self.layout_text(text, shape_type)
        lines = result.split("\n") if result else []
        line_widths = [self._get_text_width(line) for line in lines]
        avg_width = sum(line_widths) / len(line_widths) if line_widths else 0
        variance = (
            sum((width - avg_width) ** 2 for width in line_widths) / len(line_widths)
            if line_widths
            else 0
        )
        return {
            "input_text": text,
            "shape_type": shape_type,
            "rules": rules,
            "tokens": tokens,
            "num_tokens": len(tokens),
            "output": result,
            "num_lines": len(lines),
            "line_widths": line_widths,
            "max_width": rules["max_width"],
            "avg_width": avg_width,
            "std_dev": variance ** 0.5,
            "font_available": bool(self.font_metrics and self.font_metrics._pil_available),
        }


def parse_shape_map(md_text: str) -> Dict[Tuple[str, int], str]:
    mapping: Dict[Tuple[str, int], str] = {}
    for i, raw in enumerate(md_text.splitlines()):
        if i == 0:
            continue
        parts = [part.strip() for part in raw.split(",")]
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
    sections: List[Tuple[str, List[Tuple[int, str]]]] = []
    current_fname: Optional[str] = None
    current_items: List[Tuple[int, str]] = []
    current_item_idx: Optional[int] = None
    current_item_text: List[str] = []

    def finish_current_item() -> None:
        if current_item_idx is not None and current_item_text and current_fname is not None:
            full_text = " ".join(current_item_text).strip()
            if full_text:
                current_items.append((current_item_idx, full_text))

    for raw in md_text.splitlines():
        line = raw.rstrip("\r")
        stripped = line.strip()

        if stripped.startswith("### ") and "." in stripped[4:]:
            finish_current_item()
            if current_fname is not None:
                sections.append((current_fname, current_items))
            current_fname = stripped[4:].strip()
            current_items = []
            current_item_idx = None
            current_item_text = []
            continue

        if stripped and stripped[0].isdigit():
            try:
                pos = stripped.index(".")
                new_idx = int(stripped[:pos])
                new_text = stripped[pos + 1 :].lstrip()
                finish_current_item()
                current_item_idx = new_idx
                current_item_text = [new_text] if new_text else []
            except Exception:
                if stripped and current_item_idx is not None:
                    current_item_text.append(stripped)
            continue

        if stripped and current_item_idx is not None:
            current_item_text.append(stripped)

    finish_current_item()
    if current_fname is not None:
        sections.append((current_fname, current_items))
    return sections


def process_single_file(
    engine: LayoutEngine,
    input_path: str,
    output_path: str,
    shape_map: Dict[Tuple[str, int], str],
    default_shape: str,
) -> int:
    try:
        with open(input_path, "r", encoding="utf-8") as f:
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
                out_lines.append(f"{idx}. {lines[0]}")
                for more in lines[1:]:
                    out_lines.append(more)
                out_lines.append("")
                total_items += 1

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            f.write("\n".join(out_lines).rstrip("\n") + "\n")
        return total_items
    except Exception as exc:
        print(f"Error processing {input_path}: {exc}")
        return 0


def _default_shape_file() -> str:
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir / "ข้อมูลรูปร่าง.md",
        script_dir.parent / "examples" / "ข้อมูลรูปร่าง.md",
        Path.cwd() / "ข้อมูลรูปร่าง.md",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return str(script_dir / "ข้อมูลรูปร่าง.md")


def main() -> None:
    parser = argparse.ArgumentParser(description="Standalone Layout CLI")
    parser.add_argument("--input", required=True, nargs="+", help="Path to input .md file(s) or directory")
    parser.add_argument("--output", required=True, help="Path to output .md file or directory")
    parser.add_argument("--shape_file", help="Path to ข้อมูลรูปร่าง.md file")
    parser.add_argument("--default_shape", default="square_like", help="Default shape type")
    args = parser.parse_args()

    input_files: List[str] = []
    for pattern in args.input:
        if os.path.isdir(pattern):
            found = glob.glob(os.path.join(pattern, "*.md"))
            input_files.extend(
                [path for path in found if "แบ่งคำแล้ว" not in os.path.basename(path)]
            )
        else:
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

    is_batch = (
        len(input_files) > 1
        or os.path.isdir(args.output)
        or (len(input_files) == 1 and os.path.isdir(args.input[0]))
    )

    engine = LayoutEngine()

    shape_map: Dict[Tuple[str, int], str] = {}
    shape_path = args.shape_file or _default_shape_file()
    if os.path.exists(shape_path):
        print(f"Loading shape map from: {shape_path}")
        try:
            with open(shape_path, "r", encoding="utf-8") as f:
                shape_map = parse_shape_map(f.read())
            print(f"Loaded {len(shape_map)} shape rules.")
        except Exception as exc:
            print(f"Warning: Failed to load shape map: {exc}")

    print(f"Processing {len(input_files)} file(s)...\n")
    total_processed_items = 0

    for input_path in input_files:
        input_path = os.path.abspath(input_path)
        filename = os.path.basename(input_path)

        if is_batch:
            out_dir = args.output if os.path.isdir(args.output) else (os.path.dirname(args.output) or ".")
            target_path = os.path.join(out_dir, f"แบ่งคำแล้ว_{filename}")
        else:
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
