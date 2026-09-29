# การตั้งค่า Adaptive Width

Adaptive Width เป็นระบบที่ปรับความกว้างของบอลลูนอัตโนมัติตามความยาวของข้อความ โดยแบ่งเป็น 7 ช่วงตามอัตราส่วนเทียบกับข้อความต้นแบบ (prototype)

## การตั้งค่าใน config/default_config.json

```json
{
  "shapes": {
    "adaptive_width": {
      "enabled": true,
      "short_text_threshold": 1.0,
      "short_text_scale": 1.0,
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
      "max_scale": 1.8
    }
  }
}
```

## คำอธิบายพารามิเตอร์

### enabled
- **ค่าเริ่มต้น**: `true`
- **คำอธิบาย**: เปิด/ปิดการใช้งาน Adaptive Width
- **ตัวอย่าง**: `false` = ใช้ความกว้างจาก prototype เท่านั้น

### min_scale และ max_scale
- **ค่าเริ่มต้น**: `1.0` และ `1.8`
- **คำอธิบาย**: ขีดจำกัดการขยาย/ลดความกว้าง
- **ตัวอย่าง**: 
  - `min_scale: 1.0` = ลดได้ต่ำสุด 100% ของ prototype (ไม่ลด)
  - `max_scale: 1.8` = ขยายได้สูงสุด 180% ของ prototype

## ช่วงการทำงานของ Adaptive Width

ระบบแบ่งข้อความออกเป็น 7 ช่วงตามอัตราส่วนเทียบกับความกว้างของข้อความต้นแบบ (prototype):

### 1. ข้อความสั้น (< 100% ของ prototype)
- **Threshold**: `short_text_threshold: 1.0`
- **Scale**: `short_text_scale: 1.0` (100%)
- **คำอธิบาย**: ข้อความสั้นกว่า prototype ใช้ความกว้างตาม prototype
- **ตัวอย่าง**: ถ้า prototype = 100px, ข้อความ 80px → ใช้ความกว้าง 100px (100%)

### 2. ข้อความปกติ (100-200% ของ prototype)
- **Threshold**: `normal_text_threshold: 2.0`
- **Scale**: `normal_text_scale: 1.0` (100%)
- **คำอธิบาย**: ข้อความยาว 1-2 เท่าของ prototype ใช้ความกว้างตาม prototype
- **ตัวอย่าง**: ถ้า prototype = 100px, ข้อความ 150px → ใช้ความกว้าง 100px (100%)

### 3. ข้อความยาวปานกลาง (201-300% ของ prototype)
- **Threshold**: `medium_text_threshold: 3.0`
- **Scale**: `medium_text_scale: 1.25` (125%)
- **คำอธิบาย**: ข้อความยาว 2-3 เท่าของ prototype ขยายความกว้าง 125%
- **ตัวอย่าง**: ถ้า prototype = 100px, ข้อความ 250px → ใช้ความกว้าง 125px (125%)

### 4. ข้อความยาวมาก (301-400% ของ prototype)
- **Threshold**: `long_text_threshold: 4.0`
- **Scale**: `long_text_scale: 1.5` (150%)
- **คำอธิบาย**: ข้อความยาว 3-4 เท่าของ prototype ขยายความกว้าง 150%
- **ตัวอย่าง**: ถ้า prototype = 100px, ข้อความ 350px → ใช้ความกว้าง 150px (150%)

### 5. ข้อความยาวมาก s (401-500% ของ prototype)
- **Threshold**: `very_long_s_threshold: 5.0`
- **Scale**: `very_long_s_scale: 1.6` (160%)
- **คำอธิบาย**: ข้อความยาว 4-5 เท่าของ prototype ขยายความกว้าง 160%
- **ตัวอย่าง**: ถ้า prototype = 100px, ข้อความ 450px → ใช้ความกว้าง 160px (160%)

### 6. ข้อความยาวมาก m (501-600% ของ prototype)
- **Threshold**: `very_long_m_threshold: 6.0`
- **Scale**: `very_long_m_scale: 1.7` (170%)
- **คำอธิบาย**: ข้อความยาว 5-6 เท่าของ prototype ขยายความกว้าง 170%
- **ตัวอย่าง**: ถ้า prototype = 100px, ข้อความ 550px → ใช้ความกว้าง 170px (170%)

### 7. ข้อความยาวมาก l (601-700% ของ prototype)
- **Threshold**: `very_long_l_threshold: 7.0`
- **Scale**: `very_long_l_scale: 1.8` (180%)
- **คำอธิบาย**: ข้อความยาว 6-7 เท่าของ prototype ขยายความกว้าง 180%
- **ตัวอย่าง**: ถ้า prototype = 100px, ข้อความ 650px → ใช้ความกว้าง 180px (180%)

### 8. ข้อความยาวเกิน (> 700% ของ prototype)
- **Scale**: `extreme_text_scale: 1.8` (180%)
- **คำอธิบาย**: ข้อความยาวเกิน 7 เท่าของ prototype ขยายความกว้างสูงสุด 180%
- **ตัวอย่าง**: ถ้า prototype = 100px, ข้อความ 800px → ใช้ความกว้าง 180px (180%)

## ตัวอย่างการปรับแต่ง

### ต้องการให้ขยายความกว้างมากขึ้นสำหรับข้อความยาวมาก

```json
{
  "adaptive_width": {
    "max_scale": 2.0,
    "very_long_l_scale": 2.0,
    "extreme_text_scale": 2.0
  }
}
```

### ต้องการให้ขยายเร็วขึ้น (ขยายตั้งแต่ข้อความปกติ)

```json
{
  "adaptive_width": {
    "normal_text_scale": 1.1,
    "medium_text_scale": 1.3,
    "long_text_scale": 1.6
  }
}
```

### ต้องการให้ระบบอนุโลมน้อยลง (ใกล้เคียง prototype มากขึ้น)

```json
{
  "adaptive_width": {
    "max_scale": 1.4,
    "medium_text_scale": 1.15,
    "long_text_scale": 1.3,
    "very_long_s_scale": 1.35,
    "very_long_m_scale": 1.4,
    "very_long_l_scale": 1.4
  }
}
```

### ปิดการใช้งาน Adaptive Width

```json
{
  "adaptive_width": {
    "enabled": false
  }
}
```

## การทดสอบและปรับแต่ง

1. เริ่มจากค่าเริ่มต้น
2. ทดสอบกับข้อความหลายแบบ (สั้น, ปานกลาง, ยาว, ยาวมาก)
3. ปรับค่า `max_scale` ถ้าต้องการให้ขยายได้มากขึ้น
4. ปรับค่า scale ของแต่ละช่วงเพื่อควบคุมการขยายในแต่ละระดับ
5. ปรับค่า threshold ถ้าต้องการเปลี่ยนเกณฑ์การแบ่งประเภทข้อความ

## เคล็ดลับ

- **ข้อความยาวแบ่งหลายบรรทัดเกินไป**: เพิ่ม `max_scale` หรือ scale ของช่วงที่ยาว
- **ข้อความสั้นกว้างเกินไป**: ลด `short_text_scale` (แต่ไม่ควรต่ำกว่า 1.0)
- **ต้องการความแม่นยำสูง**: ลด scale ของทุกช่วงให้ใกล้เคียง 1.0 มากขึ้น
- **ต้องการความยืดหยุ่นสูง**: เพิ่ม `max_scale` และ scale ของช่วงที่ยาว
- **ต้องการปรับช่วงการทำงาน**: เปลี่ยนค่า threshold เช่น ถ้าต้องการให้ขยายเร็วขึ้น ลดค่า threshold
