# LineHarmony

> **English summary** — Thai text layout engine for comic speech balloons: balanced
> word-wrap driven by real font metrics, with Thai-specific rules (protected words never
> split, connectors never end a line, polite particles kept with the previous line).
> Built on PyThaiNLP; ~0.7 ms per layout; covered by a pytest suite.

---


ระบบจัดวางข้อความภาษาไทยสำหรับบอลลูนการ์ตูน โดยคำนึงถึงรูปทรงและความสมดุลของข้อความ

## คุณสมบัติ

- **จัดวางข้อความตามรูปทรง** รองรับ 2 รูปทรง:
  - `square_like` - สี่เหลี่ยมจัตุรัส (บอลลูนทั่วไป)
  - `tall_rect` - สี่เหลี่ยมผืนผ้าสูง (บอลลูนแคบยาว)

- **ใช้ข้อความต้นแบบเป็นเกณฑ์** ความกว้างของแต่ละรูปทรงคำนวณจากความยาวของข้อความต้นแบบใน config ไม่จำกัดจำนวนคำหรือบรรทัด

- **ตัดคำภาษาไทยอัจฉริยะ** ใช้ PyThaiNLP สำหรับการตัดคำที่แม่นยำ

- **กฎห้ามแบ่งคำ** รองรับคำที่ไม่ควรแบ่ง เช่น ชื่อเฉพาะ คำศัพท์เฉพาะทาง

- **กฎห้ามจบบรรทัด** ไม่ให้จบบรรทัดด้วยคำเชื่อม เช่น "และ", "หรือ", "เพราะ"

- **จัดการคำสุภาพ** รวมคำสุภาพท้ายบรรทัด (ครับ, ค่ะ, คะ) เข้ากับบรรทัดก่อนหน้าหากเป็นไปได้

## การติดตั้ง

```bash
# ติดตั้ง dependencies
pip install -r requirements.txt
```

## การใช้งาน

### CLI Demo

```bash
python examples/cli_layout_demo.py
```

### GUI Demo

```bash
python examples/gui_layout_demo.py
```

### ใช้งานในโค้ด

```python
from src.core.layout_engine_v2 import LayoutEngine

# สร้าง engine
engine = LayoutEngine()

# จัดวางข้อความ
text = "ต้องไปรับการรักษาในที่"
result = engine.layout_text(text, "square_like")
print(result)
# Output:
# ต้องไปรับการรักษาในที่

# ดูข้อมูลละเอียด
info = engine.get_layout_info(text, "square_like")
print(f"จำนวนบรรทัด: {info['num_lines']}")
print(f"จำนวนคำ: {info['num_tokens']}")
```

## การตั้งค่า

### config/default_config.json

```json
{
  "version": "0.1.0",
  "font": {
    "path": "THSarabunNew.ttf",
    "size": 16
  },
  "tokenizer": {
    "non_breaking_enabled": true,
    "non_breaking_words_path": "data/lexicons/non_breaking_words.json"
  },
  "layout": {
    "use_line_end_rules": true,
    "line_end_rules_path": "data/lexicons/line_end_rules.json"
  },
  "shapes": {
    "dynamic_from_prototype": true,
    "prototypes": {
      "square_like": "ต้องไปรับการรักษาในที่",
      "tall_rect": "ต้องไปรับการ"
    }
  }
}
```

### data/lexicons/line_end_rules.json

```json
{
  "disallow_line_end": [
    "และ",
    "หรือ",
    "เพราะ"
  ],
  "polite_words": [
    "ครับ",
    "ค่ะ",
    "คะ"
  ]
}
```

### data/lexicons/non_breaking_words.json

```json
{
  "non_breaking_words": [
    "คิลลาเรน",
    "จองซอลฮวา",
    "ศัลยกรรมหัวใจ",
    "ทรวงอกครับ",
    "ห้องผู้ป่วย"
  ]
}
```

## โครงสร้างโปรเจกต์

```
LineHarmony/
├── config/
│   └── default_config.json       # การตั้งค่าหลัก
├── data/
│   ├── fonts/                    # ฟอนต์สำหรับคำนวณความกว้าง
│   └── lexicons/                 # พจนานุกรมและกฎต่างๆ
│       ├── line_end_rules.json   # กฎห้ามจบบรรทัด
│       └── non_breaking_words.json # คำห้ามแบ่ง
├── examples/
│   ├── cli_layout_demo.py        # ตัวอย่าง CLI
│   └── gui_layout_demo.py        # ตัวอย่าง GUI
├── src/
│   ├── core/
│   │   ├── layout_engine_v2.py   # Layout Engine หลัก
│   │   └── shape_rules.py        # กฎของรูปทรง
│   ├── lexicon/
│   │   └── non_breaking_store_json.py # จัดการคำห้ามแบ่ง
│   ├── tokenizer/
│   │   └── thai_tokenizer.py     # ตัดคำภาษาไทย
│   └── utils/
│       └── config.py              # จัดการ config
└── requirements.txt               # Dependencies

```

## อัลกอริทึม

ระบบใช้โหมด **Balanced Word-Wrap with Font Metrics** โดย:

1. **วัดความกว้างจริง** ใช้ฟอนต์ THSarabunNew.ttf วัดความกว้างของข้อความต้นแบบจาก config
2. **ตัดคำ** ใช้ PyThaiNLP ตัดคำภาษาไทย
3. **รวมคำห้ามแบ่ง** รวมคำที่อยู่ในรายการคำห้ามแบ่ง
4. **Greedy Packing** ใส่คำลงบรรทัดจนเต็มตามความกว้างจริง (pixels)
5. **Balance Optimization** ปรับสมดุลความกว้างของแต่ละบรรทัดให้ใกล้เคียงกัน
6. **ปรับกฎปลายบรรทัด** ย้ายคำที่ไม่ควรจบบรรทัดไปบรรทัดถัดไป
7. **รวมคำสุภาพ** รวมคำสุภาพท้ายบรรทัดเข้ากับบรรทัดก่อนหน้า

### ทำไมต้องใช้ความกว้างจริง?

ตัวอักษรแต่ละตัวมีความกว้างไม่เท่ากัน:
- "iii" (3 ตัว) = 6 px (2 px/ตัว) - ตัวอักษรแคบ
- "WWW" (3 ตัว) = 28 px (9.33 px/ตัว) - ตัวอักษรกว้าง
- "ต้องไปรับการรักษาในที่" (22 ตัว) = 97 px (4.41 px/ตัว)

การนับจำนวนตัวอักษรจึงไม่แม่นยำ ต้องวัดความกว้างจริงด้วยฟอนต์

## การพัฒนา

```bash
# รัน tests
pytest tests/

# ตรวจสอบ code style
flake8 src/

# Format code
black src/
```

## License

MIT License

## ผู้พัฒนา

LineHarmony - ระบบจัดวางข้อความภาษาไทยสำหรับบอลลูนการ์ตูน
