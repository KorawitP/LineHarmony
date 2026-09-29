"""
Font Metrics Module
โมดูลสำหรับวัดความกว้างของข้อความด้วยฟอนต์
"""

from typing import Optional
from pathlib import Path
import os


class FontMetrics:
    """
    คลาสสำหรับวัดความกว้างของข้อความด้วยฟอนต์
    ใช้ PIL (Pillow) สำหรับการวัดความกว้างที่แม่นยำ
    """
    
    def __init__(self, font_path: str, font_size: int = 16):
        """
        สร้าง FontMetrics
        
        Args:
            font_path: path ไปยังไฟล์ฟอนต์ (.ttf)
            font_size: ขนาดฟอนต์ (default: 16)
        """
        self.font_path = font_path
        self.font_size = font_size
        self._font = None
        self._pil_available = False
        
        self._initialize_font()
    
    def _initialize_font(self):
        """เริ่มต้นฟอนต์ด้วย PIL"""
        try:
            from PIL import ImageFont
            
            if not os.path.exists(self.font_path):
                raise FileNotFoundError(f"ไม่พบไฟล์ฟอนต์: {self.font_path}")
            
            self._font = ImageFont.truetype(self.font_path, self.font_size)
            self._pil_available = True
        except ImportError:
            print("⚠️ ไม่พบ Pillow กรุณาติดตั้ง: pip install Pillow")
            self._pil_available = False
        except Exception as e:
            print(f"⚠️ ไม่สามารถโหลดฟอนต์ได้: {e}")
            self._pil_available = False
    
    def get_text_width(self, text: str) -> float:
        """
        วัดความกว้างของข้อความ
        
        Args:
            text: ข้อความที่ต้องการวัด
            
        Returns:
            ความกว้างของข้อความ (หน่วย: pixels)
        """
        if not text:
            return 0.0
        
        if not self._pil_available or self._font is None:
            # Fallback: ประมาณความกว้างจากจำนวนตัวอักษร
            # ภาษาไทยประมาณ 0.6 ของขนาดฟอนต์ต่อตัว
            return len(text) * self.font_size * 0.6
        
        try:
            # ใช้ PIL วัดความกว้างจริง
            bbox = self._font.getbbox(text)
            width = bbox[2] - bbox[0]
            return float(width)
        except Exception:
            # Fallback ถ้าวัดไม่ได้
            return len(text) * self.font_size * 0.6
    
    def get_max_chars_for_width(self, target_width: float, sample_text: str = "ก") -> int:
        """
        คำนวณจำนวนตัวอักษรโดยประมาณที่พอดีกับความกว้างที่กำหนด
        (ใช้สำหรับ backward compatibility)
        
        Args:
            target_width: ความกว้างเป้าหมาย (pixels)
            sample_text: ตัวอักษรตัวอย่างสำหรับประมาณ (default: "ก")
            
        Returns:
            จำนวนตัวอักษรโดยประมาณ
        """
        if target_width <= 0:
            return 0
        
        char_width = self.get_text_width(sample_text)
        if char_width <= 0:
            return int(target_width / (self.font_size * 0.6))
        
        return int(target_width / char_width)
    
    def is_available(self) -> bool:
        """ตรวจสอบว่า PIL พร้อมใช้งานหรือไม่"""
        return self._pil_available


def create_font_metrics_from_config() -> Optional[FontMetrics]:
    """
    สร้าง FontMetrics จาก config
    
    Returns:
        FontMetrics instance หรือ None ถ้าสร้างไม่ได้
    """
    try:
        from src.utils.config import get_config
        
        cfg = get_config()
        font_cfg = cfg.get("font", {}) or {}
        
        font_path = font_cfg.get("path", "THSarabunNew.ttf")
        font_size = font_cfg.get("size", 16)
        
        # ถ้า path เป็น relative ให้แปลงเป็น absolute จาก project root
        if not os.path.isabs(font_path):
            # หา project root (ที่มี config/)
            current = Path(__file__).resolve()
            project_root = current.parent.parent.parent
            font_path = str(project_root / font_path)
        
        return FontMetrics(font_path, font_size)
    except Exception as e:
        print(f"⚠️ ไม่สามารถสร้าง FontMetrics จาก config: {e}")
        return None
