#!/usr/bin/env python3
from pathlib import Path

import xml.etree.ElementTree as ET
import click
from ir_datasets_longeval import load
import os
from tqdm import tqdm
import json_repair

# We use the tracker to monitor resource consumption etc. of the indexing and retrieval.
# The tracking is optional, i.e., you can remove it or switch to an alternative such as repro_eval.
from tirex_tracker import tracking, ExportFormat


def get_llm_response(request):
    from openai import OpenAI as cli
    messages = []
    messages.append({"role": "user", "content": request})

    output = cli().chat.completions.create(model=os.environ["OPENAI_MODEL"], messages=messages)

    return output.choices[0].message.to_dict()


def build_prompt(query):
    return f"""You are employed as relevance assessor at NIST in the Information Retrieval Group working at TREC. You are already pensioned and have worked as intelligence officer for over 40 years, now you still help because you are really passionate. You will help to evaluate academic search engines for which you will be given a query that was submitted to an search engine that you interpret to create a well formalized standard TREC-style topic. Please respond exactly in json format with two fields, "narrative" that contains a standard TREC-style narrative (describing what documents will be relevant or not) and a "description" that contains a standard TREC-style description (describing what the user had in mind). Respond only with one valid json.\n\nThe query is: "{query}"""


def to_topic(query, llm_response):
    ret = ET.Element("topic")
    ret.attrib["number"] = query.query_id
    q = ET.SubElement(ret, "query")
    q.text = query.default_text()

    llm_response = json_repair.loads(llm_response["content"])

    d = ET.SubElement(ret, "description")
    d.text = llm_response["description"]

    n = ET.SubElement(ret, "narrative")
    n.text = llm_response["narrative"]

    return ret


def process_queries(queries, output):
    ret = ET.Element("topics")

    with tracking(export_file_path=output/"ir-metadata.yml", export_format=ExportFormat.IR_METADATA):
        for query in tqdm(queries.values()):
            request = build_prompt(query.default_text())
            response = get_llm_response(request)
            ret.append(to_topic(query, response))

    with open(output/"topics.xml", "w") as f:
        ET.indent(ret, space="  ")
        f.write(ET.tostring(ret, encoding="unicode"))


def all_required_environment_variables_are_set():
    required_env_to_description = {
        "OPENAI_API_KEY": "The OPENAI_API_KEY environment variable is required. Please run something like 'export OPENAI_API_KEY=...'",
        "OPENAI_BASE_URL": "The OPENAI_BASE_URL environment variable is required. Please run something like 'export OPENAI_BASE_URL=https://openrouter.ai/api/v1'",
        "OPENAI_MODEL": "The OPENAI_MODEL environment variable is required. Please run something like 'export OPENAI_MODEL=mistralai/mistral-small-3.1-24b-instruct:free'",
    }
    errors = []

    for k, v in required_env_to_description.items():
        if k not in os.environ:
            errors += ["\n\n\t- " + v]
    
    if len(errors) > 0:
        print("Error: The LLM Endpoint is not configured." + ("".join(errors)))

    return len(errors) == 0


def load_all_queries(dataset):
    ret = {}
    ir_dataset = load(dataset)
    sub_collections = [ir_dataset] if not ir_dataset.get_datasets() else ir_dataset.get_datasets()

    for snapshot in sub_collections:
        for q in snapshot.queries_iter():
            ret[q.query_id] = q

    return ret


@click.command()
@click.option("--dataset", type=str, help="The dataset id or a local directory.")
@click.option("--output", type=Path, required=True, help="The output directory.")
def main(dataset, output):
    if not all_required_environment_variables_are_set():
        exit(1)
        return

    all_queries = load_all_queries(dataset)
    process_queries(all_queries, output)


if __name__ == "__main__":
    main()
