"""
Layout Engine - Simple Word-Wrap Mode
จัดวางข้อความแบบง่าย: ตัดตามคำ ไม่ตัดกลางอักษร พร้อมกฎปลายบรรทัด
ใช้ความกว้างจริงของข้อความ (วัดด้วยฟอนต์) แทนการนับตัวอักษร
"""

from typing import List, Dict, Any, Optional
import re
from src.core.shape_rules import ShapeRuleLookup
from src.tokenizer.thai_tokenizer import ThaiTokenizer
from src.utils.config import get_config


class LayoutEngine:
    """
    Layout Engine แบบ Simple Word-Wrap
    จัดวางข้อความตามคำ ไม่ตัดกลางอักษร พร้อมกฎปลายบรรทัด
    ใช้ความกว้างจริงของข้อความ (วัดด้วยฟอนต์)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        สร้าง layout engine
        
        Args:
            config: การตั้งค่าเพิ่มเติม
        """
        self.config = config or {}
        
        # สร้าง tokenizer (pipe mode — แบ่งคำด้วย |)
        self.tokenizer = ThaiTokenizer()
        
        # สร้าง font metrics สำหรับวัดความกว้าง
        self.font_metrics = None
        try:
            from src.utils.font_metrics import create_font_metrics_from_config
            self.font_metrics = create_font_metrics_from_config()
        except Exception:
            self.font_metrics = None
        
        # Cache สำหรับความกว้างของข้อความ (เพิ่มประสิทธิภาพ)
        self._width_cache: Dict[str, float] = {}
        
        # โหลดกฎห้ามจบบรรทัดด้วยคำบางคำจาก config/json
        self.use_line_end_rules = False
        self.disallow_line_end: set[str] = set()
        self.polite_words: set[str] = set()
        self.paired_symbols: Dict[str, str] = {}  # open -> close mapping
        
        try:
            cfg = get_config()
            layout_cfg = cfg.get("layout", {}) or {}
            self.use_line_end_rules = bool(layout_cfg.get("use_line_end_rules", True))
            
            import json
            import os
            path = layout_cfg.get("line_end_rules_path", "data/lexicons/line_end_rules.json")
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f) or {}
                
                # โหลดคำห้ามจบบรรทัด
                for w in (data.get("disallow_line_end") or []):
                    if isinstance(w, str) and w.strip():
                        self.disallow_line_end.add(w.strip())
                
                # โหลดคำสุภาพ
                for w in (data.get("polite_words") or []):
                    if isinstance(w, str) and w.strip():
                        self.polite_words.add(w.strip())
                
                # โหลดสัญลักษณ์คู่
                for pair in (data.get("paired_symbols") or []):
                    if isinstance(pair, dict) and "open" in pair and "close" in pair:
                        open_sym = pair["open"].strip()
                        close_sym = pair["close"].strip()
                        if open_sym and close_sym:
                            self.paired_symbols[open_sym] = close_sym
        except Exception:
            # ใช้ค่าเริ่มต้นว่างหากอ่าน config ไม่ได้
            self.use_line_end_rules = False
            self.disallow_line_end = set()
            self.polite_words = set()
            self.paired_symbols = {}
    
    def _get_text_width(self, text: str) -> float:
        """
        วัดความกว้างของข้อความ (พร้อม cache)
        
        Args:
            text: ข้อความที่ต้องการวัด
            
        Returns:
            ความกว้างของข้อความ (pixels)
        """
        if not text:
            return 0.0
        
        # ตรวจสอบ cache ก่อน
        if text in self._width_cache:
            return self._width_cache[text]
        
        # คำนวณความกว้าง
        if self.font_metrics:
            width = self.font_metrics.get_text_width(text)
        else:
            # Fallback: ประมาณจากจำนวนตัวอักษร
            width = len(text) * 10.0
        
        # เก็บใน cache
        self._width_cache[text] = width
        return width
    
    def clear_cache(self):
        """ล้าง cache (ใช้เมื่อต้องการประหยัด memory)"""
        self._width_cache.clear()
    
    def reload_lexicons(self) -> None:
        """
        โหลด lexicon files ใหม่ (line_end_rules.json, non_breaking_words.json)
        ใช้เมื่อมีการแก้ไขไฟล์ lexicon ระหว่างการทำงาน
        """
        import json
        import os
        
        # รีเซ็ตค่า
        self.disallow_line_end = set()
        self.polite_words = set()
        self.paired_symbols = {}
        
        try:
            cfg = get_config()
            layout_cfg = cfg.get("layout", {}) or {}
            self.use_line_end_rules = bool(layout_cfg.get("use_line_end_rules", True))
            
            # โหลด line_end_rules.json
            path = layout_cfg.get("line_end_rules_path", "data/lexicons/line_end_rules.json")
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f) or {}
                
                # โหลดคำห้ามจบบรรทัด
                for w in (data.get("disallow_line_end") or []):
                    if isinstance(w, str) and w.strip():
                        self.disallow_line_end.add(w.strip())
                
                # โหลดคำสุภาพ
                for w in (data.get("polite_words") or []):
                    if isinstance(w, str) and w.strip():
                        self.polite_words.add(w.strip())
                
                # โหลดสัญลักษณ์คู่
                for pair in (data.get("paired_symbols") or []):
                    if isinstance(pair, dict) and "open" in pair and "close" in pair:
                        open_sym = pair["open"].strip()
                        close_sym = pair["close"].strip()
                        if open_sym and close_sym:
                            self.paired_symbols[open_sym] = close_sym
            
            # โหลด non_breaking_words.json สำหรับ tokenizer
            tokenizer_cfg = cfg.get("tokenizer", {}) or {}
            if tokenizer_cfg.get("non_breaking_enabled", True):
                nb_path = tokenizer_cfg.get("non_breaking_words_path", "data/lexicons/non_breaking_words.json")
                if os.path.isfile(nb_path) and hasattr(self.tokenizer, 'reload_non_breaking_words'):
                    self.tokenizer.reload_non_breaking_words(nb_path)
        except Exception:
            # ใช้ค่าเริ่มต้นว่างหากอ่าน config ไม่ได้
            self.use_line_end_rules = False
            self.disallow_line_end = set()
            self.polite_words = set()
            self.paired_symbols = {}
    
    def load_cache_from_file(self, filepath: str) -> int:
        """
        โหลดแคชจากไฟล์ JSON
        
        Args:
            filepath: path ของไฟล์ JSON
            
        Returns:
            จำนวนรายการที่โหลดได้
        """
        import json
        import os
        
        if not os.path.isfile(filepath):
            return 0
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Merge กับแคชที่มีอยู่ (ไม่ลบของเดิม)
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(key, str) and isinstance(value, (int, float)):
                        self._width_cache[key] = float(value)
                return len(data)
        except Exception:
            return 0
        
        return 0
    
    def save_cache_to_file(self, filepath: str) -> int:
        """
        บันทึกแคชลงไฟล์ JSON
        
        Args:
            filepath: path ของไฟล์ JSON
            
        Returns:
            จำนวนรายการที่บันทึก
        """
        import json
        import os
        
        try:
            # สร้างโฟลเดอร์ถ้ายังไม่มี
            os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self._width_cache, f, ensure_ascii=False, indent=2)
            
            return len(self._width_cache)
        except Exception:
            return 0
    
    def get_cache_size(self) -> int:
        """
        ดึงจำนวนรายการในแคช
        
        Returns:
            จำนวนรายการ
        """
        return len(self._width_cache)
    
    def _calculate_balance_score(self, lines: List[List[str]]) -> float:
        """
        คำนวณคะแนนความสมดุล (ยิ่งต่ำยิ่งดี)
        คำนวณจากค่าเบี่ยงเบนมาตรฐานของความกว้างแต่ละบรรทัด
        
        Args:
            lines: รายการบรรทัด (แต่ละบรรทัดเป็น list ของคำ)
            
        Returns:
            คะแนน (0 = สมดุลสมบูรณ์)
        """
        if not lines:
            return 0.0
        
        widths = [self._get_text_width("".join(line)) for line in lines]
        
        if len(widths) == 1:
            return 0.0
        
        # คำนวณค่าเฉลี่ย
        avg_width = sum(widths) / len(widths)
        
        # คำนวณค่าเบี่ยงเบนมาตรฐาน
        variance = sum((w - avg_width) ** 2 for w in widths) / len(widths)
        std_dev = variance ** 0.5
        
        return std_dev
    
    def _try_balance_lines(self, lines: List[List[str]], max_width: float) -> List[List[str]]:
        """
        พยายามปรับสมดุลความกว้างของแต่ละบรรทัดให้ใกล้เคียงกัน
        โดยย้ายคำระหว่างบรรทัดที่ติดกัน
        
        กลยุทธ์:
        1. ย้ายคำจากบรรทัดที่กว้างกว่าค่าเฉลี่ยไปบรรทัดที่แคบกว่าค่าเฉลี่ย
        2. ลองทุกความเป็นไปได้และเลือกที่ทำให้คะแนนดีที่สุด
        3. Early termination - หยุดเมื่อสมดุลดีพอหรือไม่มีการปรับปรุง
        
        Args:
            lines: รายการบรรทัดเริ่มต้น
            max_width: ความกว้างสูงสุดที่อนุญาต
            
        Returns:
            รายการบรรทัดที่ปรับสมดุลแล้ว
        """
        if len(lines) <= 1:
            return lines
        
        # คัดลอกเพื่อไม่ให้กระทบต้นฉบับ
        balanced = [line[:] for line in lines]
        
        # คำนวณคะแนนเริ่มต้น
        current_score = self._calculate_balance_score(balanced)
        
        # Early termination: ถ้าสมดุลดีพอแล้ว (std_dev < 2.0) ก็หยุดเลย
        if current_score < 2.0:
            return balanced
        
        # ลองปรับสมดุลสูงสุด 30 รอบ
        max_iterations = 30
        improved = True
        iteration = 0
        no_improvement_count = 0  # นับจำนวนรอบที่ไม่มีการปรับปรุง
        
        while improved and iteration < max_iterations:
            improved = False
            iteration += 1
            
            # คำนวณความกว้างและค่าเฉลี่ย
            widths = [self._get_text_width("".join(line)) for line in balanced]
            avg_width = sum(widths) / len(widths)
            
            best_move = None
            best_score = current_score
            
            # ลองย้ายคำระหว่างบรรทัดที่ติดกัน
            for i in range(len(balanced) - 1):
                if not balanced[i] or not balanced[i + 1]:
                    continue
                
                current_width_i = widths[i]
                current_width_i1 = widths[i + 1]
                
                # ลองย้ายคำสุดท้ายของบรรทัด i ไปบรรทัด i+1
                if len(balanced[i]) > 1:
                    word = balanced[i][-1]
                    word_width = self._get_text_width(word)
                    
                    new_width_i = current_width_i - word_width
                    new_width_i1 = current_width_i1 + word_width
                    
                    # อนุโลม 5% สำหรับการปรับสมดุล
                    if new_width_i1 <= max_width * 1.05:
                        # คำนวณว่าการย้ายนี้ทำให้ใกล้ค่าเฉลี่ยมากขึ้นหรือไม่
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
                
                # ลองย้ายคำแรกของบรรทัด i+1 ไปบรรทัด i
                if len(balanced[i + 1]) > 1:
                    word = balanced[i + 1][0]
                    word_width = self._get_text_width(word)
                    
                    new_width_i = current_width_i + word_width
                    new_width_i1 = current_width_i1 - word_width
                    
                    # อนุโลม 5% สำหรับการปรับสมดุล
                    if new_width_i <= max_width * 1.05:
                        # คำนวณว่าการย้ายนี้ทำให้ใกล้ค่าเฉลี่ยมากขึ้นหรือไม่
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
            
            # ถ้าพบการย้ายที่ดีกว่า ให้ใช้
            if best_move is not None:
                balanced = best_move
                current_score = best_score
                improved = True
                no_improvement_count = 0  # รีเซ็ตตัวนับ
                
                # Early termination: ถ้าสมดุลดีพอแล้ว ก็หยุดเลย
                if current_score < 2.0:
                    break
            else:
                no_improvement_count += 1
                
                # Early termination: ถ้าไม่มีการปรับปรุงใน 5 รอบติด ก็หยุด
                if no_improvement_count >= 5:
                    break
        
        return balanced
    
    def layout_text(self, text: str, shape_type: str) -> str:
        """
        จัดบรรทัดตามคำ (ไม่ตัดกลางอักษร) เติมจนไม่เกินเพดาน
        จากนั้นปรับสมดุลความกว้างของแต่ละบรรทัดให้ใกล้เคียงกัน
        
        อัลกอริทึม:
        1. Greedy Packing - ใส่คำให้เต็มที่สุด
        2. Balance Optimization - ปรับสมดุลความกว้างให้ใกล้เคียงกัน
        3. Apply Rules - ใช้กฎห้ามจบบรรทัด, รวมคำสุภาพ
        
        Args:
            text: ข้อความที่ต้องการจัดวาง
            shape_type: ชนิดของรูปทรง
            
        Returns:
            ข้อความที่จัดวางแล้ว (แบ่งบรรทัดด้วย \\n)
        """
        if not text or not text.strip():
            return ""
        
        if not ShapeRuleLookup.validate_shape_type(shape_type):
            raise ValueError(f"ไม่รู้จักรูปทรง: {shape_type}")

        # ใช้ Adaptive Width: ส่งข้อความไปด้วยเพื่อปรับความกว้างอัตโนมัติ
        rules = ShapeRuleLookup.get_rules(shape_type, text)
        max_width = rules["max_width"]

        tokens = self.tokenizer.tokenize(text)
        if not tokens:
            return text

        # ขั้นตอนที่ 1: Greedy Packing - ใส่คำให้เต็มที่สุด (พร้อมตรวจสอบสัญลักษณ์คู่)
        lines: List[List[str]] = []
        cur: List[str] = []
        cur_width = 0.0
        
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            tok_width = self._get_text_width(tok)
            
            if not cur:
                # บรรทัดว่าง ใส่คำแรกเสมอ
                cur.append(tok)
                cur_width = tok_width
                i += 1
            elif cur_width + tok_width <= max_width:
                # ใส่ได้ ไม่เกินความกว้าง
                cur.append(tok)
                cur_width += tok_width
                i += 1
            else:
                # เกินแล้ว - ตรวจสอบสัญลักษณ์คู่ก่อนตัดบรรทัด
                if self.paired_symbols and self._would_break_pair(cur):
                    # มีสัญลักษณ์คู่ที่ยังไม่ปิด - พยายามใส่ token เพิ่มจนกว่าจะปิดคู่
                    temp_tokens = cur[:]
                    temp_width = cur_width
                    j = i
                    
                    # ลองใส่ token ต่อไปจนกว่าจะปิดคู่หรือเกินขีดจำกัดมาก
                    max_overflow = max_width * 0.3  # อนุโลม 30% สำหรับสัญลักษณ์คู่
                    while j < len(tokens) and temp_width <= max_width + max_overflow:
                        temp_tokens.append(tokens[j])
                        temp_width += self._get_text_width(tokens[j])
                        j += 1
                        
                        # ถ้าปิดคู่แล้วให้หยุด
                        if not self._would_break_pair(temp_tokens):
                            cur = temp_tokens
                            cur_width = temp_width
                            i = j
                            break
                    else:
                        # ไม่สามารถปิดคู่ได้ในขีดจำกัด - ตัดบรรทัดปกติ
                        lines.append(cur)
                        cur = [tok]
                        cur_width = tok_width
                        i += 1
                else:
                    # ไม่มีปัญหาสัญลักษณ์คู่ - ตัดบรรทัดปกติ
                    lines.append(cur)
                    cur = [tok]
                    cur_width = tok_width
                    i += 1
        
        if cur:
            lines.append(cur)

        # ขั้นตอนที่ 2: Balance Optimization - ปรับสมดุลความกว้าง
        # (ข้าม square_like เพราะต้องการยัดให้เต็มแถวเท่านั้น)
        if len(lines) > 1 and shape_type != "square_like":
            lines = self._try_balance_lines(lines, max_width)

        # ขั้นตอนที่ 3: Apply Rules
        
        # ไม่ให้จบบรรทัดด้วยคำต้องห้าม ถ้าย้ายคำสุดท้ายไปบรรทัดถัดไปได้โดยไม่ล้น
        if self.use_line_end_rules and self.disallow_line_end:
            for i in range(len(lines) - 1):
                line = lines[i]
                next_line = lines[i + 1]
                if not line or not next_line:
                    continue
                if self._ends_with_disallowed(line):
                    last = line[-1]
                    next_line_width = self._get_text_width("".join(next_line))
                    last_width = self._get_text_width(last)
                    
                    if next_line_width + last_width <= max_width:
                        line.pop()
                        next_line.insert(0, last)

        # คำสุภาพเดี่ยวบรรทัดสุดท้าย → รวมกับบรรทัดก่อนหน้า หากไม่ล้น (อนุโลม 10%)
        if len(lines) >= 2:
            last = lines[-1]
            prev = lines[-2]
            if len(last) == 1 and last[0] in self.polite_words:
                prev_width = self._get_text_width("".join(prev))
                last_width = self._get_text_width(last[0])
                
                # อนุโลม 10% สำหรับคำสุภาพ
                if prev_width + last_width <= max_width * 1.1:
                    prev.append(last[0])
                    lines.pop()

        return "\n".join("".join(line) for line in lines)
    
    def _has_unclosed_pairs(self, tokens: List[str]) -> bool:
        """
        ตรวจสอบว่ามีสัญลักษณ์คู่ที่ยังไม่ปิดหรือไม่
        
        Args:
            tokens: รายการ token ที่ต้องการตรวจสอบ
            
        Returns:
            True ถ้ามีสัญลักษณ์คู่ที่ยังไม่ปิด
        """
        if not self.paired_symbols:
            return False
        
        # สร้าง stack สำหรับติดตามสัญลักษณ์เปิด
        stack = []
        text = "".join(tokens)
        
        i = 0
        while i < len(text):
            char = text[i]
            
            # ตรวจสอบสัญลักษณ์เปิด
            if char in self.paired_symbols:
                stack.append(char)
            else:
                # ตรวจสอบสัญลักษณ์ปิด
                for open_sym, close_sym in self.paired_symbols.items():
                    if char == close_sym:
                        if stack and stack[-1] == open_sym:
                            stack.pop()
                        break
            i += 1
        
        return len(stack) > 0
    
    def _would_break_pair(self, tokens: List[str]) -> bool:
        """
        ตรวจสอบว่าการตัดบรรทัดที่จุดนี้จะทำให้สัญลักษณ์คู่แยกกันหรือไม่
        
        Args:
            tokens: รายการ token ที่จะอยู่ในบรรทัดนี้
            
        Returns:
            True ถ้าการตัดจะทำให้สัญลักษณ์คู่แยกกัน
        """
        return self._has_unclosed_pairs(tokens)
    
    def _find_safe_break_point(self, tokens: List[str], max_width: float) -> int:
        """
        หาจุดตัดที่ปลอดภัย โดยไม่ทำให้สัญลักษณ์คู่แยกกัน
        
        Args:
            tokens: รายการ token
            max_width: ความกว้างสูงสุด
            
        Returns:
            index ของจุดตัดที่ปลอดภัย (-1 ถ้าหาไม่ได้)
        """
        if not tokens:
            return -1
        
        # หาจุดตัดที่ไม่เกินความกว้าง
        safe_point = -1
        current_width = 0.0
        
        for i, token in enumerate(tokens):
            token_width = self._get_text_width(token)
            if current_width + token_width > max_width:
                break
            current_width += token_width
            
            # ตรวจสอบว่าจุดนี้ปลอดภัยหรือไม่ (ไม่มีสัญลักษณ์คู่ที่ยังไม่ปิด)
            if not self._has_unclosed_pairs(tokens[:i+1]):
                safe_point = i
        
        return safe_point

    def _ends_with_disallowed(self, line_tokens: List[str]) -> bool:
        """
        ตรวจสอบว่าบรรทัดจบด้วยคำต้องห้ามหรือไม่
        
        Args:
            line_tokens: List ของ token ในบรรทัด
            
        Returns:
            True ถ้าจบด้วยคำต้องห้าม
        """
        if not self.use_line_end_rules or not self.disallow_line_end:
            return False
        if not line_tokens:
            return False
        
        # หา token ท้ายที่เป็นคำ (ไม่นับวรรคตอนล้วน)
        patt = re.compile(r"[\u0E00-\u0E7Fa-zA-Z0-9]")
        for t in reversed(line_tokens):
            if t and patt.search(t) is not None:
                return t in self.disallow_line_end
        return False
    
    def get_layout_info(self, text: str, shape_type: str) -> Dict[str, Any]:
        """
        ดึงข้อมูลการจัดวางแบบละเอียด
        
        Args:
            text: ข้อความที่ต้องการจัดวาง
            shape_type: ชนิดของรูปทรง
            
        Returns:
            Dict ของข้อมูลการจัดวาง
        """
        rules = ShapeRuleLookup.get_rules(shape_type, text)
        tokens = self.tokenizer.tokenize(text)
        result = self.layout_text(text, shape_type)
        
        # คำนวณความกว้างของแต่ละบรรทัด
        lines = result.split("\n") if result else []
        line_widths = [self._get_text_width(line) for line in lines]
        
        # คำนวณค่าเฉลี่ยและค่าเบี่ยงเบนมาตรฐาน
        avg_width = sum(line_widths) / len(line_widths) if line_widths else 0
        variance = sum((w - avg_width) ** 2 for w in line_widths) / len(line_widths) if line_widths else 0
        std_dev = variance ** 0.5
        
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
            "std_dev": std_dev,
            "font_available": self.font_metrics is not None if self.font_metrics else False
        }
