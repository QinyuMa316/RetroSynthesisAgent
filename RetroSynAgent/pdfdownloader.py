import os
import re
import requests
from loguru import logger
import json
import random
import glob
import difflib
from concurrent.futures import ThreadPoolExecutor, as_completed
from scholarly import scholarly
from dotenv import load_dotenv
import os

class PDFDownloader:
    def __init__(self, material, pdf_folder_name ,num_results = 5, n_thread=3):
        self.pdf_folder_name = pdf_folder_name
        self.no_download_link_json_name = 'no_download_link_titles.json'
        self.query = material + ' AND synthesis'
        self.title_list = self.get_scholar_titles(self.query, num_results)
        self.n_thread = n_thread
        self.url = 'https://www.sci-hub.se/'
        self.no_download_link_titles = self.read_data_from_json(self.no_download_link_json_name) if os.path.exists(
            self.no_download_link_json_name) else []

        load_dotenv()
        headers_dict = os.getenv("HEADERS")
        self.headers = json.loads(headers_dict)
        cookies_dict = os.getenv("COOKIES")
        self.cookies = json.loads(cookies_dict)

    # version2
    def get_scholar_titles(self, query, num_results, citations=0):
        search_query = scholarly.search_pubs(query)
        title_list = []
        count = 0
        for i in range(1000000):
            try:
                pub = next(search_query)
                if pub['num_citations'] > citations:
                    title = pub['bib']['title']
                    num_citations = int(pub['num_citations'])
                    # if not 'negative' in title:
                    title_list.append(title)
                    count += 1
                    # print(f'{count}: {title}: {num_citations}')
                    if count == num_results:
                        break
            except StopIteration:
                break
            except KeyError:
                continue
        # return entries
        return title_list

    def read_data_from_json(self, filename):
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data

    def save_data_as_json(self, filename, data):
        with open(filename, 'w') as json_file:
            json.dump(data, json_file, indent=4)
        print(f'{filename} saved!')

    def get_pdf_files(self):
        pdf_files = glob.glob(os.path.join(self.pdf_folder_name, '*.pdf'))
        return [os.path.basename(file) for file in pdf_files]

    def check_pdf_existence(self, target_pdf_name, pdf_name_list):
        similarity_threshold = 0.9
        for pdf_name in pdf_name_list:
            similarity = difflib.SequenceMatcher(None, target_pdf_name, pdf_name).ratio()
            if similarity > similarity_threshold:
                return True
        return False

    def title_href(self, title):
        data = {"request": str(title)}
        try:
            res = requests.post(self.url, headers=self.headers, data=data, cookies=self.cookies)
            _href = re.findall("""<button onclick = "location.href='(.*?)'">&darr;""", res.text)
            if _href:
                _href = _href[0]
                if 'sci-hub' not in _href:
                    download_href = "https://sci-hub.se" + _href
                else:
                    download_href = "https:" + _href

                return download_href

            elif '<p id = "smile">:(</p>' in res.text:
                # logger.error(f"No download link for {title} in sci-hub")
                self.no_download_link_titles.append(title)
                self.save_data_as_json(self.no_download_link_json_name, self.no_download_link_titles)
                return None
            else:
                # logger.error(f"Failed to get download link for title: {title}, status_code: {res.status_code}")
                return None
        except Exception as e:
            # logger.error(e)
            return None

    def get_download_pdf(self, href, title):
        try:
            res = requests.get(href, headers=self.headers, cookies=self.cookies)
            if res.status_code == 200:
                file_name = f"{str(title).replace(':', '').replace('/', '').replace('*', '').replace('|', '').replace('?', '')}.pdf"
                file_path = os.path.join(os.getcwd(), self.pdf_folder_name, file_name)
                if res.headers.get('Content-Type') == 'application/pdf':
                    with open(file_path, 'wb') as f:
                        f.write(res.content)
                        logger.info(f"{file_name} successfully saved!")
                else:
                    logger.error(f"{file_name} is invalid pdf file")
            else:
                logger.error(f"Failed to download pdf for {title}, status code: {res.status_code}")
                if res.status_code == 404:
                    self.no_download_link_titles.append(title)
                    self.save_data_as_json(self.no_download_link_json_name, self.no_download_link_titles)
        except Exception as e:
            logger.error(e)

    def download_task(self, title):
        href = self.title_href(title)
        if href:
            self.get_download_pdf(href, title)

    def download_pdfs(self, titles):
        with ThreadPoolExecutor(max_workers=self.n_thread) as executor:
            futures = [executor.submit(self.download_task, title) for title in titles]
            for future in as_completed(futures):
                future.result()

    def filter_titles(self, titles):
        pdf_file_list = self.get_pdf_files()
        pdf_name_list = [pdf.split('.pdf')[0] for pdf in pdf_file_list]

        titles_filtered1 = [title for title in titles if not self.check_pdf_existence(title, pdf_name_list)]
        titles_filtered2 = [title for title in titles_filtered1 if
                            not self.check_pdf_existence(title, self.no_download_link_titles)]
        return titles_filtered2

    def main(self):
        os.makedirs(self.pdf_folder_name, exist_ok=True)
        titles_filtered = self.filter_titles(self.title_list)

        # print(f'Total number of titles: {len(self.title_list)}, '
        #       f'{len(self.get_pdf_files())} have been downloaded, '
        #       f'{len(self.no_download_link_titles)} do not have download links, '
        #       f'{len(titles_filtered)} are planned to be downloaded.')

        random.shuffle(titles_filtered)
        self.download_pdfs(titles_filtered)


        download_pdf_filename_list = self.get_pdf_files()
        # print(f'finished downloading, '
        #       f'{len(download_pdf_filename_list)} have been downloaded, '
        #       f'{len(self.no_download_link_titles)} do not have download links, '
        #       f'{len(self.title_list)-len(self.get_pdf_files())-len(self.no_download_link_titles)} failed to be downloaded.')
        # version2
        return download_pdf_filename_list


