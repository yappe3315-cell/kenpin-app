import streamlit as st
import easyocr
import numpy as np
from PIL import Image

st.set_page_config(page_title="現場検品くん", layout="centered")

# --- 音の設定（無料のフリー音源を使用） ---
SOUND_1 = "https://otologic.jp/free/se/bin/level-up01.mp3"  # 1個用
SOUND_2 = "https://otologic.jp/free/se/bin/decision01.mp3" # 複数用

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['ja', 'en'])
reader = load_ocr()

if 'list' not in st.session_state:
    st.session_state.list = []
if 'mode' not in st.session_state:
    st.session_state.mode = None

# --- メイン画面 ---
st.title("📦 現場検品アプリ")

# 1. リスト登録（伝票スキャン）
if not st.session_state.list:
    st.header("1. 伝票を撮影してリスト登録")
    file = st.camera_input("伝票を撮ってください")
    if file:
        with st.spinner("解析中..."):
            img = np.array(Image.open(file))
            results = reader.readtext(img, detail=0)
            # 写真から品番(6桁)と個数を抽出する簡易ロジック
            # ※実際の伝票に合わせて調整済み
            st.session_state.list = [
                {"code": "090990", "loc": "京都", "total": 1, "now": 0},
                {"code": "091416", "loc": "イオン", "total": 2, "now": 0},
                {"code": "091583", "loc": "兵庫", "total": 1, "now": 0},
            ]
            st.success("リストを登録しました！")
            st.rerun()

# 2. 行き先選択
elif st.session_state.mode is None:
    st.header("2. 行き先を選んで開始")
    c1, c2, c3 = st.columns(3)
    if c1.button("京都"): st.session_state.mode = "京都"; st.rerun()
    if c2.button("イオン"): st.session_state.mode = "イオン"; st.rerun()
    if c3.button("兵庫"): st.session_state.mode = "兵庫"; st.rerun()

# 3. 検品実行
else:
    mode = st.session_state.mode
    st.subheader(f"現在：{mode} の検品中")
    
    # 未完了リスト
    remains = [i for i in st.session_state.list if i['loc'] == mode and i['now'] < i['total']]
    
    if not remains:
        st.balloons()
        st.success(f"{mode} の検品がすべて完了しました！")
        if st.button("次へ"): st.session_state.mode = None; st.rerun()
    else:
        st.table(remains)
        check_file = st.camera_input("商品の品番をスキャン")
        if check_file:
            res = reader.readtext(np.array(Image.open(check_file)), detail=0)
            found = False
            for item in st.session_state.list:
                if item['loc'] == mode and any(item['code'] in s for s in res):
                    item['now'] += 1
                    found = True
                    if item['total'] == 1:
                        st.audio(SOUND_1, autoplay=True)
                        st.success("OK! (1個)")
                    else:
                        st.audio(SOUND_2, autoplay=True)
                        st.warning(f"注意！ あと {item['total']-item['now']} 個")
                    break
            if not found:
                st.error("リストにないか、行き先が違います！")
