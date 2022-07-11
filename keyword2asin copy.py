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
        review_value = driver.find_element_by_xpath(review_value_xpath).get_attribute("textContent").replace('5つ星のうち', '')
        
    except:
        review_value = ''
    return review_value

def get_review_number(driver,review_number_xpath):
    try:
        review_number = driver.find_element_by_xpath(review_number_xpath).get_attribute("textContent").replace('個の評価', '').replace(',', '')
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
    for i in range(1,10):
        try:
            asin_text_xpath = '//*[@id="detailBullets_feature_div"]/ul/li['+str(i)+']/span/span[1]'
            asin_text = driver.find_element_by_xpath(asin_text_xpath).get_attribute("textContent")
            if "ASIN" in asin_text:
                asin_xpath = '//*[@id="detailBullets_feature_div"]/ul/li['+str(i)+']/span/span[2]'
                asin = driver.find_element_by_xpath(asin_xpath).get_attribute("textContent")
        except:
            asin = ""
    return asin



def main(keyword):
    driver = driver_set()
    wait = WebDriverWait(driver=driver, timeout=30)
    wait.until(EC.presence_of_all_elements_located)
    page_numbers = ["1"]
    product_detail = []

    # xpath一覧
    products_link_xpath = "//h2/a"
    product_title_xpath = "//span[contains(@id, 'productTitle')]"
    review_value_xpath = "//div[contains(@id, 'centerCol')]//span[contains(@class, 'a-icon-alt')]"
    review_number_xpath = "//div[contains(@id, 'centerCol')]//span[contains(@id, 'acrCustomerReviewText')]"
    price_xpath = '//*[@id="corePriceDisplay_desktop_feature_div"]/div[1]/span/span[2]/span[2]'
    price_timesale_xpath = '//*[@id="corePriceDisplay_desktop_feature_div"]/div[1]/span[2]/span[2]/span[2]'
    
    


    for page_number in page_numbers:
        driver.get(f"https://www.amazon.co.jp/s?k={keyword}&page={page_number}")
        

        # 商品リンク一覧取得
        products = driver.find_elements_by_xpath(products_link_xpath)
        links = [product.get_attribute('href') for product in products]
        wait.until(EC.presence_of_all_elements_located)

        # 商品個別ページを表示
        for link in links:
            driver.get(link)
            wait.until(EC.presence_of_all_elements_located)

            product_title = get_product_title(driver,product_title_xpath)
            price = get_price(driver,price_xpath,price_timesale_xpath)
            review_value = get_review_value(driver,review_value_xpath)
            review_number = get_review_number(driver,review_number_xpath)
            asin = get_asin(driver)
            product_detail.append([keyword, product_title, price, review_value, review_number,asin])

    # データの保存
    save_csv(product_detail, 'amazon.csv')

    # ブラウザを終了
    driver.close()


@st.cache
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8-sig')

if st.sidebar.button("検索開始"):
    # if not url:
    #     st.warning("URLを入力してください")
    #     st.stop()

    st.subheader("検索結果")
    with st.spinner("現在検索中..."):
        keywords = "財布"
        main(keywords)
        # with ThreadPoolExecutor(max_workers=20) as executor:
        #     futures = [executor.submit(main, keyword) for keyword in keywords]
            # for future in as_completed(futures):
            #     item_list.append(future.result()[0])


    # price_df = pd.DataFrame(price_list)
    # asin_df = pd.DataFrame(asin_list)
    # item_df = pd.DataFrame(item_list)

    # output = pd.concat([item_df,asin_df,price_df],axis=1)
    # output.columns = ["アイテム名","ASINコード","値段"]
    # st.dataframe(output)
    # csv = convert_df(output)
    # st.download_button(label="Download data as CSV",data=csv,file_name='ASIN.csv',mime='text/csv',)

