from openai import OpenAI

# valid inputs
VALID_MODELS: list[str] = ["text-embedding-3-small", "text-embedding-3-large"]
VALID_METRICS: list[str] = ["euclidean", "cosine", "dotproduct"]
VALID_DIMENSIONS: dict[str, int] = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072
}


def format_list(lst: list[str]) -> str: 
    """Format a list of strings as 'item1', 'item2', 'item3', ..."""
    return "'" + "', '".join(lst) + "'"


class Embedder():
    """
    Class to handle text embeddings using OpenAI's embedding models
    """
    def __init__(
            self, 
            client: OpenAI = None,
            model_name: str = "text-embedding-3-small", 
            dim: int = 1536, 
            metric: str = "cosine"
        ) -> None:
        """
        Create a new Embedder
        
        Args:
            model_name: Name of the OpenAI embedding model to use: "text-embedding-3-small", "text-embedding-3-large"
            dim: Dimension of the embeddings
            metric: Metric to use for similarity search in Pinecone: "euclidean", "cosine", or "dotproduct"
        """
        self.client: OpenAI = client
        self.model_name: str = model_name
        self.dim: int = dim
        self.metric: str = metric

        # validate inputs
        if client is None:
            raise ValueError("OpenAI client is required")
        if model_name not in VALID_MODELS:
            raise ValueError(f"Invalid model name: {model_name}. Valid model names are: {format_list(VALID_MODELS)}")
        if metric not in VALID_METRICS:
            raise ValueError(f"Invalid metric: {metric}. Valid metrics are: {format_list(VALID_METRICS)}")
        if dim > VALID_DIMENSIONS[model_name] or dim < 1:
            raise ValueError(f"Invalid dimension for model {model_name}: {dim}. Valid dimensions in range: [1, {VALID_DIMENSIONS[model_name]}]")


    def __str__(self) -> str:
        return f"Embedder(model_name={self.model_name}, dim={self.dim}, metric={self.metric})"


    def __repr__(self) -> str:
        return self.__str__()


    def embed_text(self, text: str) -> list[float]:
        """Embed a given text using the selected model"""
        text = text.replace("\n", " ")
        try:
            embedding = self.client.embeddings.create(input = [text], model=self.model_name).data[0].embedding
        except Exception as e:
            print(f"Error embedding text: {str(e)}")
            raise
        return embedding


    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts using the selected model"""
        texts = [text.replace("\n", " ") for text in texts]
        try:
            embeddings = self.client.embeddings.create(input = texts, model=self.model_name).data
        except Exception as e:
            print(f"Error embedding batch of texts: {str(e)}")
            raise
        return embeddings
    

    def normalize_l2(self, x: list[float]) -> list[float]:
        """Normalize a list of floats to have L2 norm of 1"""
        try:
            import numpy as np
        except:
            raise ImportError("This function requires numpy to be installed")
        x = np.array(x)
        if x.ndim == 1:
            norm = np.linalg.norm(x)
            if norm == 0:
                return x
            out = x / norm
            return out.tolist()
        else:
            norm = np.linalg.norm(x, 2, axis=1, keepdims=True)
            return np.where(norm == 0, x, x / norm).tolist()