import warnings
import streamlit as st
import requests
import base64
import numpy as np
import io
import soundfile as sf
import os

import logging
logging.getLogger('numba').setLevel(logging.WARNING)

warnings.simplefilter('ignore')

with st.form("my_form", clear_on_submit=False):
    character = st.text_input('キャラクター名 *必須')

    text = st.text_input('テキスト *必須')
    # st.checkbox()
    # text = st.text_input('アクセント *必須')

    submitted = st.form_submit_button("音声出力")

if submitted:
    if character is None or text is None:
        st.warning("必須項目を確認してください")
        st.stop()

    with st.spinner("音声を出力中です..."):
        KEY = st.secrets["key"]
        ENDPOINT = st.secrets["endpoint"]

        # リクエストボディを定義する
        request_body = {"text": text, "character": character}
        headers = {'Accept': 'application/json',
                   'Content-Type': 'application/json', "X-API-Key": KEY}
        # POSTリクエストを、リクエストボディ付きで送信する
        # ここでflaskのエンドポイントにアクセス、returnを受け取る
        response = requests.post(ENDPOINT, json=request_body, headers=headers)

        # receive audio_binary and revert it into np.array
        data = response.json()
        audio_base64 = data['audio']['binary']
        dtype = data['audio']['dtype']
        shape = data['audio']['shape']

        audio_bytes = base64.b64decode(audio_base64)
        audio_array = np.frombuffer(audio_bytes, dtype=dtype)
        audio_array = audio_array.reshape(shape)

        # Write the audio data to an in-memory bytes buffer
        audio_buffer = io.BytesIO()
        # Assuming a sample rate of 16000
        sf.write(audio_buffer, audio_array, 16000, format='wav')

        # Reset buffer cursor to the beginning
        audio_buffer.seek(0)

        # Play the audio from the buffer
        st.audio(audio_buffer.read(), format='audio/wav')
