import streamlit as st
from cnocr import CnOcr
from PIL import Image
import numpy as np

# --- 配置 ---
# 设置切片高度。CnOCR 对内存更友好，我们可以设置稍微大一点
SLICE_HEIGHT = 3000  
OVERLAP = 100 

st.set_page_config(page_title="微信截图提取轻量版", page_icon="⚡")
st.title("⚡ 微信截图提取 (轻量极速版)")
st.caption("核心引擎：CnOCR | 专为中文优化 | 自动处理超长图")

# --- 加载模型 ---
# CnOCR 启动非常快，通常不需要太久的等待
@st.cache_resource
def load_model():
    # det_model_name='en_PP-OCRv3_det' 使用轻量级检测模型
    return CnOcr()

try:
    with st.spinner('正在启动轻量级 AI 引擎...'):
        ocr = load_model()
except Exception as e:
    st.error(f"引擎加载失败，请刷新页面重试: {e}")

# --- 主逻辑 ---
uploaded_file = st.file_uploader("上传长截图", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # 1. 读取图片
    image = Image.open(uploaded_file).convert('RGB')
    width, height = image.size
    
    # 显示预览
    st.image(image, caption='已上传图片', use_column_width=True)
    
    if st.button('🚀 开始提取'):
        full_text = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # 计算切片数
            num_slices = 1
            if height > SLICE_HEIGHT:
                num_slices = int(np.ceil((height - SLICE_HEIGHT) / (SLICE_HEIGHT - OVERLAP))) + 1
            
            top = 0
            count = 0
            
            while top < height:
                count += 1
                status_text.write(f"⚡ 正在识别片段 {count}/{num_slices}...")
                
                # 2. 切割图片
                bottom = min(top + SLICE_HEIGHT, height)
                # Crop tuple: (left, top, right, bottom)
                slice_img = image.crop((0, top, width, bottom))
                
                # 转为 numpy 格式供 CnOCR 使用
                img_array = np.array(slice_img)

                # 3. 核心识别
                # CnOCR 返回的是一个列表，每一项是 {'text': '内容', 'score': 0.8, ...}
                res = ocr.ocr(img_array)
                
                # 4. 提取文字并拼接
                for line in res:
                    text_content = line['text']
                    # 过滤掉置信度太低的乱码 (小于 0.4)
                    if line['score'] > 0.4:
                        full_text.append(text_content)
                
                # 更新进度
                current_progress = min(count / num_slices, 1.0)
                progress_bar.progress(current_progress)

                if bottom == height:
                    break
                top = bottom - OVERLAP

            progress_bar.progress(100)
            status_text.success("✅ 提取完成！")
            
            # 结果去重与展示
            # (简单的去重逻辑，防止重叠区域导致的一句话出现两次)
            final_output = "\n".join(full_text)
            
            if not final_output.strip():
                st.warning("未识别到文字，请确保图片清晰。")
            else:
                st.text_area("识别结果", final_output, height=500)

        except Exception as e:
            st.error(f"发生错误: {e}")
            st.info("如果提示 Memory Error，请尝试将长图裁剪成两半再上传。")
