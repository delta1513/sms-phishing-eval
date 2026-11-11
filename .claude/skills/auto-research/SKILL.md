---
name: auto-research
description: Automatically improve the decision model parameters against the dataset. Only trigger this if explicitly asked to perform auto-research.
---

# The task

Your task is to trial and implement improvements to this system to reach the specified goal while remaining within the constraints specified below.

# The system

This repository is an evaluation framework for a decision model. You may run eval.py to perform the evaluation and collect results for you to use.

Running that file may re-run all evaluations at cloudflare, and this can take some time. After the file is run, you will get a set of logs, and also a confusion matrix to tell you how well the model and its instructions performed. 

# The goal

Your goal is to increase the precision metric of this system.

# The constraints

You should work to achieve the goal without breaking these constraints:
1. Recall must not drop below 100%
2. You may only alter the prompt.md file, instructions.md file, and then your own results file "results.txt" which must contain the verbatim results for precision and recall.
3. Unless specified by the user, you may only make at most 3 evaluation attempts to try and improve the system

# Some things to know

- If the results.txt file is non-existent, run an evaluation and make it.
- After you have made an improvement, commit and push your changes to the main branch.
