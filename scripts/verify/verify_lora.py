# coding=utf-8
# Copyright 2026 XRTM Team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import sys

from peft import LoraConfig, TaskType, get_peft_model
from transformers import AutoModelForCausalLM

print(f"Python: {sys.executable}")
print(f"Path: {sys.path}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_lora():
    model_name = "HuggingFaceTB/SmolLM2-135M"
    logger.info(f"Loading {model_name}...")
    try:
        model = AutoModelForCausalLM.from_pretrained(model_name)
    except Exception as e:
        logger.error(f"Failed to load base model: {e}")
        return

    logger.info("Applying LoRA config...")
    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=16,
        lora_alpha=32,
        lora_dropout=0.1,
        bias="none",
    )

    try:
        model = get_peft_model(model, peft_config)
        logger.info("LoRA applied successfully.")

        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        all_params = sum(p.numel() for p in model.parameters())
        logger.info(
            f"Trainable params: {trainable_params:,} "
            f"({100 * trainable_params / all_params:.2f}% of {all_params/1e6:.1f}M)"
        )
        print("VERIFICATION_SUCCESS")
    except Exception as e:
        logger.error(f"Failed to apply LoRA: {e}")

if __name__ == "__main__":
    verify_lora()
