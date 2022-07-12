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
import csv
st.set_page_config(page_title="URL→ASIN高速変換ツール")
st.title("URL→ASIN高速変換ツール")

st.sidebar.title("URL→ASIN高速変換ツール")




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

def click_button(driver, xpath_button):
    button = driver.find_element_by_xpath(xpath_button)
    button.click()

def input_text(driver, input_xpath, input_text):
    input_element = driver.find_element_by_xpath(input_xpath)
    input_element.send_keys(input_text)
  

def save_csv(data, file_path):
    with open(file_path, 'w') as file:
        writer = csv.writer(file, lineterminator='\n')
        writer.writerows(data)

def get_product_title(driver,product_title_xpath):
    try:
        product_title = driver.find_element_by_xpath(product_title_xpath).text
      
    except:
        product_title = ''
    return product_title

def get_review_value(driver,review_value_xpath):
    try:
        review_value = driver.find_element_by_xpath(review_value_xpath).get_attribute("textContent").replace('out of 5 stars', '')
        
    except:
        review_value = ''
    return review_value

def get_review_number(driver,review_number_xpath):
    try:
        review_number = driver.find_element_by_xpath(review_number_xpath).get_attribute("textContent").replace('ratings', '').replace(',', '')
    except:
        review_number = ''
    return review_number

def get_price(driver,price_xpath,price_timesale_xpath):
    try:
        price = driver.find_element_by_xpath(price_xpath).get_attribute("textContent")

    except:
        try:
            price = driver.find_element_by_xpath(price_timesale_xpath)
        except:
            price = ""
    return price

def get_asin(driver):
    asin = ""
    for i in range(1,10):
        try:
            asin_text_xpath = '//*[@id="detailBullets_feature_div"]/ul/li['+str(i)+']/span/span[1]'
            asin_text = driver.find_element_by_xpath(asin_text_xpath).get_attribute("textContent")
            if "ASIN" in asin_text:
                asin_xpath = '//*[@id="detailBullets_feature_div"]/ul/li['+str(i)+']/span/span[2]'
                asin = driver.find_element_by_xpath(asin_xpath).get_attribute("textContent")
                break
        except:
            asin = ""
    return asin

def main(keyword,link):
    product_detail = []
    driver = driver_set()
    driver.get(link)
    wait = WebDriverWait(driver=driver, timeout=30)
    wait.until(EC.presence_of_all_elements_located)
    product_title_xpath = "//span[contains(@id, 'productTitle')]"
    review_value_xpath = "//div[contains(@id, 'centerCol')]//span[contains(@class, 'a-icon-alt')]"
    review_number_xpath = "//div[contains(@id, 'centerCol')]//span[contains(@id, 'acrCustomerReviewText')]"
    price_xpath = '//*[@id="corePriceDisplay_desktop_feature_div"]/div[1]/span/span[2]/span[2]'
    price_timesale_xpath = '//*[@id="corePriceDisplay_desktop_feature_div"]/div[1]/span[2]/span[2]/span[2]'  
    product_title = get_product_title(driver,product_title_xpath)
    price = get_price(driver,price_xpath,price_timesale_xpath)
    review_value = get_review_value(driver,review_value_xpath)
    review_number = get_review_number(driver,review_number_xpath)
    asin = get_asin(driver)
    product_detail.append([keyword, product_title, price, review_value, review_number,asin])
    # ブラウザを終了
    driver.close()
    return product_detail

def read_link(keyword,page_number):
    driver = driver_set()
    driver.get(f"https://www.amazon.co.jp/s?k={keyword}&page={page_number}")
    wait = WebDriverWait(driver=driver, timeout=30)
    wait.until(EC.presence_of_all_elements_located)
    # xpath一覧
    products_link_xpath = "//h2/a"
    # 商品リンク一覧取得
    products = driver.find_elements_by_xpath(products_link_xpath)
    links = [product.get_attribute('href') for product in products]
    wait.until(EC.presence_of_all_elements_located)
    driver.close()
    return links

@st.cache
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8-sig')


keyword = st.sidebar.text_input("検索ワードを入力してください")

if st.sidebar.button("検索開始"):
    if keyword == "":
        st.warning("検索ワードを入力してください")
        st.stop()

    st.subheader("検索結果")
    with st.spinner("現在検索中..."):
        product_details = pd.DataFrame()
        page = ["1","2"]
        for page_number in page:
            links = read_link(keyword,page_number)

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(main, keyword,link) for link in links]
                for future in as_completed(futures):
                    _ = future.result()
                    _ = pd.DataFrame(_)
                    product_details = pd.concat([product_details,_],axis=0)
    product_details.columns = ["キーワード","商品名","値段","レビュー","レビュー数","ASIN"]
    st.dataframe(product_details)
    csv_data = convert_df(product_details)
    if st.download_button(label="Download data as CSV",data=csv_data,file_name='キーワード検索結果.csv',mime='text/csv',):
        st.success("ダウンロード完了")
        st.stop

