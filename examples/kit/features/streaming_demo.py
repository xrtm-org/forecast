import asyncio
import logging
import sys
from typing import Any

from forecast.core.config.inference import HFConfig
from forecast.providers.inference.hf_provider import HuggingFaceProvider

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
