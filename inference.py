import streamlit as st
import requests
import base64
import numpy as np
import io
import os
import soundfile as sf

import logging
logging.getLogger('numba').setLevel(logging.WARNING)

import warnings
warnings.simplefilter('ignore')

ENDPOINT = st.secrets["endpoint"]
with st.form("my_form", clear_on_submit=False):
    geturl = f"{ENDPOINT}/characters"
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    response = requests.get(geturl, headers=headers)
    data = response.json()
    characters = data["characters"]
    character = st.selectbox(label='使用するモデルを選択してください',
                 options=characters,
                 )

    api_key = st.text_input('APIキー *必須')
    
    text = st.text_input('テキスト *必須')

    pronounce = st.text_input("読み（任意）")

    accent = st.file_uploader("アクセント（任意）",type="json")

    tone = st.slider('キー指定（任意）', min_value=-1200, max_value=1200, value=0, step=100)

    speed = st.number_input("速度（任意）", value=1.0, step=0.1)

    vol = st.number_input("音量（任意）", value=1.0, step=0.1)

    interval_c = st.slider("読点の間隔（任意）", min_value=0, max_value=3, value=0, step=1)
    interval_p = st.slider("句点の間隔（任意）", min_value=0, max_value=3, value=0, step=1)

    submitted = st.form_submit_button("音声出力")

if submitted:
    if character is None or text is None or api_key=="":
        st.warning("必須項目を確認してください") 
        st.stop()
    
    with st.spinner("音声を出力中です..."):
        accent_file = "text/accent.json"
        if accent is not None:
            with open(accent_file, "wb") as file:
                file.write(accent.getbuffer())
        POST_URL = f"{ENDPOINT}/audio"
        # リクエストボディを定義する
        request_body = {"text":text,
                        "character": character,
                        "pronounce": pronounce,
                        "tone": tone,
                        "accent": accent_file,
                        "speed": speed,
                        "vol": vol,
                        "interval_c": interval_c,
                        "interval_p": interval_p
                        }
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', "X-API-Key": api_key}
        # POSTリクエストを、リクエストボディ付きで送信する
        # ここでflaskのエンドポイントにアクセス、returnを受け取る
        response = requests.post(POST_URL, json=request_body, headers=headers)

        # receive audio_binary and revert it into np.array
        data = response.json()
        audio_base64 = data['audio']['binary']
        dtype = data['audio']['dtype']
        shape = data['audio']['shape']
        rate = data['audio']['rate']

        audio_bytes = base64.b64decode(audio_base64)
        audio_array = np.frombuffer(audio_bytes, dtype=dtype)
        audio_array = audio_array.reshape(shape)

        # Write the audio data to an in-memory bytes buffer
        audio_buffer = io.BytesIO()
        sf.write(audio_buffer, audio_array, rate, format='wav')  # Assuming a sample rate of 16000
        
        # Reset buffer cursor to the beginning
        audio_buffer.seek(0)

        # Play the audio from the buffer
        st.text(data['text'])
        st.audio(audio_buffer.read(), format='audio/wav')

        try:
            os.remove("text/accent.json")
        except:
            pass
