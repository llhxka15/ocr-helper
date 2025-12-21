import streamlit as st
from PIL import Image
import pytesseract

# 设置页面配置
st.set_page_config(page_title="长图文字提取神器", page_icon="📝")

st.title("📝 长截屏文字提取器")
st.caption("基于 Tesseract OCR | 支持中文识别")

# 侧边栏说明
with st.sidebar:
    st.write("### 使用说明")
    st.write("1. 上传手机长截屏")
    st.write("2. 等待处理完成")
    st.write("3. 复制文字")

# 1. 上传文件
uploaded_file = st.file_uploader("请上传图片 (支持 png, jpg, jpeg)", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # 2. 显示图片预览
    image = Image.open(uploaded_file)
    st.image(image, caption='已上传图片', use_column_width=True)
    
    # 3. 开始识别按钮
    if st.button('🚀 开始提取文字', type="primary"):
        with st.spinner('正在努力识别中，长图可能需要十几秒...'):
            try:
                # 核心识别逻辑
                # lang='chi_sim+eng' 表示同时识别中文简体和英文
                text = pytesseract.image_to_string(image, lang='chi_sim+eng')
                
                if not text.strip():
                    st.warning("未能识别出文字，可能是图片太模糊或背景太复杂。")
                else:
                    st.success("提取成功！")
                    st.text_area("识别结果 (可全选复制)", text, height=400)
                    
            except Exception as e:
                st.error(f"出错了: {e}")
                st.info("提示：如果遇到 Memory Error，说明图片像素过大，请尝试裁剪后分段上传。")
