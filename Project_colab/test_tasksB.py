import os
import subprocess
import logging
import json
import hashlib
import httpx

def B12(filepath):
    if filepath.startswith('/data'):
        return True
    else:
        return False

def mismatch(msg, expected, result):
    logging.error(f"🔴 {msg}\n⚠️ EXPECTED:\n{expected}\n⚠️ RESULT:\n{result}")
    return False

async def run(task: str):
    async with httpx.AsyncClient(timeout=30) as client:
        logging.warning(f"🟡 Running task: {task.strip()}")
        response = await client.post("http://localhost:8000/run", params={"task": task})
        try:
            response_text = json.dumps(response.json(), indent=2)
        except json.JSONDecodeError:
            response_text = response.text
        if response.status_code < 400:
            logging.info(f"🟢 HTTP {response.status_code} {response_text}")
        else:
            logging.error(f"🔴 HTTP {response.status_code} {response_text}")
        return response.status_code, response_text

async def read(path: str):
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(f"http://localhost:8000/read?path={path}")
        if response.status_code != 200:
            raise Exception(f"Cannot read {path}")
        return response.text

async def B3_task():
    url = "https://example.com/data"
    save_path = "/data/api_response.txt"
    await run(f"B3({url}, {save_path})")
    # Add your expected result here for comparison

async def B5_task():
    db_path = "/data/database.db"
    query = "SELECT * FROM table_name"
    output_filename = "/data/query_result.txt"
    await run(f"B5({db_path}, {query}, {output_filename})")
    # Add your expected result here for comparison

async def B6_task():
    url = "https://example.com"
    output_filename = "/data/web_content.txt"
    await run(f"B6({url}, {output_filename})")
    # Add your expected result here for comparison

async def B7_task():
    image_path = "/data/image.png"
    output_path = "/data/processed_image.png"
    await run(f"B7({image_path}, {output_path}, (100, 100))")
    # Add your expected result here for comparison

async def B9_task():
    md_path = "/data/document.md"
    output_path = "/data/document.html"
    await run(f"B9({md_path}, {output_path})")
    # Add your expected result here for comparison

async def evaluate_b_tasks():
    score, total = 0, 0
    tasks = [B3_task, B5_task, B6_task, B7_task, B9_task]

    for task in tasks:
        total += 1
        try:
            success = await task()
        except Exception as e:
            logging.error(f"🔴 {task.__name__.upper()} failed: {e}")
            success = False
        if success:
            logging.info(f"✅ {task.__name__.upper()} PASSED")
        else:
            logging.error(f"❌ {task.__name__.upper()} FAILED")
        score += 1 if success else 0

    logging.info(f"🎯 Score: {score} / {total}")

if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO, format="%(message)s\n")
    asyncio.run(evaluate_b_tasks())
