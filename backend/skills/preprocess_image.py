"""
Skill: preprocess_image — 图片预处理（旋转、去倾斜、增强、去噪）
"""

from pathlib import Path

from ..config import PREPROCESSED_DIR


def preprocess_image(image_path: str) -> dict:
    path = Path(image_path)
    if not path.exists():
        return {"status": "error", "error": "图片不存在"}

    try:
        from PIL import Image, ImageEnhance, ImageFilter
    except ImportError:
        return {"status": "error", "error": "Pillow 未安装"}

    try:
        img = Image.open(str(path))
    except Exception as e:
        return {"status": "error", "error": f"图片打开失败: {e}"}

    operations = []

    # EXIF 自动旋转
    try:
        from PIL.ExifTags import Base as ExifBase
        exif = img.getexif()
        orientation = exif.get(0x0112)  # Orientation tag
        if orientation:
            rotations = {3: 180, 6: 270, 8: 90}
            if orientation in rotations:
                img = img.rotate(rotations[orientation], expand=True)
                operations.append("auto_rotate")
    except Exception:
        pass

    # 转灰度（增强 OCR 效果）
    if img.mode != "L":
        gray = img.convert("L")
    else:
        gray = img

    # 对比度增强
    enhancer = ImageEnhance.Contrast(gray.convert("RGB"))
    img_enhanced = enhancer.enhance(1.5)
    operations.append("contrast_enhance")

    # 锐化
    img_enhanced = img_enhanced.filter(ImageFilter.SHARPEN)
    operations.append("sharpen")

    # 轻度去噪
    img_enhanced = img_enhanced.filter(ImageFilter.MedianFilter(size=3))
    operations.append("denoise")

    # 保存
    out_dir = PREPROCESSED_DIR / Path(image_path).stem
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{path.stem}_clean.png"
    img_enhanced.save(str(out_path))

    return {
        "status": "success",
        "preprocessed_image_path": str(out_path),
        "operations": operations,
    }
