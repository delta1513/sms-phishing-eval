# SMS Phishing Eval

This is a hobby-project that I'm using to learn how decision models work, how to create an eval framework for them, and experiment with auto-research.

In this project, I will be getting a decision model to evaluate whether or not a particular SMS message is a scam or not.

# What is a decision model?

A decision model is an AI model that takes natural language or multimedia inputs, and produces a scalar probability in response to a natural language question referring to said input.

In this case, it looks something like this:

- State: `Here is an SMS message: "Hello world!".`
- Instruction: `Is this a scam message?`
- Output from the model: `0.123` (very likely not a scam)

# What is an eval framework?

Before you start using AI in a production product that faces users, you may want to make sure that what it is doing is actually the right thing. In the case of a decision model, this is really easy to explain because the decision model is either objectively wrong or objectively right - there's no in-between.

For my eval framework, I build a [confusion matrix](), then set some constraints (eg, maximise precision while keeping recall at 100%).

# What is auto-research?

This is just a fancy term for letting an AI coding agent progressively improve a particular metric. All I have to do is:
1. Give it mutability constraints (eg, "you may only edit the prompt file and instruction file)
2. Tell it to keep doing it until the constraint is achieved.

If I wanted to get sophisticated, I could also write a skill and a bash for-loop to send the agent through a finite number of trials.

# AI disclaimer

I don't usually stick these on my projects, but in this case, I wanted to brag that the code was written solely by hand, and reviewed (but not altered) by AI.

The only thing that my coding agents have touched is basically everything outside eval.py.

*I just wanted to make sure I still had my "python-by-hand" skills that I thought I lost over the last few years :P*
