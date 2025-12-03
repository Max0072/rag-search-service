from nltk.twitter import Query
from sentence_transformers import SentenceTransformer
from transformers import DataProcessor
from unstructured.chunking import Chunker
from utils import model_emb_dim
import faiss
import data_processor

class Settings:
    def __init__(self):
        self.chunker = Chunker()

        self.data_processor = data_processor.process_data
        self.query_processor = data_processor.preprocess_query123

        self.model = SentenceTransformer("all-mini")
        self.model_dim = model_emb_dim(self.model)

        self.index_cfg = {
            "type": "flat_ip",   # или "flat_l2", "hnsw", "ivf"
            "nlist": 1024,       # для IVF
            "M": 32,             # для HNSW
            "efSearch": 64,
            "efConstruction": 200,
        }
        self.index = Index()

        self.search_engine = SearchEngine(model, index)

        self.prompt_builder = PromptBuilder()

        self.LLM = LLM()

        self.history = []

    def set_model(self, model):
        self.model = model
        self.model_dim = model_emb_dim(self.model)

        self.set_index()

    def change_index_config(self, index_type=None, nlist=None, M=None, efSearch=None, efConstruction=None):
        self.index_cfg["type"] = index_type
        self.index_cfg["nlist"] = nlist
        self.index_cfg["M"] = M
        self.index_cfg["efSearch"] = efSearch
        self.index_cfg["efConstruction"] = efConstruction


    def set_index(self, index_type="flat_l2"):

        self.index_cfg["type"] = index_type

        dim = self.model_dim
        t = self.index_cfg["type"]

        if t == "flat_ip":
            return faiss.IndexFlatIP(dim)

        if t == "flat_l2":
            return faiss.IndexFlatL2(dim)

        if t == "hnsw":
            index = faiss.IndexHNSWFlat(dim, self.index_cfg.get("M", 32))
            index.hnsw.efSearch = self.index_cfg.get("efSearch", 64)
            index.hnsw.efConstruction = self.index_cfg.get("efConstruction", 200)
            return index

        if t == "ivf":
            quantizer = faiss.IndexFlatL2(dim)
            nlist = self.index_cfg.get("nlist", 1024)
            index = faiss.IndexIVFFlat(quantizer, dim, nlist)
            return index

        raise ValueError(f"Unknown index type: {t}")

    def set_search_engine(self, search_engine):
        self.search_engine = search_engine

