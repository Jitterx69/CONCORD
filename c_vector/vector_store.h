#ifndef VECTOR_STORE_H
#define VECTOR_STORE_H

#include <stddef.h>

typedef struct {
  float *data;
  size_t dimension;
} Vector;

typedef struct {
  Vector *vectors;
  size_t count;
  size_t capacity;
} VectorStore;

// Initialize a new store
VectorStore *vs_create(size_t initial_capacity);

// Add a vector to the store (copies data)
void vs_add(VectorStore *store, float *data, size_t dim);

// Calculate dot product
float vs_dot_product(float *v1, float *v2, size_t dim);

// Find index of most similar vector (cosine similarity)
int vs_find_nearest(VectorStore *store, float *query, size_t dim);

// Free memory
void vs_free(VectorStore *store);

#endif
