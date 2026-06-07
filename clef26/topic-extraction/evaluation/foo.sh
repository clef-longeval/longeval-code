#!/usr/bin/env bash

set -e

for i in $(ls /home/maik/workspace/longeval-26-evaluation/task-2-submissions/outputs-flat)
do
    ./evaluate.py predictions-on-topic longeval-sci-2026/clef-2026/sci $i clef-longeval-2026
done

