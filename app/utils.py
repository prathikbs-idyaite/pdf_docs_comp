import os
import uuid
import time
import logging
from pathlib import Path


# =====================================================
# CONFIG
# =====================================================

TEMP_DIR = "temp"
MAX_FILE_SIZE_MB = 50   # protect your server


# =====================================================
# TEMP DIRECTORY
# =====================================================

def ensure_temp():
    Path(TEMP_DIR).mkdir(exist_ok=True)


# =====================================================
# SAFE FILE SAVE
# =====================================================

def save_uploaded_file(uploaded_file):

    ensure_temp()

    # 🔥 rewind pointer (important for DOCX)
    uploaded_file.seek(0)

    file_size_mb = len(uploaded_file.getbuffer()) / (1024 * 1024)

    if file_size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(
            f"File too large ({file_size_mb:.1f} MB). Max allowed is {MAX_FILE_SIZE_MB}MB"
        )

    unique_name = f"{uuid.uuid4()}_{uploaded_file.name}"

    path = os.path.join(TEMP_DIR, unique_name)

    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return path



# =====================================================
# LOGGER (VERY IMPORTANT IN PROD)
# =====================================================

def setup_logger():

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s — %(levelname)s — %(message)s"
    )

    return logging.getLogger("doc_comparator")


logger = setup_logger()


# =====================================================
# TIMER DECORATOR
# =====================================================

def timer(func):

    def wrapper(*args, **kwargs):

        start = time.time()

        result = func(*args, **kwargs)

        end = time.time()

        logger.info(
            f"{func.__name__} executed in {end-start:.2f}s"
        )

        return result

    return wrapper


# =====================================================
# CLEAN TEMP FILES
# =====================================================

def cleanup_temp(older_than_minutes=60):

    now = time.time()

    for file in Path(TEMP_DIR).glob("*"):

        if file.is_file():

            age = (now - file.stat().st_mtime) / 60

            if age > older_than_minutes:
                try:
                    file.unlink()
                    logger.info(f"Deleted temp file: {file}")
                except:
                    pass
