"""
Thai Tokenizer Module
โมดูลสำหรับแบ่งคำภาษาไทย (pipe mode เท่านั้น)
ผู้ใช้แบ่งคำเองด้วยเครื่องหมาย |
"""

from typing import List, Optional, Set
import re

from src.utils.config import get_config
from src.lexicon.non_breaking_store_json import JSONNonBreakingStore


class ThaiTokenizer:
    """
    คลาสสำหรับแบ่งคำภาษาไทย (pipe mode)
    ผู้ใช้แบ่งคำเองด้วยเครื่องหมาย | เช่น "ต้อง|ไป|รับ|การรักษา"
    """

    def __init__(
        self,
        non_breaking_enabled: Optional[bool] = None,
        non_breaking_words_path: Optional[str] = None,
    ):
        """
        สร้าง tokenizer

        Args:
            non_breaking_enabled: เปิดใช้คำห้ามแบ่งหรือไม่
            non_breaking_words_path: path ไปยังไฟล์ non_breaking_words.json
        """
        # Load config defaults if not provided
        cfg = get_config()
        if non_breaking_enabled is None:
            non_breaking_enabled = bool(cfg.get("tokenizer.non_breaking_enabled", True))
        if non_breaking_words_path is None:
            non_breaking_words_path = cfg.get(
                "tokenizer.non_breaking_words_path",
                "data/lexicons/non_breaking_words.json",
            )

        self._non_breaking_enabled = non_breaking_enabled
        self._non_breaking_path = non_breaking_words_path
        self._non_breaking_words: Set[str] = set()
        self._prefixes: Set[str] = set()

        self._initialize_non_breaking()

    def _initialize_non_breaking(self):
        """โหลดคำห้ามแบ่งและเตรียมโครงสร้างค้นหา"""
        if not self._non_breaking_enabled:
            return

        try:
            import os
            path = self._non_breaking_path
            if not os.path.isabs(path):
                from pathlib import Path
                project_root = Path(__file__).resolve().parents[2]
                path = str(project_root / path)

            store = JSONNonBreakingStore(path)
            self._non_breaking_words = store.get_all()

            # สร้าง prefix set สำหรับ early termination
            for w in self._non_breaking_words:
                for i in range(1, len(w) + 1):
                    self._prefixes.add(w[:i])
        except Exception:
            self._non_breaking_words = set()
            self._prefixes = set()

    def tokenize(self, text: str) -> List[str]:
        """
        แบ่งคำจากข้อความด้วยเครื่องหมาย | (pipe)

        Args:
            text: ข้อความที่ต้องการแบ่ง (ใช้ | คั่นระหว่างคำ)

        Returns:
            List ของคำที่แบ่งแล้ว
        """
        if not text or not text.strip():
            return []

        # แยกตาม | แล้วกรองช่องว่างว่างออก
        tokens = [t for t in text.split("|") if t]

        # รวม token ตามรายการคำห้ามแบ่ง
        if self._non_breaking_enabled and self._non_breaking_words:
            tokens = self._merge_non_breaking(tokens)

        return tokens

    def reload_non_breaking_words(self, path: Optional[str] = None):
        """
        โหลดคำห้ามแบ่งใหม่จากไฟล์
        ใช้เมื่อมีการแก้ไขไฟล์ non_breaking_words.json ระหว่างการทำงาน

        Args:
            path: path ของไฟล์ (ถ้าไม่ระบุจะใช้ path เดิม)
        """
        if path:
            self._non_breaking_path = path

        # รีเซ็ตข้อมูลเก่า
        self._non_breaking_words = set()
        self._prefixes = set()

        # โหลดใหม่
        self._initialize_non_breaking()

    def _merge_non_breaking(self, tokens: List[str]) -> List[str]:
        """
        รวมชุด token ที่ประกอบกันเป็นคำห้ามแบ่งให้กลายเป็น 1 token
        ใช้กลยุทธ์ longest-match จากซ้ายไปขวา
        รองรับการแยกเครื่องหมายวรรคตอนที่ติดท้ายคำ
        """
        if not self._non_breaking_words or not tokens:
            return tokens

        # Regex สำหรับแยกเครื่องหมายวรรคตอนที่ติดท้ายคำ
        trailing_punct = re.compile(r'^(.+?)([!?。！？、，,.\s]+)$')

        result: List[str] = []
        i = 0
        while i < len(tokens):
            best_end = i  # ดัชนีสุดท้ายของ match ที่ยาวที่สุด (exclusive)
            concat = ""

            # ลอง concat token ตั้งแต่ i ไปเรื่อยๆ
            for j in range(i, len(tokens)):
                concat += tokens[j]

                # ตรวจสอบว่ายังเป็น prefix ที่เป็นไปได้หรือไม่
                if concat not in self._prefixes:
                    # ลองแยกเครื่องหมายวรรคตอนที่ติดท้าย
                    m = trailing_punct.match(concat)
                    if m:
                        core = m.group(1)
                        if core in self._non_breaking_words:
                            best_end = j + 1
                    break

                # ถ้า concat ตรงกับคำห้ามแบ่งพอดี ให้จำไว้
                if concat in self._non_breaking_words:
                    best_end = j + 1

            if best_end > i:
                # รวม token ตั้งแต่ i ถึง best_end-1 เป็น token เดียว
                merged = "".join(tokens[i:best_end])
                result.append(merged)
                i = best_end
            else:
                result.append(tokens[i])
                i += 1

        return result
