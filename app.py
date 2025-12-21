import streamlit as st
from PIL import Image
import numpy as np
import io
import zipfile

st.set_page_config(page_title="微信长图智能切片机", page_icon="🧠")
st.title("🧠 微信长图智能切片机")
st.caption("智能识别气泡间隙 | 保证文字不被切断 | 控制切片数量")

# --- 侧边栏配置 ---
with st.sidebar:
    st.header("⚙️ 切割参数")
    # 允许用户调整高度，以便控制切片总数在 10 张以内
    max_height = st.slider("单张切片最大高度 (px)", 
                           min_value=1000, 
                           max_value=5000, 
                           value=2500, 
                           step=100,
                           help="调大这个数值可以减少切片总张数，防止超过 Gemini 的 10 张限制。")
    
    st.info("💡 **原理说明**：\n程序会在达到最大高度前，自动向上寻找气泡之间的'缝隙'进行切割，确保不会把文字拦腰切断。")

def is_background_row(row_pixels, bg_color, tolerance=10):
    """
    判断这一行像素是否主要是背景色
    row_pixels: 这一行的像素数组
    bg_color: 背景色 (R, G, B)
    tolerance: 容差，防止有轻微噪点
    """
    # 计算这一行像素与背景色的差异
    diff = np.abs(row_pixels - bg_color)
    # 如果这一行大部分像素都接近背景色（平均差异很小），即使得是空隙
    # 这里我们简化逻辑：如果这一行的颜色方差极小（说明颜色单一），且接近背景色
    mean_diff = np.mean(diff)
    return mean_diff < tolerance

def find_safe_split_point(img_array, start_y, target_end_y, bg_color):
    """
    在 target_end_y 附近（向上）寻找安全的切割线
    """
    height = img_array.shape[0]
    
    # 如果目标位置超过了图片总高度，直接切到底
    if target_end_y >= height:
        return height
    
    # 从目标位置向上扫描 500px，寻找空隙
    search_limit = max(start_y, target_end_y - 500)
    
    # 倒序扫描 (从 target_end_y 往上找)
    for y in range(target_end_y, search_limit, -1):
        row = img_array[y]
        # 判断这一行是否是背景行
        # 这里用了一个技巧：检查这一行像素的标准差。
        # 纯色背景行的标准差几乎为 0。有文字或气泡的行标准差很大。
        if np.std(row) < 5.0: 
            return y
            
    # 如果实在找不到（比如有一个超级长的气泡超过了500px），只能强制切割
    return target_end_y

uploaded_file = st.file_uploader("请上传微信长截图", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # 1. 加载图片
    image = Image.open(uploaded_file).convert('RGB')
    img_array = np.array(image)
    width, total_height = image.size
    
    st.write(f"📏 图片尺寸：{width} x {total_height}")
    
    # 2. 自动通过边缘取样获取背景色 (取左上角和右上角的平均值)
    # 微信背景通常是浅灰，但可能有深色模式，所以自动取样最稳
    bg_sample = np.concatenate([img_array[0:10, 0:10], img_array[0:10, -10:]])
    bg_color = np.mean(bg_sample, axis=(0, 1))
    
    # 3. 智能切割循环
    slices = []
    current_y = 0
    
    with st.spinner('正在进行智能分析与切割...'):
        while current_y < total_height:
            # 设定预期的结束位置
            target_end = current_y + max_height
            
            # 寻找实际的安全切割点
            split_point = find_safe_split_point(img_array, current_y, target_end, bg_color)
            
            # 切割
            slice_img = image.crop((0, current_y, width, split_point))
            slices.append(slice_img)
            
            # 更新下一次的起点
            current_y = split_point
    
    num_slices = len(slices)
    
    # --- 结果展示区 ---
    st.success(f"✅ 智能切割完成！共生成 {num_slices} 张切片。")
    
    # 警告：如果切片超过 10 张，提醒用户
    if num_slices > 10:
        st.warning(f"⚠️ 注意：切片数量 ({num_slices}) 超过了 Gemini 的 10 张限制。建议在左侧调大「最大高度」参数，然后重新上传。")
    else:
        st.info("👌 切片数量在 10 张以内，可以一次性投喂给 Gemini。")

    # 创建 ZIP 下载
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for i, s_img in enumerate(slices):
            # 保存每一张
            img_byte_arr = io.BytesIO()
            s_img.save(img_byte_arr, format='PNG')
            file_name = f"chat_part_{i+1:02d}.png"
            zip_file.writestr(file_name, img_byte_arr.getvalue())
            
            # 并在页面上显示预览（只显示前3张）
            if i < 3:
                st.image(s_img, caption=f"预览：{file_name}", use_column_width=True)
    
    if num_slices > 3:
        st.caption(f"... 还有 {num_slices - 3} 张未显示")

    st.download_button(
        label="📦 下载所有切片 (ZIP)",
        data=zip_buffer.getvalue(),
        file_name="smart_slices.zip",
        mime="application/zip",
        type="primary"
    )
