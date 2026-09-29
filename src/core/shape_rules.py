"""
Shape Rules Lookup Module
โมดูลสำหรับจัดการกฎของรูปทรงบอลลูนต่างๆ
ใช้ความกว้างจริงของข้อความต้นแบบจาก config เป็นเกณฑ์ (วัดด้วยฟอนต์)
"""

from typing import Dict, Any, Optional
from src.utils.config import get_config


class ShapeRuleLookup:
    """
    คลาสสำหรับจัดการกฎของรูปทรงบอลลูน
    รองรับ 2 รูปทรง: square_like, tall_rect
    
    ระบบใช้ความกว้างจริงของข้อความต้นแบบ (prototype) จาก config
    โดยวัดด้วยฟอนต์ เป็นเกณฑ์ในการจัดวางข้อความ
    """
    
    # รายชื่อรูปทรงที่รองรับ
    SUPPORTED_SHAPES = ["square_like", "tall_rect"]
    
    # ค่าเริ่มต้นสำหรับแต่ละรูปทรง (ใช้เมื่อไม่มี prototype - หน่วย pixels)
    DEFAULT_MAX_WIDTH: Dict[str, float] = {
        "square_like": 180.0,
        "tall_rect": 100.0,
    }
    
    _font_metrics = None  # Cache FontMetrics instance
    
    @classmethod
    def _get_font_metrics(cls):
        """ดึง FontMetrics instance (cache)"""
        if cls._font_metrics is None:
            try:
                from src.utils.font_metrics import create_font_metrics_from_config
                cls._font_metrics = create_font_metrics_from_config()
            except Exception:
                cls._font_metrics = None
        return cls._font_metrics
    
    @classmethod
    def get_rules(cls, shape_type: str, text: Optional[str] = None) -> Dict[str, Any]:
        """
        ดึงกฎของรูปทรงที่ระบุ พร้อมปรับความกว้างอัตโนมัติตามข้อความ
        
        ระบบใช้ความกว้างจริงของข้อความต้นแบบ (prototype) จาก config
        โดยวัดด้วยฟอนต์ เป็นเกณฑ์พื้นฐาน แล้วปรับตามความยาวของข้อความจริง
        
        Args:
            shape_type: ชนิดของรูปทรง (square_like, tall_rect)
            text: ข้อความที่จะจัดวาง (ถ้ามี จะปรับความกว้างอัตโนมัติ)
            
        Returns:
            Dict ที่มี max_width (pixels) สำหรับรูปทรงนั้น
            
        Raises:
            ValueError: ถ้าไม่พบรูปทรงที่ระบุ
        """
        if shape_type not in cls.SUPPORTED_SHAPES:
            valid_shapes = ", ".join(cls.SUPPORTED_SHAPES)
            raise ValueError(
                f"ไม่รู้จักรูปทรง '{shape_type}'. "
                f"รูปทรงที่รองรับ: {valid_shapes}"
            )
        
        # เริ่มจากค่าเริ่มต้น
        base_width = cls.DEFAULT_MAX_WIDTH.get(shape_type, 180.0)
        prototype_text = None
        
        # พยายามโหลดจาก config (prototype) และวัดความกว้างด้วยฟอนต์
        try:
            cfg = get_config()
            shapes_cfg = cfg.get("shapes", {}) or {}
            
            # ถ้าเปิดใช้งาน dynamic_from_prototype
            if shapes_cfg.get("dynamic_from_prototype"):
                prototypes = shapes_cfg.get("prototypes") or {}
                proto = prototypes.get(shape_type) or ""
                
                if isinstance(proto, str) and proto.strip():
                    prototype_text = proto.strip()
                    # วัดความกว้างจริงด้วยฟอนต์
                    font_metrics = cls._get_font_metrics()
                    if font_metrics:
                        base_width = font_metrics.get_text_width(prototype_text)
                    else:
                        # Fallback: ประมาณจากจำนวนตัวอักษร
                        base_width = len(prototype_text) * 10.0
        except Exception:
            # ถ้าอ่าน config ไม่ได้ ใช้ค่าเริ่มต้น
            pass
        
        # ปรับความกว้างอัตโนมัติตามข้อความ (Adaptive Width)
        max_width = base_width
        if text and prototype_text:
            try:
                cfg = get_config()
                shapes_cfg = cfg.get("shapes", {}) or {}
                adaptive_cfg = shapes_cfg.get("adaptive_width", {}) or {}
                
                # ตรวจสอบว่าเปิดใช้งาน adaptive width หรือไม่
                if not adaptive_cfg.get("enabled", True):
                    return {
                        "max_width": max_width,
                        "base_width": base_width,
                        "shape_type": shape_type
                    }
                
                # โหลดค่า config
                min_scale = adaptive_cfg.get("min_scale", 1.0)
                max_scale = adaptive_cfg.get("max_scale", 1.5)
                
                # Thresholds (เกณฑ์แบ่งประเภท)
                short_threshold = adaptive_cfg.get("short_text_threshold", 1.0)
                normal_threshold = adaptive_cfg.get("normal_text_threshold", 2.0)
                medium_threshold = adaptive_cfg.get("medium_text_threshold", 3.0)
                long_threshold = adaptive_cfg.get("long_text_threshold", 4.0)
                very_long_s_threshold = adaptive_cfg.get("very_long_s_threshold", 5.0)
                very_long_m_threshold = adaptive_cfg.get("very_long_m_threshold", 6.0)
                very_long_l_threshold = adaptive_cfg.get("very_long_l_threshold", 7.0)
                
                # Scales (ตัวคูณความกว้าง)
                short_scale = adaptive_cfg.get("short_text_scale", 1.0)
                normal_scale = adaptive_cfg.get("normal_text_scale", 1.0)
                medium_scale = adaptive_cfg.get("medium_text_scale", 1.25)
                long_scale = adaptive_cfg.get("long_text_scale", 1.5)
                very_long_s_scale = adaptive_cfg.get("very_long_s_scale", 1.6)
                very_long_m_scale = adaptive_cfg.get("very_long_m_scale", 1.7)
                very_long_l_scale = adaptive_cfg.get("very_long_l_scale", 1.8)
                extreme_scale = adaptive_cfg.get("extreme_text_scale", 1.8)
                
                font_metrics = cls._get_font_metrics()
                if font_metrics:
                    # แก้ไข: ไม่นับรวมความกว้างของเครื่องหมาย | ในการคำนวณ Adaptive Width
                    clean_text = text.replace('|', '')
                    text_width = font_metrics.get_text_width(clean_text)
                    proto_width = font_metrics.get_text_width(prototype_text)
                    
                    # คำนวณอัตราส่วน
                    ratio = text_width / proto_width if proto_width > 0 else 1.0
                    
                    # ปรับความกว้างตามอัตราส่วน (ตรวจสอบจากน้อยไปมาก)
                    if ratio < short_threshold:
                        # ข้อความสั้น (< 100%)
                        scale = max(min_scale, short_scale)
                        max_width = base_width * scale
                    elif ratio < normal_threshold:
                        # ข้อความปกติ (100-200%)
                        scale = max(min_scale, normal_scale)
                        max_width = base_width * scale
                    elif ratio < medium_threshold:
                        # ข้อความยาวปานกลาง (201-300%)
                        scale = min(max_scale, medium_scale)
                        max_width = base_width * scale
                    elif ratio < long_threshold:
                        # ข้อความยาวมาก (301-400%)
                        scale = min(max_scale, long_scale)
                        max_width = base_width * scale
                    elif ratio < very_long_s_threshold:
                        # ข้อความยาวมาก s (401-500%)
                        scale = min(max_scale, very_long_s_scale)
                        max_width = base_width * scale
                    elif ratio < very_long_m_threshold:
                        # ข้อความยาวมาก m (501-600%)
                        scale = min(max_scale, very_long_m_scale)
                        max_width = base_width * scale
                    elif ratio < very_long_l_threshold:
                        # ข้อความยาวมาก l (601-700%)
                        scale = min(max_scale, very_long_l_scale)
                        max_width = base_width * scale
                    else:
                        # ข้อความยาวเกิน (> 700%)
                        scale = min(max_scale, extreme_scale)
                        max_width = base_width * scale
            except Exception:
                # ถ้าอ่าน config ไม่ได้ ใช้ค่าเดิม
                pass
        
        return {
            "max_width": max_width,
            "base_width": base_width,
            "shape_type": shape_type
        }
    
    @classmethod
    def get_max_width(cls, shape_type: str) -> float:
        """
        ดึงความกว้างสูงสุดของรูปทรง (pixels)
        (จากความกว้างจริงของข้อความต้นแบบ วัดด้วยฟอนต์)
        """
        return cls.get_rules(shape_type)["max_width"]
    
    @classmethod
    def validate_shape_type(cls, shape_type: str) -> bool:
        """
        ตรวจสอบว่ารูปทรงที่ระบุถูกต้องหรือไม่
        
        Args:
            shape_type: ชนิดของรูปทรง
            
        Returns:
            True ถ้ารูปทรงถูกต้อง, False ถ้าไม่ถูกต้อง
        """
        return shape_type in cls.SUPPORTED_SHAPES
    
    @classmethod
    def get_all_shapes(cls) -> list[str]:
        """ดึงรายชื่อรูปทรงทั้งหมดที่รองรับ"""
        return cls.SUPPORTED_SHAPES.copy()
