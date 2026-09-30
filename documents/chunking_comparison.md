# Chunking Strategy Comparison

## Purpose
Chunking determines the retrieval unit of a document index.
The same source corpus can produce very different indexes depending on the chosen boundaries.
This document describes criteria for comparing fixed and structure-aware strategies.

## Fixed-Size Strategy
A fixed-size strategy moves through text with a constant window.
If the window is 1200 characters and overlap is 200 characters, neighboring chunks share context.
The strategy is format-agnostic and therefore easy to apply to Markdown, plain text, and source code.

### Advantages
The implementation is small and predictable.
Chunk sizes are relatively uniform.
Large files cannot accidentally become a single enormous chunk.

### Disadvantages
A heading can be separated from its paragraph.
A function can be divided in the middle.
A chunk may contain the end of one topic and the beginning of another.

## Structure-Aware Strategy
A structure-aware strategy first detects meaningful boundaries.
For Markdown, headings are natural section boundaries.
For source code, classes and functions can be useful boundaries.
Plain text may require paragraph or sentence heuristics.

### Advantages
Metadata can record a meaningful section name.
Retrieved chunks are easier to explain to a user.
Semantic units are more likely to remain intact.

### Disadvantages
Every file format may require different parsing rules.
Sections can vary greatly in size.
Malformed documents can produce poor boundaries.

## Hybrid Behavior
Structure-aware chunking still needs a maximum size.
If one Markdown section is extremely long, the section should be divided into smaller pieces.
The resulting chunks should keep the original section metadata.

## Comparison Metrics
Useful basic metrics include number of chunks, average characters per chunk, minimum size,
maximum size, and amount of overlap. Retrieval evaluation is more important than these statistics,
but the statistics help identify obviously bad configurations.

## Metadata Comparison
Both strategies should preserve source and title.
Fixed chunks may have no meaningful section.
Structured chunks should record the detected heading, function, class, or file-level section.
Every chunk needs a unique chunk_id.

## Reproducibility
Given the same input files and configuration, indexing should produce stable chunk identifiers
and equivalent text boundaries. Stable identifiers are useful when updating only changed documents.

## Choosing a Strategy
There is no universally best chunking strategy.
Documentation with strong headings often benefits from structure-aware splitting.
Unstructured logs may be better suited to fixed windows.
Source code benefits from syntax-aware approaches when reliable parsers are available.

## Course Experiment
For the Day 21 exercise, both indexes are generated from the same corpus.
This makes the comparison fair: the documents and embedding model remain constant while the chunking
strategy changes. The generated JSON can then be inspected directly.


# Extended Study Notes

## Review 1
This review section reinforces the concepts from chunking_comparison.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. ## Review 1
This review section reinforces the concepts from chunking_comparison.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. 

## Review 2
This review section reinforces the concepts from chunking_comparison.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. ## Review 2
This review section reinforces the concepts from chunking_comparison.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. 

## Review 3
This review section reinforces the concepts from chunking_comparison.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. ## Review 3
This review section reinforces the concepts from chunking_comparison.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. 

## Review 4
This review section reinforces the concepts from chunking_comparison.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. ## Review 4
This review section reinforces the concepts from chunking_comparison.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. 

## Review 5
This review section reinforces the concepts from chunking_comparison.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. ## Review 5
This review section reinforces the concepts from chunking_comparison.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. 

## Review 6
This review section reinforces the concepts from chunking_comparison.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. ## Review 6
This review section reinforces the concepts from chunking_comparison.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. 