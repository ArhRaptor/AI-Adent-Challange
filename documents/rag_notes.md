# Retrieval-Augmented Generation

## Why RAG Exists
A language model does not automatically know private project documentation or newly created local files.
Retrieval-Augmented Generation, usually shortened to RAG, adds an external knowledge retrieval step.
Instead of asking the model to rely only on its internal parameters, the application searches a document index
and places relevant passages into the prompt.

## Ingestion
The ingestion phase prepares knowledge before users ask questions.
Files are discovered, read, normalized, split into chunks, embedded, and stored.
Ingestion can be performed once for static documents or repeatedly when a knowledge base changes.

## Chunk Size
Chunk size affects both retrieval precision and context completeness.
Very small chunks may match a query precisely but omit surrounding explanation.
Very large chunks preserve context but may contain several unrelated topics and waste model context.
A practical system evaluates chunk size on representative queries rather than assuming one universal value.

## Chunk Overlap
Overlap repeats a small portion of text between neighboring chunks.
It reduces the chance that an important sentence is lost at a hard boundary.
Too much overlap increases storage, embedding cost, and duplicate retrieval results.

## Retrieval
At query time the user question is embedded with a compatible embedding model.
The application compares the query vector with stored vectors.
The highest-scoring chunks become retrieval candidates.
Metadata filters can narrow results by file, product, date, section, or document type.

## Ranking
Vector similarity is only one ranking signal.
Systems may combine semantic similarity with keyword search, recency, permissions, or reranking models.
The correct ranking strategy depends on the application and evaluation data.

## Context Construction
Retrieved chunks should be clearly separated and accompanied by source metadata.
The prompt should distinguish retrieved evidence from user instructions.
Applications should avoid inserting an unlimited number of chunks because irrelevant context can reduce answer quality.

## Evaluation
A RAG system should be tested with known questions and expected source passages.
Useful metrics include retrieval recall, ranking quality, answer groundedness, latency, and cost.
Manual inspection remains important during early development.

## Failure Modes
Common failures include missing documents, poor text extraction, chunks that are too large,
chunks that are too small, inconsistent embeddings, duplicate content, and stale indexes.
Another failure is retrieving a relevant document but the wrong section of that document.

## Local Development
A local JSON index is useful for understanding the data model.
Each record can contain text, embedding, source, title, section, chunk_id, and strategy.
Later the same conceptual records can be migrated to SQLite, FAISS, or another vector store.


# Extended Study Notes

## Review 1
This review section reinforces the concepts from rag_notes.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. ## Review 1
This review section reinforces the concepts from rag_notes.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. 

## Review 2
This review section reinforces the concepts from rag_notes.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. ## Review 2
This review section reinforces the concepts from rag_notes.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. 

## Review 3
This review section reinforces the concepts from rag_notes.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. ## Review 3
This review section reinforces the concepts from rag_notes.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. 

## Review 4
This review section reinforces the concepts from rag_notes.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. ## Review 4
This review section reinforces the concepts from rag_notes.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. 

## Review 5
This review section reinforces the concepts from rag_notes.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. ## Review 5
This review section reinforces the concepts from rag_notes.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. 

## Review 6
This review section reinforces the concepts from rag_notes.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. ## Review 6
This review section reinforces the concepts from rag_notes.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. 