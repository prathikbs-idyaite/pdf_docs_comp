from loader import load_document
from comparator import smart_compare


def process(master_path, normal_path):

    master = load_document(master_path)
    normal = load_document(normal_path)

    master_text = "\n\n".join(master.values())
    normal_text = "\n\n".join(normal.values())


    return smart_compare(master_text, normal_text)
