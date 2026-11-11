import hashlib
import json
import logging
import os
import pickle
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from time import sleep

import requests

ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
AUTH_TOKEN = os.environ.get("CLOUDFLARE_AUTH_TOKEN")

logging.basicConfig(
    level=logging.DEBUG,
    stream=sys.stdout,
    format="%(asctime)s [%(levelname)s] - %(message)s",
)


@dataclass
class Result:
    data_id: str
    prediction: bool
    actual: bool
    input_tokens: int
    output_tokens: int

    @property
    def is_true_positive(self):
        return self.prediction and self.actual

    @property
    def is_true_negative(self):
        return not (self.prediction or self.actual)

    @property
    def is_false_positive(self):
        return self.prediction and not self.actual

    @property
    def is_false_negative(self):
        return not self.prediction and self.actual

    @property
    def confusion_result(self):
        if self.is_true_positive:
            return "TP"
        if self.is_true_negative:
            return "TN"
        if self.is_false_positive:
            return "FP"
        if self.is_false_negative:
            return "FN"

    def to_dict(self):
        return {
            "data_id": self.data_id,
            "prediction": self.prediction,
            "actual": self.actual,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "is_true_positive": self.is_true_positive,
            "is_true_negative": self.is_true_negative,
            "is_false_positive": self.is_false_positive,
            "is_false_negative": self.is_false_negative,
            "confusion_result": self.confusion_result,
        }

    def __hash__(self):
        return (
            hash(self.data_id)
            + hash(self.prediction)
            + hash(self.actual)
            + hash(self.input_tokens)
            + hash(self.output_tokens)
        )


@dataclass
class Sms:
    id: str
    label: str
    text: str

    @property
    def is_scam(self):
        return self.label == "scam"

    def __hash__(self):
        return hash(self.id)


class ConfusionMatrix:
    def __init__(self, data: tuple[Sms], results: list[Result]):
        self.true_positive: int = len(
            list(filter(lambda x: x.is_true_positive, results))
        )
        self.true_negative: int = len(
            list(filter(lambda x: x.is_true_negative, results))
        )
        self.false_positive: int = len(
            list(filter(lambda x: x.is_false_positive, results))
        )
        self.false_negative: int = len(
            list(filter(lambda x: x.is_false_negative, results))
        )
        self.sample_size: int = len(data)
        self.positive_sample_size: int = len(list(filter(lambda x: x.is_scam, data)))
        self.negative_sample_size: int = len(
            list(filter(lambda x: not x.is_scam, data))
        )

    @property
    def precision(self):
        return self.true_positive / (self.true_positive + self.false_positive)

    @property
    def recall(self):
        return self.true_positive / self.positive_sample_size

    @property
    def false_negative_rate(self):
        return 1 - self.recall

    def __repr__(self):
        return """
            | PP | PN |
        ----+----+----+----
          P | {} | {} |
        ----+----+----+----
          N | {} | {} |
        ----+----+----+----
            |    |    |
        
        Precision: {}
        Recall: {}
        False Negative Rate: {}
        """.format(
            self.true_positive,
            self.false_negative,
            self.false_positive,
            self.true_negative,
            self.precision,
            self.recall,
            self.false_negative_rate,
        )


def get_prompt():
    with open("prompt.md", "r") as prompt_file:
        prompt = prompt_file.read()
        return prompt


def get_instructions():
    with open("instructions.md", "r") as instructions_file:
        instructions = instructions_file.read()
        return instructions


def get_sms_data():
    with open("sms-samples/all_samples.json", "r") as sms_file:
        return json.load(sms_file)


def get_sms_data_hash():
    with open("sms-samples/all_samples.json", "rb") as sms_file:
        return hashlib.file_digest(sms_file, "sha1").hexdigest()


def debug_dump_results(results: list[Result]):
    for result in results:
        logging.debug(
            "RESULT %(data_id)s %(prediction)s %(actual)s %(confusion_result)s",
            result.to_dict(),
        )


def get_cache_hash(prompt: str, instructions: str):
    return hash(get_sms_data_hash()) + hash(prompt) + hash(instructions)


def cache_results(results: list[Result], hash: str):
    with open(f"debug_results_{hash}.pickle", "wb") as debug_file:
        pickle.dump(results, debug_file)


def access_cache(hash: str) -> list[Result] | None:
    if Path(f"debug_results_{hash}.pickle").exists():
        with open(f"debug_results_{hash}.pickle", "rb") as debug_file:
            return pickle.load(debug_file)


def run_clef_for_data(sms_data: tuple[Sms], prompt: str, instructions: str):
    results = set()

    for sms_obj in sms_data:
        payload = {
            "model": "clef-flash",
            "state": f"{prompt}{sms_obj.text}",
            "questions": {
                "scam": {
                    "type": "noul",
                    "instructions": f"{instructions}",
                },
            },
        }

        logging.debug("Clef payload: %s", payload)

        request_success = 0
        attempts = 0

        while not request_success:
            response = requests.post(
                f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/@cf/cloudflare/clef-flash",
                headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
                json=payload,
            )

            attempts += 1
            if request_success := response.status_code == 200:
                response_json = response.json()
                request_success &= response_json["success"]

            if not request_success:
                logging.error(
                    "Received HTTP %s from cloudflare with response %s",
                    response.status_code,
                    response.text,
                )

                if attempts > 3:
                    logging.critical("Failed to call clef. Quitting...")
                    sys.exit(1)

                logging.info("Retrying request. Attempt number: %s", attempts + 1)
                sleep(2**attempts)

        logging.debug("Cloudflare Clef Response: %s", response_json)

        result = Result(
            data_id=sms_obj.id,
            prediction=response_json["result"]["answers"]["scam"]["noul"] > 0.5,
            actual=sms_obj.is_scam,
            input_tokens=response_json["result"]["usage"]["input_tokens"],
            output_tokens=response_json["result"]["usage"]["output_tokens"],
        )

        results.add(result)

    return results


def run_eval():
    sms_data = list(Sms(**sms) for sms in get_sms_data())
    prompt = get_prompt()
    instructions = get_instructions()
    experiment_hash = get_cache_hash(prompt, instructions)

    if cache := access_cache(experiment_hash):
        results = cache
    else:
        results = run_clef_for_data(sms_data, prompt, instructions)

    debug_dump_results(results)
    cache_results(results, experiment_hash)

    confusion_matrix = ConfusionMatrix(sms_data, results)

    print(confusion_matrix)

    print("Input tokens used: {}".format(sum(r.input_tokens for r in results)))
    print("Output tokens used: {}".format(sum(r.output_tokens for r in results)))


run_eval()
