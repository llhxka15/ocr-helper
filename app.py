import streamlit as st
from PIL import Image
import io
import zipfile
import math

st.set_page_config(page_title="Gemini 伴侣：长图无损切片机", page_icon="✂️")
st.title("✂️ 长图无损切片机")
st.caption("把长图切成 Gemini 能看清的高清切片 | 专为 AI 投喂设计")

# --- 配置参数 ---
SLICE_HEIGHT = 2000  # 每张图的高度，2000px 是 AI 识别的最佳甜点区
OVERLAP = 100        # 重叠区域，防止文字被腰斩

uploaded_file = st.file_uploader("请上传那张超级长的截图", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # 1. 读取图片
    original_image = Image.open(uploaded_file)
    width, height = original_image.size
    
    st.write(f"📏 图片原始尺寸：{width} x {height} 像素")
    
    # 计算需要切多少张
    num_slices = math.ceil(height / (SLICE_HEIGHT - OVERLAP))
    
    st.info(f"💡 方案：这张图将被无损切分为 {num_slices} 张高清小图，每张带有重叠区域，确保文字不丢失。")

    if st.button('🔪 开始切片并打包', type="primary"):
        # 创建一个内存中的 ZIP 文件
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            top = 0
            for i in range(num_slices):
                # 计算底部
                bottom = min(top + SLICE_HEIGHT, height)
                
                # 切割
                slice_img = original_image.crop((0, top, width, bottom))
                
                # 保存到内存
                img_byte_arr = io.BytesIO()
                # 默认存为 PNG 格式，保持无损
                slice_img.save(img_byte_arr, format='PNG')
                
                # 写入 ZIP，文件名命名为 part_01.png, part_02.png 以便排序
                file_name = f"part_{i+1:02d}.png"
                zip_file.writestr(file_name, img_byte_arr.getvalue())
                
                # 更新下一张的起始位置（减去重叠区）
                top = bottom - OVERLAP
                
                # 能够让用户预览一下切片效果（只显示前两张）
                if i < 2:
                    st.image(slice_img, caption=f"预览：{file_name}", use_column_width=True)

        # 准备下载
        st.success("✅ 切片完成！请下载 ZIP 包。")
        st.download_button(
            label="📦 下载切片压缩包 (ZIP)",
            data=zip_buffer.getvalue(),
            file_name="gemini_slices.zip",
            mime="application/zip"
        )
        
        st.markdown("---")
        st.markdown("### 接下来怎么做？")
        st.markdown("1. 解压下载的 ZIP 文件。")
        st.markdown("2. 把里面的图片 **全选**，直接拖进 Gemini 的对话框。")
        st.markdown("3. 发送下面的提示词给 Gemini。")
