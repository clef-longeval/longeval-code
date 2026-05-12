#!/usr/bin/env python3
from pathlib import Path
from tira.rest_api_client import Client
import os
JUDGES = {
    "prefnugget-queryonly": {
        "image": "ghcr.io/mam10eks/prefnugget-starterkit/judge:0.0.1",
        "command": "auto-judge run --workflow /auto-judge/judges/queryonly/workflow.yml --rag-responses $inputDataset/runs/*/ --rag-topics $inputDataset/topics/*.jsonl --out-dir $outputDir",
    }
}


def main(data_dir, judge, out_dir):
    tira = Client().local_execution
    assert "CACHE_DIR" not in os.environ
    os.environ["CACHE_DIR"] = "/cache_dir"
    tira.run(
        image=JUDGES[judge]["image"],
        command=JUDGES[judge]["command"],
        input_dir=data_dir,
        output_dir=out_dir / "results",
        forward_environment_variables=["OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL", "CACHE_DIR"],
        allow_network=True,
        additional_volumes=[f"{out_dir / 'cache'}:/cache_dir:rw"],
    )
    del os.environ["CACHE_DIR"]


if __name__ == '__main__':
    out_dir = Path(__file__).parent / "longeval-rag-evaluations"
    input_dir = Path(Path(__file__).parent) / "longeval-rag"
    for approach in JUDGES.keys():
        main(input_dir, approach, out_dir / approach / os.environ["OPENAI_MODEL"])
