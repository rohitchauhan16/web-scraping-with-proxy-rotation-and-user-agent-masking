import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from fake_useragent import UserAgent
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import cycle
from threading import Event

# Function to check if a proxy is working
def check_proxy(proxy, stop_event):
    if stop_event.is_set():
        return None
    try:
        response = requests.get(base_url, proxies={"http": proxy, "https": proxy}, headers=user_mask, timeout=10)
        if response.status_code == 200:
            # print(f"Proxy {proxy} is working.")
            return proxy
        else:
            # print(f"Proxy {proxy} is not working. Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        # print(f"Proxy {proxy} failed with error: {e}")
        return None

# Base URL and user agent
base_url = 'https://singapore.coach.com/women/shoes.html'
user_mask = {'User-Agent': UserAgent().random}
proxies = []

# Fetch proxies from sslproxies.org
url = 'https://www.sslproxies.org/'
response = requests.get(url)

if response.status_code == 200:
    soup = BeautifulSoup(response.content, 'html.parser')
    rows = soup.find_all('tr')

    proxy_list = []
    for row in rows[1:]:
        cols = row.find_all('td')
        if len(cols) > 1 and cols[6].text == 'yes':
            proxy = f"http://{cols[0].text.strip()}:{cols[1].text.strip()}"
            proxy_list.append(proxy)

    # Use ThreadPoolExecutor to check proxies in parallel
    stop_event = Event() 
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_proxy = {executor.submit(check_proxy, proxy, stop_event): proxy for proxy in proxy_list}
        for future in as_completed(future_to_proxy):
            result = future.result()
            if result:
                proxies.append(result)
            if len(proxies) >= 3:  # Stop after finding 3 working proxies
                stop_event.set()
                break

proxy_pool = cycle(proxies)
proxy = next(proxy_pool)

print(f"Working proxies: {proxies}") 

# Define user agent
user_mask = {'User-Agent': UserAgent().random}

# Placeholder DataFrame
ws = pd.DataFrame(columns=[
    'Link', 'Name', 'Image', 'Category', 'Subcategory', 'Color', 'Current Price', 'Original Price', 'Description', 'Details', 
    'Tag', 'Status', 'Remarks', 'Timestamp'
])

# Set to store unique links
unique_links = set() 

base_url = [
    'https://singapore.coach.com/women/shoes.html',
    'https://singapore.coach.com/women/bags.html',
    'https://singapore.coach.com/men/shoes.html',
    'https://singapore.coach.com/men/bag.html'
    ] 

all_links = []

for product_url in base_url:
    page_num = 1 

    while True:
        url = f"{product_url}?p={page_num}" 
        
        try:
            response = requests.get(url, headers=user_mask, timeout=10) 
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                tab_contents = soup.findAll(class_='product details product-item-details')

            else:
                # print(f"Failed to retrieve the webpage: {url}. Status code: {response.status_code}")
                break
            
            if not tab_contents:
                break
            
            for tab_content in tab_contents:
                links = tab_content.find_all('a', href=True)
                for link in links:
                    if link['href'] not in unique_links:
                        unique_links.add(link['href'])
                        all_links.append(link['href'])
            
            next_page = soup.find('a', {'class': 'next'})
            if not next_page:
                break
            
            page_num += 1 

        except requests.exceptions.RequestException as e:
            # print(f"Failed to retrieve the webpage: {url}. Error: {e}") 
            break
    
print("Total unique links found:", len(all_links))

# Function to scrape data from a URL
def scrape_data(url):
    try:
        response = requests.get(url, headers=user_mask, timeout=10) 
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            product_link = url
            product_name = soup.find('span', class_='base', attrs={'itemprop': "name"}).text.strip() if soup.find('span', class_='base', attrs={'itemprop': "name"}) else 'No Product Name Available'
            img_url = soup.find('img', class_='gallery-placeholder__image')['src'] if soup.find('img', class_='gallery-placeholder__image') else 'No Image Available'
            category = url.split('/')[3]+'-'+url.split('/')[4] 
            subcategory = ''
            product_color = soup.find('div', class_='value', itemprop='coach_style_color').text.strip() if soup.find('div', class_='value', itemprop='coach_style_color') else 'No Color Available'
            current_price = soup.find('span', class_='price-wrapper', attrs={'data-price-type': "finalPrice"}).text.strip() if soup.find('span', class_='price-wrapper', attrs={'data-price-type': "finalPrice"}) else 'No Current Price Available'
            original_price = soup.find('span', class_='price-wrapper', attrs={'data-price-type': "oldPrice"}).text.strip() if soup.find('span', class_='price-wrapper', attrs={'data-price-type': "oldPrice"}) else 'No Original Price Available'
            description = soup.find('div', class_='product attribute overview').text.strip() if soup.find('div', class_='product attribute overview') else 'No Description Available'
            details = soup.find('div', class_='product attribute description').text.strip() if soup.find('div', class_='product attribute description') else 'No Details Available'
            tag = '' 
            status = '' 
            remarks = soup.find('div', class_='product-info-stock-sku').text.strip() if soup.find('div', class_='product-info-stock-sku') else 'No Remarks Available'
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            data = {
                'Link': product_link,
                'Name': product_name,
                'Image': img_url,
                'Category': category,
                'Subcategory': subcategory,
                'Color': product_color,
                'Current Price': current_price,
                'Original Price': original_price,
                'Description': description,
                'Details': details,
                'Tag': tag,
                'Status': status,
                'Remarks': remarks,
                'Timestamp': timestamp
            }
            return data 
        
        else:
            if response.status_code == 429: 
                # print(f"Failed to retrieve the webpage: {url}. Status code: {response.status_code}")
                return scrape_data(url)
            else:
                return None
                    
    except requests.exceptions.RequestException as e:
        # print(f"Failed to retrieve the webpage: {url}. Error: {e}")
        return None

# Use ThreadPoolExecutor to scrape data in parallel
with ThreadPoolExecutor(max_workers=10) as executor:
    future_to_url = {executor.submit(scrape_data, url): url for url in all_links} 
    for future in as_completed(future_to_url):
        result = future.result()
        if result:
            temp_ws = pd.DataFrame([result])
            ws = pd.concat([ws, temp_ws], ignore_index=True)

# Clean up the DataFrame
ws['Remarks'] = ws['Remarks'].apply(lambda x: ' '.join(x.split()).strip() if x else x)
ws['Details'] = ws['Details'].apply(lambda x: x.replace('\n', ',') if x else x) 


ws.to_csv('proxy_scrap.csv', index=False)  
ws