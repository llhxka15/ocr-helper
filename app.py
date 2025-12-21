import streamlit as st
from PIL import Image
import pytesseract
import numpy as np
import cv2  # 引入强大的计算机视觉库

# --- 配置区域 ---
SLICE_HEIGHT = 4000  
OVERLAP = 200 
# ----------------

st.set_page_config(page_title="微信聊天记录提取专用版", page_icon="💬")
st.title("💬 微信聊天记录提取专用版")
st.caption("自动切片 + 图像增强 | 专治微信截图识别不准")

with st.sidebar:
    st.write("### 🛠️ 增强原理")
    st.info("针对微信截图做了特殊优化：\n1. **自动放大**：解决文字模糊问题。\n2. **二值化处理**：自动滤除绿色/白色气泡背景，只保留黑色文字，极大提高准确率。")

# 图像预处理函数
def process_image_for_ocr(pil_image):
    # 1. 转换为 OpenCV 格式
    img_array = np.array(pil_image)
    
    # 转换为灰度图
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array

    # 2. 图像放大 (Upscaling) - 关键步骤！
    # 放大 2 倍，让文字细节更清晰
    scale_factor = 2
    height, width = gray.shape[:2]
    gray = cv2.resize(gray, (width * scale_factor, height * scale_factor), interpolation=cv2.INTER_CUBIC)

    # 3. 二值化 (Thresholding) - 核心步骤！
    # 使用 OTSU 算法自动寻找最佳阈值，将文字变为纯黑，背景变为纯白
    # 这步操作会把 绿色气泡、白色气泡、灰色背景 通通变成白色背景，只留下字。
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # 4. 降噪 (可选)
    # 如果噪点多，可以开启下面这行
    # binary = cv2.medianBlur(binary, 3)

    return Image.fromarray(binary)

uploaded_file = st.file_uploader("请上传微信长截图", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    width, height = image.size
    
    # 估算切片数量
    num_slices = 1
    if height > SLICE_HEIGHT:
        num_slices = int(np.ceil((height - SLICE_HEIGHT) / (SLICE_HEIGHT - OVERLAP))) + 1
    
    st.image(image, caption='原始图片', use_column_width=True)

    if st.button('🚀 开始增强识别', type="primary"):
        full_text = ""
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            top = 0
            count = 0
            while top < height:
                count += 1
                status_text.write(f"🔄 正在处理片段 {count}/{num_slices}：图像增强 -> OCR识别...")
                
                # 1. 裁剪
                bottom = min(top + SLICE_HEIGHT, height)
                slice_img = image.crop((0, top, width, bottom))
                
                # 2. 图像增强 (调用上面的函数)
                # 这一步把图片变成了适合机器阅读的“黑白扫描件”风格
                enhanced_slice = process_image_for_ocr(slice_img)
                
                # (调试用) 如果你想看看增强后长什么样，可以取消下面这行的注释
                # st.image(enhanced_slice, caption=f"片段 {count} 增强预览")

                # 3. 识别
                # --psm 6 假设是一个统一的文本块，对这种切片效果通常更好
                text = pytesseract.image_to_string(enhanced_slice, lang='chi_sim+eng', config='--psm 6')
                
                # 简单的后处理：过滤掉过短的乱码
                lines = text.split('\n')
                clean_lines = [line for line in lines if len(line.strip()) > 1] # 过滤掉只有一个字符的行（通常是噪点）
                full_text += "\n".join(clean_lines) + "\n"
                
                current_progress = min(count / num_slices, 1.0)
                progress_bar.progress(current_progress)

                if bottom == height:
                    break
                top = bottom - OVERLAP
            
            progress_bar.progress(100)
            status_text.success("✅ 提取完成！")
            
            if not full_text.strip():
                st.warning("未能识别出文字，请检查图片是否清晰。")
            else:
                st.text_area("识别结果", full_text, height=600)
                st.caption("提示：你可以直接复制上面的文字。如果有些表情符号被识别成了乱码，手动删除即可。")

        except Exception as e:
            st.error(f"发生错误: {e}")
