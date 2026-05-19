from pathlib import Path
import json
import prompts
import gzip
import os
import re
from tqdm import tqdm


class OpenAiGPT():
    def __init__(self, prompt, preamble : str = None, **kwargs) -> None:
        from openai import OpenAI as cli

        self._client = cli() # OpenAI client
        self._prompt = prompt # Outlines prompt

    def generate(self, query : str, passage : str):
        """ Generate a response with a instruct LLM.

        Args:
            query (str): the query
            passage (str): the document

        Returns:
            str: LLM response
        """
        messages = []

        formatted = self._prompt(query, passage)
        messages.append({
            "role": "user",
            "content": formatted
        })

        output = self._client.chat.completions.create(
            model=os.environ["OPENAI_MODEL"],
            messages=messages,
        )
        
        return output.choices[0].message.to_dict()


def read_failsave(file_name):
    with gzip.open(file_name, 'rt') as f:
        for l in f:
            try:
                yield json.loads(l)
            except json.decoder.JSONDecodeError:
                pass



def parse_llm_response(response: str) -> int:
    "This method is from UMBRELA https://github.com/castorini/umbrela/blob/main/src/umbrela/utils/common_utils.py and will be properly cited in the paper."
    response = response.strip().lower()
    valid_res = 1
    answer = ""
    patterns = [
        r'"o"\s*[:-=]?\s*(0|1|2|3)',
        r"\'o\'\s*[:-=]?\s*(0|1|2|3)",
        r"o\s*[:-=]?\s*(0|1|2|3)",
        r'"overall_score"\s*[:-=]?\s*(0|1|2|3)',
        r'"overall"\s*[:-=]?\s*(0|1|2|3)',
        r'"overall score"\s*[:-=]?\s*(0|1|2|3)',
        r'"final score"\s*[:-=]?\s*(0|1|2|3)',
        r'final score\s*[:-=]?\s*(0|1|2|3)',
        r"final score is (0|1|2|3)",
        r'"final_score"\s*[:-=]?\s*(0|1|2|3)',
        r'"score"\s*[:-=]?\s*(0|1|2|3)',
        r'"o_score"\s*[:-=]?\s*(0|1|2|3)',
        r"output score is (0|1|2|3)",
        r"score is (0|1|2|3)",
        r"[a-zA-Z]+\s+is\s+(0|1|2|3)\s",
        r"relevance category\s*[:-=]?\s*(0|1|2|3)",
        r"relevance category\s*[:-=]?\s*(0|1|2|3)",
        r"relevance category is (0|1|2|3)",
        r"it falls into the category (0|1|2|3)",
        r"category\s*(0|1|2|3)",
        r"relevance category (0|1|2|3)",
        r"relevance category for this passage would be (0|1|2|3)",
        r"the relevance category would be (0|1|2|3)",
        r"\n*(0|1|2|3)",
    ]
    for pattern in patterns:
        matched = None
        for m in re.finditer(pattern, response, re.IGNORECASE | re.MULTILINE | re.DOTALL):
            matched = m

        if matched:
            answer = matched.group(1).capitalize()
            break
    if answer == "":
        answer = "0"
        valid_res = 0
        #print(f"Invalid response: {response}")
    return int(answer), valid_res


def run_predictions(input_file: Path, prompt: str, target_file: Path):
    prompt_impl = getattr(prompts, prompt)

    finished_predictions = {}

    with gzip.open(target_file, 'rt') as f:
        for l in f:
            try:
                l = json.loads(l)
                qid, docno = l['query_id'], l['doc_id']

                if qid not in finished_predictions:
                    finished_predictions[qid] = set()
                finished_predictions[qid].add(docno)

            except json.decoder.JSONDecodeError:
                pass
    
    to_predict = []

    with gzip.open(input_file, 'rt') as f:
        for l in f:
            l = json.loads(l)

            if l['query_id'] in finished_predictions and l['doc_id'] in finished_predictions[l['query_id']]:
                continue

            to_predict.append(l)
    
    print(f'I must do {len(to_predict)} predictions for {target_file}.')

    if len(to_predict) == 0:
        return

    llm_impl = OpenAiGPT(prompt_impl)

    with gzip.open(target_file, 'a') as f:
        for i in tqdm(to_predict):
            prediction = llm_impl.generate(query=i['query'], passage=i['text'])
            to_write = json.dumps({'query_id': i['query_id'], 'doc_id': i['doc_id'], 'prediction': prediction}) + '\n'
            f.write(to_write.encode('UTF-8'))
            f.flush()

