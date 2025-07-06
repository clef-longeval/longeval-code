import click
from pathlib import Path
import json
import prompts
import gzip
import llm_via_rest_api
from tqdm import tqdm


@click.command()
@click.option('--output-directory', help='The directory where the outputs should be persisted in jsonl format.', type=Path, default=Path('data'))
@click.option('--prompt', prompt='prompt', help='The prompt to choose.', type=click.Choice(prompts.__all__))
@click.option('--llm-endpoint', prompt='LLM', help='The llm endpoint')
@click.option('--model', prompt='model', help='The model to choose.', type=str)
def run_predictions(output_directory: Path, prompt: str, model: str, llm_endpoint):
    for dataset in DATASETS:
        prompt_impl = getattr(prompts, prompt)
        llm_impl = getattr(llm_via_rest_api, llm)(prompt=prompt_impl, model=model)

        data_dir = output_directory / dataset.replace('/', '-')
        target_file = data_dir / 'predictions' / (llm + '-' + model + '-' + prompt + '.jsonl.gz')

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

        with gzip.open(data_dir / 'inputs.jsonl.gz', 'rt') as f:
            for l in f:
                l = json.loads(l)

                if l['query_id'] in finished_predictions and l['doc_id'] in finished_predictions[l['query_id']]:
                    continue

                to_predict.append(l)
    
        print(f'I must do {len(to_predict)} predictions for {target_file}.')

        if len(to_predict) == 0:
            continue

        with gzip.open(target_file, 'a') as f:
            for i in tqdm(to_predict):
                prediction = llm_impl.generate(query=i['query'], passage=i['text'])
                to_write = json.dumps({'query_id': i['query_id'], 'doc_id': i['doc_id'], 'prediction': prediction}) + '\n'
                f.write(to_write.encode('UTF-8'))
                f.flush()

if __name__ == '__main__':
    run_predictions()
