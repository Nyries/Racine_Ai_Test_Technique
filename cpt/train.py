import argparse
import random

import numpy as np
import torch
import yaml
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_loss_curve(log_history: list, output_path: str) -> None:
    import matplotlib.pyplot as plt

    train_steps = [(e["step"], e["loss"]) for e in log_history if "loss" in e]
    eval_steps = [(e["step"], e["eval_loss"]) for e in log_history if "eval_loss" in e]

    if not train_steps:
        print("No loss data to plot.")
        return

    fig, ax = plt.subplots(figsize=(10, 5))
    xs, ys = zip(*train_steps)
    ax.plot(xs, ys, label="train loss", alpha=0.8)
    if eval_steps:
        xs_e, ys_e = zip(*eval_steps)
        ax.plot(xs_e, ys_e, label="eval loss", marker="o", markersize=4)
    ax.set_xlabel("Step")
    ax.set_ylabel("Cross-entropy loss")
    ax.set_title("CPT — Qwen3.5-0.8B-Base on Middle East geopolitics corpus")
    ax.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Loss curve saved to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument(
        "--push-to-hub",
        metavar="MODEL_ID",
        default=None,
        help="push trained model to HuggingFace Hub, e.g. 'your-username/qwen3.5-0.8b-middle-east-cpt'",
    )
    parser.add_argument("--private", action="store_true", help="make the HF model private")
    args = parser.parse_args()

    cfg = load_config(args.config)
    model_cfg = cfg["model"]
    data_cfg = cfg["data"]
    train_cfg = cfg["training"]

    set_seed(train_cfg["seed"])

    print(f"Loading tokenizer: {model_cfg['name']}")
    tokenizer = AutoTokenizer.from_pretrained(model_cfg["name"])
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print(f"Loading model: {model_cfg['name']}")
    dtype = torch.bfloat16 if train_cfg["bf16"] else torch.float32
    model = AutoModelForCausalLM.from_pretrained(model_cfg["name"], torch_dtype=dtype)
    if train_cfg.get("gradient_checkpointing"):
        model.gradient_checkpointing_enable()

    print("Loading and tokenizing dataset...")
    ds = load_dataset(
        "json",
        data_files={"train": data_cfg["train_file"], "eval": data_cfg["eval_file"]},
    )
    max_len = data_cfg["max_seq_length"]

    def tokenize(batch):
        return tokenizer(
            batch["text"],
            truncation=True,
            max_length=max_len,
            padding=False,
        )

    tokenized = ds.map(tokenize, batched=True, remove_columns=["text"])
    print(f"  train: {len(tokenized['train'])} sequences")
    print(f"  eval : {len(tokenized['eval'])} sequences")

    collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    training_args = TrainingArguments(
        output_dir=train_cfg["output_dir"],
        num_train_epochs=train_cfg["num_train_epochs"],
        per_device_train_batch_size=train_cfg["per_device_train_batch_size"],
        per_device_eval_batch_size=train_cfg["per_device_eval_batch_size"],
        gradient_accumulation_steps=train_cfg["gradient_accumulation_steps"],
        learning_rate=train_cfg["learning_rate"],
        lr_scheduler_type=train_cfg["lr_scheduler_type"],
        warmup_steps=train_cfg["warmup_steps"],
        weight_decay=train_cfg["weight_decay"],
        bf16=train_cfg["bf16"],
        logging_steps=train_cfg["logging_steps"],
        eval_strategy="steps",
        eval_steps=train_cfg["eval_steps"],
        save_steps=train_cfg["save_steps"],
        save_total_limit=train_cfg["save_total_limit"],
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        report_to="none",
        seed=train_cfg["seed"],
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["eval"],
        data_collator=collator,
    )

    print("Starting training...")
    trainer.train()

    final_dir = train_cfg["output_dir"] + "/final"
    trainer.save_model(final_dir)
    tokenizer.save_pretrained(final_dir)
    print(f"Model saved to {final_dir}")

    save_loss_curve(trainer.state.log_history, train_cfg["loss_curve_png"])

    if args.push_to_hub:
        print(f"\nPushing model to HuggingFace Hub: {args.push_to_hub}")
        trainer.model.push_to_hub(args.push_to_hub, private=args.private)
        tokenizer.push_to_hub(args.push_to_hub, private=args.private)
        print(f"Model pushed: https://huggingface.co/{args.push_to_hub}")


if __name__ == "__main__":
    main()
