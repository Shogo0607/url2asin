import time
from numpy import ma
import pandas as pd
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import streamlit as st
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome import service as fs
from selenium.webdriver.common.keys import Keys
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image
st.set_page_config(page_title="JAN→ASIN高速変換ツール")
st.title("JAN→ASIN高速変換ツール")

st.sidebar.title("JAN→ASIN高速変換ツール")

col1,col2 = st.columns(2)

with col1:
    st.subheader("手順")
    image = Image.open('./example.png')
    st.write("CSVは[jan]とヘッダーを付けて、下記のように縦に入力したファイルをアップロードしてください")
    st.image(image, caption='CSVの入力例',width=300)

file = st.sidebar.file_uploader("CSVファイルを入力してください",type=["csv"])

jan_list = list()
asin_list = list()
item_list = list()

def driver_set():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')  
    chrome_options.add_argument('--disable-dev-shm-usage') 
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver.maximize_window()
    driver.implicitly_wait(3)
    return driver

def main(jan):
    driver = driver_set()
    try:
        driver.get("https://mnsearch.com/search?kwd="+str(jan))
        time.sleep(1)
        item_list_xpath = '//*[@id="main_contents"]/section[2]/section[1]/div/a/span'
        item_list_text = driver.find_element(By.XPATH, item_list_xpath).text
        element = driver.find_element(By.XPATH, item_list_xpath)
        driver.execute_script("arguments[0].click();", element)
        asin_xpath = '//*[@id="__main_content"]/section[3]/section[3]/section[2]/section/div[1]/span'
        asin_text = driver.find_element(By.XPATH, asin_xpath).text
    except:
        asin_text = "検索結果なし"
        item_list_text = "検索結果なし"
    driver.close()
    return jan, asin_text, item_list_text, 

@st.cache
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8-sig')

if st.sidebar.button("検索開始"):
    if not file:
        st.warning("CSVファイルを入力してください")
        st.stop()
    else:
        df = pd.read_csv(file)
        jans = df["jan"].tolist()

    with col2:
        st.subheader("検索結果")
        with st.spinner("現在検索中..."):
            with ThreadPoolExecutor(max_workers=60) as executor:
                futures = [executor.submit(main, value) for value in jans]
                for future in as_completed(futures):
                    jan_list.append(future.result()[0])
                    asin_list.append(future.result()[1])
                    item_list.append(future.result()[2])
    
        jan_df = pd.DataFrame(jan_list)
        asin_df = pd.DataFrame(asin_list)
        item_df = pd.DataFrame(item_list)

        output = pd.concat([jan_df,asin_df,item_df],axis=1)
        output.columns = ["JANコード","ASINコード","商品名"]
        st.dataframe(output)
        csv = convert_df(output)
        st.download_button(label="Download data as CSV",data=csv,file_name='ASIN.csv',mime='text/csv',)
