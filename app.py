import streamlit as st
from PIL import Image
import pytesseract
import numpy as np

# --- 配置区域 ---
# 设置切片高度。太高容易爆内存，太低识别慢。4000px是个不错的平衡点。
SLICE_HEIGHT = 4000  
# 设置重叠区域高度。防止文字刚好在切割线上被切断，设置重叠区能保证文字完整。
# 识别后可能会有少量重复文字，属于正常现象。
OVERLAP = 200 
# ----------------

st.set_page_config(page_title="长图文字提取神器Pro", page_icon="📝")
st.title("📝 长截屏文字提取器 Pro")
st.caption("自动切片处理超长图 | 基于 Tesseract OCR | 支持中文")

with st.sidebar:
    st.write("### Pro版升级说明")
    st.info("已针对超长图进行优化。程序会自动将长图切割成多段进行识别，解决了'Image too large'报错的问题。")

uploaded_file = st.file_uploader("请上传图片 (支持 png, jpg, jpeg)", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    # 计算需要切多少片
    width, height = image.size
    # 估算切片数量用于进度条
    num_slices = 1
    if height > SLICE_HEIGHT:
        num_slices = int(np.ceil((height - SLICE_HEIGHT) / (SLICE_HEIGHT - OVERLAP))) + 1
        st.caption(f"📊 图片高度 {height}px，将自动切割成约 {num_slices} 个片段进行处理。")

    st.image(image, caption='已上传图片 (预览)', use_column_width=True)
    
    if st.button('🚀 开始专业提取', type="primary"):
        full_text = ""
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            top = 0
            count = 0
            while top < height:
                count += 1
                status_text.write(f"⏳ 正在处理第 {count}/{num_slices} 个片段...")
                
                # 1. 计算当前切片的底部坐标
                bottom = min(top + SLICE_HEIGHT, height)
                
                # 2. 裁剪图片
                # crop区域是 (左, 上, 右, 下)
                slice_img = image.crop((0, top, width, bottom))
                
                # 3. 识别当前片段
                text = pytesseract.image_to_string(slice_img, lang='chi_sim+eng')
                full_text += text + "\n"
                
                # 更新进度条
                current_progress = min(count / num_slices, 1.0)
                progress_bar.progress(current_progress)

                # 4. 计算下一片的起始位置
                if bottom == height:
                    break # 已经是最后一张了
                # 核心逻辑：往下走一步，但要往回退一个OVERLAP的距离，形成重叠
                top = bottom - OVERLAP
            
            progress_bar.progress(100)
            status_text.success("✅ 所有片段处理完成！")
            
            if not full_text.strip():
                st.warning("未能识别出文字。")
            else:
                st.success("提取成功！请向下滚动查看结果。")
                st.info("💡 提示：由于采用了重叠切割以防止文字断裂，结果中可能会出现少量重复的文本行，请手动查阅。")
                st.text_area("最终识别结果 (可全选复制)", full_text, height=500)

        except Exception as e:
            st.error(f"处理过程中发生未知错误: {e}")
        finally:
            # 清理内存
            del image
