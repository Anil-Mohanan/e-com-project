import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# ======== CLIENT FACTORIES =========== #

# These functions create the external service clients Only when called
# This is called 'Lazy initializtion' - we don't connect to pinecode at django startup,
#only when the first embedding task actaully runs

def _get_pinecone_index():
       from pinecone import Pinecone

       pc = Pinecone(api_key = settings.PINECONE_API_KEY)
       #Pinecode() created the client using api_key

       return pc.Index("products")
       #Index("products") connects to the specific index created in  pinecone dashboard
       # 

def _get_embedding(text: str) -> list[float]:
       from huggingface_hub import InferenceClient
       # InferenceClient is the HTTP client for HuggingFace's free hosted models

       client = InferenceClient(token = settings.HUGGINGFACE_API_KEY)

       result = client.feature_extraction(
              text,
              model =  'sentence-transformers/all-MiniLM-L6-v2'
              # This model conversts text -> a list of 384 float numbers(The vector)
       )

       return result[0].tolist()
       #result[0] is the embedding for the first (and only ) sentence
       # .tolist() converts the numpy array to a plain Python list that Pinecone accepts


#========= CORE OPERATIONS ======= #

def upsert_product_embedding(product_id:int, name: str, brand:str, description:str) -> None:
       """
       Called by the celery task when product is created or updated.
       Converts product text into a vector and saves it to pinecone.
       'upsert' = insert if new, update if already exists (no duplicates)

       """

       try:
              text = f"{name} . Brand: {brand}. {description}"

              # combine name + brand + descripton into one string.
              # this is the document feed to the semantic matching. 
              # The richer the text the more accurate the semantic mathincg.

              vector = _get_embedding(text)
              # vector is now a list of 384 floats, eg. [0.12, -0.45, 0.88,...]

              index = _get_pinecone_index()
              index.upsert(vectors=[{
                     "id": str(product_id),
                     #Pinecode requried the ID To be a string
                     "values": vector, 
                     # The 384-number embedding
                     "metadata": {"product_id": product_id, "name": name}
                     # metadata is stored alongside the vector
              }])

              logger.info(f"Upserted embedding for product_id{product_id} ('{name}')")

       except Exception as e:
              logger.error(f'Failed to upsert embedding for product_id={product_id}: {e}',exc_info=True)

              # exc_info = True logs the full traceback - ciritcal for debugging API failures

def semantic_search(query: str, top_k: int = 5) -> list[int]:

       """
       Called by the search service when redis cahce return no reuslts
       conversts the user's search query to a vector, then ask pinecone
       for the 'top_k' most matematically similar product vectors.
       Returns a list of product_ids from postgresql
       """

       try:
              query_vector = _get_embedding(query)
              # Same model, same process - now we embed the user's search string

              index = _get_pinecone_index()
              results = index.query(
                     vector = query_vector, 
                     top_k =top_k,# top_k = 5 means "give me the most 5 most simller products"
                     include_metadata= True # include_metadata=True returns the metadata dict we stored during upsert
              )
              product_ids = [int(match.id) for match in results.matches]

              # results["matches"] is a list of the cloese vectors
              # each match has an "ID" which is product_id (as stirng, so we cast to int)

              logger.info(f"Semantic Search for '{query}' returned {len(product_ids)} results ")
              return product_ids
       except Exception as e:
              logger.error(f"Semantic search failed for query = '{query}': {e}", exc_info=True)
              return []
              # return empty list on failure - the caller handles the empty case gracefully
