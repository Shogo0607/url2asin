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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

st.set_page_config(page_title="URL→ASIN高速変換ツール")
st.title("URL→ASIN高速変換ツール")

st.sidebar.title("URL→ASIN高速変換ツール")

url = st.sidebar.text_input("URLを入力してください")


price_list = list()
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

def main(url,i):
    time.sleep(i)
    driver = driver_set()
    wait = WebDriverWait(driver=driver, timeout=30)
    driver.get(str(url))
    wait.until(EC.presence_of_all_elements_located)

    try:
        # アイテム名
        item_list_xpath = '//*[@id="search"]/div[1]/div[1]/div/span[3]/div[2]/div['+str(i)+']/div/div/div/div/div/div[2]/div/div/div[1]/h2/a'
        item_list_text = driver.find_element(By.XPATH, item_list_xpath).text
    except:
        item_list_text = ""
    
    element = driver.find_elements_by_id('search')
    aTag    = element.find_element_by_tag_name("a")
    url_tag     = aTag.get_attribute("href")
    driver.get(str(url_tag))
    try:           
        wait.until(EC.presence_of_all_elements_located)
        # 値段
        price_text_xpath = '//*[@id="priceblock_ourprice"]'
        price_text = driver.find_element(By.XPATH, price_text_xpath).text
        print("###############################################################",price_text)
    except:
        price_text = ""

    try:
        # ASIN
        for j in range(1,4):
            asin_xpath = '//*[@id="detailBullets_feature_div"]/ul/li['+str(j)+']/span/span[1]'
            asin_name_text = driver.find_element(By.XPATH, asin_xpath).text
            if "ASIN" in asin_name_text:
                asin_xpath = '//*[@id="detailBullets_feature_div"]/ul/li['+str(j)+']/span/span[2]'
                asin_text = driver.find_element(By.XPATH, asin_xpath).text
                break
            else:
                continue
    except:
        asin_text = ""
    driver.close()
    return item_list_text, asin_text, price_text

@st.cache
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8-sig')

if st.sidebar.button("検索開始"):
    if not url:
        st.warning("URLを入力してください")
        st.stop()

    st.subheader("検索結果")
    with st.spinner("現在検索中..."):
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(main, url,i) for i in range(2,5)]
            for future in as_completed(futures):
                item_list.append(future.result()[0])
                asin_list.append(future.result()[1])
                price_list.append(future.result()[2])


    price_df = pd.DataFrame(price_list)
    asin_df = pd.DataFrame(asin_list)
    item_df = pd.DataFrame(item_list)

    output = pd.concat([item_df,asin_df,price_df],axis=1)
    output.columns = ["アイテム名","ASINコード","値段"]
    st.dataframe(output)
    csv = convert_df(output)
    st.download_button(label="Download data as CSV",data=csv,file_name='ASIN.csv',mime='text/csv',)

