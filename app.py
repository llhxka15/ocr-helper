import streamlit as st
from PIL import Image
import numpy as np
import io
import zipfile

# --- 关键修正 1：解除像素限制 ---
# 允许处理无限大的图片（防止 DecompressionBombError）
Image.MAX_IMAGE_PIXELS = None 

st.set_page_config(page_title="微信长图智能切片机", page_icon="🧠")
st.title("🧠 微信长图智能切片机")
st.caption("智能识别气泡间隙 | 修复超长图无法上传问题")

with st.sidebar:
    st.header("⚙️ 切割参数")
    max_height = st.slider("单张切片最大高度 (px)", 1000, 5000, 2500, 100)

def find_safe_split_point(img_array, start_y, target_end_y, bg_color):
    height = img_array.shape[0]
    if target_end_y >= height: return height
    search_limit = max(start_y, target_end_y - 500)
    for y in range(target_end_y, search_limit, -1):
        # 判断标准差，寻找纯色背景行
        if np.std(img_array[y]) < 5.0: 
            return y
    return target_end_y

uploaded_file = st.file_uploader("请上传微信长截图", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # 1. 加载图片
    image = Image.open(uploaded_file).convert('RGB')
    
    # --- 关键修正 2：不显示原图预览 ---
    # 不要运行 st.image(image)，因为长图回显会撑爆手机浏览器导致 Network Error
    width, total_height = image.size
    st.info(f"✅ 图片已接收！尺寸：{width} x {total_height} 像素")
    st.caption("已隐藏原图预览以节省流量和内存。")
    
    img_array = np.array(image)
    
    # 获取背景色
    bg_sample = np.concatenate([img_array[0:10, 0:10], img_array[0:10, -10:]])
    bg_color = np.mean(bg_sample, axis=(0, 1))
    
    slices = []
    current_y = 0
    
    with st.spinner('正在后台静默切图...'):
        while current_y < total_height:
            target_end = current_y + max_height
            split_point = find_safe_split_point(img_array, current_y, target_end, bg_color)
            
            slice_img = image.crop((0, current_y, width, split_point))
            slices.append(slice_img)
            current_y = split_point
    
    num_slices = len(slices)
    st.success(f"🔪 切割完成！共 {num_slices} 张。")

    # ZIP 下载逻辑
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for i, s_img in enumerate(slices):
            img_byte_arr = io.BytesIO()
            s_img.save(img_byte_arr, format='PNG')
            file_name = f"part_{i+1:02d}.png"
            zip_file.writestr(file_name, img_byte_arr.getvalue())
            
            # 只预览前 2 张，防止卡顿
            if i < 2:
                st.image(s_img, caption=f"切片预览 {i+1}", use_column_width=True)

    st.download_button(
        label="📦 下载切片压缩包",
        data=zip_buffer.getvalue(),
        file_name="slices.zip",
        mime="application/zip",
        type="primary"
    )

