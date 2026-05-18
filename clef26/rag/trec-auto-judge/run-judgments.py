#!/usr/bin/env python3
from pathlib import Path
from tira.rest_api_client import Client
import os


JUDGES = {
    "prefnugget-queryonly": {
        "image": "ghcr.io/mam10eks/prefnugget-starterkit/judge:0.0.1",
        "command": "auto-judge run --workflow /auto-judge/judges/queryonly/workflow.yml --rag-responses $inputDataset/runs/*/ --rag-topics $inputDataset/topics/*.jsonl --out-dir $outputDir",
        "llm": True,
    },
    "prefnugget-grounded": {
        "image": "ghcr.io/mam10eks/prefnugget-starterkit/judge:0.0.1",
        "command": "auto-judge run --workflow /auto-judge/judges/grounded/workflow.yml --rag-responses $inputDataset/runs/*/ --rag-topics $inputDataset/topics/*.jsonl --out-dir $outputDir",
        "llm": True,
    },
    "ir-axioms": {
        "image": "mam10eks/trec-auto-judge-base:ir-axioms-0.0.1",
        "command": "echo 127.0.0.1\ localhost >> /etc/hosts; auto-judge run --workflow /auto-judge/judges/ir_axioms/workflow.yml --rag-responses $inputDataset/runs/*/ --rag-topics $inputDataset/topics/*.jsonl --out-dir $outputDir",
        "llm": False,
        "mount_hf_model": ["facebook/fasttext-en-vectors"],
    }
}


def run_llm_judge(image, command, data_dir, out_dir):
    tira = Client().local_execution
    assert "CACHE_DIR" not in os.environ
    os.environ["CACHE_DIR"] = "/cache_dir"
    tira.run(
        image=image,
        command=command,
        input_dir=data_dir,
        output_dir=out_dir / "results",
        forward_environment_variables=["OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL", "CACHE_DIR"],
        allow_network=True,
        additional_volumes=[f"{out_dir / 'cache'}:/cache_dir:rw"],
    )
    del os.environ["CACHE_DIR"]


def run_no_llm_judge(image, command, mount_hf_model, data_dir, out_dir):
    tira = Client().local_execution
    hf_models = None

    if mount_hf_model:
        from tira.io_utils import huggingface_model_mounts

        hf_models = huggingface_model_mounts(mount_hf_model)
        hf_models = [k + ":" + v["bind"] + ":" + v["mode"] for k, v in hf_models.items()]

    tira.run(
        image=image,
        command=command,
        input_dir=data_dir,
        output_dir=out_dir / "results",
        additional_volumes=hf_models,
    )


def main(data_dir, judge, out_dir):
    judge = JUDGES[judge]
    if judge["llm"]:
        run_llm_judge(judge["image"], judge["command"], data_dir, out_dir / os.environ["OPENAI_MODEL"])
    else:
        run_no_llm_judge(judge["image"], judge["command"], judge.get("mount_hf_model"), data_dir, out_dir)


if __name__ == '__main__':
    # main data
    out_dir = Path(__file__).parent / "longeval-rag-evaluations"
    input_dir = Path(Path(__file__).parent) / "longeval-rag"

# for fast tests
#    out_dir = Path(__file__).parent / "kiddy-rag-evaluations"
#    input_dir = Path(Path(__file__).parent) / "kiddy-rag"
    for approach in JUDGES.keys():
        main(input_dir, approach, out_dir / approach)
