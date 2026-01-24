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

import asyncio
import logging
import sys
from typing import Any

from xrtm.forecast.core.config.inference import HFConfig
from xrtm.forecast.providers.inference.hf_provider import HuggingFaceProvider

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("VERIFY_STREAM")


# Mock classes to simulate behavior if dependencies missing
class MockTokenIterator:
    def __iter__(self):
        yield "Hello"
        yield " World"
        yield "!"


async def verify_streaming_provider(provider_name: str, provider: Any):
    r"""Verification loop for a provider's streaming implementation."""
    logger.info(f"--- Verifying Streaming for {provider_name} ---")

    chunks = []
    try:
        # stream() returns an AsyncIterable
        async for chunk in provider.stream("Test prompt"):
            chunks.append(chunk)

            # Verify Standardization
            # Expected format: {"contentBlockDelta": {"delta": {"text": "..."}}}
            if not isinstance(chunk, dict):
                logger.error(f"❌ {provider_name}: Chunk is not a dict: {type(chunk)}")
                return False

            if "contentBlockDelta" in chunk:
                delta = chunk["contentBlockDelta"]
                if "delta" not in delta or "text" not in delta["delta"]:
                    logger.error(f"❌ {provider_name}: Invalid delta structure: {chunk}")
                    return False

            elif "messageStop" in chunk:
                pass  # Valid stop signal
            else:
                logger.error(f"❌ {provider_name}: Unknown chunk format: {chunk}")
                return False

        logger.info(f"✅ {provider_name}: Received {len(chunks)} valid chunks.")
        return True

    except NotImplementedError:
        logger.warning(f"⚠️ {provider_name}: Streaming not implemented.")
        return False
    except Exception as e:
        logger.error(f"❌ {provider_name}: Streaming failed with error: {e}")
        return False


async def main():
    # 1. Setup Local Provider (HuggingFace)
    # We use a tiny model for speed
    config = HFConfig(model_id="sshleifer/tiny-gpt2")
    try:
        hf_provider = HuggingFaceProvider(config=config)
    except ImportError:
        logger.error("Skipping HF verification (dependencies missing)")
        hf_provider = None

    results = []
    if hf_provider:
        success = await verify_streaming_provider("HuggingFace", hf_provider)
        results.append(success)

    if all(results) and len(results) > 0:
        logger.info("🎉 All Streaming Verifications PASSED")
        sys.exit(0)
    else:
        logger.error("💥 Some Streaming Verifications FAILED")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
