import os
import random
import string

# Configuration
BASE_DIR = "test_files"
NUM_DIRECTORIES = 5
NUM_SUBDIRECTORIES = 3
NUM_SMALL_FILES = 10
NUM_MEDIUM_FILES = 5
NUM_LARGE_FILES = 2

# Size ranges in MB and GB
SMALL_FILE_SIZE_RANGE_MB = (1, 5)  # in megabytes
MEDIUM_FILE_SIZE_RANGE_MB = (5, 50)  # in megabytes
LARGE_FILE_SIZE_RANGE_GB = (1, 5)  # in gigabytes

def create_random_string(size):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=size))

def create_file(path, size):
    with open(path, 'wb') as f:
        f.write(os.urandom(size))

def create_files_in_dir(directory, num_files, size_range, size_unit='MB'):
    size_multiplier = 1024 * 1024 if size_unit == 'MB' else 1024 * 1024 * 1024
    for _ in range(num_files):
        filename = create_random_string(10) + ".txt"
        filepath = os.path.join(directory, filename)
        file_size = random.randint(*size_range) * size_multiplier
        create_file(filepath, file_size)

def create_directories(base_dir, num_dirs, num_subdirs, small_files, medium_files, large_files):
    for _ in range(num_dirs):
        dir_name = create_random_string(8)
        dir_path = os.path.join(base_dir, dir_name)
        os.makedirs(dir_path, exist_ok=True)
        
        create_files_in_dir(dir_path, small_files, SMALL_FILE_SIZE_RANGE_MB, 'MB')
        create_files_in_dir(dir_path, medium_files, MEDIUM_FILE_SIZE_RANGE_MB, 'MB')
        create_files_in_dir(dir_path, large_files, LARGE_FILE_SIZE_RANGE_GB, 'GB')
        
        for _ in range(num_subdirs):
            sub_dir_name = create_random_string(8)
            sub_dir_path = os.path.join(dir_path, sub_dir_name)
            os.makedirs(sub_dir_path, exist_ok=True)
            
            create_files_in_dir(sub_dir_path, small_files, SMALL_FILE_SIZE_RANGE_MB, 'MB')
            create_files_in_dir(sub_dir_path, medium_files, MEDIUM_FILE_SIZE_RANGE_MB, 'MB')
            create_files_in_dir(sub_dir_path, large_files, LARGE_FILE_SIZE_RANGE_GB, 'GB')

if __name__ == "__main__":
    os.makedirs(BASE_DIR, exist_ok=True)
    create_directories(BASE_DIR, NUM_DIRECTORIES, NUM_SUBDIRECTORIES, NUM_SMALL_FILES, NUM_MEDIUM_FILES, NUM_LARGE_FILES)
    print(f"Test files created in '{BASE_DIR}' directory.")
