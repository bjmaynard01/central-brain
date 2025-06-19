#!/usr/bin/env python3

import argparse
import os
import uuid
import json
import requests
import psycopg2
from psycopg2.extras import execute_values

# ---- Config ----
OLLAMA_EMBED_URL = "http://ollama:11434/api/embeddings"
VECTORDB_CONN = "postgresql://postgres:password@vectordb:5432/postgres"

# ---- Chunker (simple paragraph split for now) ----
def chunk_text(text, max_words=200):
    paragraphs = text.split('\n\n')
    chunks = []
    for p in paragraphs:
        words = p.split()
        for i in range(0, len(words), max_words):
            chunk = ' '.join(words[i:i + max_words]).strip()
            if chunk:
                chunks.append(chunk)
    return chunks

# ---- Embed a list of texts ----
def embed_chunks(chunks):
    response = requests.post(OLLAMA_EMBED_URL, json={"model": "nomic-embed-text", "prompt": chunks})
    response.raise_for_status()
    return response.json().get("embeddings", [])

# ---- Insert chunks into Postgres ----
def insert_chunks(doc_id, chunks, embeddings, source="manual_upload"):
    conn = psycopg2.connect(VECTORDB_CONN)
    with conn:
        with conn.cursor() as cur:
            data = [
                (str(uuid.uuid4()), doc_id, i, chunk, json.dumps(embed), None, source)
                for i, (chunk, embed) in enumerate(zip(chunks, embeddings))
            ]
            execute_values(cur, """
                INSERT INTO vectors (id, doc_id, chunk_index, content, embedding, user_id, source)
                VALUES %s
            """, data)
    conn.close()

# ---- Delete document by doc_id ----
def delete_doc(doc_id):
    conn = psycopg2.connect(VECTORDB_CONN)
    with conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM vectors WHERE doc_id = %s", (doc_id,))
    conn.close()
    print(f"Deleted document: {doc_id}")

# ---- Main CLI ----
def main():
    parser = argparse.ArgumentParser(description="Manage document ingestion for LibreChat RAG")
    subparsers = parser.add_subparsers(dest="command")

    # Upload command
    upload = subparsers.add_parser("upload")
    upload.add_argument("path", help="Path to file (txt, md) or folder")

    # Delete command
    delete = subparsers.add_parser("delete")
    delete.add_argument("doc_id", help="Document ID to delete")

    args = parser.parse_args()

    if args.command == "upload":
        path = args.path
        files = []
        if os.path.isdir(path):
            for fname in os.listdir(path):
                if fname.endswith(('.txt', '.md')):
                    files.append(os.path.join(path, fname))
        else:
            files.append(path)

        for fpath in files:
            with open(fpath, 'r', encoding='utf-8') as f:
                text = f.read()
            chunks = chunk_text(text)
            embeddings = embed_chunks(chunks)
            doc_id = str(uuid.uuid4())
            insert_chunks(doc_id, chunks, embeddings)
            print(f"Uploaded: {fpath} as doc_id={doc_id}")

    elif args.command == "delete":
        delete_doc(args.doc_id)

if __name__ == "__main__":
    main()