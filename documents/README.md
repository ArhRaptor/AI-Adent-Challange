# AI Agent Course — Local Knowledge Base

## Overview
This document set is a synthetic educational corpus for Day 21: document indexing.
It contains notes about AI agents, MCP, RAG, Android development, Python services, and software architecture.
The goal is to test fixed-size and structure-aware chunking, embeddings, metadata, and local indexing.

## Indexing Pipeline
A document indexing pipeline normally has four stages: loading, normalization, chunking, and embedding.
Loading reads source files. Normalization removes irrelevant formatting while preserving useful structure.
Chunking divides large documents into smaller retrieval units. Embedding converts each chunk into a vector.

## Metadata
Every chunk should preserve metadata such as source, title, section, chunk_id, and chunking strategy.
Metadata makes retrieval results explainable because the application can show where a result came from.

## Fixed Chunking
Fixed chunking divides text by a configured character or token window.
It is simple, deterministic, and works with almost any input format.
Its main weakness is that boundaries can split a paragraph, function, or logical section.

## Structured Chunking
Structured chunking uses document boundaries such as Markdown headings, classes, and functions.
It usually preserves meaning better, but requires format-specific parsing.
Large sections still need a secondary size limit.

## Embeddings
Embeddings represent text as numeric vectors.
Semantically related chunks should be closer in vector space than unrelated chunks.
An embedding index stores the vector together with the original text and metadata.

## Local Index
For this exercise JSON is used as a transparent local index.
A production system may use SQLite, FAISS, or a dedicated vector database.
JSON is convenient for inspecting the complete result during learning.

## Next Step
After indexing, the next natural step is semantic retrieval:
embed a query, compare it with document vectors, select the nearest chunks, and pass them to an LLM.
