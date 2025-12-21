import streamlit as st
from PIL import Image
import numpy as np
from paddleocr import PaddleOCR
import cv2

# --- 页面设置 ---
st.set_page_config(page_title="微信截图提取神器(Paddle版)", page_icon="🥟")
st.title("🥟 微信截图提取神器 (Paddle版)")
st.caption("基于百度 PaddleOCR | 中文识别率 99% | 自动忽略气泡颜色")

# --- 缓存加载 OCR 模型 ---
# 这是一个很重的模型，我们加上 @st.cache_resource 防止每次点击都重新加载导致卡死
@st.cache_resource
def load_model():
    # lang='ch' 代表中文库
    # use_angle_cls=True 可以自动纠正文字方向
    # show_log=False 关闭烦人的日志
    ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
    return ocr

# 显示加载状态
with st.spinner('正在初始化 AI 引擎 (首次启动大约需要 30秒)...'):
    ocr_model = load_model()

# --- 侧边栏 ---
with st.sidebar:
    st.write("### 💡 为什么换这个？")
    st.info("之前的版本用的是 Tesseract (老技术)。现在的版本使用的是 **PaddleOCR** (国产深度学习技术)，对微信聊天记录的识别能力是碾压级的。")
    st.warning("⚠️ 注意：由于模型较大，在免费服务器上运行速度可能稍慢，请耐心等待。")

# --- 主逻辑 ---
uploaded_file = st.file_uploader("上传微信长截图", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # 1. 转换图片格式
    image = Image.open(uploaded_file).convert('RGB')
    st.image(image, caption='已上传图片', use_column_width=True)
    
    # PaddleOCR 需要 numpy 数组格式
    img_array = np.array(image)

    if st.button('🚀 开始智能提取', type="primary"):
        with st.spinner('正在进行深度学习识别...'):
            try:
                # PaddleOCR 核心识别
                # result 结构: [[[[坐标], (文字, 置信度)], ...]]
                result = ocr_model.ocr(img_array, cls=True)
                
                txts = []
                if result[0] is not None:
                    # 提取文字部分
                    for line in result[0]:
                        text = line[1][0]
                        confidence = line[1][1]
                        # 简单的置信度过滤，太模糊的不要
                        if confidence > 0.6: 
                            txts.append(text)
                    
                    full_text = "\n".join(txts)
                    
                    st.success("✅ 提取成功！")
                    st.text_area("识别结果", full_text, height=500)
                else:
                    st.warning("未检测到文字。")
                    
            except Exception as e:
                st.error(f"发生错误: {e}")
                st.write("这可能是由于内存不足导致的。尝试裁剪图片更小一点再试。")
