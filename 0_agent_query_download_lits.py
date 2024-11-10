from RetroSynAgent.pdfprocessor import PDFProcessor
from RetroSynAgent.pdfdownloader import PDFDownloader


if __name__ == '__main__':
    material = 'Polyimide'
    pdf_folder_name = 'literature_pdfs_' + material
    result_folder_name = 'results_' + material
    result_json_name = 'gpt_results'
    # [1] query literatures & download
    pdf_folder_name2 = pdf_folder_name + '_test'
    downloader = PDFDownloader(material, pdf_folder_name=pdf_folder_name2, num_results=50, n_thread=3)
    pdf_name_list = downloader.main()
    print(f'successfully downloaded {len(pdf_name_list)} pdfs for {material}')
    # extract infos from pdf about reactiosn by llm
    pdf_processor = PDFProcessor(pdf_folder_name=pdf_folder_name, result_folder_name=result_folder_name,
                                 result_json_name=result_json_name)
    pdf_processor.load_existing_results()
    reactions_text = pdf_processor.process_pdfs_txt(save_batch_size=1)
    # pdf_processor.process_pdfs_img_txt(save_batch_size=1)
    # get 'results_Polyimide/gpt_results.json'

