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
import os
import sqlite3

from forecast.providers.tools import PandasSkill, SQLSkill


async def run_data_analysis():
    r"""
    Demonstrates institutional data analysis by querying a SQLite database
    and performing statistical analysis with Pandas.
    """
    print("--- Enterprise Data Example ---")
    db_path = "enterprise_data.db"

    # 1. Setup a dummy database
    print(f"Setting up {db_path}...")
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE inventory (id INTEGER, warehouse TEXT, value REAL)")
    conn.execute("INSERT INTO inventory VALUES (1, 'North', 50000.0), (2, 'South', 75000.0), (3, 'North', 25000.0)")
    conn.commit()
    conn.close()

    # 2. Instantiate Skills
    sql = SQLSkill(db_url=db_path)
    pd_skill = PandasSkill()

    # 3. Query Data
    print("Querying inventory data...")
    data = await sql.run(query="SELECT * FROM inventory")
    print(f"Retrieved {len(data)} records.")

    # 4. Analyze with Pandas
    print("Calculating statistics...")
    stats = await pd_skill.run(data=data, operation="describe")
    total_val = await pd_skill.run(data=data, operation="sum", column="value")

    print("\n--- Results ---")
    print(f"Total Portfolio Value: ${total_val:,.2f}")
    print(f"Stats: {stats['value']}")

    # Cleanup
    os.remove(db_path)


if __name__ == "__main__":
    asyncio.run(run_data_analysis())
