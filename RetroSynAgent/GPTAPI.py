'''
messages = [
{"role": "system", "content": "xxx"},
{"role": "user", "content": prompt},
{"role": "assistant", "content": response},
]

response = self.client.chat.completions.create(
    model=self.model,
    messages=messages,
    temperature=self.temperature,
)
'''
from openai import OpenAI
from dotenv import load_dotenv
import os
class GPTAPI:
    def __init__(self, model = "gpt-4o", temperature = 0.0):
        # Load environment variables
        load_dotenv()
        self.api_key = os.getenv('API_KEY')
        self.base_url = os.getenv('BASE_URL')
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.model = model
        self.temperature = temperature

    def answer_wo_vision(self, prompt, content=None):
        # Construct message
        messages = [{"role": "system", "content": prompt}]
        if content is not None:
            messages.append({"role": "user", "content": "content:\n" + content})
        # Send request and get response
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        # Extract and return the answer
        answer = response.choices[0].message.content
        return answer


    def answer_wo_vision_txt_list(self, prompt, content_list):
        messages = [{"role": "system", "content": prompt}]
        for content in content_list:
            messages.append({"role": "user", "content": content})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        answer = response.choices[0].message.content
        return answer

    # parse reactions & properties based on pdf to (imgs & txt)
    def answer_w_vision_img_list_txt(self, prompt, base64_img_list, content):
        content_list = []
        content_list.append({"type":"text", "text": "content:\n" + content})
        for base64_img in base64_img_list:
            content_list.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_img}"}})

        messages = [
            # {"role": "system", "content": "Answer the question based on the provided content and images."},
            {"role": "system", "content": prompt},
            {"role": "user", "content": content_list}
        ]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        answer = response.choices[0].message.content
        return answer
