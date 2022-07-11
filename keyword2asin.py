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
st.set_page_config(page_title="キーワード→ASIN高速変換ツール")
st.title("キーワード→ASIN高速変換ツール")

st.sidebar.title("キーワード→ASIN高速変換ツール")




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

def save_csv(data, file_path):
    with open(file_path, 'w') as file:
        writer = csv.writer(file, lineterminator='\n')
        writer.writerows(data)

def get_product_title(driver,product_title_xpath):
    try:
        product_title = driver.find_element(By.XPATH, product_title_xpath).text
      
    except:
        product_title = ''
    return product_title

def get_review_value(driver,review_value_xpath):
    try:
        review_value = driver.find_element(By.XPATH, review_value_xpath).text.replace('5つ星のうち', '')
        
    except:
        review_value = ''
    return review_value

def get_review_number(driver,review_number_xpath):
    try:
        review_number = driver.find_element(By.XPATH, review_number_xpath).text.replace('個の評価', '').replace(',', '')
    except:
        review_number = ''
    return review_number

def get_price(driver,price_xpath,price_timesale_xpath):
    try:
        price = driver.find_element(By.XPATH, price_xpath).text
    except:
        try:
            price = driver.find_element(By.XPATH, price_timesale_xpath).text
        except:
            price = ""
    return price

def get_asin(driver):
    for i in range(1,10):
        try:
            asin_text_xpath = '//*[@id="detailBullets_feature_div"]/ul/li['+str(i)+']/span/span[1]'
            asin_text = driver.find_element(By.XPATH, asin_text_xpath).text
            if "ASIN" in asin_text:
                asin_xpath = '//*[@id="detailBullets_feature_div"]/ul/li['+str(i)+']/span/span[2]'
                asin = driver.find_element(By.XPATH, asin_xpath).text
                break
        except:
            asin = ""
    return asin

def main(keyword,page_number):
    driver = driver_set()
    driver.get(f"https://www.amazon.co.jp/s?k={keyword}&page={page_number}")
    wait = WebDriverWait(driver=driver, timeout=30)
    wait.until(EC.presence_of_all_elements_located)
    product_detail = []

    # xpath一覧
    products_link_xpath = "//h2/a"
    product_title_xpath = "//span[contains(@id, 'productTitle')]"
    review_value_xpath = "//div[contains(@id, 'centerCol')]//span[contains(@class, 'a-icon-alt')]"
    review_number_xpath = "//div[contains(@id, 'centerCol')]//span[contains(@id, 'acrCustomerReviewText')]"
    price_xpath = '//*[@id="corePriceDisplay_desktop_feature_div"]/div[1]/span/span[2]/span[2]'
    price_timesale_xpath = '//*[@id="corePriceDisplay_desktop_feature_div"]/div[1]/span[2]/span[2]/span[2]'
   

    # 商品リンク一覧取得
    products = driver.find_elements(products_link_xpath)
    links = [product.get_attribute('href') for product in products]
    wait.until(EC.presence_of_all_elements_located)

    # 商品個別ページを表示
    for link in links[0:3]:
        driver.get(link)
        wait.until(EC.presence_of_all_elements_located)

        product_title = get_product_title(driver,product_title_xpath)
        price = get_price(driver,price_xpath,price_timesale_xpath)
        review_value = get_review_value(driver,review_value_xpath)
        review_number = get_review_number(driver,review_number_xpath)
        asin = get_asin(driver)
        product_detail.append([keyword, product_title, price, review_value, review_number,asin])

    # # データの保存
    # save_csv(product_detail, 'amazon.csv')

    # ブラウザを終了
    driver.close()
    return product_detail


@st.cache
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8-sig')

keyword = st.sidebar.text_input("検索ワードを入力してください")
start_button = st.sidebar.button("検索開始")
if not start_button:
    st.warning("検索開始を押してください")
    st.stop()

st.subheader("検索結果")
with st.spinner("現在検索中..."):
    product_details = pd.DataFrame()
    page_numbers = ["1","2"]
    # main(keyword)
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(main, keyword,page_number) for page_number in page_numbers]
        for future in as_completed(futures):
            _ = future.result()
            _ = pd.DataFrame(_)
            product_details = pd.concat([product_details,_],axis=0)
product_details.columns = ["キーワード","商品名","値段","レビュー","レビュー数","ASIN"]
# product_details.to_csv("amazon.csv",index=False,encoding="utf-8-sig")
# save_csv(product_details, 'amazon.csv')
# asin_df = pd.DataFrame(asin_list)
# item_df = pd.DataFrame(item_list)

# output = pd.concat([item_df,asin_df,price_df],axis=1)
# output.columns = ["アイテム名","ASINコード","値段"]
st.dataframe(product_details)
csv_data = convert_df(product_details)
done = 1
st.download_button(label="Download data as CSV",data=csv_data,file_name='キーワード検索結果.csv',mime='text/csv',)

