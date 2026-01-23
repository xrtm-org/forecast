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

r"""Demonstration of the Inference Cache for LLM response caching.

This example shows how to use the InferenceCache to reduce API costs and
latency by caching LLM responses based on content-addressable hashing.

Run:
    python examples/core/run_cache_demo.py
"""

from forecast.core.cache import InferenceCache


def main():
    """Demonstrate inference cache usage."""
    print("=" * 60)
    print("Inference Cache Demo")
    print("=" * 60)

    # Initialize cache
    cache = InferenceCache(db_path=".cache/demo_inference.db")
    print(f"\n1. Initialized cache at: {cache.db_path}")

    # Compute cache key
    model_id = "gemini-pro"
    prompt = "What is the capital of France?"
    temperature = 0.0

    key = cache.compute_key(model_id, prompt, temperature=temperature)
    print(f"\n2. Computed cache key: {key[:32]}...")

    # Check if cached (should be miss on first run)
    cached_result = cache.get(key)
    if cached_result:
        print(f"\n3. Cache HIT: {cached_result}")
    else:
        print("\n3. Cache MISS - Would call LLM API here")

        # Simulate LLM response
        simulated_response = "The capital of France is Paris."

        # Store in cache
        cache.set(key, simulated_response, {"model": model_id, "tokens": 8})
        print(f"   Stored response in cache: {simulated_response}")

    # Demonstrate cache hit
    print("\n4. Second lookup (should be cache hit):")
    cached_result = cache.get(key)
    print(f"   Cache HIT: {cached_result}")

    # Show whitespace normalization
    print("\n5. Whitespace normalization demo:")
    key_with_spaces = cache.compute_key(model_id, "What   is  the  capital   of  France?", temperature=temperature)
    print(f"   Original key:   {key[:32]}...")
    print(f"   With spaces:    {key_with_spaces[:32]}...")
    print(f"   Keys match: {key == key_with_spaces}")

    # Show cache statistics
    print("\n6. Cache statistics:")
    stats = cache.stats()
    for k, v in stats.items():
        print(f"   {k}: {v}")

    # Cleanup
    cache.close()
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
